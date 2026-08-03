from __future__ import annotations
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime
import time
from zoneinfo import ZoneInfo
import pandas as pd
import requests
from bs4 import BeautifulSoup
URL_SOEDONO = "https://apprssm.rssoedono.jatimprov.go.id/bed/"
DETAIL_URL = (
    "https://apprssm.rssoedono.jatimprov.go.id/"
    "bed/Home/lihat_detail"
)
JAKARTA = ZoneInfo("Asia/Jakarta")
def _headers() -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": URL_SOEDONO,
    }
def fetch_main_page(session: requests.Session) -> str:
    response = session.get(
        URL_SOEDONO,
        headers=_headers(),
        params={"_scrape_ts": int(time.time() * 1000)},
        timeout=60,
        verify=False,
    )
    response.raise_for_status()
    if not response.text.strip():
        raise ValueError("Halaman bed Soedono mengirim HTML kosong.")
    return response.text
def extract_class_list(html: str) -> list[dict[str, str]]:
    """Mengambil nama dan kode seluruh kelas dari card utama."""
    soup = BeautifulSoup(html, "html.parser")
    classes: list[dict[str, str]] = []
    for card in soup.select(".bed-card"):
        button = card.select_one("button.card-detail[data-id]")
        label = card.select_one(".bed-capacity-label")
        if button is None or label is None:
            continue
        class_code = str(button.get("data-id", "")).strip()
        class_name = " ".join(label.get_text(" ", strip=True).split())
        if class_code and class_name:
            classes.append(
                {
                    "kode_kelas": class_code,
                    "kelas": class_name,
                }
            )
    if not classes:
        raise ValueError(
            "Card kelas Soedono tidak ditemukan. Struktur website berubah."
        )
    return classes
def fetch_class_detail(
    session: requests.Session,
    class_code: str,
) -> str:
    headers = _headers()
    headers["X-Requested-With"] = "XMLHttpRequest"
    response = session.post(
        DETAIL_URL,
        headers=headers,
        data={"rowid": class_code},
        timeout=60,
        verify=False,
    )
    response.raise_for_status()
    if not response.text.strip():
        raise ValueError(
            f"Detail kelas {class_code} mengirim HTML kosong."
        )
    return response.text
def parse_class_detail(
    html: str,
    class_name: str,
) -> list[dict]:
    """Membaca tabel detail ruang dari HTML modal."""
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict] = []
    for table_row in soup.select(
        "table.modal-detail-table tbody tr"
    ):
        cells = [
            " ".join(cell.get_text(" ", strip=True).split())
            for cell in table_row.select("td")
        ]
        if len(cells) < 5:
            continue
        rows.append(
            {
                "kelas": class_name,
                "nama_ruang": cells[0],
                "kapasitas": cells[1],
                "tersedia": cells[2],
                "renovasi": cells[3],
                "sisrute": cells[4],
            }
        )
    if not rows:
        raise ValueError(
            f"Tabel detail kelas {class_name} tidak memiliki data."
        )
    return rows
def clean_bed_data(rows: list[dict]) -> pd.DataFrame:
    result = pd.DataFrame(rows)
    for column in ["kelas", "nama_ruang"]:
        result[column] = (
            result[column]
            .astype(str)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
    numeric_columns = [
        "kapasitas",
        "tersedia",
        "renovasi",
        "sisrute",
    ]
    for column in numeric_columns:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )
    result = result.dropna(
        subset=["kelas", "nama_ruang", *numeric_columns]
    )
    result[numeric_columns] = result[numeric_columns].astype(int)
    result["terisi"] = (
        result["kapasitas"]
        - result["tersedia"]
        - result["renovasi"]
        - result["sisrute"]
    ).clip(lower=0)
    result["terisi_pria"] = 0
    result["terisi_wanita"] = 0
    result["tidak_siap"] = 0
    result["keterangan"] = ""
    scrape_time = datetime.now(JAKARTA)
    result["kode_rs"] = "RSSM"
    result["nama_rs"] = "RSUD dr. Soedono Madiun"
    result["kategori_pasien"] = "Umum"
    result["waktu_update_sumber"] = scrape_time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    result["waktu_scraping"] = scrape_time.strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )
    result["sumber_url"] = URL_SOEDONO
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
        raise ValueError("Hasil scraping Soedono kosong.")
    numeric_columns = [
        "kapasitas",
        "terisi",
        "tersedia",
        "renovasi",
        "sisrute",
    ]
    if (data[numeric_columns] < 0).any().any():
        raise ValueError("Ditemukan angka negatif pada data Soedono.")
    reconciled = (
        data["terisi"]
        + data["tersedia"]
        + data["renovasi"]
        + data["sisrute"]
    )
    if (reconciled != data["kapasitas"]).any():
        raise ValueError(
            "Data Soedono tidak memenuhi kapasitas = digunakan + "
            "tersedia + renovasi + Sisrute."
        )
def scrape_soedono() -> pd.DataFrame:
    all_rows: list[dict] = []
    with requests.Session() as session:
        main_html = fetch_main_page(session)
        classes = extract_class_list(main_html)
        for class_item in classes:
            detail_html = fetch_class_detail(
                session,
                class_item["kode_kelas"],
            )
            all_rows.extend(
                parse_class_detail(
                    detail_html,
                    class_item["kelas"],
                )
            )
    clean_data = clean_bed_data(all_rows)
    validate_bed_data(clean_data)
    return clean_data
if __name__ == "__main__":
    dataframe = scrape_soedono()
    print("Scraping RSUD dr. Soedono Madiun berhasil.")
    print(f"Jumlah ruang: {len(dataframe)}")
    print(f"Jumlah kelas: {dataframe['kelas'].nunique()}")
    print(dataframe.head(10).to_string(index=False))
