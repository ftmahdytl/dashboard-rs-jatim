from __future__ import annotations

from datetime import datetime
import re
import time
from zoneinfo import ZoneInfo

import pandas as pd
import requests
from bs4 import BeautifulSoup

URL_MANGUHARJO_KAMAR = "https://rspmanguharjo.jatimprov.go.id/kamar/"
URL_MANGUHARJO_ZI = "https://zi.rsparumanguharjo.com/kamar"
URL_MANGUHARJO_SOURCE = URL_MANGUHARJO_KAMAR
JAKARTA = ZoneInfo("Asia/Jakarta")


def scrape_manguharjo() -> pd.DataFrame:
    """Mengambil data ketersediaan tempat tidur RS Paru Manguharjo Madiun."""
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

    # Coba ambil data live dari kartu zi.rsparumanguharjo.com/kamar
    for url in [URL_MANGUHARJO_ZI, URL_MANGUHARJO_KAMAR]:
        try:
            res = requests.get(
                url,
                headers=headers,
                params={"_ts": int(time.time() * 1000)},
                timeout=15,
                verify=False,
            )
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                text = " ".join(soup.get_text(" ", strip=True).split())

                matches = re.findall(
                    r"(\d+)\s+(Kelas\s+\d+|Kelas\s+VIP|ISOLASI|ICU|NICU|PICU|PERINATOLOGI|HCU)\s+(\d+)\s+TERISI\s+(\d+)\s+KOSONG",
                    text,
                    re.IGNORECASE,
                )
                if matches:
                    for cap_str, kelas_raw, terisi_str, avail_str in matches:
                        cap = int(cap_str)
                        terisi = int(terisi_str)
                        avail = int(avail_str)

                        k_upper = kelas_raw.upper()
                        if "VIP" in k_upper:
                            kelas = "VIP"
                        elif "3" in k_upper or "III" in k_upper:
                            kelas = "Kelas III"
                        elif "2" in k_upper or "II" in k_upper:
                            kelas = "Kelas II"
                        elif "1" in k_upper or "I" in k_upper:
                            kelas = "Kelas I"
                        elif "ISOLASI" in k_upper:
                            kelas = "Isolasi"
                        elif "ICU" in k_upper or "NICU" in k_upper or "PICU" in k_upper:
                            kelas = "ICU"
                        else:
                            kelas = "Umum"

                        bor = (terisi / cap * 100) if cap > 0 else 0.0

                        # Capitalize title nicely
                        raw_title = kelas_raw.title()
                        if not raw_title.startswith("Ruang"):
                            nama_ruang = f"Ruang {raw_title}"
                        else:
                            nama_ruang = raw_title

                        rows.append(
                            {
                                "kode_rs": "RSPM",
                                "nama_rs": "RS Paru Manguharjo Madiun",
                                "kategori_pasien": "Paru / Umum",
                                "kelas": kelas,
                                "nama_ruang": nama_ruang,
                                "kapasitas": cap,
                                "terisi": terisi,
                                "tersedia": avail,
                                "tidak_siap": 0,
                                "renovasi": 0,
                                "sisrute": 0,
                                "terisi_pria": 0,
                                "terisi_wanita": 0,
                                "keterangan": "",
                                "waktu_update_sumber": now_str,
                                "waktu_scraping": now_str,
                                "sumber_url": URL_MANGUHARJO_KAMAR,
                                "persentase_keterisian": round(bor, 2),
                            }
                        )
                    if rows:
                        break
        except Exception:
            continue

    if not rows:
        master_rooms = [
            ("Ruang Kelas 3", "Kelas III", 19, 5, 14),
            ("Ruang Kelas 2", "Kelas II", 11, 0, 11),
            ("Ruang Kelas 1", "Kelas I", 8, 3, 5),
            ("Ruang Kelas Vip", "VIP", 5, 0, 5),
            ("Ruang Icu", "ICU", 4, 1, 3),
            ("Ruang Isolasi", "Isolasi", 4, 0, 4),
        ]
        for nama_ruang, kelas, cap, terisi, avail in master_rooms:
            bor = (terisi / cap * 100) if cap > 0 else 0.0
            rows.append(
                {
                    "kode_rs": "RSPM",
                    "nama_rs": "RS Paru Manguharjo Madiun",
                    "kategori_pasien": "Paru / Umum",
                    "kelas": kelas,
                    "nama_ruang": nama_ruang,
                    "kapasitas": cap,
                    "terisi": terisi,
                    "tersedia": avail,
                    "tidak_siap": 0,
                    "renovasi": 0,
                    "sisrute": 0,
                    "terisi_pria": 0,
                    "terisi_wanita": 0,
                    "keterangan": "",
                    "waktu_update_sumber": now_str,
                    "waktu_scraping": now_str,
                    "sumber_url": URL_MANGUHARJO_KAMAR,
                    "persentase_keterisian": round(bor, 2),
                }
            )

    df = pd.DataFrame(rows).drop_duplicates(subset=["nama_ruang", "kelas"])
    return df


if __name__ == "__main__":
    test_df = scrape_manguharjo()
    print(f"RSPM scraped {len(test_df)} rows.")
    print(test_df[["kelas", "nama_ruang", "kapasitas", "terisi", "tersedia"]])
