from __future__ import annotations
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime
import time
from zoneinfo import ZoneInfo
import pandas as pd
import requests
URL_SAIFUL_ANWAR = (
    "https://rsusaifulanwar.jatimprov.go.id/ketersediaan-bed/"
)
API_SAIFUL_ANWAR = "https://aplicares.rssa.my.id/api/beds/"
JAKARTA = ZoneInfo("Asia/Jakarta")
REQUIRED_FIELDS = {
    "kode_ruang",
    "nama_ruang",
    "namakelas",
    "kapasitas",
    "tersedia_pria_wanita",
    "updated",
}
def fetch_bed_data() -> list[dict]:
    """Mengambil semua halaman data bed dari API Saiful Anwar."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
        "Referer": URL_SAIFUL_ANWAR,
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    rows: list[dict] = []
    next_url: str | None = API_SAIFUL_ANWAR
    first_request = True
    with requests.Session() as session:
        while next_url:
            response = session.get(
                next_url,
                headers=headers,
                params=(
                    {"_scrape_ts": int(time.time() * 1000)}
                    if first_request
                    else None
                ),
                timeout=60,
                verify=False,
            )
            response.raise_for_status()
            payload = response.json()
            page_rows = payload.get("results")
            if not isinstance(page_rows, list):
                raise ValueError(
                    "API Saiful Anwar tidak mengirim daftar results."
                )
            rows.extend(page_rows)
            next_url = payload.get("next")
            first_request = False
    if not rows:
        raise ValueError("API Saiful Anwar mengirim data kosong.")
    return rows
def clean_bed_data(rows: list[dict]) -> pd.DataFrame:
    """Menormalisasi JSON API ke format dashboard bersama."""
    for index, row in enumerate(rows):
        missing = REQUIRED_FIELDS.difference(row)
        if missing:
            raise ValueError(
                f"Data API baris {index} kehilangan kolom: "
                f"{', '.join(sorted(missing))}"
            )
    result = pd.DataFrame(rows).rename(
        columns={
            "namakelas": "kelas",
            "tersedia_pria_wanita": "tersedia",
            "updated": "waktu_update_sumber",
        }
    )
    for column in ["kode_ruang", "kelas", "nama_ruang"]:
        result[column] = (
            result[column]
            .astype(str)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
    for column in ["kapasitas", "tersedia"]:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )
    result = result.dropna(
        subset=[
            "kode_ruang",
            "kelas",
            "nama_ruang",
            "kapasitas",
            "tersedia",
        ]
    )
    result[["kapasitas", "tersedia"]] = (
        result[["kapasitas", "tersedia"]]
        .fillna(0)
        .astype(int)
    )
    result["terisi"] = (
        result["kapasitas"] - result["tersedia"]
    ).clip(lower=0)
    result["renovasi"] = 0
    result["sisrute"] = 0
    result["tidak_siap"] = 0
    result["keterangan"] = ""
    # API hanya menyediakan ketersediaan berdasarkan jenis kelamin,
    # bukan jumlah pasien terisi pria/wanita.
    result["terisi_pria"] = 0
    result["terisi_wanita"] = 0
    parsed_update = pd.to_datetime(
        result["waktu_update_sumber"],
        errors="coerce",
    )
    result["waktu_update_sumber"] = parsed_update.dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    fallback_update = datetime.now(JAKARTA).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    result["waktu_update_sumber"] = (
        result["waktu_update_sumber"].fillna(fallback_update)
    )
    result["kode_rs"] = "RSSA"
    result["nama_rs"] = "RSUD Dr. Saiful Anwar"
    result["kategori_pasien"] = "Umum"
    result["waktu_scraping"] = datetime.now(JAKARTA).strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )
    result["sumber_url"] = URL_SAIFUL_ANWAR
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
        raise ValueError("Hasil scraping Saiful Anwar kosong.")
    if (data[["kapasitas", "terisi", "tersedia"]] < 0).any().any():
        raise ValueError("Ditemukan angka negatif pada data bed.")
    if (data["terisi"] + data["tersedia"] != data["kapasitas"]).any():
        raise ValueError(
            "Ada data dengan terisi + tersedia tidak sama dengan kapasitas."
        )
def scrape_saiful_anwar() -> pd.DataFrame:
    rows = fetch_bed_data()
    clean_data = clean_bed_data(rows)
    validate_bed_data(clean_data)
    return clean_data
if __name__ == "__main__":
    dataframe = scrape_saiful_anwar()
    print("Scraping RSUD Dr. Saiful Anwar berhasil.")
    print(f"Jumlah ruang: {len(dataframe)}")
    print(f"Jumlah kelas: {dataframe['kelas'].nunique()}")
    print(dataframe.head(10).to_string(index=False))
