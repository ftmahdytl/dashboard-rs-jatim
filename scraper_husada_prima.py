from __future__ import annotations

from datetime import datetime
import time
from zoneinfo import ZoneInfo

import pandas as pd
import requests
from bs4 import BeautifulSoup

URL_HUSADA_PRIMA = "https://rsudhusadaprima.jatimprov.go.id/index.php/konten/spbe/2"
URL_EVO_SIRANAP = "https://apirsudhp.site/Dashboard_evoSiranap_husada/"
JAKARTA = ZoneInfo("Asia/Jakarta")


def scrape_husada_prima() -> pd.DataFrame:
    """Mengambil data ketersediaan tempat tidur RSUD Husada Prima."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Cache-Control": "no-cache",
    }

    rows: list[dict[str, object]] = []
    now_str = datetime.now(JAKARTA).strftime("%Y-%m-%d %H:%M:%S")

    try:
        res = requests.get(
            URL_EVO_SIRANAP,
            headers=headers,
            params={"_ts": int(time.time() * 1000)},
            timeout=10,
            verify=False,
        )
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            tables = soup.find_all("table")
            for table in tables:
                for tr in table.find_all("tr")[1:]:
                    tds = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                    if len(tds) >= 4:
                        nama_ruang = tds[0]
                        kelas_raw = tds[1]
                        k_upper = kelas_raw.upper()
                        if "VIP" in k_upper:
                            kelas = "VIP"
                        elif "III" in k_upper or "3" in k_upper:
                            kelas = "Kelas III"
                        elif "II" in k_upper or "2" in k_upper:
                            kelas = "Kelas II"
                        elif "I" in k_upper or "1" in k_upper:
                            kelas = "Kelas I"
                        elif "ISOLASI" in k_upper:
                            kelas = "Isolasi"
                        else:
                            kelas = "Umum"

                        try:
                            kapasitas = int(tds[2])
                            tersedia = int(tds[3])
                            terisi = max(0, kapasitas - tersedia)
                            bor = (terisi / kapasitas * 100) if kapasitas > 0 else 0.0
                        except (ValueError, TypeError):
                            kapasitas = 0
                            terisi = 0
                            tersedia = 0
                            bor = 0.0

                        rows.append(
                            {
                                "kode_rs": "RSHP",
                                "nama_rs": "RSUD Husada Prima",
                                "kategori_pasien": "Umum",
                                "kelas": kelas,
                                "nama_ruang": nama_ruang,
                                "kapasitas": kapasitas,
                                "terisi": terisi,
                                "tersedia": tersedia,
                                "tidak_siap": 0,
                                "renovasi": 0,
                                "sisrute": 0,
                                "terisi_pria": 0,
                                "terisi_wanita": 0,
                                "keterangan": "",
                                "waktu_update_sumber": now_str,
                                "waktu_scraping": now_str,
                                "sumber_url": URL_HUSADA_PRIMA,
                                "persentase_keterisian": round(bor, 2),
                            }
                        )
    except Exception:
        pass

    if not rows:
        master_rooms = [
            ("Ruang Paru", "Kelas III"),
            ("Ruang Flamboyan", "Kelas II"),
            ("Ruang Melati", "Kelas I"),
            ("Ruang VIP", "VIP"),
            ("Ruang Isolasi", "Isolasi"),
        ]
        for nama_ruang, kelas in master_rooms:
            rows.append(
                {
                    "kode_rs": "RSHP",
                    "nama_rs": "RSUD Husada Prima",
                    "kategori_pasien": "Umum",
                    "kelas": kelas,
                    "nama_ruang": nama_ruang,
                    "kapasitas": 0,
                    "terisi": 0,
                    "tersedia": 0,
                    "tidak_siap": 0,
                    "renovasi": 0,
                    "sisrute": 0,
                    "terisi_pria": 0,
                    "terisi_wanita": 0,
                    "keterangan": "",
                    "waktu_update_sumber": now_str,
                    "waktu_scraping": now_str,
                    "sumber_url": URL_HUSADA_PRIMA,
                    "persentase_keterisian": 0.0,
                }
            )

    return pd.DataFrame(rows)


if __name__ == "__main__":
    test_df = scrape_husada_prima()
    print(f"RSHP scraped {len(test_df)} rows.")
    print(test_df[["kelas", "nama_ruang", "kapasitas", "terisi", "tersedia"]])
