"""Executado no estágio Linux: preserva versões e registra hashes dos novos wheels."""
from email.parser import BytesParser
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import zipfile

def metadata(path):
    with zipfile.ZipFile(path) as archive:
        names = [n for n in archive.namelist() if n.endswith('.dist-info/METADATA')]
        if len(names) != 1:
            raise ValueError('METADATA deve ser único')
        return BytesParser().parsebytes(archive.read(names[0]))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--service', type=Path, default=Path('/service.whl'))
    parser.add_argument('--wheel-dir', type=Path, default=Path('/wheels'))
    parser.add_argument('--output', type=Path, default=Path('/requirements.linux.lock'))
    args = parser.parse_args()
    info = metadata(args.service)
    normalized = re.sub(r'[-_.]+', '_', info['Name'])
    target = args.wheel_dir / f"{normalized}-{info['Version']}-py3-none-any.whl"
    if args.service.resolve() != target.resolve():
        shutil.copy2(args.service, target)
    lines = []
    seen = set()
    for path in sorted(args.wheel_dir.glob('*.whl')):
        info = metadata(path)
        name = re.sub(r'[-_.]+', '-', info['Name']).lower()
        if name in seen:
            raise ValueError(f'Wheel duplicado: {name}')
        seen.add(name)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{name}=={info['Version']} --hash=sha256:{digest}\n")
    args.output.write_text(''.join(lines), encoding='utf-8')

if __name__ == '__main__':
    main()
