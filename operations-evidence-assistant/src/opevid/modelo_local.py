"""Baixa apenas arquivos públicos fixados; o texto dos casos fica local."""
from __future__ import annotations

from hashlib import file_digest, sha256
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

REPO = "HuggingFaceTB/SmolLM2-135M-Instruct"
REV = "12fd25f77366fa6b3b4b768ec3050bf629380bac"
FILES = {"README.md", "config.json", "generation_config.json", "special_tokens_map.json",
         "tokenizer.json", "tokenizer_config.json", "model.safetensors"}


def sha(path):
    with path.open("rb") as f:
        return file_digest(f, "sha256").hexdigest()


def obter_snapshot(lock_path: Path, cache: Path, *, baixar: bool):
    lock = json.loads(lock_path.read_bytes())
    if (lock["schema"] != "opevid-m11-1-model-lock-v1" or lock["repository"] != REPO
            or lock["revision"] != REV or set(lock["files"]) != FILES):
        raise ValueError("A identificação do modelo não corresponde à revisão da aula.")
    if baixar:
        cache.mkdir(parents=True, exist_ok=True)
    for name, expected in lock["files"].items():
        path = cache / name
        if path.is_file() and path.stat().st_size == expected["bytes"] and sha(path) == expected["sha256"]:
            continue
        if not baixar:
            raise ValueError(f"Arquivo ausente ou não corresponde ao manifesto: {path}")
        print(f"Obtendo {name} ({expected['bytes']/(1024**2):.2f} MiB)...", flush=True)
        url = f"https://huggingface.co/{REPO}/resolve/{REV}/{name}?download=true"
        temp_path = None
        try:
            h = sha256()
            count = 0
            progress_step = 32 * 1024**2
            next_progress = progress_step
            with NamedTemporaryFile(dir=cache, suffix=".part", delete=False) as tmp:
                temp_path = Path(tmp.name)
                with urlopen(url, timeout=60) as source:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        count += len(chunk)
                        if count > expected["bytes"]:
                            raise ValueError(f"Tamanho inesperado em {name}.")
                        tmp.write(chunk)
                        h.update(chunk)
                        if count >= next_progress:
                            print(f"  {count/(1024**2):.0f}/{expected['bytes']/(1024**2):.0f} MiB", flush=True)
                            next_progress += progress_step
            if count != expected["bytes"] or h.hexdigest() != expected["sha256"]:
                raise ValueError(f"Download não confere com o manifesto: {name}.")
            temp_path.replace(path)
        finally:
            if temp_path:
                temp_path.unlink(missing_ok=True)
    return cache, lock
