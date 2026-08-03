from __future__ import annotations
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime
from io import StringIO
import time
from zoneinfo import ZoneInfo
import pandas as pd
import requests
from bs4 import BeautifulSoup
URL_SOETOMO = (
    "https://itki.rsudrsoetomo.jatimprov.go.id/"
    "dashboard-kamar/public/umum"
)
REQUIRED_COLUMNS = [
    "Kelas",
    "Nama Ruang",
    "Kapasitas",
    "Tersedia",
    "Terisi Pria",
    "Terisi Wanita",
]
JAKARTA = ZoneInfo("Asia/Jakarta")
CLASS_LABELS = {
    "KB": "Kamar Bayi (KB)",
}
def fetch_html() -> str:
    """Mengambil HTML dashboard kamar RSUD Dr. Soetomo."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://itki.rsudrsoetomo.jatimprov.go.id/",
        "Cache-Control": "no-cache",
    }
    # Parameter unik mencegah proxy/server mengirim salinan HTML lama.
    response = requests.get(
        URL_SOETOMO,
        headers=headers,
        params={"_scrape_ts": int(time.time() * 1000)},
        timeout=60,
        verify=False,
    )
    response.raise_for_status()
    if not response.text.strip():
        raise ValueError("Website terbuka, tetapi isi HTML kosong.")
    return response.text
def _clean_header(value: object) -> str:
    if isinstance(value, tuple):
        parts = [
            str(item).strip()
            for item in value
            if str(item).strip() and not str(item).startswith("Unnamed")
        ]
        value = " ".join(parts)
    return " ".join(str(value).replace("\n", " ").split())
def extract_source_update(html: str) -> str:
    """Mengambil teks Last Update dari halaman."""
    soup = BeautifulSoup(html, "html.parser")
    label = soup.find(id="lblLastUpdate")
    if label is None:
        return datetime.now(JAKARTA).strftime("%Y-%m-%d %H:%M:%S")
    text = label.get_text(" ", strip=True)
    return text.replace("Last Update :", "").strip()
def extract_bed_tables(html: str) -> pd.DataFrame:
    """Membaca semua tabel bed yang memiliki kolom yang dibutuhkan."""
    tables = pd.read_html(StringIO(html))
    valid_tables: list[pd.DataFrame] = []
    for table in tables:
        table.columns = [_clean_header(column) for column in table.columns]
        if set(REQUIRED_COLUMNS).issubset(table.columns):
            valid_tables.append(table[REQUIRED_COLUMNS].copy())
    if not valid_tables:
        raise ValueError(
            "Tabel bed tidak ditemukan. Struktur website mungkin berubah."
        )
    return pd.concat(valid_tables, ignore_index=True)
def clean_bed_data(
    raw_data: pd.DataFrame,
    source_update: str,
) -> pd.DataFrame:
    """Membersihkan data mentah dan menyamakan nama kolom."""
    result = raw_data.rename(
        columns={
            "Kelas": "kelas",
            "Nama Ruang": "nama_ruang",
            "Kapasitas": "kapasitas",
            "Tersedia": "tersedia",
            "Terisi Pria": "terisi_pria",
            "Terisi Wanita": "terisi_wanita",
        }
    ).copy()
    for column in ["kelas", "nama_ruang"]:
        result[column] = (
            result[column]
            .astype(str)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
    result["kelas"] = result["kelas"].replace(CLASS_LABELS)
    numeric_columns = [
        "kapasitas",
        "tersedia",
        "terisi_pria",
        "terisi_wanita",
    ]
    for column in numeric_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    result = result.dropna(
        subset=["kelas", "nama_ruang", "kapasitas", "tersedia"]
    )
    result = result[
        ~result["kelas"].str.lower().eq("kelas")
        & ~result["nama_ruang"].str.lower().eq("nama ruang")
    ]
    result[numeric_columns] = result[numeric_columns].fillna(0).astype(int)
    result["terisi"] = (
        result["terisi_pria"] + result["terisi_wanita"]
    )
    result["renovasi"] = 0
    result["sisrute"] = 0
    result["tidak_siap"] = 0
    result["keterangan"] = ""
    # Jika pembagian pria/wanita tidak lengkap, gunakan kapasitas - tersedia.
    calculated_occupied = (
        result["kapasitas"] - result["tersedia"]
    ).clip(lower=0)
    result["terisi"] = result["terisi"].where(
        result["terisi"] == calculated_occupied,
        calculated_occupied,
    )
    result["kode_rs"] = "RSDS"
    result["nama_rs"] = "RSUD Dr. Soetomo"
    result["kategori_pasien"] = "Umum"
    result["waktu_update_sumber"] = source_update
    result["waktu_scraping"] = datetime.now(JAKARTA).strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )
    result["sumber_url"] = URL_SOETOMO
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
    ]
    return result[ordered_columns].reset_index(drop=True)
def create_room_summary(detail: pd.DataFrame) -> pd.DataFrame:
    """Meringkas unit bed berdasarkan kelas dan ruang."""
    summary = (
        detail.groupby(
            [
                "kode_rs",
                "nama_rs",
                "kategori_pasien",
                "kelas",
                "nama_ruang",
            ],
            as_index=False,
        )
        .agg(
            kapasitas=("kapasitas", "sum"),
            terisi=("terisi", "sum"),
            tersedia=("tersedia", "sum"),
            tidak_siap=("tidak_siap", "sum"),
            renovasi=("renovasi", "sum"),
            sisrute=("sisrute", "sum"),
            terisi_pria=("terisi_pria", "sum"),
            terisi_wanita=("terisi_wanita", "sum"),
            waktu_update_sumber=("waktu_update_sumber", "first"),
            waktu_scraping=("waktu_scraping", "first"),
            sumber_url=("sumber_url", "first"),
            keterangan=("keterangan", "first"),
        )
    )
    summary["persentase_keterisian"] = (
        summary["terisi"]
        .div(summary["kapasitas"].replace(0, pd.NA))
        .mul(100)
        .fillna(0)
        .round(2)
    )
    return summary
def validate_bed_data(data: pd.DataFrame) -> None:
    if data.empty:
        raise ValueError("Hasil scraping kosong.")
    numeric_columns = ["kapasitas", "terisi", "tersedia"]
    if (data[numeric_columns] < 0).any().any():
        raise ValueError("Ditemukan angka negatif pada data bed.")
    if (data["tersedia"] > data["kapasitas"]).any():
        raise ValueError("Ada nilai tersedia yang melebihi kapasitas.")
def scrape_soetomo() -> pd.DataFrame:
    """Menjalankan pengambilan, parsing, pembersihan, dan validasi."""
    html = fetch_html()
    source_update = extract_source_update(html)
    raw_data = extract_bed_tables(html)
    clean_data = clean_bed_data(raw_data, source_update)
    summary = create_room_summary(clean_data)
    validate_bed_data(summary)
    return summary
if __name__ == "__main__":
    dataframe = scrape_soetomo()
    print("Scraping berhasil.")
    print(f"Jumlah ruang: {len(dataframe)}")
    print(
        "Update sumber:",
        dataframe["waktu_update_sumber"].iloc[0],
    )
    print(dataframe.head(10).to_string(index=False))
