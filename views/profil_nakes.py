from __future__ import annotations

from html import escape
import io

import pandas as pd
import streamlit as st

from components.nakes_charts import (
    PLOT_CONFIG,
    composition_treemap,
    dokter_kategori_bar,
    dokter_kategori_donut,
    format_period,
    gender_heatmap,
    gender_pyramid,
    hospital_lollipop,
    nakes_composition_heatmap,
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

    if selected_hospital != "Semua RS":
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
        "tenaga kesehatan pada rumah sakit daerah provinsi jawa timur"
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
        "Periode",
        periods,
        format_func=format_period,
    )

    group = f2.selectbox(
        "Profesi",
        ["Semua profesi"] + GROUPS,
    )

    hospital = f3.selectbox(
        "Rumah sakit",
        ["Semua RS"] + HOSPITALS_NAKES,
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
            f"Data dari {int(base['nama_rs'].nunique())} "
            "RS Daerah Jawa Timur"
        ),
        "color": "#2563EB",
        "trend": total_history,
    },
]


for group_name, label in [
    (
        "Dokter",
        "Dokter",
    ),
    (
        "Perawat",
        "Perawat",
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
            "label": "Pertumbuhan jumlah nakes",
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
    "Dokter": "dokter",
    "Perawat": "perawat",
    "Tenaga Kesehatan Lainnya": (
        "nakes lainnya"
    ),
}[largest_group]


rs_count = base["nama_rs"].nunique()
rs_message = (
    f"Data mencakup {rs_count} Rumah Sakit Daerah "
    "Pemprov Jawa Timur."
)

growth_message = (
    (
        f"Total tenaga berubah {growth:+.1f}% "
        f"dibanding {format_period(previous_period)}."
    )
    if growth is not None
    else (
        "Belum tersedia periode pembanding "
        "untuk menghitung pertumbuhan."
    )
)


render_insights(
    [
        (
            f"{leader['nama_rs']} memiliki "
            "total tenaga kesehatan tertinggi: "
            f"{fmt_number(float(leader['jumlah']))} "
            "orang."
        ),
        (
            "Komposisi profesi tenaga kesehatan terbanyak adalah "
            f"{largest_label.lower()}: "
            f"{fmt_number(float(group_totals.max()))} "
            "orang."
        ),
        rs_message,
        growth_message,
    ],
    title="Ringkasan Eksekutif",
)


tree_col, doc_col = st.columns(
    [1, 1],
    gap="large",
)

with tree_col:
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

with doc_col:
    section_heading(
        "Distribusi Kategori Dokter",
        "Sebaran Dokter Spesialis, Dokter Umum, Dokter Gigi, dan Dokter Gigi Spesialis.",
    )

    st.plotly_chart(
        dokter_kategori_bar(base),
        use_container_width=True,
        config=PLOT_CONFIG,
    )

section_heading("Pertumbuhan Jumlah Tenaga Kesehatan")

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
        indexed=False,
    ),
    use_container_width=True,
    config=PLOT_CONFIG,
)


rank_col, heatmap_col = st.columns(
    [1, 1],
    gap="large",
)


with rank_col:
    section_heading(
        "Jumlah tenaga kesehatan berdasarkan rumah sakit",
        (
            "Batang yang lebih panjang "
            "menunjukkan jumlah tenaga "
            "yang lebih besar."
        ),
    )

    st.plotly_chart(
        hospital_lollipop(ranking),
        use_container_width=True,
        config=PLOT_CONFIG,
    )


with heatmap_col:
    section_heading(
        "Komposisi Tenaga Kesehatan",
        (
            "Proporsi tiap profesi "
            "pada masing-masing rumah sakit."
        ),
    )

    st.plotly_chart(
        nakes_composition_heatmap(base),
        use_container_width=True,
        config=PLOT_CONFIG,
    )


def _to_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Data Nakes")
        return output.getvalue()
    except Exception:
        return df.to_csv(index=False).encode("utf-8-sig")


section_heading("Unduh Data")


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


with st.container(border=True):
    col_info, col_action = st.columns([2.5, 1], gap="medium")

    with col_info:
        st.markdown(
            "<div style='padding-top:2px;'>"
            "<b style='font-size:1.02rem; color:#0f2f6b;'>Unduh Data Tenaga Kesehatan</b><br>"
            "<span style='color:#64748b; font-size:0.88rem;'>"
            f"Total {len(table)} baris data · {int(base['nama_rs'].nunique())} rumah sakit · periode {format_period(period)}"
            "</span>"
            "</div>",
            unsafe_allow_html=True,
        )

    with col_action:
        with st.popover("📥 Unduh Data", use_container_width=True):
            st.markdown("**Pilih format file:**")
            st.download_button(
                "📄 Format CSV (.csv)",
                data=table.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"profil_nakes_{period}.csv",
                mime="text/csv",
                use_container_width=True,
            )
            st.download_button(
                "📊 Format Excel (.xlsx)",
                data=_to_excel(table),
                file_name=f"profil_nakes_{period}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )