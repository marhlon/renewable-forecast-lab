"""Gera contexto Docker a partir de um release com reprodução aprovada; não exige Docker."""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import uuid
from auditar_distribuicao import PROJECT, load_bundle, sha, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-dir', type=Path, default=PROJECT)
    args = parser.parse_args()
    project = args.project_dir.resolve()
    release, manifest, run, receipt = load_bundle(project)
    root = project / 'dist/container_service'
    context_id = manifest['release_id'] + '_' + uuid.uuid4().hex[:8]
    output = root / context_id
    output.mkdir(parents=True)
    template = PROJECT / 'deploy/container_template'
    for name in ('Dockerfile', 'serve.py', 'lock_linux.py'):
        shutil.copy2(template / name, output / name)
    candidates = list((release / 'wheelhouse').glob('renewcast_event_service-*-py3-none-any.whl'))
    if len(candidates) != 1:
        raise ValueError('Esperado exatamente um wheel Python puro do serviço.')
    shutil.copy2(candidates[0], output / 'service.whl')
    shutil.copytree(release / 'artifacts', output / 'artifacts')
    shutil.copy2(release / 'reference_response.json', output / 'reference_response.json')
    pins = {k: v for k, v in manifest['dependencies'].items() if k != 'renewcast-event-service'}
    (output / 'requirements.versions.txt').write_text(''.join(f'{k}=={v}\n' for k,v in sorted(pins.items())), encoding='utf-8')
    py_version = manifest['platform']['python']
    write_json(output / 'context.json', {
        'schema': 'renewcast-container-context-v1', 'context_id': context_id,
        'source_release_id': manifest['release_id'], 'source_release_sha256': sha(release / 'release.json'),
        'source_verification_sha256': sha(run / 'verification.json'),
        'python_version': py_version, 'base_image_tag': f'python:{py_version}-slim-bookworm',
        'platform': 'linux/amd64', 'dependencies': manifest['dependencies'],
        'model_sha256': receipt['model_sha256'], 'policy_sha256': receipt['policy_sha256'],
        'probability_tolerance': 1e-12, 'model_retrained': False,
        'files_sha256': {p.relative_to(output).as_posix(): sha(p) for p in sorted(output.rglob('*')) if p.is_file()},
    })
    write_json(root / 'latest_context.json', {'directory': context_id, 'context_sha256': sha(output / 'context.json')})
    print(f'Contexto preparado: {output}')
    print(f'Imagem base solicitada: python:{py_version}-slim-bookworm; destino linux/amd64.')
    print('Modelo/política preservados. Wheels Windows não foram copiados para o contexto.')
    print('Preparação concluída; build e execução Docker continuam pendentes.')


if __name__ == '__main__':
    main()
