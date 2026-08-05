from __future__ import annotations

import streamlit as st

from database import initialize_database


st.set_page_config(
    page_title="Monitoring Bed RS Pemprov Jatim",
    page_icon="🏥",
    layout="wide",
)

initialize_database()


overview_page = st.Page(
    "views/overview.py",
    title="Overview",
    icon="📊",
    default=True,
)

bed_page = st.Page(
    "views/ketersediaan_bed.py",
    title="Ketersediaan Bed Rumah Sakit",
    icon="🛏️",
)

nakes_page = st.Page(
    "views/profil_nakes.py",
    title="Profil Tenaga Kesehatan",
    icon="🩺",
)


navigation = st.navigation(
    [
        overview_page,
        bed_page,
        nakes_page,
    ]
)

navigation.run()