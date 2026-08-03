from __future__ import annotations
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime
from io import StringIO
import re
import time
from zoneinfo import ZoneInfo
import pandas as pd
import requests
URL_DAHA_HUSADA = "https://rsuddahahusada.jatimprov.go.id/"
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
        URL_DAHA_HUSADA,
        headers=headers,
        params={"_scrape_ts": int(time.time() * 1000)},
        timeout=90,
        verify=False,
    )
    response.raise_for_status()
    if not response.text.strip():
        raise ValueError("Halaman RSUD Daha Husada mengirim HTML kosong.")
    return response.text
def extract_source_update(html: str) -> str:
    match = re.search(
        r"Terakhir\s*:\s*"
        r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
        html,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1)
    return datetime.now(JAKARTA).strftime("%Y-%m-%d %H:%M:%S")
def extract_bed_table(html: str) -> pd.DataFrame:
    required_columns = [
        "Bangsal",
        "Kelas",
        "Total",
        "Terisi",
        "Tersedia",
    ]
    for table in pd.read_html(StringIO(html)):
        table.columns = [str(column).strip() for column in table.columns]
        if set(required_columns).issubset(table.columns):
            return table[required_columns].copy()
    raise ValueError("Tabel ketersediaan RSUD Daha Husada tidak ditemukan.")
def normalize_class(value: object) -> str:
    text = " ".join(str(value).split())
    mapping = {
        "Kelas 1": "Kelas I",
        "Kelas 2": "Kelas II",
        "Kelas 3": "Kelas III",
        "Kelas VIP": "VIP",
    }
    return mapping.get(text, text)
def clean_bed_data(
    raw_data: pd.DataFrame,
    source_update: str,
) -> pd.DataFrame:
    result = raw_data.rename(
        columns={
            "Bangsal": "nama_ruang",
            "Kelas": "kelas",
            "Total": "kapasitas",
            "Terisi": "terisi",
            "Tersedia": "tersedia",
        }
    ).copy()
    result["nama_ruang"] = (
        result["nama_ruang"]
        .astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .str.title()
        .str.replace("Icu", "ICU", regex=False)
        .str.replace("Vip", "VIP", regex=False)
    )
    result["kelas"] = result["kelas"].map(normalize_class)
    numeric_columns = ["kapasitas", "terisi", "tersedia"]
    for column in numeric_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    result = result.dropna(
        subset=["kelas", "nama_ruang", *numeric_columns]
    )
    result[numeric_columns] = result[numeric_columns].astype(int)
    result["tidak_siap"] = (
        result["kapasitas"] - result["terisi"] - result["tersedia"]
    )
    result["renovasi"] = 0
    result["sisrute"] = 0
    result["terisi_pria"] = 0
    result["terisi_wanita"] = 0
    result["keterangan"] = result["tidak_siap"].map(
        lambda value: (
            f"{value} bed tidak berstatus terisi/tersedia"
            if value > 0
            else ""
        )
    )
    result["kode_rs"] = "RSDH"
    result["nama_rs"] = "RSUD Daha Husada Kediri"
    result["kategori_pasien"] = "Rawat Inap"
    result["waktu_update_sumber"] = source_update
    result["waktu_scraping"] = datetime.now(JAKARTA).strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )
    result["sumber_url"] = URL_DAHA_HUSADA
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
        raise ValueError("Hasil scraping RSUD Daha Husada kosong.")
    numeric_columns = [
        "kapasitas",
        "terisi",
        "tersedia",
        "tidak_siap",
    ]
    if (data[numeric_columns] < 0).any().any():
        raise ValueError(
            "Ditemukan angka negatif pada data RSUD Daha Husada."
        )
    reconciled = data["terisi"] + data["tersedia"] + data["tidak_siap"]
    if (reconciled != data["kapasitas"]).any():
        raise ValueError(
            "Data Daha Husada tidak memenuhi kapasitas = terisi + "
            "tersedia + tidak siap."
        )
def scrape_daha_husada() -> pd.DataFrame:
    html = fetch_html()
    source_update = extract_source_update(html)
    raw_data = extract_bed_table(html)
    clean_data = clean_bed_data(raw_data, source_update)
    validate_bed_data(clean_data)
    return clean_data
if __name__ == "__main__":
    dataframe = scrape_daha_husada()
    print("Scraping RSUD Daha Husada berhasil.")
    print(f"Jumlah bangsal: {dataframe['nama_ruang'].nunique()}")
    print(f"Jumlah kombinasi bangsal-kelas: {len(dataframe)}")
    print(dataframe.to_string(index=False))
