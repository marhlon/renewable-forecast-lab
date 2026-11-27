"""Reconfere em arquivo novo, preservando o recibo registrado no cadastro."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,subprocess,sys,uuid
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reports/fechamento_m00_m09/bloco3_engenharia'
def main():
    original=BASE/'auditoria_bloco3.json'
    before=hashlib.sha256(original.read_bytes()).hexdigest()
    output=BASE/'reverificacoes'/f'{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}_{uuid.uuid4().hex[:8]}.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    command=[sys.executable,'-X','utf8',str(ROOT/'scripts/auditar_bloco3.py'),'--output',str(output)]
    result=subprocess.run(command,cwd=ROOT,check=False)
    if hashlib.sha256(original.read_bytes()).hexdigest()!=before:
        raise RuntimeError('Auditoria original foi alterada; preservar evidência antes de continuar.')
    print(f'Recibo original preservado. Nova conferência: {output}')
    return result.returncode
if __name__=='__main__':raise SystemExit(main())
