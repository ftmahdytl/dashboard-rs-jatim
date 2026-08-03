from __future__ import annotations
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime
import time
from zoneinfo import ZoneInfo
import pandas as pd
import requests
URL_PARU_JEMBER = "http://save.rsparujember.com:8004/"
API_PARU_JEMBER = "http://103.165.213.138:7000/api/display/kamar"
JAKARTA = ZoneInfo("Asia/Jakarta")
def fetch_data() -> list[dict]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": URL_PARU_JEMBER,
    }
    response = requests.get(
        API_PARU_JEMBER,
        headers=headers,
        params={"_scrape_ts": int(time.time() * 1000)},
        timeout=90,
        verify=False,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") is not True:
        raise ValueError("API RS Paru Jember mengirim status gagal.")
    pages = payload.get("list", [])
    rows = [
        item
        for page in pages
        if isinstance(page, list)
        for item in page
        if isinstance(item, dict)
    ]
    if not rows:
        raise ValueError("API RS Paru Jember mengirim data kamar kosong.")
    return rows
def normalize_class(value: object) -> str:
    text = " ".join(str(value).split()).upper()
    mapping = {
        "KELAS I": "Kelas I",
        "KELAS II": "Kelas II",
        "KELAS III": "Kelas III",
        "KELAS VIP": "VIP",
        "NON KELAS": "Non Kelas",
        "HCU": "HCU",
        "ICU": "ICU",
    }
    return mapping.get(text, text.title())
def clean_bed_data(rows: list[dict]) -> pd.DataFrame:
    result = pd.DataFrame(rows)
    required = [
        "nama_kamar",
        "nama_kelas",
        "kapasitas",
        "sisa",
        "timestamp",
    ]
    missing = [column for column in required if column not in result]
    if missing:
        raise ValueError(
            "Kolom API RS Paru Jember tidak lengkap: "
            + ", ".join(missing)
        )
    result = result.rename(
        columns={
            "nama_kamar": "nama_ruang",
            "nama_kelas": "kelas",
            "sisa": "tersedia",
        }
    )
    result["kelas"] = result["kelas"].map(normalize_class)
    result["nama_ruang"] = (
        result["nama_ruang"]
        .astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .str.title()
        .str.replace("Icu", "ICU", regex=False)
        .str.replace("Hcu", "HCU", regex=False)
        .str.replace("Nicu", "NICU", regex=False)
        .str.replace("Vip", "VIP", regex=False)
        .str.replace(" Iii", " III", regex=False)
        .str.replace(" Ii", " II", regex=False)
    )
    for column in ["kapasitas", "tersedia"]:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    result = result.dropna(
        subset=["kelas", "nama_ruang", "kapasitas", "tersedia"]
    )
    result[["kapasitas", "tersedia"]] = result[
        ["kapasitas", "tersedia"]
    ].astype(int)
    parsed_updates = pd.to_datetime(result["timestamp"], errors="coerce")
    latest_source_update = parsed_updates.max()
    if pd.isna(latest_source_update):
        source_update = datetime.now(JAKARTA).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    else:
        source_update = latest_source_update.strftime("%Y-%m-%d %H:%M:%S")
    result["kategori_pasien"] = "Rawat Inap"
    result["terisi"] = result["kapasitas"] - result["tersedia"]
    result["tidak_siap"] = 0
    result["renovasi"] = 0
    result["sisrute"] = 0
    result["terisi_pria"] = 0
    result["terisi_wanita"] = 0
    result["keterangan"] = result["tarif"].map(
        lambda value: (
            f"Tarif Rp{int(value):,}".replace(",", ".")
            if pd.notna(value) and str(value).strip().isdigit()
            else ""
        )
    )
    result["kode_rs"] = "RSPJ"
    result["nama_rs"] = "RS Paru Jember"
    result["waktu_update_sumber"] = source_update
    result["waktu_scraping"] = datetime.now(JAKARTA).strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )
    result["sumber_url"] = URL_PARU_JEMBER
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
        raise ValueError("Hasil scraping RS Paru Jember kosong.")
    numeric_columns = ["kapasitas", "terisi", "tersedia"]
    if (data[numeric_columns] < 0).any().any():
        raise ValueError("Ditemukan angka negatif pada data RS Paru Jember.")
    if ((data["terisi"] + data["tersedia"]) != data["kapasitas"]).any():
        raise ValueError(
            "Data RS Paru Jember tidak memenuhi kapasitas = "
            "terisi + tersedia."
        )
def scrape_paru_jember() -> pd.DataFrame:
    rows = fetch_data()
    clean_data = clean_bed_data(rows)
    validate_bed_data(clean_data)
    return clean_data
if __name__ == "__main__":
    dataframe = scrape_paru_jember()
    print("Scraping RS Paru Jember berhasil.")
    print(f"Jumlah kamar: {dataframe['nama_ruang'].nunique()}")
    print(f"Jumlah kombinasi kamar-kelas: {len(dataframe)}")
    print(dataframe.to_string(index=False))
