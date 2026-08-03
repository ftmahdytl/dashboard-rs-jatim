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

import base64
import os

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
