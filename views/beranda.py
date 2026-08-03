from __future__ import annotations

import pandas as pd
import streamlit as st

from database import load_latest_many
from hospitals import HOSPITALS
from theme import (
    inject_base_style,
    render_hero,
    render_section_heading,
)

inject_base_style()

# ---------------------------------------------------------------------
# Halaman Beranda (Fast Render)
# ---------------------------------------------------------------------

import os

# ---------------------------------------------------------------------
# Check 3 Logos (Pemprov Jatim -> Kominfo -> UNAIR)
# ---------------------------------------------------------------------
pemprov_path = "assets/logos/logo_pemprov.png" if os.path.exists("assets/logos/logo_pemprov.png") else ("assets/logos/logo_pemprov.jpg" if os.path.exists("assets/logos/logo_pemprov.jpg") else None)
kominfo_path = "assets/logos/logo_kominfo.png" if os.path.exists("assets/logos/logo_kominfo.png") else ("assets/logos/logo_kominfo.jpg" if os.path.exists("assets/logos/logo_kominfo.jpg") else None)
unair_path = "assets/logos/logo_unair.png" if os.path.exists("assets/logos/logo_unair.png") else ("assets/logos/logo_unair.jpg" if os.path.exists("assets/logos/logo_unair.jpg") else None)

# Executive Hero Banner Container
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
        l1, l2, l3 = st.columns(3)
        with l1:
            if pemprov_path:
                st.image(pemprov_path, width=65)
            else:
                st.caption("**[ PEMPROV JATIM ]**")
        with l2:
            if kominfo_path:
                st.image(kominfo_path, width=65)
            else:
                st.caption("**[ DISKOMINFO ]**")
        with l3:
            if unair_path:
                st.image(unair_path, width=65)
            else:
                st.caption("**[ UNAIR ]**")

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
# Direktori Profil & Biodata 14 RSUD Pemprov Jawa Timur (3 Kartu per Baris)
# ---------------------------------------------------------------------
st.markdown("")
render_section_heading(
    "🏥 Direktori Profil & Biodata 14 RSUD Pemprov Jatim",
    "Informasi lengkap kelas layanan, alamat presisi, kontak IGD 24 jam, dan link website resmi 14 Rumah Sakit Pemerintah Provinsi Jawa Timur.",
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
        "url": "https://rsudsoedono.jatimprov.go.id/",
    },
    {
        "nama": "RSUD Haji Provinsi Jawa Timur",
        "kode": "RSHJ",
        "tipe": "Kelas B (Rujukan Umum & Haji)",
        "kota": "Kota Surabaya",
        "alamat": "Jl. ITENAS No. 12-14, Sukolilo, Surabaya",
        "telepon": "(031) 5924000 / 5924001",
        "url": "https://rshaji.jatimprov.go.id/",
    },
    {
        "nama": "RS Jiwa Menur Provinsi Jawa Timur",
        "kode": "RSMN",
        "tipe": "Khusus Kesehatan Jiwa & NAPZA",
        "kota": "Kota Surabaya",
        "alamat": "Jl. Menur No. 120, Gubeng, Surabaya",
        "telepon": "(031) 5021635 / 5021637",
        "url": "https://rsjmenur.jatimprov.go.id/",
    },
    {
        "nama": "RSUD Karsa Husada Batu",
        "kode": "RSKH",
        "tipe": "Kelas B (Rujukan Kota Batu & Malang)",
        "kota": "Kota Batu",
        "alamat": "Jl. Ahmad Yani No. 10-13, Batu",
        "telepon": "(0341) 591076",
        "url": "https://rsudkarsahusada.jatimprov.go.id/",
    },
    {
        "nama": "RSUD Sumberglagah",
        "kode": "RSSG",
        "tipe": "Kelas C (Rujukan Mojokerto)",
        "kota": "Kabupaten Mojokerto",
        "alamat": "Jl. Raya Sumberglagah, Pacet, Mojokerto",
        "telepon": "(0321) 690412",
        "url": "https://rssumberglagah.jatimprov.go.id/web_rs/kamar/",
    },
    {
        "nama": "RS Paru Jember",
        "kode": "RSPJ",
        "tipe": "Khusus Paru & Respiratori",
        "kota": "Kabupaten Jember",
        "alamat": "Jl. Nusa Indah No. 28, Patrang, Jember",
        "telepon": "(0331) 484300",
        "url": "http://rsparujember.jatimprov.go.id/kamar",
    },
    {
        "nama": "RS Paru Manguharjo Madiun",
        "kode": "RSPM",
        "tipe": "Khusus Paru & Respiratori",
        "kota": "Kota Madiun",
        "alamat": "Jl. Yos Sudarso No. 108, Manguharjo, Madiun",
        "telepon": "(0351) 462719",
        "url": "https://rspmanguharjo.jatimprov.go.id/kamar/",
    },
    {
        "nama": "RS Mata Masyarakat Jawa Timur",
        "kode": "RSMM",
        "tipe": "Khusus Kesehatan Mata",
        "kota": "Kota Surabaya",
        "alamat": "Jl. Gayung Kebonsari No. 49, Gayungan, Surabaya",
        "telepon": "(031) 8283508",
        "url": "https://rsmm.jatimprov.go.id/informasi-ketersediaan-kamar/",
    },
    {
        "nama": "RSU Mohammad Noer Pamekasan",
        "kode": "RSMNO",
        "tipe": "Kelas C (Rujukan Madura)",
        "kota": "Kabupaten Pamekasan",
        "alamat": "Jl. Bonorogo No. 17, Pamekasan, Madura",
        "telepon": "(0324) 322432",
        "url": "https://rsumohnoer.jatimprov.go.id/",
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

            with st.container(border=True):
                top_l, top_r = st.columns([1.5, 1])
                with top_l:
                    if logo_path:
                        st.image(logo_path, width=75)
                    else:
                        st.caption(f"**[{kode}]**")
                with top_r:
                    st.markdown(
                        f'<div style="text-align:right;"><span style="background:#f1f5f9; color:#475569; font-size:0.75rem; font-weight:600; padding:4px 10px; border-radius:10px;">{profile["kota"]}</span></div>',
                        unsafe_allow_html=True,
                    )

                st.markdown(
                    f'<h4 style="margin:6px 0 4px; color:#0f2f6b; font-size:1.05rem; font-weight:800; line-height:1.3;">{profile["nama"]}</h4>'
                    f'<p style="margin:0 0 8px; color:#2563eb; font-size:0.8rem; font-weight:700;">{profile["tipe"]}</p>'
                    f'<p style="margin:0 0 4px; color:#475569; font-size:0.8rem; line-height:1.35;">📍 {profile["alamat"]}</p>'
                    f'<p style="margin:0 0 10px; color:#475569; font-size:0.8rem;">☎️ IGD/Telp: <b>{profile["telepon"]}</b></p>',
                    unsafe_allow_html=True,
                )
                st.link_button(
                    "🌐 Buka Website Resmi",
                    profile["url"],
                    use_container_width=True,
                )
