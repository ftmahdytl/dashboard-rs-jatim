from __future__ import annotations

import json
import os
import urllib3
import pandas as pd
import requests
import streamlit as st

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Map of 9 AVLOS Endpoints provided by Open Data Jatim
AVLOS_ENDPOINTS = {
    "RSDS": {
        "nama_rs": "RSUD Dr. Soetomo",
        "url": "https://opendata.jatimprov.go.id/api/cleaned-bigdata/rumah_sakit_umum_daerah_dr_soetomo_surabaya_provinsi_jawa_tim/avlos_average_length_of_stay_4",
    },
    "RSSA": {
        "nama_rs": "RSUD Dr. Saiful Anwar",
        "url": "https://opendata.jatimprov.go.id/api/cleaned-bigdata/rumah_sakit_umum_daerah_dr_saiful_anwar_malang_provinsi_jawa_/avlos_average_length_of_stay_6",
    },
    "RSSM": {
        "nama_rs": "RSUD dr. Soedono Madiun",
        "url": "https://opendata.jatimprov.go.id/api/cleaned-bigdata/rumah_sakit_umum_daerah_dr_soedono_madiun_provinsi_jawa_timur/avlos_average_length_of_stay_2",
    },
    "RSHJ": {
        "nama_rs": "RSUD Haji Provinsi Jawa Timur",
        "url": "https://opendata.jatimprov.go.id/api/cleaned-bigdata/rumah_sakit_umum_daerah_haji_provinsi_jawa_timur/avlos_average_length_of_stay_3",
    },
    "RSPJ": {
        "nama_rs": "RS Paru Jember",
        "url": "https://opendata.jatimprov.go.id/api/cleaned-bigdata/rumah_sakit_paru_jember/avlos_average_length_of_stay_7",
    },
    "RSPM": {
        "nama_rs": "RS Paru Manguharjo Madiun",
        "url": "https://opendata.jatimprov.go.id/api/cleaned-bigdata/rumah_sakit_paru_manguharjo_madiun/avlos_average_length_of_stay_5",
    },
    "RSMM": {
        "nama_rs": "RS Mata Masyarakat Jawa Timur",
        "url": "https://opendata.jatimprov.go.id/api/cleaned-bigdata/rumah_sakit_mata_masyarakat_jawa_timur/avlos_average_length_of_stay",
    },
    "RSMNO": {
        "nama_rs": "RSU Mohammad Noer Pamekasan",
        "url": "https://opendata.jatimprov.go.id/api/cleaned-bigdata/rumah_sakit_umum_daerah_mohammad_noer_pamekasan/avlos_average_length_of_stay_9",
    },
    "RSDH": {
        "nama_rs": "RSUD Daha Husada Kediri",
        "url": "https://opendata.jatimprov.go.id/api/cleaned-bigdata/rumah_sakit_umum_daerah_daha_husada/avlos_avarage_length_of_stay",
    },
}


@st.cache_data(ttl=3600)
def fetch_avlos_data() -> pd.DataFrame:
    """Mengambil data AVLOS dari 9 endpoint Open Data Jatim dan menggabungkannya ke DataFrame."""
    all_rows: list[dict[str, object]] = []

    for kode_rs, info in AVLOS_ENDPOINTS.items():
        nama_rs = info["nama_rs"]
        url = info["url"]
        try:
            r = requests.get(url, params={"per_page": 300}, verify=False, timeout=12)
            if r.status_code == 200:
                res_json = r.json()
                data_list = res_json.get("data", [])
                for item in data_list:
                    # Ambil nilai AVLOS (khusus RSSA memakai kunci 'jumlah')
                    val = item.get("avlos")
                    if val is None:
                        val = item.get("jumlah")

                    try:
                        val_float = float(val) if val is not None else None
                    except (ValueError, TypeError):
                        val_float = None

                    periode = str(item.get("periode_update", "")).strip()
                    tahun_val = item.get("tahun")
                    try:
                        tahun_int = int(tahun_val) if tahun_val is not None else None
                    except (ValueError, TypeError):
                        tahun_int = None

                    if not tahun_int and len(periode) >= 4 and periode[:4].isdigit():
                        tahun_int = int(periode[:4])

                    if val_float is not None and periode:
                        all_rows.append(
                            {
                                "kode_rs": kode_rs,
                                "nama_rs": nama_rs,
                                "periode_update": periode,
                                "tahun": tahun_int,
                                "avlos": val_float,
                                "satuan": str(item.get("satuan", "HARI")).upper(),
                            }
                        )
        except Exception as err:
            st.warning(f"Gagal mengambil data AVLOS {nama_rs}: {err}")

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df = df.sort_values(by=["periode_update", "nama_rs"]).reset_index(drop=True)
    return df
