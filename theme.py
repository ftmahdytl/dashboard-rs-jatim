from __future__ import annotations

import pandas as pd
import streamlit as st

BASE_CSS = """
<style>
.stApp {background: linear-gradient(180deg, #eef4ff 0, #f8fafc 340px);}
.block-container {max-width: 1280px; padding-top: 3.5rem !important; padding-bottom: 2.5rem;}
[data-testid="stMetric"] {
    background: rgba(255,255,255,.96);
    border: 1px solid #dbe7ff;
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 8px 24px rgba(30,64,175,.07);
}
div[data-testid="stDataFrame"] {
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    overflow: hidden;
}
.table-wrap {
    max-height: 620px;
    overflow: auto;
    background: white;
    border: 1px solid #dbe7ff;
    border-radius: 14px;
    margin: 8px 0 16px;
}
.stable-table {
    width: 100%;
    border-collapse: collapse;
    font-size: .92rem;
}
.stable-table thead th {
    position: sticky;
    top: 0;
    z-index: 1;
    background: #eaf1ff;
    color: #17346b;
    padding: 11px 12px;
    text-align: left;
    border-bottom: 1px solid #cddcff;
}
.stable-table td {
    padding: 9px 12px;
    border-bottom: 1px solid #edf2f7;
}
.stable-table tbody tr:nth-child(even) {background: #f8faff;}
.stable-table tbody tr:hover {background: #eef4ff;}
.hero {
    background: linear-gradient(125deg, #0f2f6b, #2563eb);
    border-radius: 24px;
    padding: 28px 32px;
    color: white;
    margin-bottom: 18px;
    box-shadow: 0 14px 35px rgba(37,99,235,.22);
}
.hero h1, .hero p, .hero .hero-caption {
    color: white !important;
}
.hero h1 {margin: 0 0 8px; font-size: 2rem;}
.hero p {margin: 0; opacity: .88;}
.hero-caption {margin-top: 10px !important; font-size: .82rem !important; opacity: .85;}

.filter-bar {
    background: rgba(255,255,255,.96);
    border: 1px solid #dbe7ff;
    border-radius: 18px;
    padding: 18px 22px 6px;
    margin-bottom: 18px;
    box-shadow: 0 8px 24px rgba(30,64,175,.06);
}

.gauge-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 14px;
    height: 440px;
    overflow-y: auto;
    background: rgba(255,255,255,.96);
    border: 1px solid #dbe7ff;
    border-radius: 20px;
    padding: 20px 14px;
    box-shadow: 0 8px 24px rgba(30,64,175,.06);
    margin-bottom: 6px;
    scrollbar-width: thin;
    scrollbar-color: #93b4f5 #eef2fb;
}
.gauge-grid::-webkit-scrollbar {width: 8px;}
.gauge-grid::-webkit-scrollbar-track {
    background: #eef2fb;
    border-radius: 999px;
}
.gauge-grid::-webkit-scrollbar-thumb {
    background: #93b4f5;
    border-radius: 999px;
}
.gauge-grid::-webkit-scrollbar-thumb:hover {background: #6d99ee;}
.gauge-card {
    scroll-snap-align: start;
    text-align: center;
}
.gauge-scroll-hint {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: .78rem;
    color: #64748b;
    margin: 0 0 18px;
}
.gauge {
    width: 130px;
    height: 130px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 12px;
    position: relative;
}
.gauge::before {
    content: "";
    position: absolute;
    inset: 10px;
    background: white;
    border-radius: 50%;
    box-shadow: inset 0 0 0 1px #eef2f7;
}
.gauge-value {
    position: relative;
    z-index: 1;
    font-weight: 800;
    font-size: 1.35rem;
    color: #17346b;
}
.gauge-name {
    font-size: .95rem;
    font-weight: 700;
    color: #17346b;
    margin: 0;
    line-height: 1.25;
}
.gauge-sub {
    font-size: .78rem;
    color: #64748b;
    margin-top: 2px;
}
.legend-row {
    display: flex;
    gap: 18px;
    flex-wrap: wrap;
    font-size: .78rem;
    color: #475569;
    margin: 2px 0 4px;
}
.legend-dot {
    display: inline-block;
    width: 9px;
    height: 9px;
    border-radius: 50%;
    margin-right: 5px;
}
.insight-card {
    background: rgba(255,255,255,.96);
    border: 1px solid #dbe7ff;
    border-left: 5px solid #2563eb;
    border-radius: 14px;
    padding: 14px 16px;
    height: 100%;
    box-shadow: 0 8px 24px rgba(30,64,175,.06);
}
.insight-card h4 {
    margin: 0 0 4px;
    font-size: .78rem;
    text-transform: uppercase;
    letter-spacing: .03em;
    color: #64748b;
}
.insight-card .insight-value {
    font-size: 1.15rem;
    font-weight: 800;
    color: #0f2f6b;
    margin: 0 0 2px;
}
.insight-card .insight-detail {
    font-size: .8rem;
    color: #475569;
    margin: 0;
}

.stButton > button {
    border-radius: 999px !important;
    font-weight: 600 !important;
    white-space: nowrap !important;
    font-size: 0.84rem !important;
    padding: 0.35rem 0.5rem !important;
}

.dist-card {
    background: rgba(255,255,255,.97);
    border: 1px solid #dbe7ff;
    border-radius: 20px;
    padding: 22px 26px 8px;
    margin: 4px 0 18px;
    box-shadow: 0 8px 24px rgba(30,64,175,.06);
}
.dist-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 2px;
}
.dist-card-header h3 {
    margin: 0 0 4px;
    font-size: 1.25rem;
    color: #0f2f6b;
}
.dist-card-header p {
    margin: 0;
    color: #64748b;
    font-size: .86rem;
}
.dist-trophy {
    display: flex;
    align-items: center;
    gap: 6px;
    background: #eef4ff;
    border: 1px solid #dbe7ff;
    border-radius: 14px;
    padding: 8px 14px;
    font-size: .8rem;
    color: #33415c;
    white-space: nowrap;
}
.dist-trophy b {color: #1e3a8a;}
.dist-empty-count {
    font-size: .8rem;
    color: #64748b;
    margin: 4px 0 12px;
}
.dist-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 9px 0;
    border-bottom: 1px solid #eef2f7;
}
.dist-row:last-child {border-bottom: none;}
.dist-rank {
    flex: 0 0 22px;
    height: 22px;
    border-radius: 50%;
    background: #eef1ff;
    color: #4338ca;
    font-size: .74rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
}
.dist-name {
    flex: 0 0 200px;
    font-size: .87rem;
    font-weight: 600;
    color: #1e293b;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.dist-bar-track {
    flex: 1 1 auto;
    height: 14px;
    background: #eef1f8;
    border-radius: 999px;
    overflow: hidden;
}
.dist-bar-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #6366f1, #4338ca);
}
.dist-value {
    flex: 0 0 64px;
    text-align: right;
    font-size: .84rem;
    font-weight: 700;
    color: #1e293b;
}

.section-heading {
    margin: 26px 0 12px;
}
.section-heading h3 {
    margin: 0 0 2px;
    font-size: 1.28rem;
    color: #0f2f6b;
}
.section-heading p {
    margin: 0;
    color: #64748b;
    font-size: .86rem;
}

.filter-vdivider {
    width: 1px;
    height: 40px;
    background: #dbe7ff;
    margin: 6px auto 0;
}
.metric-toggle-label {
    font-size: .74rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .04em;
    color: #94a3b8;
    margin: 0 0 6px 2px;
}
</style>
"""


def inject_base_style() -> None:
    st.markdown(BASE_CSS, unsafe_allow_html=True)


def render_hero(title: str, subtitle: str, caption: str | None = None) -> None:
    caption_html = (
        f'<p class="hero-caption">{caption}</p>' if caption else ""
    )
    html = (
        f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p>'
        f"{caption_html}</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_section_heading(title: str, subtitle: str | None = None) -> None:
    """Judul section yang konsisten (dipakai berulang di halaman Overview)."""
    subtitle_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f'<div class="section-heading"><h3>{title}</h3>{subtitle_html}</div>',
        unsafe_allow_html=True,
    )


def render_stable_table(dataframe: pd.DataFrame, labels: dict[str, str]) -> None:
    """Menampilkan tabel HTML stabil tanpa komponen data-grid React."""
    display = dataframe.rename(columns=labels).copy()
    html_table = display.to_html(
        index=False,
        escape=True,
        classes="stable-table",
        border=0,
    )
    st.markdown(
        f'<div class="table-wrap">{html_table}</div>',
        unsafe_allow_html=True,
    )


def format_datetime_text(value: object) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return str(value)
    return parsed.strftime("%d-%m-%Y %H:%M:%S")


# Ambang batas status ketersediaan bed (persentase tersedia terhadap
# kapasitas). Dipakai untuk mewarnai gauge dan grafik pada halaman
# Overview agar rumah sakit yang mendekati penuh mudah dikenali.
STATUS_AMAN = ("Aman", "#16a34a")
STATUS_WASPADA = ("Waspada", "#f59e0b")
STATUS_KRITIS = ("Kritis", "#dc2626")
STATUS_TANPA_DATA = ("Belum ada data", "#94a3b8")


def get_availability_status(
    percentage: float | None,
) -> tuple[str, str]:
    """Mengembalikan (label, warna) berdasarkan persentase bed tersedia.

    Menangani baik ``None`` maupun ``NaN``: ketika beberapa baris RS
    tanpa data digabung ke satu ``pandas.DataFrame`` bersama baris RS
    yang punya angka, kolom tersebut otomatis berubah jadi ``float64``
    dan nilai ``None`` ikut berubah jadi ``NaN`` (bukan ``None`` lagi).
    Tanpa pengecekan ``pd.isna``, RS tanpa data akan salah dikira
    "Kritis" dan gauge-nya menampilkan teks "nan%".
    """
    if percentage is None or pd.isna(percentage):
        return STATUS_TANPA_DATA
    if percentage >= 25:
        return STATUS_AMAN
    if percentage >= 10:
        return STATUS_WASPADA
    return STATUS_KRITIS


def get_occupancy_status(
    percentage: float | None,
) -> tuple[str, str]:
    """Mengembalikan (label, warna) berdasarkan BOR (persentase keterisian).

    Arah ambang batasnya kebalikan dari ``get_availability_status``:
    di sini semakin TINGGI persentase (semakin penuh bed-nya), semakin
    kritis statusnya. Ambang mengikuti indikator BOR ideal Kemenkes
    (60-85%): di atas 90% dianggap penuh/kritis, 75-90% mulai padat
    (waspada), di bawah itu masih aman.
    """
    if percentage is None or pd.isna(percentage):
        return STATUS_TANPA_DATA
    if percentage > 90:
        return STATUS_KRITIS
    if percentage > 75:
        return STATUS_WASPADA
    return STATUS_AMAN


def render_insight_card(
    title: str,
    value: str,
    detail: str,
    accent_color: str = "#2563eb",
) -> None:
    """Menampilkan satu kartu insight (judul, nilai besar, keterangan)."""
    html = (
        f'<div class="insight-card" style="border-left-color:{accent_color};">'
        f"<h4>{title}</h4>"
        f'<p class="insight-value">{value}</p>'
        f'<p class="insight-detail">{detail}</p>'
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_gauge_ring(
    code: str,
    name: str,
    percentage: float | None,
    sub_label: str,
    status_fn=get_availability_status,
    is_capacity_only: bool = False,
) -> str:
    """Membuat markup HTML satu gauge ring (donut).

    ``status_fn`` menentukan cara memberi warna/label status dari
    ``percentage``.
    """
    if is_capacity_only:
        fill = "#94a3b8"
        value_text = "-"
    else:
        _, color = status_fn(percentage)
        is_missing = percentage is None or pd.isna(percentage)
        if is_missing:
            fill = "#e2e8f0"
            value_text = "N/A"
        else:
            clamped = max(0.0, min(100.0, percentage))
            fill = (
                f"conic-gradient({color} 0% {clamped:.1f}%, "
                f"#e5e7eb {clamped:.1f}% 100%)"
            )
            value_text = f"{percentage:.1f}%"

    gauge_style = f"background: {fill};"

    return (
        '<div class="gauge-card">'
        f'<div class="gauge" style="{gauge_style}">'
        f'<span class="gauge-value">{value_text}</span>'
        "</div>"
        f'<p class="gauge-name">{name}</p>'
        f'<p class="gauge-sub">{sub_label}</p>'
        "</div>"
    )


# ---------------------------------------------------------------------
# Distribusi tempat tidur per kelas (kartu peringkat dengan filter pill)
# ---------------------------------------------------------------------
KELAS_FILTER_OPTIONS = [
    "Semua Kelas",
    "VVIP",
    "VIP",
    "Kelas I",
    "Kelas II",
    "Kelas III",
    "HCU",
    "ICU",
    "NICU",
    "PICU",
]

_KELAS_CANONICAL_MAP = {
    "VVIP": "VVIP",
    "KELAS VVIP": "VVIP",
    "VIP": "VIP",
    "KELAS VIP": "VIP",
    "KELAS 1": "Kelas I",
    "KELAS I": "Kelas I",
    "KELAS 2": "Kelas II",
    "KELAS II": "Kelas II",
    "KELAS 3": "Kelas III",
    "KELAS III": "Kelas III",
    "ICU": "ICU",
    "NICU": "NICU",
    "PICU": "PICU",
    "HCU": "HCU",
    "ISOLASI": "Isolasi",
}

KELAS_ORDER_MAP = {
    "VVIP": 1,
    "VIP": 2,
    "Kelas Utama": 3,
    "Kelas I": 4,
    "Kelas II": 5,
    "Kelas III": 6,
    "HCU": 7,
    "ICU": 8,
    "NICU": 9,
    "PICU": 10,
    "Isolasi": 11,
    "Kamar Bayi (KB)": 12,
    "Non Kelas": 13,
}


def get_kelas_sort_key(kelas_name: object) -> int:
    """Mengembalikan integer urutan standar kelas (VVIP -> 1, VIP -> 2, Kelas I -> 4, II -> 5, III -> 6, HCU -> 7, ICU -> 8, NICU -> 9, PICU -> 10)."""
    text = str(kelas_name).strip()
    if text in KELAS_ORDER_MAP:
        return KELAS_ORDER_MAP[text]
    upper = text.upper()
    if "VVIP" in upper:
        return 1
    if "VIP" in upper:
        return 2
    if "NICU" in upper:
        return 9
    if "PICU" in upper:
        return 10
    if "III" in upper or "3" in upper:
        return 6
    if "II" in upper or "2" in upper:
        return 5
    if " I" in upper or " 1" in upper or upper == "KELAS I" or upper == "KELAS 1":
        return 4
    if "HCU" in upper:
        return 7
    if "ICU" in upper:
        return 8
    if "ISOLASI" in upper:
        return 11
    return 99


def canonicalize_kelas(raw: object) -> str | None:
    """Menyamakan variasi penulisan kelas dari tiap RS."""
    text = " ".join(str(raw).split()).upper()
    if "VVIP" in text:
        return "VVIP"
    if "VIP" in text:
        return "VIP"
    if "NICU" in text:
        return "NICU"
    if "PICU" in text:
        return "PICU"
    if "III" in text or " 3" in text or "KELAS 3" in text:
        return "Kelas III"
    if "II" in text or " 2" in text or "KELAS 2" in text:
        return "Kelas II"
    if " I" in text or " 1" in text or "KELAS 1" in text or text == "KELAS I":
        return "Kelas I"
    if "HCU" in text:
        return "HCU"
    if "ICU" in text:
        return "ICU"
    if "ISOLASI" in text:
        return "Isolasi"
    return _KELAS_CANONICAL_MAP.get(text)


def render_bed_class_distribution(
    rows: list[dict],
    selected_kelas: str,
    total_hospitals: int,
) -> None:
    """Menampilkan kartu peringkat jumlah bed per kelas antar-RS.

    ``rows`` sudah harus diurutkan menurun berdasarkan ``value`` dan
    hanya berisi RS yang benar-benar punya kelas ini (RS tanpa kelas
    tersebut sengaja tidak disertakan, bukan ditampilkan 0).
    """
    header = (
        '<div class="dist-card-header"><div>'
        "<h3>Ketersediaan Tempat Tidur menurut Kelas</h3>"
        "<p>Pilih kelas di atas untuk membandingkan jumlah bed di "
        "setiap rumah sakit.</p>"
        "</div>"
    )
    if rows:
        top = rows[0]
        header += (
            '<div class="dist-trophy">🏆 Terbanyak: '
            f'<b>{top["nama_rs"]}</b> · {top["value"]} bed</div>'
        )
    header += "</div>"

    if not rows:
        body = (
            '<p class="dist-empty-count">Belum ada rumah sakit dengan '
            f'data kelas "{selected_kelas}".</p>'
        )
        st.markdown(
            f'<div class="dist-card">{header}{body}</div>',
            unsafe_allow_html=True,
        )
        return

    max_value = max(item["value"] for item in rows) or 1
    count_text = (
        f'<p class="dist-empty-count">Menampilkan {len(rows)} dari '
        f'{total_hospitals} rumah sakit yang memiliki kelas '
        f'"{selected_kelas}".</p>'
        if len(rows) < total_hospitals
        else ""
    )

    row_html = []
    for index, item in enumerate(rows, start=1):
        width_pct = (item["value"] / max_value * 100) if max_value else 0
        row_html.append(
            '<div class="dist-row">'
            f'<span class="dist-rank">{index}</span>'
            f'<span class="dist-name">{item["nama_rs"]}</span>'
            '<div class="dist-bar-track">'
            f'<div class="dist-bar-fill" style="width:{width_pct:.1f}%">'
            "</div></div>"
            f'<span class="dist-value">{item["value"]} bed</span>'
            "</div>"
        )

    st.markdown(
        f'<div class="dist-card">{header}{count_text}{"".join(row_html)}</div>',
        unsafe_allow_html=True,
    )
