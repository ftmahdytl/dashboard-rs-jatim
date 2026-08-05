from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json
import re

import pandas as pd
import requests
import streamlit as st


API_ROOT = "https://opendata.jatimprov.go.id/api/cleaned-bigdata"
CACHE_DIR = Path(__file__).parent / "data"
CACHE_FILE = CACHE_DIR / "nakes_api_cache.csv"
CACHE_STATUS_FILE = CACHE_DIR / "nakes_api_status.json"

HOSPITALS_NAKES = [
    "RSUD Dr. Soetomo",
    "RSUD Dr. Saiful Anwar",
    "RSUD dr. Soedono Madiun",
    "RSUD Haji Provinsi Jawa Timur",
    "RS Jiwa Menur Provinsi Jawa Timur",
    "RSUD Karsa Husada Batu",
    "RSUD Sumberglagah",
    "RSU Mohammad Noer Pamekasan",
    "RSUD Dungus Madiun",
    "RSUD Daha Husada Kediri",
    "RSUD Husada Prima",
    "RS Paru Jember",
    "RS Mata Masyarakat Jawa Timur",
    "RS Paru Manguharjo Madiun",
]

GROUPS = [
    "Dokter/Tenaga Medis",
    "Perawat",
    "Tenaga Kesehatan Lainnya",
]


def _url(organization: str, endpoint: str) -> str:
    return f"{API_ROOT}/{organization}/{endpoint}"


# Endpoint tanpa parameter periode agar semester baru ikut terbaca otomatis.
# Nilai None berarti dataset belum tersedia pada portal sumber.
NAKES_ENDPOINTS: dict[str, dict[str, str | None]] = {
    "RSUD Dr. Soetomo": {
        "Dokter/Tenaga Medis": _url(
            "rumah_sakit_umum_daerah_dr_soetomo_surabaya_provinsi_jawa_tim",
            "jumlah_doktertenaga_medis_berdasarkan_jenis_kelamin_4",
        ),
        "Perawat": _url(
            "rumah_sakit_umum_daerah_dr_soetomo_surabaya_provinsi_jawa_tim",
            "jumlah_perawat_berdasarkan_jenis_kelamin_4",
        ),
        "Bidan": None,
        "Tenaga Kesehatan Lainnya": _url(
            "rumah_sakit_umum_daerah_dr_soetomo_surabaya_provinsi_jawa_tim",
            "jumlah_tenaga_kesehatan_lainnya_berdasarkan_jenis_kelamin_4",
        ),
    },
    "RSUD Dr. Saiful Anwar": {
        "Dokter/Tenaga Medis": _url(
            "rumah_sakit_umum_daerah_dr_saiful_anwar_malang_provinsi_jawa_",
            "jumlah_doktertenaga_medis_berdasarkan_jenis_kelamin_2",
        ),
        "Perawat": _url(
            "rumah_sakit_umum_daerah_dr_saiful_anwar_malang_provinsi_jawa_",
            "jumlah_perawat_berdasarkan_jenis_kelamin_2",
        ),
        "Bidan": _url(
            "rumah_sakit_umum_daerah_dr_saiful_anwar_malang_provinsi_jawa_",
            "jumlah_bidan_2",
        ),
        "Tenaga Kesehatan Lainnya": _url(
            "rumah_sakit_umum_daerah_dr_saiful_anwar_malang_provinsi_jawa_",
            "jumlah_tenaga_kesehatan_lainnya_berdasarkan_jenis_kelamin",
        ),
    },
    "RSUD dr. Soedono Madiun": {
        "Dokter/Tenaga Medis": _url(
            "rumah_sakit_umum_daerah_dr_soedono_madiun_provinsi_jawa_timur",
            "jumlah_doktertenaga_medis_berdasarkan_jenis_kelamin",
        ),
        "Perawat": _url(
            "rumah_sakit_umum_daerah_dr_soedono_madiun_provinsi_jawa_timur",
            "jumlah_perawat_berdasarkan_jenis_kelamin",
        ),
        "Bidan": _url(
            "rumah_sakit_umum_daerah_dr_soedono_madiun_provinsi_jawa_timur",
            "jumlah_bidan",
        ),
        "Tenaga Kesehatan Lainnya": _url(
            "rumah_sakit_umum_daerah_dr_soedono_madiun_provinsi_jawa_timur",
            "jumlah_tenaga_kesehatan_lainnya_berdasarkan_jenis_kelamin_3",
        ),
    },
    "RSUD Haji Provinsi Jawa Timur": {
        "Dokter/Tenaga Medis": _url(
            "rumah_sakit_umum_daerah_haji_provinsi_jawa_timur",
            "jumlah_doktertenaga_medis_berdasarkan_jenis_kelamin_5",
        ),
        "Perawat": _url(
            "rumah_sakit_umum_daerah_haji_provinsi_jawa_timur",
            "jumlah_perawat_berdasarkan_jenis_kelamin_5",
        ),
        "Bidan": _url(
            "rumah_sakit_umum_daerah_haji_provinsi_jawa_timur",
            "jumlah_bidan_5",
        ),
        "Tenaga Kesehatan Lainnya": _url(
            "rumah_sakit_umum_daerah_haji_provinsi_jawa_timur",
            "jumlah_tenaga_kesehatan_lainnya_berdasarkan_jenis_kelamin_5",
        ),
    },
    "RS Jiwa Menur Provinsi Jawa Timur": {
        "Dokter/Tenaga Medis": _url(
            "rumah_sakit_jiwa_menur_surabaya_provinsi_jawa_timur",
            "jumlah_doktertenaga_medis_berdasarkan_jenis_kelamin_3",
        ),
        "Perawat": _url(
            "rumah_sakit_jiwa_menur_surabaya_provinsi_jawa_timur",
            "jumlah_perawat_berdasarkan_jenis_kelamin_3",
        ),
        "Bidan": _url(
            "rumah_sakit_jiwa_menur_surabaya_provinsi_jawa_timur",
            "jumlah_bidan_3",
        ),
        "Tenaga Kesehatan Lainnya": _url(
            "rumah_sakit_jiwa_menur_surabaya_provinsi_jawa_timur",
            "jumlah_tenaga_kesehatan_lainnya_berdasarkan_jenis_kelamin_2",
        ),
    },
    "RSUD Karsa Husada Batu": {
        "Dokter/Tenaga Medis": _url(
            "rumah_sakit_umum_daerah_karsa_husada",
            "jumlah_doktertenaga_medis_berdasarkan_jenis_kelamin_12",
        ),
        "Perawat": _url(
            "rumah_sakit_umum_daerah_karsa_husada",
            "jumlah_perawat_berdasarkan_jenis_kelamin_12",
        ),
        "Bidan": _url(
            "rumah_sakit_umum_daerah_karsa_husada",
            "jumlah_tenaga_bidan",
        ),
        "Tenaga Kesehatan Lainnya": _url(
            "rumah_sakit_umum_daerah_karsa_husada",
            "jumlah_tenaga_kesehatan_lainnya_berdasarkan_jenis_kelamin_12",
        ),
    },
    "RSUD Sumberglagah": {
        group: None for group in GROUPS
    },
    "RSU Mohammad Noer Pamekasan": {
        "Dokter/Tenaga Medis": _url(
            "rumah_sakit_umum_daerah_mohammad_noer_pamekasan",
            "jumlah_doktertenaga_medis_berdasarkan_jenis_kelamin_11",
        ),
        "Perawat": _url(
            "rumah_sakit_umum_daerah_mohammad_noer_pamekasan",
            "jumlah_perawat_berdasarkan_jenis_kelamin_11",
        ),
        "Bidan": None,
        "Tenaga Kesehatan Lainnya": _url(
            "rumah_sakit_umum_daerah_mohammad_noer_pamekasan",
            "jumlah_tenaga_kesehatan_lainnya_berdasarkan_jenis_kelamin_11",
        ),
    },
    "RSUD Dungus Madiun": {
        "Dokter/Tenaga Medis": _url(
            "rumah_sakit_umum_daerah_dungus",
            "jumlah_doktertenaga_medis_berdasarkan_jenis_kelamin_13",
        ),
        "Perawat": _url(
            "rumah_sakit_umum_daerah_dungus",
            "jumlah_perawat_berdasarkan_jenis_kelamin_13",
        ),
        "Bidan": None,
        "Tenaga Kesehatan Lainnya": _url(
            "rumah_sakit_umum_daerah_dungus",
            "jumlah_tenaga_kesehatan_lainnya_berdasarkan_jenis_kelamin_13",
        ),
    },
    "RSUD Daha Husada Kediri": {
        "Dokter/Tenaga Medis": _url(
            "rumah_sakit_umum_daerah_daha_husada",
            "jumlah_doktertenaga_medis_berdasarkan_jenis_kelamin_9",
        ),
        "Perawat": _url(
            "rumah_sakit_umum_daerah_daha_husada",
            "jumlah_perawat_berdasarkan_jenis_kelamin_9",
        ),
        "Bidan": None,
        "Tenaga Kesehatan Lainnya": _url(
            "rumah_sakit_umum_daerah_daha_husada",
            "jmlh_tng_kshtn_lnny_brdsrkn_jns_klmn",
        ),
    },
    "RSUD Husada Prima": {
        group: None for group in GROUPS
    },
    "RS Paru Jember": {
        "Dokter/Tenaga Medis": _url(
            "rumah_sakit_paru_jember",
            "jumlah_doktertenaga_medis_berdasarkan_jenis_kelamin_8",
        ),
        "Perawat": _url(
            "rumah_sakit_paru_jember",
            "jumlah_perawat_berdasarkan_jenis_kelamin_8",
        ),
        "Bidan": _url(
            "rumah_sakit_paru_jember",
            "jumlah_tenaga_bidan",
        ),
        "Tenaga Kesehatan Lainnya": _url(
            "rumah_sakit_paru_jember",
            "jumlah_tenaga_kesehatan_lainnya_berdasarkan_jenis_kelamin_8",
        ),
    },
    "RS Mata Masyarakat Jawa Timur": {
        "Dokter/Tenaga Medis": _url(
            "rumah_sakit_mata_masyarakat_jawa_timur",
            "jumlah_doktertenaga_medis_berdasarkan_jenis_kelamin_7",
        ),
        "Perawat": _url(
            "rumah_sakit_mata_masyarakat_jawa_timur",
            "jumlah_perawat_berdasarkan_jenis_kelamin_7",
        ),
        "Bidan": None,
        "Tenaga Kesehatan Lainnya": _url(
            "rumah_sakit_mata_masyarakat_jawa_timur",
            "jumlah_tenaga_kesehatan_lainnya_berdasarkan_jenis_kelamin_7",
        ),
    },
    "RS Paru Manguharjo Madiun": {
        "Dokter/Tenaga Medis": _url(
            "rumah_sakit_paru_manguharjo_madiun",
            "jumlah_doktertenaga_medis_berdasarkan_jenis_kelamin_6",
        ),
        "Perawat": _url(
            "rumah_sakit_paru_manguharjo_madiun",
            "jumlah_perawat_berdasarkan_jenis_kelamin_6",
        ),
        "Bidan": None,
        "Tenaga Kesehatan Lainnya": _url(
            "rumah_sakit_paru_manguharjo_madiun",
            "jumlah_tenaga_kesehatan_lainnya_berdasarkan_jenis_kelamin_6",
        ),
    },
}


def _clean_text(
    value: object,
    fallback: str = "Tidak dirinci",
) -> str:
    if value is None or (
        isinstance(value, float) and pd.isna(value)
    ):
        return fallback

    text = str(value).strip()

    if text and text.lower() not in {"nan", "none", "-"}:
        return text

    return fallback


def _gender(value: object) -> str:
    key = re.sub(
        r"[^a-z]",
        "",
        str(value).lower(),
    )

    if key in {
        "l",
        "lk",
        "lakilaki",
        "pria",
        "male",
    }:
        return "Laki-laki"

    if key in {
        "p",
        "pr",
        "perempuan",
        "wanita",
        "female",
    }:
        return "Perempuan"

    return "Tidak dirinci"


def _number(value: object) -> float | None:
    try:
        number = float(
            str(value)
            .replace(".", "")
            .replace(",", ".")
        )
    except (TypeError, ValueError):
        return None

    return number if number >= 0 else None


def _fetch_all_pages(
    url: str,
    timeout: int = 35,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    page = 1

    with requests.Session() as session:
        while page <= 100:
            response = session.get(
                url,
                params={"page": page},
                timeout=timeout,
            )
            response.raise_for_status()

            payload = response.json()

            page_rows = (
                payload.get("data", [])
                if isinstance(payload, dict)
                else []
            )

            if not isinstance(page_rows, list):
                raise ValueError(
                    "Format data API tidak dikenali"
                )

            rows.extend(
                item
                for item in page_rows
                if isinstance(item, dict)
            )

            pagination = (
                payload.get("pagination", {})
                if isinstance(payload, dict)
                else {}
            )

            total_pages = int(
                pagination.get("total_page") or 1
            )

            has_next = bool(
                pagination.get(
                    "has_next",
                    page < total_pages,
                )
            )

            if not has_next and page >= total_pages:
                break

            page += 1

    return rows


def _normalize_rows(
    hospital: str,
    group: str,
    url: str,
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []

    for row in rows:
        period = _clean_text(
            row.get("periode_update"),
            "",
        )

        if not re.fullmatch(
            r"20\d{2}-S[12]",
            period.upper(),
        ):
            continue

        qualification = _clean_text(
            row.get("kualifikasi_pendidikan")
            or row.get("kualifikasi_pendidikan_")
            or row.get(
                "kualifikasi_pendidikan_terakhir"
            )
            or row.get(
                "jenis_ketenagaan_kesehatan_lainnya"
            )
            or row.get(
                "jenis_tenaga_kesehatan_lainnya"
            )
        )

        common = {
            "nama_rs": hospital,
            "periode": period.upper(),
            "kelompok": group,
            "kualifikasi": qualification,
            "sumber_api": url,
        }

        separate_gender = (
            "laki_laki" in row
            or "perempuan" in row
        )

        if separate_gender:
            gender_fields = (
                ("Laki-laki", "laki_laki"),
                ("Perempuan", "perempuan"),
            )

            for gender_name, field in gender_fields:
                amount = _number(row.get(field))

                if amount is not None:
                    output.append(
                        {
                            **common,
                            "jenis_kelamin": gender_name,
                            "jumlah": amount,
                        }
                    )

            continue

        amount = _number(
            row.get(
                "jumlah",
                row.get("jumlah_tenaga_bidan"),
            )
        )

        if amount is not None:
            output.append(
                {
                    **common,
                    "jenis_kelamin": _gender(
                        row.get("kategori")
                    ),
                    "jumlah": amount,
                }
            )

    return output


def _read_cache() -> pd.DataFrame:
    if not CACHE_FILE.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(CACHE_FILE)
        if not df.empty and "kelompok" in df.columns:
            df["kelompok"] = df["kelompok"].replace({"Bidan": "Tenaga Kesehatan Lainnya"})
        return df
    except Exception:
        return pd.DataFrame()


def _write_cache(
    data: pd.DataFrame,
    statuses: list[dict[str, object]],
) -> None:
    try:
        CACHE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        data.to_csv(
            CACHE_FILE,
            index=False,
        )

        CACHE_STATUS_FILE.write_text(
            json.dumps(
                statuses,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except OSError:
        # Dashboard tetap berjalan bila host read-only.
        pass


@st.cache_data(
    ttl=3600,
    show_spinner=False,
)
def load_nakes_data() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    list[str],
]:
    tasks = [
        (hospital, group, url)
        for hospital, endpoints
        in NAKES_ENDPOINTS.items()
        for group, url in endpoints.items()
        if url
    ]

    normalized: list[dict[str, object]] = []
    errors: list[str] = []
    statuses: list[dict[str, object]] = []

    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:
        future_map = {
            executor.submit(
                _fetch_all_pages,
                url,
            ): (hospital, group, url)
            for hospital, group, url in tasks
        }

        for future in as_completed(future_map):
            hospital, group, url = future_map[future]

            try:
                raw_rows = future.result()

                clean_rows = _normalize_rows(
                    hospital,
                    group,
                    url,
                    raw_rows,
                )

                normalized.extend(clean_rows)

                statuses.append(
                    {
                        "nama_rs": hospital,
                        "kelompok": group,
                        "status": "Tersedia",
                        "baris": len(clean_rows),
                    }
                )

            except Exception as exc:
                errors.append(
                    f"{hospital} - {group}: {exc}"
                )

                statuses.append(
                    {
                        "nama_rs": hospital,
                        "kelompok": group,
                        "status": "Gagal diakses",
                        "baris": 0,
                    }
                )

    for hospital, endpoints in NAKES_ENDPOINTS.items():
        for group, url in endpoints.items():
            if url is None:
                statuses.append(
                    {
                        "nama_rs": hospital,
                        "kelompok": group,
                        "status": "Belum tersedia",
                        "baris": 0,
                    }
                )

    fresh = pd.DataFrame(normalized)
    cache = _read_cache()

    if errors and not cache.empty:
        failed_keys = {
            (
                item["nama_rs"],
                item["kelompok"],
            )
            for item in statuses
            if item["status"] == "Gagal diakses"
        }

        cached_failed = cache[
            cache.apply(
                lambda row: (
                    row["nama_rs"],
                    row["kelompok"],
                ) in failed_keys,
                axis=1,
            )
        ]

        fresh = pd.concat(
            [fresh, cached_failed],
            ignore_index=True,
        )

    expected_columns = [
        "nama_rs",
        "periode",
        "kelompok",
        "kualifikasi",
        "jenis_kelamin",
        "jumlah",
        "sumber_api",
    ]

    if fresh.empty:
        fresh = pd.DataFrame(
            columns=expected_columns
        )
    else:
        fresh["kelompok"] = fresh["kelompok"].replace({"Bidan": "Tenaga Kesehatan Lainnya"})
        fresh = (
            fresh
            .drop_duplicates()
            .reset_index(drop=True)
        )

        fresh["jumlah"] = (
            pd.to_numeric(
                fresh["jumlah"],
                errors="coerce",
            )
            .fillna(0)
        )

        _write_cache(
            fresh,
            statuses,
        )

    return (
        fresh,
        pd.DataFrame(statuses),
        errors,
    )


def period_key(value: object) -> int:
    match = re.fullmatch(
        r"(20\d{2})-S([12])",
        str(value).upper(),
    )

    if not match:
        return -1

    return (
        int(match.group(1)) * 10
        + int(match.group(2))
    )