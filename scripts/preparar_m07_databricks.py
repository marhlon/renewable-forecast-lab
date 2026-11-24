"""Prepara os tres arquivos locais usados na aula M07.3; nao inicia Spark.

Na raiz: python scripts/preparar_m07_databricks.py
Entrada original e treino aceito permanecem inalterados.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from datetime import datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


PROJECT = Path(__file__).resolve().parents[1]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parquet_bytes(table: pa.Table) -> bytes:
    buffer = io.BytesIO()
    pq.write_table(table, buffer, compression="snappy", version="2.6")
    return buffer.getvalue()


def preparar(generation: Path, training: Path, snapshot: Path, notebook: Path, output: Path):
    parts = sorted(training.glob("*.parquet")) if training.is_dir() else [training]
    sources = [generation, snapshot, notebook, *parts]
    if not parts or any(not p.is_file() for p in sources):
        raise FileNotFoundError("Falta entrada, treino, snapshot ou notebook; confira os caminhos exibidos no --help.")
    originals = {str(p.resolve()): sha(p.read_bytes()) for p in sources}
    params = json.loads(snapshot.read_text(encoding="utf-8-sig"))
    if params.get("schema") != "renewcast-training-snapshot-v1":
        raise ValueError("Use snapshot_treino.json do laboratorio Delta concluido.")
    expected = {"horizon_hours": 24, "availability_delay_hours_assumed": 2,
                "window_hours": 6, "cutoff": "2026-07-11T06:00:00", "rows": 7485}
    for key, value in expected.items():
        if params.get(key) != value:
            raise ValueError(f"Este recorte M07.3 espera {key}={value!r}; recebido {params.get(key)!r}.")
    cutoff = datetime.fromisoformat(params["cutoff"])
    gen = pq.read_table(generation, columns=["din_instante", "val_geracao"])
    dtype = gen.schema.field("din_instante").type
    if not pa.types.is_timestamp(dtype) or dtype.tz is not None:
        raise ValueError("din_instante deve ser timestamp sem fuso. Nao converter o eixo silenciosamente.")
    gen = gen.cast(pa.schema([("din_instante", pa.timestamp("us")), ("val_geracao", pa.float64())]))
    gen = gen.sort_by("din_instante")
    times = gen["din_instante"].to_pylist()
    values = gen["val_geracao"].to_pylist()
    if len(times) != 8760 or any(t is None for t in times) or len(set(times)) != len(times):
        raise ValueError("A aula espera a serie aceita de 8760 timestamps unicos/preenchidos.")
    if any(t.minute or t.second or t.microsecond for t in times):
        raise ValueError("Existe timestamp fora da hora cheia.")
    if any((b-a).total_seconds() != 3600 for a,b in zip(times,times[1:])):
        raise ValueError("Este recorte aceito deve ter grade horaria completa.")
    if any(v is not None and not math.isfinite(v) for v in values):
        raise ValueError("Geracao nao finita na entrada.")

    train = pa.concat_tables([pq.read_table(p) for p in parts]).sort_by([("serie","ascending"),("forecast_origin","ascending")])
    if train.num_rows != params["rows"]:
        raise ValueError("Contagem de treino diverge do snapshot aceito.")
    timestamp_columns = ["forecast_origin", "history_end", "target_time", "target_available_at"]
    for name in timestamp_columns:
        typ = train.schema.field(name).type
        if not pa.types.is_timestamp(typ) or typ.tz is not None:
            raise ValueError(f"{name}: esperado timestamp sem fuso.")
    keys = list(zip(train["serie"].to_pylist(),train["forecast_origin"].to_pylist()))
    if len(set(keys)) != len(keys):
        raise ValueError("Chave de treino duplicada.")
    for row in train.select(["features_validas","target_generation","target_available_at"]).to_pylist():
        if row["features_validas"] is not True or row["target_generation"] is None or row["target_available_at"] is None or row["target_available_at"] >= cutoff:
            raise ValueError("Treino de referencia viola o contrato temporal.")

    payloads = {"geracao.parquet": parquet_bytes(gen), "treino_referencia.parquet": parquet_bytes(train)}
    contract = {
        "schema": "renewcast-databricks-input-v1", "conjunto": "CJU_BA5EIGT",
        "parameters": {k: params[k] for k in expected if k != "rows"},
        "generation_rows": gen.num_rows, "training_rows": train.num_rows,
        "files": {name: {"sha256": sha(data), "bytes": len(data)} for name,data in payloads.items()},
        "distributed_notebook_sha256": sha(notebook.read_bytes()),
        "historical_source_versions_verified": False, "availability_is_assumed": True,
    }
    encoded = json.dumps(contract,sort_keys=True,separators=(",", ":"),ensure_ascii=False).encode()
    contract["package_id"] = sha(encoded)
    contract["preparation_sources_sha256"] = originals
    payloads["manifesto_entrada.json"] = (json.dumps(contract,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode()
    output = output.resolve()
    if output.exists() and any(output.iterdir()):
        for name,data in payloads.items():
            path = output/name
            if not path.is_file() or path.read_bytes() != data:
                raise ValueError(f"Destino ja existe com outro conteudo: {output}. Use --output-dir explicito para outro recorte.")
        print("Pacote existente conferido; nenhuma copia nova.")
    else:
        output.mkdir(parents=True,exist_ok=True)
        for name,data in payloads.items():
            (output/name).write_bytes(data)
    if any(sha(Path(name).read_bytes()) != digest for name,digest in originals.items()):
        raise ValueError("Uma entrada mudou durante a preparacao.")
    print(f"Geracao: {gen.num_rows}; treino de referencia: {train.num_rows}; pacote: {contract['package_id'][:12]}")
    print(f"Envie SOMENTE estes tres arquivos para o volume indicado no notebook:")
    for name in payloads:
        print(output/name)
    print(f"Notebook a importar no Workspace: {notebook.resolve()}")
    return contract


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation",type=Path,default=PROJECT/"data/interim/CJU_BA5EIGT_hourly.parquet")
    parser.add_argument("--training",type=Path,default=PROJECT/"reports/scale/CJU_BA5EIGT/laboratorio_temporal/treino_autoria.parquet")
    parser.add_argument("--snapshot",type=Path,default=PROJECT/"reports/scale/CJU_BA5EIGT/m07_2_delta/snapshot_treino.json")
    parser.add_argument("--notebook",type=Path,default=PROJECT/"notebooks/databricks/m07_3_reproducao.ipynb")
    parser.add_argument("--output-dir",type=Path,default=PROJECT/"dist/databricks/CJU_BA5EIGT/m07_3")
    args=parser.parse_args(argv)
    try:
        preparar(args.generation,args.training,args.snapshot,args.notebook,args.output_dir)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        parser.exit(1,f"Erro: {exc}\n")


if __name__ == "__main__":
    main()
