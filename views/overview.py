from __future__ import annotations

import base64
import json
import os
import urllib.parse
import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from database import load_latest_many, save_snapshot
from hospitals import HOSPITALS
from theme import (
    canonicalize_kelas,
    get_availability_status,
    get_occupancy_status,
    inject_base_style,
    render_bed_class_distribution,
    render_gauge_ring,
    render_section_heading,
)

inject_base_style()

@st.cache_data
def get_base64_logo(file_path: str) -> str | None:
    if file_path and os.path.exists(file_path):
        ext = file_path.split(".")[-1].lower()
        mime = "image/png" if ext == "png" else "image/jpeg"
        with open(file_path, "rb") as img_file:
            b64 = base64.b64encode(img_file.read()).decode("utf-8")
        return f"data:{mime};base64,{b64}"
    return None

# ---------------------------------------------------------------------
# Check 3 Logos (Pemprov Jatim -> Kominfo -> UNAIR)
# ---------------------------------------------------------------------
pemprov_path = "assets/logos/logo_pemprov.png" if os.path.exists("assets/logos/logo_pemprov.png") else ("assets/logos/logo_pemprov.jpg" if os.path.exists("assets/logos/logo_pemprov.jpg") else None)
kominfo_path = "assets/logos/logo_kominfo.png" if os.path.exists("assets/logos/logo_kominfo.png") else ("assets/logos/logo_kominfo.jpg" if os.path.exists("assets/logos/logo_kominfo.jpg") else None)
unair_path = "assets/logos/logo_unair.png" if os.path.exists("assets/logos/logo_unair.png") else ("assets/logos/logo_unair.jpg" if os.path.exists("assets/logos/logo_unair.jpg") else None)

# Executive Hero Banner Container (dari Beranda)
with st.container(border=True):
    badge_col, logo_col = st.columns([1.2, 2.8])
    with badge_col:
        st.markdown(
            '<div style="display:inline-flex; align-items:center; gap:6px; background:#dcfce7; border:1px solid #86efac; color:#15803d; font-size:0.78rem; font-weight:700; padding:5px 16px; border-radius:999px; margin-top:4px;">'
            '<span style="display:inline-block; width:8px; height:8px; background:#22c55e; border-radius:50%;"></span>'
            'LIVE SYSTEM STATUS: AKTIF'
            '</div>',
            unsafe_allow_html=True,
        )
    with logo_col:
        pemprov_b64 = get_base64_logo(pemprov_path)
        kominfo_b64 = get_base64_logo(kominfo_path)
        unair_b64 = get_base64_logo(unair_path)

        pemprov_img = f'<img src="{pemprov_b64}" style="height:48px; max-width:65px; object-fit:contain;" alt="Pemprov Jatim" />' if pemprov_b64 else '<span style="font-size:0.72rem; font-weight:700; color:#1e40af;">PEMPROV JATIM</span>'
        kominfo_img = f'<img src="{kominfo_b64}" style="height:42px; max-width:65px; object-fit:contain;" alt="Kominfo" />' if kominfo_b64 else '<span style="font-size:0.72rem; font-weight:700; color:#1e40af;">DISKOMINFO</span>'
        unair_img = f'<img src="{unair_b64}" style="height:42px; max-width:65px; object-fit:contain;" alt="UNAIR" />' if unair_b64 else '<span style="font-size:0.72rem; font-weight:700; color:#1e40af;">UNAIR</span>'

        st.markdown(
            f'<div style="display:flex; justify-content:flex-end; align-items:center; gap:16px;">'
            f'{pemprov_img}'
            f'{kominfo_img}'
            f'{unair_img}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<h1 style="margin:14px 0 6px; color:#0f2f6b; font-size:2.1rem; font-weight:800; line-height:1.22; letter-spacing:-0.5px;">'
        'SISTEM MONITORING LAYANAN RUMAH SAKIT PEMPROV JAWA TIMUR'
        '</h1>'
        '<p style="margin:0 0 16px; color:#2563eb; font-size:1.05rem; font-weight:700;">'
        'Berbasis Automated Web Scraping Real-Time'
        '</p>'
        '<div style="background:white; border:1px solid #dbe7ff; border-radius:16px; padding:18px 24px; color:#334155; font-size:0.96rem; line-height:1.65; box-shadow:0 4px 12px rgba(0,0,0,0.02); margin-bottom:18px;">'
        'Dashboard ini dirancang sebagai platform pusat informasi dan pemantauan terpadu untuk <b>14 Rumah Sakit Umum Daerah (RSUD) dan Rumah Sakit Khusus</b> milik Pemerintah Provinsi Jawa Timur. Melalui teknologi <b>Automated Web Scraping</b>, sistem ini secara berkala menyerap data langsung dari portal resmi masing-masing RSUD guna menyajikan transparansi ketersediaan tempat tidur, persebaran fasilitas rujukan medis, serta kontak layanan darurat 24 jam secara akurat dan terintegrasi.'
        '</div>',
        unsafe_allow_html=True,
    )

    f1, f2, f3 = st.columns(3)
    with f1:
        st.info("⚡ **Automated Scraping Real-Time**")
    with f2:
        st.info("🗺️ **GIS Pemetaan Geografis RSUD**")
    with f3:
        st.info("🏥 **Informasi Rujukan & Kontak 24 Jam**")

# ---------------------------------------------------------------------
# Ringkas snapshot terbaru tiap RS
# ---------------------------------------------------------------------
hospital_codes = {
    name: str(info["kode_rs"]) for name, info in HOSPITALS.items()
}
code_to_name = {code: name for name, code in hospital_codes.items()}

latest_by_code = load_latest_many(list(hospital_codes.values()))

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
# Tombol Ambil / Perbarui Data
# ---------------------------------------------------------------------
st.markdown("")
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
        "Mengambil data terbaru untuk seluruh rumah sakit sekaligus — "
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
# KPI Provinsi
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

with col_left:
    render_section_heading(
        "🗺️ Peta Persebaran Geografis RSUD Jatim",
        "Titik lokasi RSUD Pemprov Jatim (Klik lingkaran untuk langsung buka Google Maps).",
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
        is_no_data = r.kode_rs in ["RSHP"]

        if is_no_data:
            status_str = "Data Belum Tersedia"
            color_hex = "#94A3B8"
            kapasitas_str = "-"
            bor_str = "-"
            terisi_str = "-"
            tersedia_str = "-"
        elif is_cap_only:
            status_str = "Hanya Data Kapasitas"
            color_hex = "#94A3B8"
            kapasitas_str = f"{int(r.kapasitas):,}".replace(",", ".") if r.ada_data else "-"
            bor_str = "-"
            terisi_str = "-"
            tersedia_str = "-"
        elif r.ada_data:
            status_str, _ = get_occupancy_status(r.bor)
            kapasitas_str = f"{int(r.kapasitas):,}".replace(",", ".")
            bor_str = f"{r.bor:.1f}%"
            terisi_str = f"{int(r.terisi):,}".replace(",", ".")
            tersedia_str = f"{int(r.tersedia):,}".replace(",", ".")
            if r.bor <= 75.0:
                color_hex = "#22C55E"
            elif r.bor <= 90.0:
                color_hex = "#EAB308"
            else:
                color_hex = "#EF4444"
        else:
            status_str = "Data Belum Tersedia"
            color_hex = "#94A3B8"
            kapasitas_str = "-"
            bor_str = "-"
            terisi_str = "-"
            tersedia_str = "-"

        query_q = urllib.parse.quote(str(r.nama_rs))
        gmaps_url = f"https://www.google.com/maps/search/?api=1&query={query_q}"

        map_rows.append(
            {
                "nama_rs": r.nama_rs,
                "kode_rs": r.kode_rs,
                "kota": kota,
                "lat": lat,
                "lon": lon,
                "status": status_str,
                "kapasitas_text": kapasitas_str,
                "terisi_text": terisi_str,
                "tersedia_text": tersedia_str,
                "bor_text": bor_str,
                "color_hex": color_hex,
                "gmaps_url": gmaps_url,
            }
        )

    if map_rows:
        map_json = json.dumps(map_rows)
        leaflet_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                html, body, #map {{ width: 100%; height: 100%; margin: 0; padding: 0; background: #f8fafc; border-radius: 12px; }}
                .leaflet-tooltip {{ font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border-radius: 8px; padding: 8px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border: none; }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map = L.map('map', {{ zoomControl: true }}).setView([-7.6, 112.5], 7);
                L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                    maxZoom: 18,
                    attribution: '&copy; <a href="https://carto.com/">CARTO</a>'
                }}).addTo(map);

                var data = {map_json};
                data.forEach(function(h) {{
                    var marker = L.circleMarker([h.lat, h.lon], {{
                        color: '#ffffff',
                        fillColor: h.color_hex,
                        fillOpacity: 0.92,
                        radius: 9,
                        weight: 2
                    }}).addTo(map);

                    var tooltipHtml = "<b>" + h.nama_rs + " (" + h.kode_rs + ")</b><br/>" +
                        "📍 " + h.kota + "<br/>" +
                        "🌐 Lat " + h.lat + ", Lon " + h.lon + "<br/>" +
                        "Status: <b>" + h.status + "</b><br/>" +
                        "Kapasitas: <b>" + h.kapasitas_text + "</b> | Terisi: <b>" + h.terisi_text + "</b> | Tersedia: <b>" + h.tersedia_text + "</b><br/>" +
                        "BOR: <b>" + h.bor_text + "</b><br/>" +
                        "<span style='color:#2563EB; font-weight:bold; margin-top:4px; display:inline-block;'>👉 Klik lingkaran untuk buka Google Maps</span>";

                    marker.bindTooltip(tooltipHtml, {{ sticky: true }});

                    marker.on('click', function() {{
                        window.open(h.gmaps_url, '_blank');
                    }});
                }});
            </script>
        </body>
        </html>
        """
        components.html(leaflet_html, height=430)

with col_right:
    render_section_heading(
        "📊 Status Keterisian Tempat Tidur (BOR)",
        "Ringkasan persentase keterisian kamar tiap rumah sakit.",
    )

    regular_rs = summary[~summary["kode_rs"].isin(["RSKH", "RSSG", "RSHP"])].sort_values(
        ["ada_data", "bor"], ascending=[False, False]
    )
    cap_only_rs = summary[summary["kode_rs"].isin(["RSKH", "RSSG", "RSHP"])].sort_values(
        ["ada_data"], ascending=[False]
    )
    gauge_summary = pd.concat([regular_rs, cap_only_rs], ignore_index=True)

    gauge_html = ['<div class="gauge-grid">']
    for row in gauge_summary.itertuples():
        is_cap_only = row.kode_rs in ["RSKH", "RSSG"]
        is_rshp = row.kode_rs == "RSHP"
        if is_rshp:
            pct = None
            sub_label = "Data Belum Tersedia"
        elif is_cap_only:
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
                is_capacity_only=(is_cap_only or is_rshp),
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
        "Kapasitas / Belum Ada Data</span>"
        "</div>"
    )
    st.markdown(legend_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Ketersediaan Tempat Tidur menurut Kelas (Pills & Distribution)
# ---------------------------------------------------------------------
st.markdown("")
available_classes_set = set()
for hospital_name, kode_rs in hospital_codes.items():
    snapshot = latest_by_code.get(kode_rs, pd.DataFrame())
    if not snapshot.empty:
        mapped_list = snapshot["kelas"].map(canonicalize_kelas).dropna().unique()
        for k in mapped_list:
            available_classes_set.add(k)

from theme import get_kelas_sort_key

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
    "Pilih kelas untuk membandingkan jumlah bed di tiap RS pada kartu di bawah.",
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

with filter_right:
    m_cols = st.columns(2)
    with m_cols[0]:
        t_active = st.session_state[METRIC_FILTER_KEY] == "Tersedia"
        if st.button(
            "Tersedia",
            key="metric_tersedia",
            type="primary" if t_active else "secondary",
            use_container_width=True,
        ):
            st.session_state[METRIC_FILTER_KEY] = "Tersedia"
            st.rerun()
    with m_cols[1]:
        i_active = st.session_state[METRIC_FILTER_KEY] == "Terisi"
        if st.button(
            "Terisi",
            key="metric_terisi",
            type="primary" if i_active else "secondary",
            use_container_width=True,
        ):
            st.session_state[METRIC_FILTER_KEY] = "Terisi"
            st.rerun()

selected_kelas = st.session_state[KELAS_FILTER_KEY]
selected_metric = st.session_state[METRIC_FILTER_KEY]
metric_column = "tersedia" if selected_metric == "Tersedia" else "terisi"

distribution_rows: list[dict[str, object]] = []
for hospital_name, kode_rs in hospital_codes.items():
    snapshot = latest_by_code.get(kode_rs, pd.DataFrame())

    if kode_rs in ["RSKH", "RSSG"]:
        metric_column = "kapasitas"

    if snapshot.empty:
        distribution_rows.append(
            {
                "nama_rs": hospital_name,
                "value": 0,
            }
        )
        continue

    working = snapshot.copy()
    working["kelas_clean"] = working["kelas"].map(canonicalize_kelas)

    if selected_kelas != "Semua Kelas":
        subset = working[working["kelas_clean"] == selected_kelas]
    else:
        subset = working

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
# Bar Chart Berdiri: Perbandingan Kapasitas, Terisi, dan Tersedia per RSUD
# ---------------------------------------------------------------------
st.markdown("")
render_section_heading(
    "📊 Perbandingan Kapasitas, Bed Terisi, dan Bed Tersedia per RSUD",
)

barchart_data: list[dict[str, object]] = []
for row in summary.itertuples():
    rs_name = str(row.nama_rs)
    code = str(row.kode_rs)
    
    if code == "RSHP":
        continue
    elif code in ["RSKH", "RSSG"]:
        if pd.notna(row.kapasitas) and row.ada_data:
            barchart_data.append({
                "nama_rs": rs_name,
                "kode_rs": code,
                "Kategori": "Total Kapasitas",
                "Jumlah": int(row.kapasitas),
            })
    else:
        if pd.notna(row.kapasitas) and row.ada_data:
            barchart_data.append({
                "nama_rs": rs_name,
                "kode_rs": code,
                "Kategori": "Total Kapasitas",
                "Jumlah": int(row.kapasitas),
            })
            barchart_data.append({
                "nama_rs": rs_name,
                "kode_rs": code,
                "Kategori": "Bed Terisi",
                "Jumlah": int(row.terisi),
            })
            barchart_data.append({
                "nama_rs": rs_name,
                "kode_rs": code,
                "Kategori": "Bed Tersedia",
                "Jumlah": int(row.tersedia),
            })

df_bar = pd.DataFrame(barchart_data)

if not df_bar.empty:
    bars = (
        alt.Chart(df_bar)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(
                "nama_rs:N",
                title=None,
                axis=alt.Axis(
                    labelAngle=-48,
                    labelAlign="right",
                    labelFontSize=10,
                    labelFontWeight="bold",
                    labelLimit=300,
                    labelOverlap=False,
                ),
            ),
            xOffset=alt.XOffset(
                "Kategori:N",
                sort=["Total Kapasitas", "Bed Terisi", "Bed Tersedia"],
            ),
            y=alt.Y(
                "Jumlah:Q",
                title="Jumlah Tempat Tidur",
                axis=alt.Axis(
                    grid=True,
                    values=list(range(0, 1150, 100)),
                ),
            ),
            color=alt.Color(
                "Kategori:N",
                scale=alt.Scale(
                    domain=["Total Kapasitas", "Bed Terisi", "Bed Tersedia"],
                    range=["#2563EB", "#F59E0B", "#10B981"],
                ),
                legend=alt.Legend(title=None, orient="top", padding=10),
            ),
            tooltip=[
                alt.Tooltip("nama_rs:N", title="Rumah Sakit"),
                alt.Tooltip("Kategori:N", title="Kategori"),
                alt.Tooltip("Jumlah:Q", title="Jumlah Bed", format=","),
            ],
        )
    )

    text = bars.mark_text(
        align="center",
        baseline="bottom",
        dy=-3,
        fontSize=8.5,
        fontWeight="bold",
    ).encode(
        text=alt.Text("Jumlah:Q", format="d")
    )

    chart_bar = (bars + text).properties(height=480)
    st.altair_chart(chart_bar, use_container_width=True)

# ---------------------------------------------------------------------
# Direktori Profil & Biodata RSUD Pemprov Jawa Timur (Di Bagian Paling Bawah)
# ---------------------------------------------------------------------
st.markdown("")
st.divider()
render_section_heading(
    "🏥 Direktori Profil & Biodata RSUD Pemprov Jatim",
    "Informasi lengkap kelas layanan, alamat presisi, kontak IGD 24 jam, dan link website resmi Rumah Sakit Pemerintah Provinsi Jawa Timur.",
)

HOSPITAL_PROFILES = [
    {
        "nama": "RSUD Dr. Soetomo",
        "kode": "RSDS",
        "tipe": "Kelas A (Rujukan Utama Jatim)",
        "kota": "Kota Surabaya",
        "alamat": "Jl. Mayjen Prof. Dr. Moestopo No. 6-8, Gubeng, Surabaya",
        "telepon": "(031) 5501078 / 5501234",
        "url": "https://rsudrsoetomo.jatimprov.go.id/",
    },
    {
        "nama": "RSUD Dr. Saiful Anwar",
        "kode": "RSSA",
        "tipe": "Kelas A (Rujukan Utama Malang Raya)",
        "kota": "Kota Malang",
        "alamat": "Jl. Jaksa Agung Suprapto No. 2, Klojen, Malang",
        "telepon": "(0341) 362101 / 362102",
        "url": "https://rsusaifulanwar.jatimprov.go.id/",
    },
    {
        "nama": "RSUD dr. Soedono Madiun",
        "kode": "RSSM",
        "tipe": "Kelas B (Rujukan Madiun Raya)",
        "kota": "Kota Madiun",
        "alamat": "Jl. dr. Soetomo No. 59, Kartoharjo, Madiun",
        "telepon": "(0351) 464325 / 464326",
        "url": "https://rssoedono.jatimprov.go.id/utama/",
    },
    {
        "nama": "RSUD Haji Provinsi Jawa Timur",
        "kode": "RSHJ",
        "tipe": "Kelas B (Rujukan Umum & Haji)",
        "kota": "Kota Surabaya",
        "alamat": "Jl. ITENAS No. 12-14, Sukolilo, Surabaya",
        "telepon": "(031) 5924000 / 5924001",
        "url": "https://rsuhaji.jatimprov.go.id/",
    },
    {
        "nama": "RS Jiwa Menur Provinsi Jawa Timur",
        "kode": "RSMN",
        "tipe": "Khusus Kesehatan Jiwa & NAPZA",
        "kota": "Kota Surabaya",
        "alamat": "Jl. Menur No. 120, Gubeng, Surabaya",
        "telepon": "(031) 5021635 / 5021637",
        "url": "https://rsmenur.jatimprov.go.id/",
    },
    {
        "nama": "RSUD Karsa Husada Batu",
        "kode": "RSKH",
        "tipe": "Kelas B (Rujukan Kota Batu & Malang)",
        "kota": "Kota Batu",
        "alamat": "Jl. Ahmad Yani No. 10-13, Batu",
        "telepon": "(0341) 591076",
        "url": "https://rsukarsahusadabatu.jatimprov.go.id/",
    },
    {
        "nama": "RSUD Sumberglagah",
        "kode": "RSSG",
        "tipe": "Kelas C (Rujukan Mojokerto)",
        "kota": "Kabupaten Mojokerto",
        "alamat": "Jl. Raya Sumberglagah, Pacet, Mojokerto",
        "telepon": "(0321) 690412",
        "url": "https://rssumberglagah.jatimprov.go.id/web_rs/",
    },
    {
        "nama": "RS Paru Jember",
        "kode": "RSPJ",
        "tipe": "Khusus Paru & Respiratori",
        "kota": "Kabupaten Jember",
        "alamat": "Jl. Nusa Indah No. 28, Patrang, Jember",
        "telepon": "(0331) 484300",
        "url": "https://www.rspjember.jatimprov.go.id/",
    },
    {
        "nama": "RS Paru Manguharjo Madiun",
        "kode": "RSPM",
        "tipe": "Khusus Paru & Respiratori",
        "kota": "Kota Madiun",
        "alamat": "Jl. Yos Sudarso No. 108, Manguharjo, Madiun",
        "telepon": "(0351) 462719",
        "url": "https://rspmanguharjo.jatimprov.go.id/",
    },
    {
        "nama": "RS Mata Masyarakat Jawa Timur",
        "kode": "RSMM",
        "tipe": "Khusus Kesehatan Mata",
        "kota": "Kota Surabaya",
        "alamat": "Jl. Gayung Kebonsari No. 49, Gayungan, Surabaya",
        "telepon": "(031) 8283508",
        "url": "https://rsmm.jatimprov.go.id/",
    },
    {
        "nama": "RSU Mohammad Noer Pamekasan",
        "kode": "RSMNO",
        "tipe": "Kelas C (Rujukan Madura)",
        "kota": "Kabupaten Pamekasan",
        "alamat": "Jl. Bonorogo No. 17, Pamekasan, Madura",
        "telepon": "(0324) 322432",
        "url": "https://rsumohammadnoer.jatimprov.go.id/",
    },
    {
        "nama": "RSUD Daha Husada Kediri",
        "kode": "RSDH",
        "tipe": "Kelas C (Rujukan Kediri)",
        "kota": "Kota Kediri",
        "alamat": "Jl. Veteran No. 48, Mojoroto, Kediri",
        "telepon": "(0354) 771034",
        "url": "https://rsuddahahusada.jatimprov.go.id/",
    },
    {
        "nama": "RSUD Dungus Madiun",
        "kode": "RSDG",
        "tipe": "Kelas C (Rujukan Kabupaten Madiun)",
        "kota": "Kabupaten Madiun",
        "alamat": "Jl. Raya Dungus, Wungu, Madiun",
        "telepon": "(0351) 457008",
        "url": "https://rsuddungus.jatimprov.go.id/",
    },
    {
        "nama": "RSUD Husada Prima",
        "kode": "RSHP",
        "tipe": "Kelas C (Umum & Paru)",
        "kota": "Kota Surabaya",
        "alamat": "Jl. Karang Tembok No. 39, Semampir, Surabaya",
        "telepon": "(031) 3713337",
        "url": "https://rsudhusadaprima.jatimprov.go.id/",
    },
]

for i in range(0, len(HOSPITAL_PROFILES), 3):
    cols = st.columns(3)
    chunk = HOSPITAL_PROFILES[i : i + 3]
    for col, profile in zip(cols, chunk):
        with col:
            kode = profile["kode"]
            png_path = f"assets/logos/{kode}.png"
            jpg_path = f"assets/logos/{kode}.jpg"
            logo_path = png_path if os.path.exists(png_path) else (jpg_path if os.path.exists(jpg_path) else None)
            logo_b64 = get_base64_logo(logo_path)
            
            logo_html = f'<img src="{logo_b64}" style="height:38px; max-width:90px; object-fit:contain;" alt="{kode}" />' if logo_b64 else f'<span style="background:#eef4ff; color:#1e3a8a; font-weight:700; font-size:0.75rem; padding:4px 10px; border-radius:10px;">{kode}</span>'

            st.markdown(
                f'<div class="dist-card" style="padding:22px 24px; margin-bottom:20px; display:flex; flex-direction:column; justify-content:space-between; min-height:310px; height:100%;">'
                f'<div>'
                f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">'
                f'{logo_html}'
                f'<span style="background:#f1f5f9; color:#475569; font-size:0.75rem; font-weight:600; padding:4px 10px; border-radius:10px;">{profile["kota"]}</span>'
                f'</div>'
                f'<h4 style="margin:8px 0 4px; color:#0f2f6b; font-size:1.08rem; font-weight:800; line-height:1.3;">{profile["nama"]}</h4>'
                f'<p style="margin:0 0 10px; color:#2563eb; font-size:0.82rem; font-weight:700;">{profile["tipe"]}</p>'
                f'<p style="margin:0 0 6px; color:#475569; font-size:0.82rem; line-height:1.35;">📍 {profile["alamat"]}</p>'
                f'<p style="margin:0 0 12px; color:#475569; font-size:0.82rem;">☎️ IGD/Telp: <b>{profile["telepon"]}</b></p>'
                f'</div>'
                f'<a href="{profile["url"]}" target="_blank" style="text-decoration:none;">'
                f'<div style="text-align:center; background:#f8fafc; border:1px solid #dbe7ff; color:#1e40af; font-size:0.82rem; font-weight:700; padding:9px 12px; border-radius:12px; transition:all 0.2s ease;">🌐 Website Resmi</div>'
                f'</a>'
                f'</div>',
                unsafe_allow_html=True,
            )
