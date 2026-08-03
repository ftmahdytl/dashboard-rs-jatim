from __future__ import annotations

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st

from database import load_latest_many, save_snapshot
from hospitals import HOSPITALS
from theme import (
    KELAS_FILTER_OPTIONS,
    canonicalize_kelas,
    get_availability_status,
    get_occupancy_status,
    inject_base_style,
    render_bed_class_distribution,
    render_gauge_ring,
    render_hero,
    render_section_heading,
    render_stable_table,
)

inject_base_style()

hospital_codes = {
    name: str(info["kode_rs"]) for name, info in HOSPITALS.items()
}
code_to_name = {code: name for name, code in hospital_codes.items()}

latest_by_code = load_latest_many(list(hospital_codes.values()))

# ---------------------------------------------------------------------
# Ringkas snapshot terbaru tiap RS menjadi satu baris per rumah sakit.
# ---------------------------------------------------------------------
rows: list[dict[str, object]] = []
for hospital_name, kode_rs in hospital_codes.items():
    snapshot = latest_by_code.get(kode_rs, pd.DataFrame())
    if snapshot.empty:
        rows.append(
            {
                "kode_rs": kode_rs,
                "nama_rs": hospital_name,
                "kapasitas": None,
                "terisi": None,
                "tersedia": None,
                "pct_tersedia": None,
                "bor": None,
                "waktu_update_sumber": None,
                "waktu_scraping": None,
                "url": HOSPITALS[hospital_name]["url"],
                "ada_data": False,
            }
        )
        continue

    kapasitas = int(snapshot["kapasitas"].sum())
    terisi = int(snapshot["terisi"].sum())
    tersedia = int(snapshot["tersedia"].sum())
    pct_tersedia = (tersedia / kapasitas * 100) if kapasitas else 0.0
    bor = (terisi / kapasitas * 100) if kapasitas else 0.0

    rows.append(
        {
            "kode_rs": kode_rs,
            "nama_rs": hospital_name,
            "kapasitas": kapasitas,
            "terisi": terisi,
            "tersedia": tersedia,
            "pct_tersedia": pct_tersedia,
            "bor": bor,
            "waktu_update_sumber": snapshot["waktu_update_sumber"].max(),
            "waktu_scraping": snapshot["waktu_scraping"].max(),
            "url": HOSPITALS[hospital_name]["url"],
            "ada_data": True,
        }
    )

summary = pd.DataFrame(rows)
have_data = summary[summary["ada_data"]].copy()
missing = summary[~summary["ada_data"]].copy()

# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------
if not have_data.empty:
    last_update = pd.to_datetime(
        have_data["waktu_scraping"], errors="coerce"
    ).max()
    caption = (
        f"Update terakhir: {last_update.strftime('%d-%m-%Y %H:%M:%S')} WIB "
        f"· {len(have_data)}/{len(summary)} rumah sakit sudah memiliki data"
    )
else:
    caption = "Belum ada data — ambil data pertama menggunakan tombol di bawah."

render_hero(
    "Sistem Monitoring Layanan Rumah Sakit",
    "Pemerintah Provinsi Jawa Timur Berbasis Automated Web Scraping",
    caption=caption,
)

# ---------------------------------------------------------------------
# Ambil / perbarui data seluruh RS — satu tombol untuk semua kasus:
# mengisi RS yang belum punya snapshot sama sekali sekaligus
# menyegarkan RS yang datanya sudah ada.
# ---------------------------------------------------------------------
if not missing.empty:
    st.warning(
        "Belum ada data untuk: "
        + ", ".join(missing["nama_rs"].tolist())
        + ". Klik tombol di bawah untuk mengambil data seluruh RS."
    )

button_col, caption_col = st.columns([1.3, 3])
with button_col:
    fetch_all_clicked = st.button(
        "🔄 Ambil / Perbarui Data Semua RS",
        type="primary",
        use_container_width=True,
    )
with caption_col:
    st.caption(
        "Mengambil data terbaru untuk seluruh 13 rumah sakit sekaligus — "
        "baik yang belum punya data maupun yang datanya ingin disegarkan. "
        "Data lama tidak akan disimpan dobel apabila waktu update di "
        "website sumber belum berubah."
    )

if fetch_all_clicked:
    progress = st.progress(0.0, text="Memulai scraping seluruh RS...")
    total = len(HOSPITALS)
    failed: list[str] = []
    updated = 0
    for index, (hospital_name, info) in enumerate(
        HOSPITALS.items(), start=1
    ):
        progress.progress(
            (index - 1) / total,
            text=f"Mengambil data {hospital_name}...",
        )
        try:
            fresh_data = info["scraper"]()
            if save_snapshot(fresh_data):
                updated += 1
        except Exception as error:  # noqa: BLE001
            failed.append(f"{hospital_name}: {error}")
    progress.progress(1.0, text="Selesai.")

    if failed:
        st.error(
            "Sebagian RS gagal diperbarui:\n"
            + "\n".join(f"- {item}" for item in failed)
        )
    if updated:
        st.success(f"{updated} rumah sakit berhasil diperbarui datanya.")
    elif not failed:
        st.info("Scraping berhasil, tetapi tidak ada data baru yang berubah.")
    st.rerun()

if have_data.empty:
    st.info(
        "Belum ada data sama sekali. Klik tombol pengambilan data di atas "
        "untuk mulai memantau ketersediaan bed."
    )
    st.stop()

# ---------------------------------------------------------------------
# KPI provinsi
# ---------------------------------------------------------------------
total_capacity = int(have_data["kapasitas"].sum())
total_occupied = int(have_data["terisi"].sum())
total_available = int(have_data["tersedia"].sum())
provincial_bor = (
    total_occupied / total_capacity * 100 if total_capacity else 0.0
)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Kapasitas Bed", f"{total_capacity:,}".replace(",", "."))
kpi2.metric("Total Terisi", f"{total_occupied:,}".replace(",", "."))
kpi3.metric("Total Tersedia", f"{total_available:,}".replace(",", "."))
kpi4.metric("BOR Provinsi", f"{provincial_bor:.1f}%")

# ---------------------------------------------------------------------
# Penataan 2 Kolom Interaktif (Peta Lokasi & Status BOR Ringkas)
# ---------------------------------------------------------------------
st.markdown("")
col_left, col_right = st.columns([1.18, 0.82], gap="large")

GREEN_PIN = "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png"
GOLD_PIN = "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-gold.png"
RED_PIN = "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png"
GREY_PIN = "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png"


def make_icon_data(pin_url: str) -> dict[str, object]:
    return {
        "url": pin_url,
        "width": 25,
        "height": 41,
        "anchorY": 41,
    }


with col_left:
    render_section_heading(
        "🗺️ Peta Persebaran Geografis RSUD Jatim",
        "Titik lokasi 13 RSUD Pemprov Jatim beserta status BOR.",
    )

    map_rows = []
    for r in summary.itertuples():
        h_info = HOSPITALS.get(r.nama_rs, {})
        lat = h_info.get("lat")
        lon = h_info.get("lon")
        kota = h_info.get("kota", "Jawa Timur")

        if lat is None or lon is None:
            continue

        is_cap_only = r.kode_rs in ["RSKH", "RSSG"]
        if is_cap_only:
            status_str = "Hanya Data Kapasitas"
            color_rgb = [148, 163, 184, 220]
            bor_str = "-"
            terisi_str = "-"
            tersedia_str = "-"
        elif r.ada_data:
            status_str, _ = get_occupancy_status(r.bor)
            bor_str = f"{r.bor:.1f}%"
            terisi_str = f"{int(r.terisi):,}".replace(",", ".")
            tersedia_str = f"{int(r.tersedia):,}".replace(",", ".")
            if r.bor <= 75.0:
                color_rgb = [34, 197, 94, 220]
            elif r.bor <= 90.0:
                color_rgb = [234, 179, 8, 220]
            else:
                color_rgb = [239, 68, 68, 220]
        else:
            status_str = "Belum Ada Data"
            color_rgb = [148, 163, 184, 220]
            bor_str = "-"
            terisi_str = "-"
            tersedia_str = "-"

        map_rows.append(
            {
                "nama_rs": r.nama_rs,
                "kode_rs": r.kode_rs,
                "kota": kota,
                "lat": lat,
                "lon": lon,
                "status": status_str,
                "kapasitas_text": f"{int(r.kapasitas):,}".replace(",", ".")
                if r.ada_data
                else "-",
                "terisi_text": terisi_str,
                "tersedia_text": tersedia_str,
                "bor_text": bor_str,
                "color": color_rgb,
            }
        )

    df_map = pd.DataFrame(map_rows)

    if not df_map.empty:
        layer = pdk.Layer(
            "ScatterplotLayer",
            df_map,
            get_position=["lon", "lat"],
            get_fill_color="color",
            get_radius=9000,
            radius_min_pixels=10,
            radius_max_pixels=25,
            pickable=True,
        )

        view_state = pdk.ViewState(
            latitude=-7.65,
            longitude=112.55,
            zoom=7.3,
            pitch=0,
        )

        deck_map = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={
                "html": "<b>{nama_rs}</b> ({kota})<br/>"
                "Status: <b>{status}</b><br/>"
                "Kapasitas: {kapasitas_text} bed<br/>"
                "Terisi: {terisi_text} bed<br/>"
                "Tersedia: {tersedia_text} bed<br/>"
                "BOR: <b>{bor_text}</b>",
                "style": {
                    "backgroundColor": "#0f2f6b",
                    "color": "white",
                    "borderRadius": "10px",
                    "padding": "10px 14px",
                    "fontSize": "13px",
                    "boxShadow": "0 4px 12px rgba(0,0,0,0.3)",
                },
            },
            map_style="light",
        )
        st.pydeck_chart(deck_map, use_container_width=True)

with col_right:
    render_section_heading(
        "🛏️ Status BOR per Rumah Sakit",
        "Warna ring menandai keterisian RS.",
    )

    # Move capacity-only hospitals (RSKH and RSSG) to the very end
    regular_rs = summary[~summary["kode_rs"].isin(["RSKH", "RSSG"])].sort_values(
        ["ada_data", "bor"], ascending=[False, False]
    )
    cap_only_rs = summary[summary["kode_rs"].isin(["RSKH", "RSSG"])].sort_values(
        ["ada_data"], ascending=[False]
    )
    gauge_summary = pd.concat([regular_rs, cap_only_rs], ignore_index=True)

    gauge_html = ['<div class="gauge-grid">']
    for row in gauge_summary.itertuples():
        is_cap_only = row.kode_rs in ["RSKH", "RSSG"]
        if is_cap_only:
            pct = None
            sub_label = (
                f"{int(row.kapasitas):,} bed (Kapasitas)".replace(",", ".")
                if row.ada_data
                else "Belum ada data"
            )
        else:
            pct = row.bor
            sub_label = (
                f"{int(row.terisi)}/{int(row.kapasitas)} bed terisi"
                if row.ada_data
                else "Belum ada data"
            )

        gauge_html.append(
            render_gauge_ring(
                code=row.kode_rs,
                name=str(row.nama_rs),
                percentage=pct,
                sub_label=sub_label,
                status_fn=get_occupancy_status,
                is_capacity_only=is_cap_only,
            )
        )
    gauge_html.append("</div>")
    st.markdown("".join(gauge_html), unsafe_allow_html=True)

    legend_html = (
        '<div class="legend-row" style="margin-top:6px;">'
        '<span><span class="legend-dot" style="background:#16a34a;"></span>'
        "Aman (&le;75%)</span>"
        '<span><span class="legend-dot" style="background:#f59e0b;"></span>'
        "Waspada (75-90%)</span>"
        '<span><span class="legend-dot" style="background:#dc2626;"></span>'
        "Kritis (&gt;90%)</span>"
        '<span><span class="legend-dot" style="background:#94a3b8;"></span>'
        "Hanya Kapasitas</span>"
        "</div>"
    )
    st.markdown(legend_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Ketersediaan Tempat Tidur menurut Kelas — kartu peringkat dengan
# filter kelas dinamis (pill) + toggle Tersedia/Terisi.
# ---------------------------------------------------------------------
from theme import get_kelas_sort_key

# Extract unique classes that actually exist in current active snapshots
available_classes_set = set()
for hospital_name, kode_rs in hospital_codes.items():
    snapshot = latest_by_code.get(kode_rs, pd.DataFrame())
    if not snapshot.empty:
        mapped_list = snapshot["kelas"].map(canonicalize_kelas).dropna().unique()
        for k in mapped_list:
            available_classes_set.add(k)

sorted_available_classes = sorted(
    list(available_classes_set),
    key=get_kelas_sort_key
)
dynamic_kelas_options = ["Semua Kelas"] + sorted_available_classes

KELAS_FILTER_KEY = "overview_kelas_filter"
METRIC_FILTER_KEY = "overview_metric_filter"

if (
    KELAS_FILTER_KEY not in st.session_state
    or st.session_state[KELAS_FILTER_KEY] not in dynamic_kelas_options
):
    st.session_state[KELAS_FILTER_KEY] = dynamic_kelas_options[0]

if METRIC_FILTER_KEY not in st.session_state:
    st.session_state[METRIC_FILTER_KEY] = "Tersedia"

render_section_heading(
    "🏷️ Filter Kelas Tempat Tidur",
    "Pilih kelas untuk membandingkan jumlah bed di tiap RS pada kartu "
    "di bawah.",
)

filter_left, filter_divider, filter_right = st.columns([5, 0.25, 1.7])
with filter_left:
    num_opts = len(dynamic_kelas_options)
    if num_opts <= 7:
        k_cols = st.columns(num_opts)
        for col, option in zip(k_cols, dynamic_kelas_options):
            with col:
                is_active = st.session_state[KELAS_FILTER_KEY] == option
                if st.button(
                    option,
                    key=f"kelasfilter_{option}",
                    type="primary" if is_active else "secondary",
                    use_container_width=True,
                ):
                    st.session_state[KELAS_FILTER_KEY] = option
                    st.rerun()
    else:
        mid = (num_opts + 1) // 2
        row1_options = dynamic_kelas_options[:mid]
        row2_options = dynamic_kelas_options[mid:]

        r1_cols = st.columns(len(row1_options))
        for col, option in zip(r1_cols, row1_options):
            with col:
                is_active = st.session_state[KELAS_FILTER_KEY] == option
                if st.button(
                    option,
                    key=f"kelasfilter_{option}",
                    type="primary" if is_active else "secondary",
                    use_container_width=True,
                ):
                    st.session_state[KELAS_FILTER_KEY] = option
                    st.rerun()

        r2_cols = st.columns(len(row2_options))
        for col, option in zip(r2_cols, row2_options):
            with col:
                is_active = st.session_state[KELAS_FILTER_KEY] == option
                if st.button(
                    option,
                    key=f"kelasfilter_{option}",
                    type="primary" if is_active else "secondary",
                    use_container_width=True,
                ):
                    st.session_state[KELAS_FILTER_KEY] = option
                    st.rerun()
with filter_divider:
    st.markdown('<div class="filter-vdivider"></div>', unsafe_allow_html=True)
with filter_right:
    st.markdown(
        '<p class="metric-toggle-label">Tampilkan</p>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        metric_cols = st.columns(2)
        for col, option in zip(metric_cols, ["Tersedia", "Terisi"]):
            with col:
                is_active = st.session_state[METRIC_FILTER_KEY] == option
                if st.button(
                    option,
                    key=f"metricfilter_{option}",
                    type="primary" if is_active else "secondary",
                    use_container_width=True,
                ):
                    st.session_state[METRIC_FILTER_KEY] = option
                    st.rerun()

selected_kelas = st.session_state[KELAS_FILTER_KEY]
selected_metric = st.session_state[METRIC_FILTER_KEY]
metric_column = "tersedia" if selected_metric == "Tersedia" else "terisi"

distribution_rows: list[dict[str, object]] = []
for hospital_name, kode_rs in hospital_codes.items():
    snapshot = latest_by_code.get(kode_rs, pd.DataFrame())
    if snapshot.empty:
        continue
    if selected_kelas == "Semua Kelas":
        subset = snapshot
    else:
        mapped_kelas = snapshot["kelas"].map(canonicalize_kelas)
        subset = snapshot[mapped_kelas == selected_kelas]
    if subset.empty:
        # RS ini memang tidak punya kelas tersebut sama sekali —
        # sengaja dilewati, bukan ditampilkan dengan angka 0.
        continue
    distribution_rows.append(
        {
            "nama_rs": hospital_name,
            "value": int(subset[metric_column].sum()),
        }
    )

distribution_rows.sort(key=lambda item: item["value"], reverse=True)

render_bed_class_distribution(
    rows=distribution_rows,
    selected_kelas=selected_kelas,
    total_hospitals=len(hospital_codes),
)

# ---------------------------------------------------------------------
# Tabel ringkasan seluruh RS
# ---------------------------------------------------------------------
render_section_heading(
    "📋 Tabel Ringkasan Seluruh Rumah Sakit",
    "Rincian angka lengkap ke-13 rumah sakit, diurutkan dari bed "
    "tersedia terbanyak.",
)

table_view = summary.copy()
table_view["status"] = table_view["pct_tersedia"].map(
    lambda value: get_availability_status(value)[0]
)
table_view["pct_tersedia_text"] = table_view["pct_tersedia"].map(
    lambda value: f"{value:.1f}%" if pd.notna(value) else "-"
)
table_view["bor_text"] = table_view["bor"].map(
    lambda value: f"{value:.1f}%" if pd.notna(value) else "-"
)
table_view["waktu_update_text"] = pd.to_datetime(
    table_view["waktu_update_sumber"], errors="coerce"
).dt.strftime("%d-%m-%Y %H:%M:%S")
table_view["waktu_update_text"] = table_view["waktu_update_text"].fillna(
    "Belum ada data"
)
table_view["kapasitas"] = table_view["kapasitas"].fillna(0).astype(int)

# Set '-' for capacity-only hospitals in table_view
for r_idx in table_view.index:
    if table_view.loc[r_idx, "kode_rs"] in ["RSKH", "RSSG"]:
        table_view.loc[r_idx, "terisi"] = "-"
        table_view.loc[r_idx, "tersedia"] = "-"
        table_view.loc[r_idx, "pct_tersedia_text"] = "-"
        table_view.loc[r_idx, "bor_text"] = "-"
        table_view.loc[r_idx, "status"] = "-"

table_view = table_view.sort_values(
    ["ada_data"], ascending=[False]
)

display_columns = [
    "nama_rs",
    "kapasitas",
    "terisi",
    "tersedia",
    "pct_tersedia_text",
    "bor_text",
    "status",
    "waktu_update_text",
]

render_stable_table(
    table_view[display_columns],
    {
        "nama_rs": "Rumah Sakit",
        "kapasitas": "Kapasitas",
        "terisi": "Terisi",
        "tersedia": "Tersedia",
        "pct_tersedia_text": "% Tersedia",
        "bor_text": "BOR",
        "status": "Status",
        "waktu_update_text": "Update Website",
    },
)

st.caption(
    "Buka halaman **Ketersediaan Bed** pada menu di sebelah kiri untuk "
    "melihat detail ruang per kelas, tren historis, dan mengatur "
    "scraping otomatis per rumah sakit."
)
