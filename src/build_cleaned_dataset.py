import re
import unicodedata
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_PATH = DATA_DIR / "cleaned_data" / "dataset_nettoye.csv"


def normalize_text(x: object) -> object:
    """Lowercase + strip + remove accents. Keeps NaN as-is."""
    if pd.isna(x):
        return x
    s = str(x).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", errors="ignore").decode("ascii")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def main() -> None:
    demandes = pd.read_csv(DATA_DIR / "demandes_service_public.csv", encoding="utf-8")
    communes = pd.read_csv(DATA_DIR / "details_communes.csv", encoding="utf-8")
    centres = pd.read_csv(DATA_DIR / "centres_service.csv", encoding="utf-8")
    socio = pd.read_csv(DATA_DIR / "donnees_socioeconomiques.csv", encoding="utf-8")

    # Normalize join keys (do NOT touch IDs)
    for df, col in [
        (demandes, "commune"),
        (communes, "commune"),
        (centres, "commune"),
        (socio, "commune"),
    ]:
        if col in df.columns:
            df[col] = df[col].map(normalize_text)

    # Deduplicate commune tables (1 row per commune)
    communes = communes.sort_values("commune").drop_duplicates(subset=["commune"], keep="first")
    socio = socio.sort_values("commune").drop_duplicates(subset=["commune"], keep="first")

    # Aggregate centres by commune to avoid multiplying demandes rows
    centres_agg = (
        centres.groupby("commune", as_index=False)
        .agg(
            nb_centres=("centre_id", "nunique"),
            capacite_totale_jour=("personnel_capacite_jour", "sum"),
            capacite_moyenne_jour=("personnel_capacite_jour", "mean"),
            guichets_totaux=("nombre_guichets", "sum"),
            guichets_moyens=("nombre_guichets", "mean"),
        )
    )

    merged = (
        demandes.merge(communes, on="commune", how="left", suffixes=("_demandes", "_commune"))
        .merge(centres_agg, on="commune", how="left")
        .merge(socio, on="commune", how="left", suffixes=("", "_socio"))
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUT_PATH, index=False, encoding="utf-8")

    print(f"Wrote: {OUT_PATH}")
    print("rows, cols:", merged.shape)
    if "demande_id" in merged.columns:
        print("demande_id nunique:", merged["demande_id"].nunique())


if __name__ == "__main__":
    main()

