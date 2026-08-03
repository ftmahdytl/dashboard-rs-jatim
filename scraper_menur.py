from __future__ import annotations
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime
import time
from zoneinfo import ZoneInfo
import pandas as pd
import requests
URL_MENUR = "https://online.rsmenur.cloud/rawatinap/ketersediaan-bed"
API_MENUR = "https://online.rsmenur.cloud/api/rawatinap/ketersediaan-bed"
JAKARTA = ZoneInfo("Asia/Jakarta")
def fetch_data() -> tuple[list[dict], str]:
    """Meminta JSON terbaru dari API yang digunakan tombol REFRESH."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": URL_MENUR,
    }
    response = requests.get(
        API_MENUR,
        headers=headers,
        params={"_scrape_ts": int(time.time() * 1000)},
        timeout=90,
        verify=False,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or not payload:
        raise ValueError("API RS Jiwa Menur tidak mengirim data ruang.")
    # Website menampilkan waktu ketika API selesai diminta, bukan timestamp
    # tersendiri dari database. Karena itu waktu sumber mengikuti respons API.
    source_update = datetime.now(JAKARTA).strftime("%Y-%m-%d %H:%M:%S")
    return payload, source_update
def normalize_class(value: object) -> str:
    text = str(value).strip()
    mapping = {
        "1": "Kelas I",
        "2": "Kelas II",
        "3": "Kelas III",
    }
    return mapping.get(text, text)
def clean_bed_data(
    payload: list[dict],
    source_update: str,
) -> pd.DataFrame:
    rows: list[dict] = []
    for room_group in payload:
        room_name = str(room_group.get("nama", "")).strip()
        room_data = room_group.get("data", [])
        if not room_name or not isinstance(room_data, list):
            continue
        for item in room_data:
            rows.append(
                {
                    "kategori_pasien": "Rawat Inap",
                    "kelas": normalize_class(item.get("kelas", "")),
                    "nama_ruang": room_name,
                    "kapasitas": item.get("bed_kapasitas"),
                    "terisi": item.get("bed_terisi"),
                    "tersedia": item.get("bed_kosong"),
                }
            )
    if not rows:
        raise ValueError("Data ruang-kelas RS Jiwa Menur kosong.")
    result = pd.DataFrame(rows)
    numeric_columns = ["kapasitas", "terisi", "tersedia"]
    for column in numeric_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    result = result.dropna(
        subset=["kelas", "nama_ruang", *numeric_columns]
    )
    result[numeric_columns] = result[numeric_columns].astype(int)
    result["tidak_siap"] = 0
    result["renovasi"] = 0
    result["sisrute"] = 0
    result["terisi_pria"] = 0
    result["terisi_wanita"] = 0
    result["keterangan"] = ""
    result["kode_rs"] = "RSMN"
    result["nama_rs"] = "RS Jiwa Menur Provinsi Jawa Timur"
    result["waktu_update_sumber"] = source_update
    result["waktu_scraping"] = datetime.now(JAKARTA).strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )
    result["sumber_url"] = URL_MENUR
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
        raise ValueError("Hasil scraping RS Jiwa Menur kosong.")
    numeric_columns = ["kapasitas", "terisi", "tersedia"]
    if (data[numeric_columns] < 0).any().any():
        raise ValueError("Ditemukan angka negatif pada data RS Jiwa Menur.")
    if ((data["terisi"] + data["tersedia"]) != data["kapasitas"]).any():
        raise ValueError(
            "Data Menur tidak memenuhi kapasitas = terisi + kosong."
        )
def scrape_menur() -> pd.DataFrame:
    payload, source_update = fetch_data()
    clean_data = clean_bed_data(payload, source_update)
    validate_bed_data(clean_data)
    return clean_data
if __name__ == "__main__":
    dataframe = scrape_menur()
    print("Scraping RS Jiwa Menur berhasil.")
    print(f"Jumlah ruang: {dataframe['nama_ruang'].nunique()}")
    print(f"Jumlah kombinasi ruang-kelas: {len(dataframe)}")
    print(dataframe.to_string(index=False))
