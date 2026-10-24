"""Pipeline local/CI: fixa imagem base, constrói contêiner e confere inferência HTTP."""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import shutil
import subprocess
import time
import urllib.request
import urllib.error
import uuid
from auditar_distribuicao import PROJECT, check_files, child, read_json, sha, write_json


def execute(args, log):
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding='utf-8', errors='replace')
    with log.open('a', encoding='utf-8') as stream:
        stream.write('\n' + subprocess.list2cmdline(args) + '\n' + result.stdout)
    if result.returncode:
        raise RuntimeError(f'Comando falhou ({result.returncode}). Log: {log}\n{result.stdout[-3000:]}')
    return result.stdout.strip()


def http(url, payload=None):
    data = None if payload is None else json.dumps(payload, allow_nan=False).encode()
    request = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=4) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def compare_response(reference, response, tolerance):
    if set(reference) != set(response):
        raise ValueError('Campos da resposta divergem da referência.')
    for key in reference:
        if key == 'p_event':
            actual = float(response[key])
            equal = math.isfinite(actual) and math.isclose(float(reference[key]), actual, rel_tol=0, abs_tol=tolerance)
        else:
            equal = reference[key] == response[key]
        if not equal:
            raise ValueError(f'Resposta mudou em {key}: {reference[key]!r} -> {response[key]!r}. Migração não aprovada.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--context', type=Path)
    parser.add_argument('--output-root', type=Path, default=PROJECT / 'reports/containers/CJU_BA5EIGT/h24_event_v1')
    args = parser.parse_args()
    if args.context is None:
        root = PROJECT / 'dist/container_service'
        pointer = read_json(root / 'latest_context.json')
        context = child(root, pointer['directory'])
        if sha(context / 'context.json') != pointer['context_sha256']:
            raise ValueError('Hash do contexto não corresponde ao ponteiro.')
    else:
        context = args.context.resolve()
    metadata = read_json(context / 'context.json')
    if metadata['schema'] != 'renewcast-container-context-v1':
        raise ValueError('Contrato de contexto desconhecido.')
    check_files(context, metadata['files_sha256'])
    if not shutil.which('docker'):
        raise RuntimeError('Docker não encontrado. Instale/abra Docker Desktop com contêineres Linux; confira docker info. O contexto preparado foi preservado.')
    output = args.output_root.resolve() / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8])
    output.mkdir(parents=True)
    log = output / 'pipeline.log'
    if execute(['docker', 'info', '--format', '{{.OSType}}'], log) != 'linux':
        raise ValueError('Este exercício exige o mecanismo Docker de contêineres Linux.')
    # Um lock separado do contexto conserva o digest entre reconstruções e pode viajar com ele.
    lock_path = context / 'base_image.lock.json'
    if lock_path.exists():
        base = read_json(lock_path)
        if base['context_sha256'] != sha(context / 'context.json'):
            raise ValueError('Lock da imagem base pertence a outro contexto.')
        digest = base['digest']
        if '@sha256:' not in digest:
            raise ValueError('Imagem base precisa de digest.')
        execute(['docker', 'pull', '--platform', 'linux/amd64', digest], log)
    else:
        tag = metadata['base_image_tag']
        print(f'Obtendo imagem base {tag}...', flush=True)
        execute(['docker', 'pull', '--platform', 'linux/amd64', tag], log)
        image = json.loads(execute(['docker', 'image', 'inspect', tag], log))[0]
        digests = image.get('RepoDigests', [])
        if not digests:
            raise ValueError('A imagem base não possui digest de repositório.')
        digest = digests[0]
        write_json(lock_path, {'digest': digest, 'tag': tag, 'context_sha256': sha(context / 'context.json')})
    image_tag = 'renewcast-event:' + uuid.uuid4().hex[:12]
    print('Construindo imagem Linux e capturando wheels compatíveis; pode levar alguns minutos...', flush=True)
    execute(['docker', 'build', '--platform', 'linux/amd64', '--build-arg', f'PYTHON_BASE={digest}', '-t', image_tag, str(context)], log)
    image = json.loads(execute(['docker', 'image', 'inspect', image_tag], log))[0]
    write_json(output / 'image.json', image)
    print('Executando API pelo ID da imagem; porta publicada somente no computador local...', flush=True)
    container_id = execute(['docker', 'run', '-d', '--read-only', '--tmpfs', '/tmp:rw,size=64m',
                            '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                            '-p', '127.0.0.1::8000', image['Id']], log)
    try:
        info = json.loads(execute(['docker', 'inspect', container_id], log))[0]
        binding = info['NetworkSettings']['Ports']['8000/tcp'][0]
        address = 'http://127.0.0.1:' + binding['HostPort']
        deadline = time.monotonic() + 90
        while True:
            try:
                code, health = http(address + '/health')
                if code == 200 and health.get('model_loaded'):
                    break
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                pass
            state = json.loads(execute(['docker', 'inspect', container_id], log))[0]['State']
            if not state['Running'] or time.monotonic() > deadline:
                raise RuntimeError('API não iniciou no contêiner. Consulte server.log e pipeline.log.')
            time.sleep(0.5)
        request = read_json(context / 'artifacts/example_request.json')
        reference = read_json(context / 'reference_response.json')
        code, response = http(address + '/predict-decision', request)
        if code != 200:
            raise ValueError(f'HTTP {code} no pedido válido: {response}')
        compare_response(reference, response, metadata['probability_tolerance'])
        bad = copy.deepcopy(request)
        del bad['features'][next(iter(bad['features']))]
        bad_code, bad_response = http(address + '/predict-decision', bad)
        if bad_code != 422:
            raise ValueError('Feature ausente não foi recusada com 422.')
        probe = "import json,platform,importlib.metadata as m; x=json.load(open('/app/context.json')); print(json.dumps({'python':platform.python_version(),'system':platform.system(),'dependencies':{n:m.version(n) for n in x['dependencies']}}))"
        environment = json.loads(execute(['docker', 'exec', container_id, 'python', '-c', probe], log))
        if environment['dependencies'] != metadata['dependencies'] or environment['python'] != metadata['python_version']:
            raise ValueError('Versões da imagem divergem das capturadas.')
        linux_lock = execute(['docker', 'exec', container_id, 'cat', '/requirements.linux.lock'], log)
        (output / 'requirements.linux.lock').write_text(linux_lock + '\n', encoding='utf-8')
        write_json(output / 'environment.json', environment)
        write_json(output / 'response.json', response)
        write_json(output / 'rejected_request.json', {'status_code': bad_code, 'response': bad_response})
    finally:
        logs = subprocess.run(['docker', 'logs', container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (output / 'server.log').write_bytes(logs.stdout)
        subprocess.run(['docker', 'rm', '-f', container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    receipt = {
        'verified': True, 'source_release_id': metadata['source_release_id'], 'context_id': metadata['context_id'],
        'context_sha256': sha(context / 'context.json'), 'base_image_digest': digest,
        'base_image_lock_sha256': sha(lock_path), 'image_id': image['Id'], 'image_size_bytes': image['Size'],
        'controller_sha256': sha(Path(__file__)), 'platform': 'linux/amd64',
        'model_sha256': response['model_sha256'], 'policy_sha256': response['policy_sha256'],
        'reference_probability': reference['p_event'], 'container_probability': response['p_event'],
        'absolute_difference': abs(reference['p_event'] - response['p_event']),
        'valid_request_status': code, 'invalid_request_status': bad_code, 'model_retrained': False,
        'scope': 'Linux container compatibility for one request; no load test or operational approval',
        'output_sha256': {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()},
    }
    write_json(output / 'verification.json', receipt)
    write_json(args.output_root.resolve() / 'latest_run.json', {'directory': str(output), 'verification_sha256': sha(output / 'verification.json')})
    print(f'HTTP 200/422; diferença={receipt["absolute_difference"]:.3g}; imagem={image["Id"]}')
    print(f'Compatibilidade do contêiner aprovada no protocolo. Evidências: {output}')


if __name__ == '__main__':
    main()
