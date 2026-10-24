"""M04.1: cadastro ONS/ANEEL para localizar as usinas de um conjunto.

Salvar em src/renewable_forecast/asset_registry.py.
Preserva fontes, normaliza CEG e entrega uma linha por usina, sem treino.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd


SOURCES = {
    "relationships": "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/usina_conjunto/RELACIONAMENTO_USINA_CONJUNTO.csv",
    "capacity": "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/capacidade-geracao/CAPACIDADE_GERACAO.csv",
    "siga_daily": "https://dadosabertos.aneel.gov.br/dataset/6d90b77c-c5f5-4d81-bdec-7bc619494bb9/resource/2f65a1b0-19b8-4360-8238-b34ab4693d55/download/siga-empreendimentos-geracao-diario.csv",
}


def canonical_ceg(values: pd.Series) -> pd.Series:
    """Normaliza apenas zeros à esquerda do sufixo: .01 e .1 viram .1.

    Preserva tipo, regime, UF, núcleo, dígito e valor numérico do sufixo.
    Não remove a versão nem usa similaridade de nomes como chave.
    """
    parts = values.astype("string").str.strip().str.upper().str.extract(
        r"^([A-Z]{3}\.[A-Z]{2}\.[A-Z]{2}\.\d{6}-\d)\.(\d+)$"
    )
    suffix = pd.to_numeric(parts[1], errors="raise").astype("Int64").astype("string")
    return parts[0] + "." + suffix


def read_source_csv(raw: bytes) -> pd.DataFrame:
    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = raw.decode("cp1252")
    data = pd.read_csv(io.StringIO(decoded), sep=";", dtype="string")
    for column in data:
        data[column] = data[column].str.strip().replace("", pd.NA)
    return data


def fetch_source(name, output, *, refresh=False):
    """Cache da resposta original com URL, horário de coleta e hash."""
    raw_path = output / "raw" / f"{name}.csv"
    info_path = output / "raw" / f"{name}.metadata.json"
    if raw_path.exists() and info_path.exists() and not refresh:
        raw = raw_path.read_bytes()
        info = json.loads(info_path.read_text(encoding="utf-8"))
        if hashlib.sha256(raw).hexdigest() != info["sha256"]:
            raise ValueError(f"O cache de {name} foi alterado; confira a fonte.")
        print(f"Cache preservado: {name}", flush=True)
        return read_source_csv(raw), info
    print(f"Baixando fonte oficial: {name}", flush=True)
    request = Request(SOURCES[name], headers={"User-Agent": "Renewcast-Lab/0.1"})
    with urlopen(request, timeout=40) as response:
        raw = response.read()
        info = {
            "url": SOURCES[name], "http_status": response.status,
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
            "http_last_modified": response.headers.get("Last-Modified"),
            "etag": response.headers.get("ETag"),
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
        }
    data = read_source_csv(raw)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    # Preserve a cópia anterior quando a atualização for explicitamente pedida.
    if raw_path.exists():
        archive = output / "raw" / "previous" / hashlib.sha256(raw_path.read_bytes()).hexdigest()[:16]
        archive.mkdir(parents=True, exist_ok=True)
        (archive / raw_path.name).write_bytes(raw_path.read_bytes())
        if info_path.exists():
            (archive / info_path.name).write_bytes(info_path.read_bytes())
    raw_path.write_bytes(raw)
    info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")
    return data, info


def build_asset_registry(relationships, capacity, siga, *, conjunto_id, as_of):
    """Vínculos na data pedida, segundo os cadastros coletados agora.

    Não afirma que coordenadas e capacidades atuais eram conhecidas no passado.
    """
    date = pd.Timestamp(as_of).normalize()
    members = relationships.loc[relationships["id_ons_conjunto"].eq(conjunto_id)].copy()
    if members.empty:
        raise ValueError(f"Conjunto não encontrado: {conjunto_id}")
    start = pd.to_datetime(members["dat_iniciorelacionamento"], errors="raise")
    end = pd.to_datetime(members["dat_fimrelacionamento"], errors="raise")
    members = members.loc[(start <= date) & (end.isna() | (end >= date))].copy()
    if members.empty:
        raise ValueError("Nenhum vínculo informado como vigente na data escolhida.")
    members["ceg_key"] = canonical_ceg(members["ceg"])
    if members["ceg_key"].isna().any() or members["ceg_key"].duplicated().any():
        raise ValueError("CEG ausente, não reconhecido ou vínculo duplicado no conjunto.")

    units = capacity.copy()
    units["ceg_key"] = canonical_ceg(units["ceg"])
    units = units.loc[units["ceg_key"].isin(members["ceg_key"])].copy()
    commercial = pd.to_datetime(units["dat_entradaoperacao"], errors="raise")
    retired = pd.to_datetime(units["dat_desativacao"], errors="raise")
    units = units.loc[(commercial <= date) & (retired.isna() | (retired > date))].copy()
    if units["cod_equipamento"].isna().any() or units["cod_equipamento"].duplicated().any():
        raise ValueError("Identificador de equipamento ausente ou duplicado na capacidade.")
    units["capacity_mw"] = pd.to_numeric(units["val_potenciaefetiva"], errors="raise")
    if not np.isfinite(units["capacity_mw"].to_numpy(dtype=float)).all() or (units["capacity_mw"] <= 0).any():
        raise ValueError("Capacidade ONS ausente, não finita ou não positiva.")

    # ONS possui registros por unidade geradora. Agregar ANTES de juntar.
    per_plant = units.groupby("ceg_key", as_index=False).agg(
        capacity_ons_mw=("capacity_mw", "sum"),
        capacity_records=("cod_equipamento", "size"),
    )
    coordinates = siga.copy()
    coordinates["ceg_key"] = canonical_ceg(coordinates["CodCEG"])
    coordinates = coordinates.loc[coordinates["ceg_key"].isin(members["ceg_key"])].copy()
    if coordinates["ceg_key"].duplicated().any():
        raise ValueError("O SIGA contém mais de um registro para o mesmo CEG normalizado.")
    selected = coordinates[[
        "ceg_key", "CodCEG", "NomEmpreendimento", "SigUFPrincipal", "SigTipoGeracao",
        "DscFaseUsina", "NumCoordNEmpreendimento", "NumCoordEEmpreendimento",
        "MdaPotenciaFiscalizadaKw", "DatGeracaoConjuntoDados",
    ]].rename(columns={
        "CodCEG": "ceg_aneel", "NomEmpreendimento": "name_aneel",
        "NumCoordNEmpreendimento": "latitude", "NumCoordEEmpreendimento": "longitude",
        "DatGeracaoConjuntoDados": "siga_dataset_date",
    })
    for column in ("latitude", "longitude", "MdaPotenciaFiscalizadaKw"):
        selected[column] = pd.to_numeric(selected[column].str.replace(",", ".", regex=False), errors="raise")
    selected["capacity_aneel_mw"] = selected.pop("MdaPotenciaFiscalizadaKw") / 1000.0

    registry = members.merge(per_plant, on="ceg_key", how="left", validate="one_to_one")
    registry = registry.merge(selected, on="ceg_key", how="left", validate="one_to_one", indicator=True)
    if not registry["_merge"].eq("both").all():
        missing = registry.loc[registry["_merge"].ne("both"), "ceg"].tolist()
        raise ValueError(f"CEGs sem correspondência única no SIGA: {missing}")
    numeric = registry[["capacity_ons_mw", "latitude", "longitude", "capacity_aneel_mw"]]
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError("Uma usina está sem capacidade ou coordenadas completas.")
    if not (registry["latitude"].between(-90, 90) & registry["longitude"].between(-180, 180)).all():
        raise ValueError("Coordenadas fora dos limites geográficos.")
    registry["capacity_difference_mw"] = registry["capacity_ons_mw"] - registry["capacity_aneel_mw"]
    registry["capacity_weight"] = registry["capacity_ons_mw"] / registry["capacity_ons_mw"].sum()
    registry["membership_as_of"] = date.date().isoformat()
    registry["historical_snapshot_verified"] = False
    return registry.drop(columns="_merge").sort_values("nom_usina").reset_index(drop=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conjunto", default="CJU_BA5EIGT")
    parser.add_argument("--as-of", required=True, help="Data de referência: AAAA-MM-DD")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args(argv)
    sources, provenance = {}, {}
    for name in SOURCES:
        sources[name], provenance[name] = fetch_source(name, args.output_dir, refresh=args.refresh)
    registry = build_asset_registry(
        sources["relationships"], sources["capacity"], sources["siga_daily"],
        conjunto_id=args.conjunto, as_of=args.as_of,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "asset_registry.csv"
    registry.to_csv(csv_path, index=False, encoding="utf-8-sig")
    metadata = {
        "conjunto_id": args.conjunto, "membership_as_of": args.as_of,
        "plants": len(registry), "capacity_records": int(registry["capacity_records"].sum()),
        "capacity_ons_mw": float(registry["capacity_ons_mw"].sum()),
        "capacity_aneel_mw": float(registry["capacity_aneel_mw"].sum()),
        "max_absolute_capacity_difference_mw": float(registry["capacity_difference_mw"].abs().max()),
        "sources": provenance,
        "ceg_normalization": "preserve full CEG; normalize leading zeros of numeric final suffix",
        "join_contract": "one relationship, one aggregated capacity and one SIGA record per CEG",
        "membership_dates": "start inclusive; end inclusive by calendar date",
        "capacity_dates": "commercial operation <= date; deactivation > date or absent",
        "historical_snapshot_verified": False,
        "scope": "membership dates from current registry; historical coordinates/capacity versions not verified",
        "coordinates_scope": "registered plant location, not individual turbine locations",
        "ons_attribution": "Operador Nacional do Sistema Elétrico — dados abertos, CC-BY",
        "aneel_attribution": "ANEEL — SIGA, Open Database License (ODbL)",
        "transformations": "CEG formatting, capacity aggregation, kW to MW, decimal conversion and joins",
    }
    (args.output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("\nCadastro do conjunto:")
    print(registry[["nom_usina", "capacity_records", "capacity_ons_mw", "capacity_aneel_mw", "latitude", "longitude", "capacity_weight"]].round(6).to_string(index=False))
    print(f"\nUsinas: {metadata['plants']}; registros de capacidade ONS: {metadata['capacity_records']}")
    print(f"Capacidade total ONS: {metadata['capacity_ons_mw']:.3f} MW")
    print(f"Maior diferença ONS/ANEEL por usina: {metadata['max_absolute_capacity_difference_mw']:.6f} MW")
    print("Escopo: cadastro coletado agora, com datas de vínculo; versões históricas não verificadas.")
    print("Arquivo:", csv_path.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
