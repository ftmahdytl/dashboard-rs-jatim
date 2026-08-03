from __future__ import annotations
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime
import re
import time
from zoneinfo import ZoneInfo
import pandas as pd
import requests
from bs4 import BeautifulSoup
URL_HAJI = "https://apps.rsuhaji.jatimprov.go.id/bed_display"
JAKARTA = ZoneInfo("Asia/Jakarta")
def fetch_html() -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    response = requests.get(
        URL_HAJI,
        headers=headers,
        params={"_scrape_ts": int(time.time() * 1000)},
        timeout=90,
        verify=False,
    )
    response.raise_for_status()
    if not response.text.strip():
        raise ValueError("Halaman bed RSUD Haji mengirim HTML kosong.")
    return response.text
def extract_source_update(soup: BeautifulSoup) -> str:
    text = " ".join(soup.get_text(" ", strip=True).split())
    match = re.search(
        r"Last\s+Update\s*:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1)
    return datetime.now(JAKARTA).strftime("%Y-%m-%d %H:%M:%S")
def parse_bed_rows(html: str) -> tuple[list[dict], str]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if table is None:
        raise ValueError("Tabel ketersediaan RSUD Haji tidak ditemukan.")
    source_update = extract_source_update(soup)
    current_service: str | None = None
    rows: list[dict] = []
    for table_row in table.find_all("tr"):
        cells = [
            " ".join(cell.get_text(" ", strip=True).split())
            for cell in table_row.find_all("td", recursive=False)
        ]
        # Baris judul layanan: Umum, Anak, Kandungan, dan seterusnya.
        if (
            len(cells) == 6
            and "JML BED" in cells
            and cells[0]
        ):
            current_service = cells[0]
            continue
        if len(cells) != 8 or current_service is None:
            continue
        rows.append(
            {
                "kategori_pasien": current_service,
                "nama_ruang": cells[1],
                "kelas": cells[2],
                "kapasitas": cells[3],
                "terisi": cells[4],
                "kosong": cells[5],
                "tersedia": cells[6],
                "keterangan": cells[7],
            }
        )
    if not rows:
        raise ValueError("Tabel RSUD Haji tidak memiliki data ruang.")
    return rows, source_update
def clean_bed_data(
    rows: list[dict],
    source_update: str,
) -> pd.DataFrame:
    result = pd.DataFrame(rows)
    for column in [
        "kategori_pasien",
        "kelas",
        "nama_ruang",
        "keterangan",
    ]:
        result[column] = (
            result[column]
            .astype(str)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
    numeric_columns = ["kapasitas", "terisi", "kosong", "tersedia"]
    for column in numeric_columns:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )
    result = result.dropna(
        subset=[
            "kategori_pasien",
            "kelas",
            "nama_ruang",
            *numeric_columns,
        ]
    )
    result[numeric_columns] = result[numeric_columns].astype(int)
    result["tidak_siap"] = (
        result["kosong"] - result["tersedia"]
    ).clip(lower=0)
    result["renovasi"] = 0
    result["sisrute"] = 0
    result["terisi_pria"] = 0
    result["terisi_wanita"] = 0
    result["kode_rs"] = "RSHJ"
    result["nama_rs"] = "RSUD Haji Provinsi Jawa Timur"
    result["waktu_update_sumber"] = source_update
    result["waktu_scraping"] = datetime.now(JAKARTA).strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )
    result["sumber_url"] = URL_HAJI
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
        .drop_duplicates(
            subset=["kategori_pasien", "kelas", "nama_ruang"]
        )
        .sort_values(["kategori_pasien", "kelas", "nama_ruang"])
        .reset_index(drop=True)
    )
def validate_bed_data(data: pd.DataFrame) -> None:
    if data.empty:
        raise ValueError("Hasil scraping RSUD Haji kosong.")
    numeric_columns = [
        "kapasitas",
        "terisi",
        "tersedia",
        "tidak_siap",
    ]
    if (data[numeric_columns] < 0).any().any():
        raise ValueError("Ditemukan angka negatif pada data RSUD Haji.")
    reconciled = (
        data["terisi"] + data["tersedia"] + data["tidak_siap"]
    )
    if (reconciled != data["kapasitas"]).any():
        raise ValueError(
            "Data Haji tidak memenuhi kapasitas = isi + siap + "
            "kosong belum siap."
        )
def scrape_haji() -> pd.DataFrame:
    html = fetch_html()
    rows, source_update = parse_bed_rows(html)
    clean_data = clean_bed_data(rows, source_update)
    validate_bed_data(clean_data)
    return clean_data
if __name__ == "__main__":
    dataframe = scrape_haji()
    print("Scraping RSUD Haji berhasil.")
    print(f"Jumlah data ruang-kelas: {len(dataframe)}")
    print(
        f"Jumlah kelompok layanan: "
        f"{dataframe['kategori_pasien'].nunique()}"
    )
    print(dataframe.head(10).to_string(index=False))
