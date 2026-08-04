from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from components.nakes_charts import (
    PLOT_CONFIG,
    composition_treemap,
    gender_heatmap,
    gender_pyramid,
    hospital_lollipop,
    profession_radar,
    trend_chart,
)
from components.nakes_ui import (
    GENDER_COLORS,
    PROFESSION_COLORS,
    fmt_number,
    inject_nakes_style,
    render_insights,
    render_kpi_grid,
    section_heading,
    short_name,
)
from nakes_api import (
    GROUPS,
    HOSPITALS_NAKES,
    load_nakes_data,
    period_key,
)
from theme import inject_base_style, render_hero


inject_base_style()
inject_nakes_style()


def _scope(
    frame: pd.DataFrame,
    selected_group: str,
    selected_hospital: str,
    selected_qualification: str,
) -> pd.DataFrame:
    result = frame.copy()

    if selected_group != "Semua profesi":
        result = result[
            result["kelompok"] == selected_group
        ]

    if selected_hospital != "Semua 14 RS":
        result = result[
            result["nama_rs"] == selected_hospital
        ]

    if selected_qualification != "Semua kualifikasi":
        result = result[
            result["kualifikasi"]
            == selected_qualification
        ]

    return result


def _series(
    frame: pd.DataFrame,
    periods: list[str],
    group_name: str | None = None,
    gender_name: str | None = None,
    percentage: bool = False,
) -> list[float]:
    values: list[float] = []

    for item in periods:
        part = frame[
            frame["periode"] == item
        ]

        if group_name:
            part = part[
                part["kelompok"] == group_name
            ]

        if gender_name:
            numerator = float(
                part[
                    part["jenis_kelamin"]
                    == gender_name
                ]["jumlah"].sum()
            )

            known = float(
                part[
                    part["jenis_kelamin"].isin(
                        [
                            "Laki-laki",
                            "Perempuan",
                        ]
                    )
                ]["jumlah"].sum()
            )

            values.append(
                numerator / known * 100
                if percentage and known
                else numerator
            )
        else:
            values.append(
                float(part["jumlah"].sum())
            )

    return values


render_hero(
    "Profil Tenaga Kesehatan",
    (
        "Komposisi, pemerataan, dan perkembangan "
        "tenaga kesehatan pada 14 rumah sakit provinsi"
    ),
    caption=(
        "Sumber: API Open Data Jawa Timur · "
        "Cache diperbarui otomatis setiap 1 jam"
    ),
)

with st.spinner(
    "Mengambil data tenaga kesehatan "
    "dari Open Data Jawa Timur..."
):
    data, endpoint_status, errors = (
        load_nakes_data()
    )

if data.empty:
    st.error(
        "Data belum dapat dimuat. "
        "Periksa koneksi internet lalu "
        "coba perbarui data."
    )

    if errors:
        with st.expander("Detail kendala API"):
            st.write(
                "\n".join(
                    f"- {item}"
                    for item in errors
                )
            )

    st.stop()


periods_ascending = sorted(
    data["periode"].dropna().unique(),
    key=period_key,
)

periods = list(
    reversed(periods_ascending)
)


with st.container(border=True):
    f1, f2, f3, refresh = st.columns(
        [1.05, 1.45, 2.05, 0.82]
    )

    period = f1.selectbox(
        "Semester",
        periods,
    )

    group = f2.selectbox(
        "Profesi",
        ["Semua profesi"] + GROUPS,
    )

    hospital = f3.selectbox(
        "Rumah sakit",
        ["Semua 14 RS"] + HOSPITALS_NAKES,
    )

    with refresh:
        st.markdown(
            "<div style='height:1.78rem'></div>",
            unsafe_allow_html=True,
        )

        if st.button(
            "Perbarui data",
            type="primary",
            use_container_width=True,
        ):
            load_nakes_data.clear()
            st.rerun()


qualification = "Semua kualifikasi"

qualification_source = _scope(
    data,
    group,
    hospital,
    qualification,
)

if (
    group != "Semua profesi"
    and not qualification_source.empty
):
    qualifications = sorted(
        qualification_source[
            "kualifikasi"
        ]
        .dropna()
        .unique()
    )

    if len(qualifications) > 1:
        qualification = st.selectbox(
            "Kualifikasi/jenis rinci",
            (
                ["Semua kualifikasi"]
                + qualifications
            ),
        )


all_period_scope = _scope(
    data,
    group,
    hospital,
    qualification,
)

base = all_period_scope[
    all_period_scope["periode"] == period
].copy()


st.markdown(
    (
        '<div class="nakes-filter-note">'
        "Tampilan aktif: "
        f"<b>{escape(period)}</b> · "
        f"<b>{escape(group)}</b> · "
        f"<b>{escape(hospital)}</b>"
        "</div>"
    ),
    unsafe_allow_html=True,
)


if base.empty:
    st.warning(
        "Belum ada data untuk kombinasi filter ini. "
        "Nilai kosong tidak dianggap sebagai nol."
    )
    st.stop()


period_index = periods_ascending.index(period)

previous_period = (
    periods_ascending[period_index - 1]
    if period_index > 0
    else None
)

previous = (
    all_period_scope[
        all_period_scope["periode"]
        == previous_period
    ]
    if previous_period
    else pd.DataFrame(
        columns=base.columns
    )
)


total = float(
    base["jumlah"].sum()
)

previous_total = float(
    previous["jumlah"].sum()
)

growth = (
    (total - previous_total)
    / previous_total
    * 100
    if previous_total
    else None
)

group_totals = (
    base.groupby("kelompok")["jumlah"]
    .sum()
    .reindex(
        GROUPS,
        fill_value=0,
    )
)

gender_totals = (
    base.groupby("jenis_kelamin")[
        "jumlah"
    ].sum()
)

male = float(
    gender_totals.get(
        "Laki-laki",
        0,
    )
)

female = float(
    gender_totals.get(
        "Perempuan",
        0,
    )
)

known_gender = male + female

male_pct = (
    male / known_gender * 100
    if known_gender
    else 0
)

female_pct = (
    female / known_gender * 100
    if known_gender
    else 0
)


history_periods = periods_ascending[-8:]

total_history = _series(
    all_period_scope,
    history_periods,
)

cards = [
    {
        "label": "Total tenaga kesehatan",
        "value": fmt_number(total),
        "note": (
            f"{int(base['nama_rs'].nunique())} "
            "RS memiliki data"
        ),
        "color": "#2563EB",
        "trend": total_history,
    },
]


for group_name, label in [
    (
        "Dokter/Tenaga Medis",
        "Dokter",
    ),
    (
        "Perawat",
        "Perawat",
    ),
    (
        "Bidan",
        "Bidan",
    ),
    (
        "Tenaga Kesehatan Lainnya",
        "Nakes lainnya",
    ),
]:
    amount = float(
        group_totals.get(
            group_name,
            0,
        )
    )

    cards.append(
        {
            "label": label,
            "value": fmt_number(amount),
            "note": (
                f"{amount / total * 100:.1f}% "
                "dari total"
                if total
                else "Belum ada data"
            ),
            "color": (
                PROFESSION_COLORS[
                    group_name
                ]
            ),
            "trend": _series(
                all_period_scope,
                history_periods,
                group_name=group_name,
            ),
        }
    )


cards.extend(
    [
        {
            "label": "Laki-laki",
            "value": f"{male_pct:.1f}%",
            "note": (
                f"{fmt_number(male)} orang"
            ),
            "color": (
                GENDER_COLORS["Laki-laki"]
            ),
            "trend": _series(
                all_period_scope,
                history_periods,
                gender_name="Laki-laki",
                percentage=True,
            ),
        },
        {
            "label": "Perempuan",
            "value": f"{female_pct:.1f}%",
            "note": (
                f"{fmt_number(female)} orang"
            ),
            "color": (
                GENDER_COLORS["Perempuan"]
            ),
            "trend": _series(
                all_period_scope,
                history_periods,
                gender_name="Perempuan",
                percentage=True,
            ),
        },
        {
            "label": "Pertumbuhan semester",
            "value": (
                f"{growth:+.1f}%"
                if growth is not None
                else "-"
            ),
            "note": (
                f"dibanding {previous_period}"
                if previous_period
                else "Belum ada pembanding"
            ),
            "color": (
                "#10B981"
                if (
                    growth is not None
                    and growth >= 0
                )
                else "#EF4444"
            ),
            "trend": total_history,
        },
    ]
)


render_kpi_grid(cards)


ranking = (
    base.groupby(
        "nama_rs",
        as_index=False,
    )["jumlah"]
    .sum()
    .sort_values(
        "jumlah",
        ascending=False,
    )
)

leader = ranking.iloc[0]

largest_group = group_totals.idxmax()

largest_label = {
    "Dokter/Tenaga Medis": "dokter",
    "Perawat": "perawat",
    "Bidan": "bidan",
    "Tenaga Kesehatan Lainnya": (
        "nakes lainnya"
    ),
}[largest_group]


gender_message = (
    (
        "Tenaga perempuan mendominasi "
        f"{female_pct:.1f}% dari data gender."
    )
    if female >= male
    else (
        "Tenaga laki-laki mendominasi "
        f"{male_pct:.1f}% dari data gender."
    )
)

growth_message = (
    (
        f"Total tenaga berubah {growth:+.1f}% "
        f"dibanding {previous_period}."
    )
    if growth is not None
    else (
        "Belum tersedia semester pembanding "
        "untuk menghitung pertumbuhan."
    )
)


render_insights(
    [
        (
            f"{leader['nama_rs']} memiliki "
            "total tertinggi: "
            f"{fmt_number(float(leader['jumlah']))} "
            "orang."
        ),
        (
            "Komposisi terbesar adalah "
            f"{largest_label}: "
            f"{fmt_number(float(group_totals.max()))} "
            "orang."
        ),
        gender_message,
        growth_message,
    ]
)


left, right = st.columns(
    [1, 1],
    gap="large",
)

with left:
    section_heading(
        "Komposisi Tenaga Kesehatan",
        (
            "Luas bidang menunjukkan "
            "kontribusi tiap profesi."
        ),
    )

    st.plotly_chart(
        composition_treemap(
            group_totals
        ),
        use_container_width=True,
        config=PLOT_CONFIG,
    )


with right:
    section_heading(
        "Komposisi Gender per Profesi",
        (
            "Laki-laki di kiri dan perempuan "
            "di kanan garis tengah."
        ),
    )

    st.plotly_chart(
        gender_pyramid(base),
        use_container_width=True,
        config=PLOT_CONFIG,
    )


section_heading(
    "Perkembangan Tenaga Kesehatan",
    (
        "Gunakan indeks untuk melihat pola "
        "perubahan; pilih jumlah aktual "
        "untuk membaca volumenya."
    ),
)

trend_mode = st.radio(
    "Mode tren",
    [
        "Indeks perubahan",
        "Jumlah aktual",
    ],
    horizontal=True,
    label_visibility="collapsed",
)

trend = (
    all_period_scope.groupby(
        [
            "periode",
            "kelompok",
        ],
        as_index=False,
    )["jumlah"]
    .sum()
)

trend["urutan"] = trend[
    "periode"
].map(period_key)


st.plotly_chart(
    trend_chart(
        trend,
        indexed=(
            trend_mode
            == "Indeks perubahan"
        ),
    ),
    use_container_width=True,
    config=PLOT_CONFIG,
)


if trend_mode == "Indeks perubahan":
    st.caption(
        "Indeks 100 adalah nilai pada periode "
        "awal masing-masing profesi. Nilai 110 "
        "berarti meningkat 10% dari periode awal."
    )


rank_col, radar_col = st.columns(
    [1.3, 0.8],
    gap="large",
)


with rank_col:
    section_heading(
        "Peringkat Rumah Sakit",
        (
            "Titik yang lebih ke kanan "
            "menunjukkan jumlah tenaga "
            "yang lebih besar."
        ),
    )

    st.plotly_chart(
        hospital_lollipop(ranking),
        use_container_width=True,
        config=PLOT_CONFIG,
    )


with radar_col:
    radar_hospital = (
        hospital
        if hospital != "Semua 14 RS"
        else str(leader["nama_rs"])
    )

    section_heading(
        "Profil Profesi Rumah Sakit",
        (
            f"Komposisi "
            f"{short_name(radar_hospital)} "
            "dibanding rata-rata RS."
        ),
    )

    selected_vector = (
        base[
            base["nama_rs"]
            == radar_hospital
        ]
        .groupby("kelompok")["jumlah"]
        .sum()
    )

    hospital_group = (
        base.groupby(
            [
                "nama_rs",
                "kelompok",
            ]
        )["jumlah"]
        .sum()
        .reset_index()
    )

    benchmark_vector = (
        hospital_group.groupby(
            "kelompok"
        )["jumlah"]
        .mean()
    )

    st.plotly_chart(
        profession_radar(
            selected_vector,
            benchmark_vector,
            radar_hospital,
        ),
        use_container_width=True,
        config=PLOT_CONFIG,
    )


section_heading(
    "Komposisi Gender Antar-Rumah Sakit",
    (
        "Dua matriks menampilkan proporsi "
        "laki-laki dan perempuan dari "
        "data gender yang tersedia."
    ),
)

male_col, female_col = st.columns(
    2,
    gap="large",
)


with male_col:
    st.caption("**Laki-laki (%)**")

    st.plotly_chart(
        gender_heatmap(
            base,
            "Laki-laki",
            [
                [0, "#EFF6FF"],
                [1, "#2563EB"],
            ],
        ),
        use_container_width=True,
        config=PLOT_CONFIG,
    )


with female_col:
    st.caption("**Perempuan (%)**")

    st.plotly_chart(
        gender_heatmap(
            base,
            "Perempuan",
            [
                [0, "#FDF2F8"],
                [1, "#EC4899"],
            ],
        ),
        use_container_width=True,
        config=PLOT_CONFIG,
    )


section_heading(
    "Data Rinci",
    (
        "Gunakan tabel untuk memeriksa "
        "angka dan mengunduh hasil "
        "sesuai filter."
    ),
)


table = (
    base.groupby(
        [
            "nama_rs",
            "kelompok",
            "jenis_kelamin",
        ],
        as_index=False,
    )["jumlah"]
    .sum()
    .sort_values(
        [
            "nama_rs",
            "kelompok",
            "jenis_kelamin",
        ]
    )
)

table["jumlah"] = (
    table["jumlah"]
    .round()
    .astype(int)
)

table = table.rename(
    columns={
        "nama_rs": "Rumah sakit",
        "kelompok": "Profesi",
        "jenis_kelamin": "Jenis kelamin",
        "jumlah": "Jumlah",
    }
)


download_col, status_col = st.columns(
    [1, 3]
)


with download_col:
    st.download_button(
        "Unduh CSV sesuai filter",
        data=table.to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name=(
            f"profil_nakes_{period}.csv"
        ),
        mime="text/csv",
        use_container_width=True,
    )


with status_col:
    st.caption(
        f"{len(table)} baris · "
        f"{int(base['nama_rs'].nunique())} "
        f"rumah sakit · periode {period}"
    )


st.dataframe(
    table,
    use_container_width=True,
    hide_index=True,
    height=min(
        520,
        40 + len(table) * 35,
    ),
)


with st.expander(
    "Lihat status ketersediaan API "
    "14 rumah sakit"
):
    status_display = (
        endpoint_status.copy()
    )

    status_display["nama_rs"] = (
        status_display["nama_rs"]
        .map(short_name)
    )

    status_display = (
        status_display.rename(
            columns={
                "nama_rs": "Rumah sakit",
                "kelompok": "Profesi",
                "status": "Status",
                "baris": "Baris",
            }
        )
    )

    st.dataframe(
        status_display,
        use_container_width=True,
        hide_index=True,
    )