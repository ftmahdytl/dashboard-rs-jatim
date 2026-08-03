from __future__ import annotations

import streamlit as st

from database import initialize_database

st.set_page_config(
    page_title="Monitoring Bed RS Pemprov Jatim",
    page_icon="🏥",
    layout="wide",
)

initialize_database()

beranda_page = st.Page(
    "views/beranda.py",
    title="Beranda",
    icon="🏠",
    default=True,
)
overview_page = st.Page(
    "views/overview.py",
    title="Overview",
    icon="📊",
)
bed_page = st.Page(
    "views/ketersediaan_bed.py",
    title="Ketersediaan Bed",
    icon="🛏️",
)

navigation = st.navigation([beranda_page, overview_page, bed_page])
navigation.run()
