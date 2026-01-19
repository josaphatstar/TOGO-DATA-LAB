import re
import unicodedata
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_DIR = DATA_DIR / "cleaned_data"


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
    logs = pd.read_csv(DATA_DIR / "logs_activite.csv", encoding="utf-8")

    # Normalize join keys (do NOT touch IDs)
    for df, col in [
        (demandes, "commune"),
        (communes, "commune"),
        (centres, "commune"),
        (socio, "commune"),
        (logs, "centre_id"),  # keep id, but normalize? no change; just present for completeness
    ]:
        if col in df.columns:
            df[col] = df[col].map(normalize_text)

    # Deduplicate commune tables (1 row per commune)
    communes = communes.sort_values("commune").drop_duplicates(subset=["commune"], keep="first")
    socio = socio.sort_values("commune").drop_duplicates(subset=["commune"], keep="first")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save cleaned tables individually (no merged dataset)
    demandes.to_csv(OUT_DIR / "demandes_service_public_nettoye.csv", index=False, encoding="utf-8")
    communes.to_csv(OUT_DIR / "details_communes_nettoye.csv", index=False, encoding="utf-8")
    centres.to_csv(OUT_DIR / "centres_service_nettoye.csv", index=False, encoding="utf-8")
    socio.to_csv(OUT_DIR / "donnees_socioeconomiques_nettoye.csv", index=False, encoding="utf-8")
    logs.to_csv(OUT_DIR / "logs_activite_nettoye.csv", index=False, encoding="utf-8")

    print("Wrote cleaned tables separately into data/cleaned_data/:")
    for fname in [
        "demandes_service_public_nettoye.csv",
        "details_communes_nettoye.csv",
        "centres_service_nettoye.csv",
        "donnees_socioeconomiques_nettoye.csv",
        "logs_activite_nettoye.csv",
    ]:
        print(" -", fname)


if __name__ == "__main__":
    main()

