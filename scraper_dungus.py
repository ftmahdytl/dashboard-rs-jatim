from __future__ import annotations
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime
import json
import re
import time
from zoneinfo import ZoneInfo
import pandas as pd
import requests
URL_DUNGUS = "https://rsuddungus.jatimprov.go.id/ketersediaan-bed/"
JAKARTA = ZoneInfo("Asia/Jakarta")
def fetch_html() -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    response = requests.get(
        URL_DUNGUS,
        headers=headers,
        params={"_scrape_ts": int(time.time() * 1000)},
        timeout=90,
        verify=False,
    )
    response.raise_for_status()
    if not response.text.strip():
        raise ValueError("Halaman bed RSUD Dungus mengirim HTML kosong.")
    return response.text
def extract_aplicare_data(html: str) -> list[dict]:
    match = re.search(
        r"const\s+Data\s*=\s*(\{.*?\})\s*;",
        html,
        flags=re.DOTALL,
    )
    if match is None:
        raise ValueError("JSON BPJS Aplicare RSUD Dungus tidak ditemukan.")
    payload = json.loads(match.group(1))
    rows = payload.get("response", {}).get("list", [])
    if not isinstance(rows, list) or not rows:
        raise ValueError("BPJS Aplicare RSUD Dungus mengirim data kosong.")
    return rows
def clean_bed_data(rows: list[dict]) -> pd.DataFrame:
    result = pd.DataFrame(rows)
    required = [
        "namakelas",
        "namaruang",
        "kapasitas",
        "tersedia",
        "last_update",
    ]
    missing = [column for column in required if column not in result]
    if missing:
        raise ValueError(
            "Kolom Aplicare Dungus tidak lengkap: " + ", ".join(missing)
        )
    result = result.rename(
        columns={
            "namakelas": "kelas",
            "namaruang": "nama_ruang",
        }
    )
    for column in ["kelas", "nama_ruang"]:
        result[column] = (
            result[column]
            .astype(str)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
            .str.title()
            .str.replace("Icu", "ICU", regex=False)
            .str.replace("Hcu", "HCU", regex=False)
            .str.replace("Nicu", "NICU", regex=False)
            .str.replace("Picu", "PICU", regex=False)
            .str.replace("Vip", "VIP", regex=False)
            .str.replace("Kelas Iii", "Kelas III", regex=False)
            .str.replace("Kelas Ii", "Kelas II", regex=False)
        )
    for column in ["kapasitas", "tersedia", "last_update"]:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    result = result.dropna(
        subset=[
            "kelas",
            "nama_ruang",
            "kapasitas",
            "tersedia",
            "last_update",
        ]
    )
    result[["kapasitas", "tersedia"]] = result[
        ["kapasitas", "tersedia"]
    ].astype(int)
    latest_epoch_ms = int(result["last_update"].max())
    latest_source_update = datetime.fromtimestamp(
        latest_epoch_ms / 1000,
        tz=JAKARTA,
    ).strftime("%Y-%m-%d %H:%M:%S")
    result["kategori_pasien"] = "Rawat Inap"
    result["terisi"] = result["kapasitas"] - result["tersedia"]
    result["tidak_siap"] = 0
    result["renovasi"] = 0
    result["sisrute"] = 0
    result["terisi_pria"] = 0
    result["terisi_wanita"] = 0
    result["keterangan"] = result.apply(
        lambda row: (
            f"Status Aplicare: {row.get('stat', '-')} · "
            f"Update: {row.get('lastupdate', '-')}"
        ),
        axis=1,
    )
    result["kode_rs"] = "RSDG"
    result["nama_rs"] = "RSUD Dungus Madiun"
    result["waktu_update_sumber"] = latest_source_update
    result["waktu_scraping"] = datetime.now(JAKARTA).strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )
    result["sumber_url"] = URL_DUNGUS
    result["persentase_keterisian"] = (
        result["terisi"]
        .div(result["kapasitas"].replace(0, pd.NA))
        .mul(100)
        .fillna(0)
        .round(2)
    )
    ordered_columns = [
        "kode_rs",
        "nama_rs",
        "kategori_pasien",
        "kelas",
        "nama_ruang",
        "kapasitas",
        "terisi",
        "tersedia",
        "tidak_siap",
        "renovasi",
        "sisrute",
        "terisi_pria",
        "terisi_wanita",
        "keterangan",
        "waktu_update_sumber",
        "waktu_scraping",
        "sumber_url",
        "persentase_keterisian",
    ]
    return (
        result[ordered_columns]
        .drop_duplicates(subset=["kelas", "nama_ruang"])
        .sort_values(["kelas", "nama_ruang"])
        .reset_index(drop=True)
    )
def validate_bed_data(data: pd.DataFrame) -> None:
    if data.empty:
        raise ValueError("Hasil scraping RSUD Dungus kosong.")
    numeric_columns = ["kapasitas", "terisi", "tersedia"]
    if (data[numeric_columns] < 0).any().any():
        raise ValueError("Ditemukan angka negatif pada data RSUD Dungus.")
    if ((data["terisi"] + data["tersedia"]) != data["kapasitas"]).any():
        raise ValueError(
            "Data Dungus tidak memenuhi kapasitas = terisi + tersedia."
        )
def scrape_dungus() -> pd.DataFrame:
    html = fetch_html()
    rows = extract_aplicare_data(html)
    clean_data = clean_bed_data(rows)
    validate_bed_data(clean_data)
    return clean_data
if __name__ == "__main__":
    dataframe = scrape_dungus()
    print("Scraping RSUD Dungus berhasil.")
    print(f"Jumlah ruang: {dataframe['nama_ruang'].nunique()}")
    print(f"Jumlah kombinasi ruang-kelas: {len(dataframe)}")
    print(dataframe.to_string(index=False))
