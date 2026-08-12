from __future__ import annotations

from datetime import datetime
import time

import altair as alt
import pandas as pd
import streamlit as st

from database import (
    load_change_details,
    load_history_summary,
    load_latest,
    save_snapshot,
)
from hospitals import HOSPITALS, JAKARTA
from theme import (
    format_datetime_text,
    get_kelas_sort_key,
    inject_base_style,
    render_hero,
    render_stable_table,
)

inject_base_style()
render_hero(
    "Monitoring Ketersediaan Tempat Tidur",
    "Rumah Sakit Pemerintah Provinsi Jawa Timur · Data otomatis",
)

# Filter & kontrol scraping
with st.container(border=True):
    filter_col, toggle_col, interval_col, refresh_col, link_col = st.columns(
        [2.4, 1.3, 1.3, 1.3, 1.3]
    )

    with filter_col:
        selected_hospital_name = st.selectbox(
            "Pilih rumah sakit",
            options=list(HOSPITALS),
        )

    hospital = HOSPITALS[selected_hospital_name]
    selected_code = str(hospital["kode_rs"])
    selected_url = str(hospital["url"])
    selected_scraper = hospital["scraper"]

    with toggle_col:
        st.markdown("<div style='height: 1.65rem;'></div>", unsafe_allow_html=True)
        auto_scrape = st.toggle(
            "Scraping otomatis",
            value=True,
            help="Saat aktif, dashboard mengambil data secara berkala.",
        )

    with interval_col:
        interval_minutes = st.selectbox(
            "Interval update",
            options=[1, 5, 10, 15, 30],
            index=1,
            format_func=lambda value: f"{value} menit",
            disabled=not auto_scrape,
        )

    with refresh_col:
        st.markdown("<div style='height: 1.8rem;'></div>", unsafe_allow_html=True)
        manual_refresh = st.button(
            "Ambil data sekarang",
            type="primary",
            use_container_width=True,
        )

    with link_col:
        st.markdown("<div style='height: 1.8rem;'></div>", unsafe_allow_html=True)
        st.link_button(
            "Sumber data",
            selected_url,
            use_container_width=True,
        )

    st.caption(
        f"Data aktif: **{selected_hospital_name}** · Data tidak akan "
        "disimpan dua kali apabila waktu update pada website masih sama."
    )

error_state_key = f"last_scrape_error_{selected_code}"
check_state_key = f"last_auto_check_epoch_{selected_code}"
initial_state_key = f"initial_scrape_done_{selected_code}"


def run_scraping(show_message: bool = False) -> bool:
    try:
        fresh_data = selected_scraper()
        is_new = save_snapshot(fresh_data)
        st.session_state[error_state_key] = None

        if show_message:
            if is_new:
                st.success("Data terbaru berhasil diambil dan disimpan.")
            else:
                st.info("Scraping berhasil, tetapi data sumber belum berubah.")
        return is_new
    except Exception as error:
        st.session_state[error_state_key] = str(error)
        if show_message:
            st.error(f"Scraping gagal: {error}")
        return False
    finally:
        st.session_state[check_state_key] = time.time()


if initial_state_key not in st.session_state:
    with st.spinner(f"Mengambil data pertama dari {selected_hospital_name}..."):
        run_scraping()
    st.session_state[initial_state_key] = True

if manual_refresh:
    with st.spinner("Mengambil data terbaru..."):
        run_scraping(show_message=True)


@st.fragment(
    run_every=f"{interval_minutes}m" if auto_scrape else None
)
def automatic_scraper() -> None:
    if auto_scrape:
        last_check = st.session_state.get(check_state_key, 0)
        seconds_since_check = time.time() - last_check
        if seconds_since_check >= interval_minutes * 60:
            has_new_data = run_scraping()
            if has_new_data:
                st.rerun()

        latest_fragment_data = load_latest(selected_code)
        if not latest_fragment_data.empty:
            last_check_epoch = st.session_state.get(
                check_state_key,
                time.time(),
            )
            last_check_text = datetime.fromtimestamp(
                last_check_epoch,
                tz=JAKARTA,
            ).strftime("%d-%m-%Y %H:%M:%S")
            st.caption(
                "🟢 Scraping otomatis aktif · Pemeriksaan terakhir: "
                f"{last_check_text} WIB"
            )
        else:
            st.caption("🟡 Scraping otomatis aktif · Menunggu data pertama")
    else:
        st.caption("⚪ Scraping otomatis nonaktif")


automatic_scraper()

last_error = st.session_state.get(error_state_key)
if last_error:
    st.warning(
        "Data terbaru belum dapat diambil. Dashboard menampilkan data "
        f"terakhir yang tersimpan. Detail: {last_error}"
    )

data = load_latest(selected_code)

if data.empty:
    st.error(
        "Belum ada data yang dapat ditampilkan. Pastikan internet aktif, "
        "lalu klik “Ambil data sekarang”."
    )
    st.stop()

is_capacity_only = selected_code in ["RSKH", "RSSG"]
is_no_data = selected_code in ["RSHP"]
is_soedono = selected_code == "RSSM"

total_capacity = int(data["kapasitas"].sum())
total_occupied = int(data["terisi"].sum())
total_available = int(data["tersedia"].sum())
total_not_ready = int(data["tidak_siap"].sum()) if "tidak_siap" in data else 0
total_renovation = int(data["renovasi"].sum()) if ("renovasi" in data and is_soedono) else 0
total_sisrute = int(data["sisrute"].sum()) if ("sisrute" in data and is_soedono) else 0
total_rooms = int(
    data[["kelas", "nama_ruang"]]
    .drop_duplicates()
    .shape[0]
)

if is_no_data:
    cap_str = "-"
    occ_str = "-"
    avail_str = "-"
    occupancy_str = "-"
    total_rooms_str = "-"
elif is_capacity_only:
    cap_str = f"{total_capacity:,}".replace(",", ".")
    occ_str = "-"
    avail_str = "-"
    occupancy_str = "-"
    total_rooms_str = f"{total_rooms:,}".replace(",", ".")
else:
    cap_str = f"{total_capacity:,}".replace(",", ".")
    occ_str = f"{total_occupied:,}".replace(",", ".")
    avail_str = f"{total_available:,}".replace(",", ".")
    occupancy = (total_occupied / total_capacity * 100) if total_capacity else 0.0
    occupancy_str = f"{occupancy:.1f}%"
    total_rooms_str = f"{total_rooms:,}".replace(",", ".")

kpi_cards_html = (
    '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-bottom: 20px;">'
    '<div style="background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); border: 1px solid #BFDBFE; border-radius: 16px; padding: 18px 20px; box-shadow: 0 4px 14px rgba(30, 64, 175, 0.08); transition: transform 0.2s ease;">'
    '<div style="font-size: 0.8rem; font-weight: 750; color: #1E40AF; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">Total Kapasitas</div>'
    f'<div style="font-size: 1.95rem; font-weight: 850; color: #0F2F6B; line-height: 1.1;">{cap_str}</div>'
    '<div style="margin-top: 8px; font-size: 0.75rem; font-weight: 650; color: #3B82F6;">Tempat Tidur RS</div>'
    '</div>'
    '<div style="background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%); border: 1px solid #FDE68A; border-radius: 16px; padding: 18px 20px; box-shadow: 0 4px 14px rgba(180, 83, 9, 0.08); transition: transform 0.2s ease;">'
    '<div style="font-size: 0.8rem; font-weight: 750; color: #92400E; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">Bed Terisi</div>'
    f'<div style="font-size: 1.95rem; font-weight: 850; color: #78350F; line-height: 1.1;">{occ_str}</div>'
    '<div style="margin-top: 8px; font-size: 0.75rem; font-weight: 650; color: #D97706;">Sedang Digunakan</div>'
    '</div>'
    '<div style="background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%); border: 1px solid #A7F3D0; border-radius: 16px; padding: 18px 20px; box-shadow: 0 4px 14px rgba(5, 150, 105, 0.08); transition: transform 0.2s ease;">'
    '<div style="font-size: 0.8rem; font-weight: 750; color: #065F46; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">Bed Tersedia</div>'
    f'<div style="font-size: 1.95rem; font-weight: 850; color: #047857; line-height: 1.1;">{avail_str}</div>'
    '<div style="margin-top: 8px; font-size: 0.75rem; font-weight: 650; color: #059669;">Siap Pakai Pasien</div>'
    '</div>'
    '<div style="background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%); border: 1px solid #DDD6FE; border-radius: 16px; padding: 18px 20px; box-shadow: 0 4px 14px rgba(109, 40, 217, 0.08); transition: transform 0.2s ease;">'
    '<div style="font-size: 0.8rem; font-weight: 750; color: #5B21B6; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">Tingkat Keterisian</div>'
    f'<div style="font-size: 1.95rem; font-weight: 850; color: #4C1D95; line-height: 1.1;">{occupancy_str}</div>'
    '<div style="margin-top: 8px; font-size: 0.75rem; font-weight: 650; color: #7C3AED;">Bed Occupancy Rate</div>'
    '</div>'
    '<div style="background: linear-gradient(135deg, #ECFEFF 0%, #CFFAFE 100%); border: 1px solid #A5F3FC; border-radius: 16px; padding: 18px 20px; box-shadow: 0 4px 14px rgba(14, 116, 144, 0.08); transition: transform 0.2s ease;">'
    '<div style="font-size: 0.8rem; font-weight: 750; color: #0E7490; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">Ruang–Kelas</div>'
    f'<div style="font-size: 1.95rem; font-weight: 850; color: #083344; line-height: 1.1;">{total_rooms_str}</div>'
    '<div style="margin-top: 8px; font-size: 0.75rem; font-weight: 650; color: #0891B2;">Unit Kamar Tercatat</div>'
    '</div>'
    '</div>'
)
st.markdown(kpi_cards_html, unsafe_allow_html=True)

if total_not_ready or (is_soedono and (total_renovation or total_sisrute)):
    status_parts = []
    if total_not_ready:
        not_ready_label = "siap" if selected_code == "RSHJ" else "kosong belum siap"
        status_parts.append(f"{not_ready_label} **{total_not_ready}**")
    if is_soedono and total_renovation:
        status_parts.append(f"renovasi **{total_renovation}**")
    if is_soedono and total_sisrute:
        status_parts.append(f"Sisrute **{total_sisrute}**")
    st.info(
        "Status bed lain pada sumber: "
        + " · ".join(status_parts)
        + ". "
        "Nilai tersebut tidak dihitung sebagai bed terisi atau tersedia."
    )

last_check_epoch = st.session_state.get(check_state_key)
if last_check_epoch is None:
    last_check_text = format_datetime_text(data["waktu_scraping"].iloc[0])
else:
    last_check_text = datetime.fromtimestamp(
        last_check_epoch,
        tz=JAKARTA,
    ).strftime("%d-%m-%Y %H:%M:%S")

source_update_text = format_datetime_text(
    data["waktu_update_sumber"].max()
)
st.caption(
    f"Rumah sakit: {selected_hospital_name} · "
    f"Update website: {source_update_text} WIB · "
    f"Terakhir diperiksa: {last_check_text} WIB"
)

if is_no_data:
    st.info(
        "ℹ️ **Informasi:** Data ketersediaan tempat tidur belum dipublikasikan "
        "pada portal resmi RSUD Husada Prima. Dashboard memantau secara "
        "otomatis dan akan menyajikan tabel serta grafik setelah portal RSUD "
        "memperbarui data ruangannya."
    )
    st.stop()

tab_overview, tab_rooms, tab_history = st.tabs(
    ["Ringkasan", "Detail Ruang", "Riwayat"]
)

with tab_overview:
    class_summary = (
        data.groupby("kelas", as_index=False)
        .agg(
            kapasitas=("kapasitas", "sum"),
            terisi=("terisi", "sum"),
            tersedia=("tersedia", "sum"),
            tidak_siap=("tidak_siap", "sum"),
            renovasi=("renovasi", "sum"),
            sisrute=("sisrute", "sum"),
        )
    )
    class_summary["_sort_key"] = class_summary["kelas"].map(get_kelas_sort_key)
    class_summary = class_summary.sort_values("_sort_key").drop(columns=["_sort_key"])

    tooltip_list = [
        alt.Tooltip("kelas:N", title="Kelas"),
        alt.Tooltip("kapasitas:Q", title="Kapasitas"),
        alt.Tooltip("terisi:Q", title="Terisi"),
        alt.Tooltip("tersedia:Q", title="Tersedia"),
        alt.Tooltip("tidak_siap:Q", title="Kosong belum siap"),
    ]
    if is_soedono:
        tooltip_list.extend([
            alt.Tooltip("renovasi:Q", title="Renovasi"),
            alt.Tooltip("sisrute:Q", title="Sisrute"),
        ])

    chart = (
        alt.Chart(class_summary)
        .mark_bar(cornerRadiusTopRight=7, cornerRadiusBottomRight=7)
        .encode(
            y=alt.Y(
                "kelas:N",
                sort="-x",
                title=None,
                axis=alt.Axis(labelLimit=190),
            ),
            x=alt.X("kapasitas:Q" if (is_capacity_only or is_no_data) else "tersedia:Q", title="Kapasitas bed" if (is_capacity_only or is_no_data) else "Bed tersedia"),
            color=alt.value("#2563EB"),
            tooltip=tooltip_list,
        )
        .properties(height=max(340, len(class_summary) * 30))
    )

    st.subheader("Ketersediaan Bed per Kelas" if not (is_capacity_only or is_no_data) else "Kapasitas Bed per Kelas")
    st.altair_chart(chart, use_container_width=True)
    class_table_view = class_summary.copy()
    class_table_labels = {
        "kelas": "Kelas",
        "kapasitas": "Kapasitas",
        "terisi": "Terisi",
        "tersedia": "Tersedia",
    }
    if is_soedono:
        class_table_labels["renovasi"] = "Renovasi"
        class_table_labels["sisrute"] = "Sisrute"
    else:
        for col in ["renovasi", "sisrute"]:
            if col in class_table_view.columns:
                class_table_view = class_table_view.drop(columns=[col])

    if selected_code == "RSHJ":
        class_table_labels["tidak_siap"] = "Siap"
    elif "tidak_siap" in class_table_view.columns:
        class_table_view = class_table_view.drop(columns=["tidak_siap"])

    for num_col in ["kapasitas", "terisi", "tersedia"]:
        if num_col in class_table_view.columns:
            if is_no_data:
                class_table_view[num_col] = "-"
            elif is_capacity_only and num_col in ["terisi", "tersedia"]:
                class_table_view[num_col] = "-"
            else:
                class_table_view[num_col] = class_table_view[num_col].map(
                    lambda val: f"{int(val):,}".replace(",", ".") if pd.notna(val) else "0"
                )

    render_stable_table(
        class_table_view,
        class_table_labels,
    )

with tab_rooms:
    class_options = sorted(data["kelas"].dropna().unique().tolist(), key=get_kelas_sort_key)
    selected_classes = st.multiselect(
        "Filter kelas",
        class_options,
        placeholder="Semua kelas",
    )

    room_view = data.copy()
    if selected_classes:
        room_view = room_view[
            room_view["kelas"].isin(selected_classes)
        ]

    room_columns = [
        "kategori_pasien",
        "kelas",
        "nama_ruang",
        "kapasitas",
        "terisi",
        "tersedia",
    ]
    room_table_labels = {
        "kategori_pasien": "Kelompok Layanan",
        "kelas": "Kelas",
        "nama_ruang": "Nama Ruang",
        "kapasitas": "Kapasitas",
        "terisi": "Terisi",
        "tersedia": "Tersedia",
        "keterangan": "Keterangan Sumber",
        "persentase_keterisian": "Keterisian",
    }
    if is_soedono:
        room_table_labels["renovasi"] = "Renovasi"
        room_table_labels["sisrute"] = "Sisrute"
        room_columns.extend(["renovasi", "sisrute"])

    if selected_code == "RSHJ" and data["tidak_siap"].sum():
        room_columns.append("tidak_siap")
        room_table_labels["tidak_siap"] = "Siap"

    if data["keterangan"].fillna("").str.strip().ne("").any():
        room_columns.append("keterangan")
    room_columns.append("persentase_keterisian")
    
    unique_rooms = room_view["nama_ruang"].dropna().unique()
    has_room_names = len(unique_rooms) > 1 or (len(unique_rooms) == 1 and unique_rooms[0].strip() != "")

    room_view["_kelas_sort"] = room_view["kelas"].map(get_kelas_sort_key)
    if has_room_names:
        room_view = room_view[room_columns + ["_kelas_sort"]].sort_values(
            ["nama_ruang", "_kelas_sort"],
            ascending=[True, True],
        ).drop(columns=["_kelas_sort"])
    else:
        room_view = room_view[room_columns + ["_kelas_sort"]].sort_values(
            ["_kelas_sort"],
            ascending=[True],
        ).drop(columns=["_kelas_sort"])

    if is_no_data:
        room_view["kapasitas"] = "-"
        room_view["terisi"] = "-"
        room_view["tersedia"] = "-"
        room_view["persentase_keterisian"] = "-"
    elif is_capacity_only:
        room_view["kapasitas"] = room_view["kapasitas"].map(
            lambda val: f"{int(val):,}".replace(",", ".") if pd.notna(val) else "0"
        )
        room_view["terisi"] = "-"
        room_view["tersedia"] = "-"
        room_view["persentase_keterisian"] = "-"
    else:
        room_view["persentase_keterisian"] = (
            room_view["persentase_keterisian"]
            .map(lambda value: f"{float(value):.1f}%" if pd.notna(value) else "0.0%")
        )
        for num_col in ["kapasitas", "terisi", "tersedia"]:
            if num_col in room_view.columns:
                room_view[num_col] = room_view[num_col].map(
                    lambda val: f"{int(val):,}".replace(",", ".") if pd.notna(val) else "0"
                )

    st.subheader(f"Daftar Lengkap Ruang ({len(room_view)} ruang)")
    st.caption(
        "Grafik pada tab Ringkasan menampilkan kelas. "
        "Nama gedung, lantai, dan ruang ditampilkan pada tabel ini."
    )
    render_stable_table(
        room_view,
        room_table_labels,
    )

    csv_data = room_view.to_csv(
        index=False,
        encoding="utf-8-sig",
    ).encode("utf-8-sig")
    st.download_button(
        "Unduh data CSV",
        data=csv_data,
        file_name=f"ketersediaan_bed_{selected_code.lower()}.csv",
        mime="text/csv",
    )

with tab_history:
    history = load_history_summary(selected_code)

    if len(history) < 2:
        st.info(
            "Grafik tren akan muncul setelah minimal dua waktu update "
            "berhasil tersimpan."
        )
    else:
        history["waktu_update_sumber"] = pd.to_datetime(
            history["waktu_update_sumber"],
            errors="coerce",
        )
        history["waktu_scraping"] = pd.to_datetime(
            history["waktu_scraping"],
            errors="coerce",
        )
        history = history.dropna(subset=["waktu_scraping"])

        history_chart = (
            alt.Chart(history)
            .mark_line(point=True, strokeWidth=3)
            .encode(
                x=alt.X(
                    "waktu_scraping:T",
                    title="Waktu pengambilan data",
                ),
                y=alt.Y(
                    "tersedia:Q",
                    title="Total bed tersedia",
                    scale=alt.Scale(zero=False),
                ),
                color=alt.value("#10B981"),
                tooltip=[
                    alt.Tooltip(
                        "waktu_scraping:T",
                        title="Diambil sistem",
                        format="%d-%m-%Y %H:%M:%S",
                    ),
                    alt.Tooltip(
                        "waktu_update_sumber:T",
                        title="Update website",
                        format="%d-%m-%Y %H:%M:%S",
                    ),
                    alt.Tooltip(
                        "tersedia:Q",
                        title="Bed tersedia",
                    ),
                ],
            )
            .properties(height=380)
        )
        st.subheader("Tren Total Bed Tersedia")
        st.altair_chart(history_chart, use_container_width=True)
        history_display = history.copy()
        history_display["waktu_scraping"] = (
            history_display["waktu_scraping"]
            .dt.strftime("%d-%m-%Y %H:%M:%S")
        )
        history_display["waktu_update_sumber"] = (
            history_display["waktu_update_sumber"]
            .dt.strftime("%d-%m-%Y %H:%M:%S")
        )
        history_labels = {
            "waktu_scraping": "Diambil Sistem",
            "waktu_update_sumber": "Update Website",
            "kapasitas": "Kapasitas",
            "terisi": "Terisi",
            "tersedia": "Tersedia",
        }
        if is_soedono:
            history_labels["renovasi"] = "Renovasi"
            history_labels["sisrute"] = "Sisrute"
        else:
            for col in ["renovasi", "sisrute"]:
                if col in history_display.columns:
                    history_display = history_display.drop(columns=[col])

        if selected_code == "RSHJ":
            history_labels["tidak_siap"] = "Siap"
        elif "tidak_siap" in history_display.columns:
            history_display = history_display.drop(columns=["tidak_siap"])

        render_stable_table(
            history_display,
            history_labels,
        )

    st.divider()
    st.subheader("Detail Perubahan Bed per Ruang")
    st.caption(
        "Menampilkan kelas dan ruang yang angkanya berubah dibandingkan "
        "pengambilan data tepat sebelumnya."
    )

    change_details = load_change_details(selected_code)

    if change_details.empty:
        st.info(
            "Belum ada perubahan pada tingkat ruang. Perubahan akan "
            "muncul setelah minimal dua snapshot dengan isi berbeda."
        )
    else:
        change_classes = sorted(
            change_details["kelas"].dropna().unique().tolist()
        )
        selected_change_classes = st.multiselect(
            "Filter kelas yang berubah",
            change_classes,
            placeholder="Semua kelas",
            key="history_change_class_filter",
        )

        if selected_change_classes:
            change_details = change_details[
                change_details["kelas"].isin(selected_change_classes)
            ]

        change_columns = [
            "waktu_scraping",
            "kategori_pasien",
            "kelas",
            "nama_ruang",
            "terisi_sebelum",
            "terisi_sekarang",
            "tersedia_sebelum",
            "tersedia_sekarang",
        ]
        if selected_code == "RSHJ" and change_details["delta_tidak_siap"].ne(0).any():
            change_columns.append("delta_tidak_siap")

        if (
            change_details["delta_renovasi"].ne(0).any()
            or change_details["delta_sisrute"].ne(0).any()
        ):
            change_columns.extend(
                ["delta_renovasi", "delta_sisrute"]
            )
        change_columns.append("perubahan")
        change_display = change_details[change_columns].copy()
        change_display["waktu_scraping"] = pd.to_datetime(
            change_display["waktu_scraping"],
            errors="coerce",
        ).dt.strftime("%d-%m-%Y %H:%M:%S")

        render_stable_table(
            change_display,
            {
                "waktu_scraping": "Waktu Perubahan",
                "kategori_pasien": "Kelompok Layanan",
                "kelas": "Kelas",
                "nama_ruang": "Nama Ruang",
                "terisi_sebelum": "Terisi Sebelum",
                "terisi_sekarang": "Terisi Sekarang",
                "tersedia_sebelum": "Tersedia Sebelum",
                "tersedia_sekarang": "Tersedia Sekarang",
                "delta_tidak_siap": "Δ Siap",
                "delta_renovasi": "Δ Renovasi",
                "delta_sisrute": "Δ Sisrute",
                "perubahan": "Keterangan",
            },
        )
