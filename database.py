from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "monitoring_bed.db"

CONTENT_COLUMNS = [
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
]


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA journal_mode=WAL;")
    return connection


def initialize_database() -> None:
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bed_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kode_rs TEXT NOT NULL,
                nama_rs TEXT NOT NULL,
                kategori_pasien TEXT NOT NULL,
                kelas TEXT NOT NULL,
                nama_ruang TEXT NOT NULL,
                kapasitas INTEGER NOT NULL,
                terisi INTEGER NOT NULL,
                tersedia INTEGER NOT NULL,
                tidak_siap INTEGER NOT NULL DEFAULT 0,
                renovasi INTEGER NOT NULL DEFAULT 0,
                sisrute INTEGER NOT NULL DEFAULT 0,
                terisi_pria INTEGER NOT NULL,
                terisi_wanita INTEGER NOT NULL,
                keterangan TEXT NOT NULL DEFAULT '',
                waktu_update_sumber TEXT NOT NULL,
                waktu_scraping TEXT NOT NULL,
                sumber_url TEXT NOT NULL,
                persentase_keterisian REAL NOT NULL
            )
            """
        )
        existing_columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(bed_history)"
            ).fetchall()
        }
        if "renovasi" not in existing_columns:
            connection.execute(
                """
                ALTER TABLE bed_history
                ADD COLUMN renovasi INTEGER NOT NULL DEFAULT 0
                """
            )
        if "tidak_siap" not in existing_columns:
            connection.execute(
                """
                ALTER TABLE bed_history
                ADD COLUMN tidak_siap INTEGER NOT NULL DEFAULT 0
                """
            )
        if "sisrute" not in existing_columns:
            connection.execute(
                """
                ALTER TABLE bed_history
                ADD COLUMN sisrute INTEGER NOT NULL DEFAULT 0
                """
            )
        if "keterangan" not in existing_columns:
            connection.execute(
                """
                ALTER TABLE bed_history
                ADD COLUMN keterangan TEXT NOT NULL DEFAULT ''
                """
            )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_bed_update
            ON bed_history(waktu_update_sumber)
            """
        )


def save_snapshot(data: pd.DataFrame) -> bool:
    """Menyimpan snapshot hanya jika isi data berubah."""
    initialize_database()
    kode_rs = str(data["kode_rs"].iloc[0])

    with connect() as connection:
        latest_scrape = connection.execute(
            """
            SELECT MAX(waktu_scraping)
            FROM bed_history
            WHERE kode_rs = ?
            """,
            (kode_rs,),
        ).fetchone()[0]

        if latest_scrape is not None:
            previous = pd.read_sql_query(
                """
                SELECT
                    kategori_pasien,
                    kelas,
                    nama_ruang,
                    kapasitas,
                    terisi,
                    tersedia,
                    tidak_siap,
                    renovasi,
                    sisrute,
                    terisi_pria,
                    terisi_wanita,
                    keterangan
                FROM bed_history
                WHERE kode_rs = ? AND waktu_scraping = ?
                """,
                connection,
                params=(kode_rs, latest_scrape),
            )

            current_compare = (
                data[CONTENT_COLUMNS]
                .sort_values(["kategori_pasien", "kelas", "nama_ruang"])
                .reset_index(drop=True)
            )
            previous_compare = (
                previous[CONTENT_COLUMNS]
                .sort_values(["kategori_pasien", "kelas", "nama_ruang"])
                .reset_index(drop=True)
            )

            if current_compare.equals(previous_compare):
                return False

        data.to_sql(
            "bed_history",
            connection,
            if_exists="append",
            index=False,
        )

    return True


@st.cache_data(ttl=15)
def load_latest(kode_rs: str) -> pd.DataFrame:
    initialize_database()
    with connect() as connection:
        latest = connection.execute(
            """
            SELECT MAX(waktu_scraping)
            FROM bed_history
            WHERE kode_rs = ?
            """,
            (kode_rs,),
        ).fetchone()[0]

        if latest is None:
            return pd.DataFrame()

        return pd.read_sql_query(
            """
            SELECT *
            FROM bed_history
            WHERE kode_rs = ? AND waktu_scraping = ?
            ORDER BY kategori_pasien, kelas, nama_ruang
            """,
            connection,
            params=(kode_rs, latest),
        ).drop(columns=["id"])


@st.cache_data(ttl=15)
def load_latest_many(kode_list: list[str]) -> dict[str, pd.DataFrame]:
    """Mengambil snapshot terbaru untuk beberapa rumah sakit sekaligus.

    Dipakai oleh halaman Overview agar seluruh rumah sakit dapat
    dibandingkan tanpa perlu memilih satu per satu.
    """
    return {kode_rs: load_latest(kode_rs) for kode_rs in kode_list}


def load_history_summary(kode_rs: str) -> pd.DataFrame:
    initialize_database()
    with connect() as connection:
        return pd.read_sql_query(
            """
            SELECT
                waktu_scraping,
                waktu_update_sumber,
                SUM(kapasitas) AS kapasitas,
                SUM(terisi) AS terisi,
                SUM(tersedia) AS tersedia,
                SUM(tidak_siap) AS tidak_siap,
                SUM(renovasi) AS renovasi,
                SUM(sisrute) AS sisrute
            FROM bed_history
            WHERE kode_rs = ?
            GROUP BY waktu_scraping, waktu_update_sumber
            ORDER BY waktu_scraping
            """,
            connection,
            params=(kode_rs,),
        )


def load_change_details(
    kode_rs: str,
    max_snapshots: int = 50,
) -> pd.DataFrame:
    """Membandingkan setiap snapshot dengan snapshot tepat sebelumnya."""
    initialize_database()

    with connect() as connection:
        snapshot_rows = connection.execute(
            """
            SELECT DISTINCT waktu_scraping
            FROM bed_history
            WHERE kode_rs = ?
            ORDER BY waktu_scraping DESC
            LIMIT ?
            """,
            (kode_rs, max_snapshots),
        ).fetchall()

        snapshot_times = sorted(row[0] for row in snapshot_rows)
        changes: list[pd.DataFrame] = []

        for previous_time, current_time in zip(
            snapshot_times,
            snapshot_times[1:],
        ):
            previous = pd.read_sql_query(
                """
                SELECT
                    kategori_pasien,
                    kelas,
                    nama_ruang,
                    kapasitas,
                    terisi,
                    tersedia,
                    tidak_siap,
                    renovasi,
                    sisrute,
                    keterangan
                FROM bed_history
                WHERE kode_rs = ? AND waktu_scraping = ?
                """,
                connection,
                params=(kode_rs, previous_time),
            )
            current = pd.read_sql_query(
                """
                SELECT
                    kategori_pasien,
                    kelas,
                    nama_ruang,
                    kapasitas,
                    terisi,
                    tersedia,
                    tidak_siap,
                    renovasi,
                    sisrute,
                    keterangan,
                    waktu_update_sumber
                FROM bed_history
                WHERE kode_rs = ? AND waktu_scraping = ?
                """,
                connection,
                params=(kode_rs, current_time),
            )

            comparison = previous.merge(
                current,
                on=["kategori_pasien", "kelas", "nama_ruang"],
                how="outer",
                suffixes=("_sebelum", "_sekarang"),
                indicator=True,
            )

            numeric_columns = [
                "kapasitas_sebelum",
                "terisi_sebelum",
                "tersedia_sebelum",
                "tidak_siap_sebelum",
                "renovasi_sebelum",
                "sisrute_sebelum",
                "kapasitas_sekarang",
                "terisi_sekarang",
                "tersedia_sekarang",
                "tidak_siap_sekarang",
                "renovasi_sekarang",
                "sisrute_sekarang",
            ]
            comparison[numeric_columns] = (
                comparison[numeric_columns]
                .fillna(0)
                .astype(int)
            )

            comparison["delta_kapasitas"] = (
                comparison["kapasitas_sekarang"]
                - comparison["kapasitas_sebelum"]
            )
            comparison["delta_terisi"] = (
                comparison["terisi_sekarang"]
                - comparison["terisi_sebelum"]
            )
            comparison["delta_tersedia"] = (
                comparison["tersedia_sekarang"]
                - comparison["tersedia_sebelum"]
            )
            comparison["delta_renovasi"] = (
                comparison["renovasi_sekarang"]
                - comparison["renovasi_sebelum"]
            )
            comparison["delta_tidak_siap"] = (
                comparison["tidak_siap_sekarang"]
                - comparison["tidak_siap_sebelum"]
            )
            comparison["delta_sisrute"] = (
                comparison["sisrute_sekarang"]
                - comparison["sisrute_sebelum"]
            )

            changed = comparison[
                (comparison["delta_kapasitas"] != 0)
                | (comparison["delta_terisi"] != 0)
                | (comparison["delta_tersedia"] != 0)
                | (comparison["delta_renovasi"] != 0)
                | (comparison["delta_tidak_siap"] != 0)
                | (comparison["delta_sisrute"] != 0)
                | (
                    comparison["keterangan_sebelum"].fillna("")
                    != comparison["keterangan_sekarang"].fillna("")
                )
                | (comparison["_merge"] != "both")
            ].copy()

            if changed.empty:
                continue

            changed["waktu_scraping"] = current_time
            changed["waktu_update_sumber"] = (
                changed["waktu_update_sumber"].fillna("-")
            )
            changes.append(changed)

    if not changes:
        return pd.DataFrame()

    result = pd.concat(changes, ignore_index=True)

    def describe_change(row: pd.Series) -> str:
        if row["_merge"] == "right_only":
            return "Ruang baru terdeteksi"
        if row["_merge"] == "left_only":
            return "Ruang tidak lagi ditemukan"
        if row["delta_terisi"] > 0 and row["delta_tersedia"] < 0:
            return f"{row['delta_terisi']} bed baru terisi"
        if row["delta_terisi"] < 0 and row["delta_tersedia"] > 0:
            return f"{row['delta_tersedia']} bed menjadi tersedia"

        descriptions: list[str] = []
        if row["delta_terisi"]:
            descriptions.append(
                f"terisi {row['delta_terisi']:+d}"
            )
        if row["delta_tersedia"]:
            descriptions.append(
                f"tersedia {row['delta_tersedia']:+d}"
            )
        if row["delta_kapasitas"]:
            descriptions.append(
                f"kapasitas {row['delta_kapasitas']:+d}"
            )
        if row["delta_renovasi"]:
            descriptions.append(
                f"renovasi {row['delta_renovasi']:+d}"
            )
        if row["delta_tidak_siap"]:
            descriptions.append(
                f"kosong belum siap {row['delta_tidak_siap']:+d}"
            )
        if row["delta_sisrute"]:
            descriptions.append(
                f"Sisrute {row['delta_sisrute']:+d}"
            )
        return ", ".join(descriptions)

    result["perubahan"] = result.apply(describe_change, axis=1)

    ordered_columns = [
        "waktu_scraping",
        "waktu_update_sumber",
        "kategori_pasien",
        "kelas",
        "nama_ruang",
        "kapasitas_sebelum",
        "kapasitas_sekarang",
        "terisi_sebelum",
        "terisi_sekarang",
        "tersedia_sebelum",
        "tersedia_sekarang",
        "delta_terisi",
        "delta_tersedia",
        "delta_tidak_siap",
        "delta_renovasi",
        "delta_sisrute",
        "perubahan",
    ]

    return (
        result[ordered_columns]
        .sort_values(
            [
                "waktu_scraping",
                "kategori_pasien",
                "kelas",
                "nama_ruang",
            ],
            ascending=[False, True, True, True],
        )
        .reset_index(drop=True)
    )
