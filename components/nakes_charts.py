from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go

from components.nakes_ui import (
    GENDER_COLORS,
    PROFESSION_COLORS,
    short_name,
)


GROUPS = list(PROFESSION_COLORS)

PLOT_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
}


def _base_layout(
    height: int,
    **kwargs: object,
) -> dict[str, object]:
    layout: dict[str, object] = {
        "height": height,
        "margin": {
            "l": 18,
            "r": 18,
            "t": 22,
            "b": 24,
        },
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {
            "family": "Inter, Arial, sans-serif",
            "color": "#334155",
            "size": 12,
        },
        "hoverlabel": {
            "bgcolor": "#0F172A",
            "font": {"color": "white"},
        },
    }

    layout.update(kwargs)
    return layout


def composition_treemap(
    values: pd.Series,
) -> go.Figure:
    ordered = values.reindex(
        GROUPS,
        fill_value=0,
    )

    display_names = {
        "Dokter": "Dokter",
        "Perawat": "Perawat",
        "Tenaga Kesehatan Lainnya": "Nakes Lainnya",
    }

    active_groups = [
        group
        for group in GROUPS
        if ordered[group] > 0
    ]

    labels = [
        display_names[group]
        for group in active_groups
    ]

    colors = [
        PROFESSION_COLORS[group]
        for group in active_groups
    ]

    figure = go.Figure(
        go.Treemap(
            labels=labels,
            parents=[""] * len(labels),
            values=[
                ordered[group]
                for group in active_groups
            ],
            marker={
                "colors": colors,
                "line": {
                    "color": "white",
                    "width": 4,
                },
            },
            texttemplate=(
                "<b>%{label}</b><br>"
                "<span style='font-size:20px'>"
                "%{value:,.0f}"
                "</span>"
            ),
            hovertemplate=(
                "<b>%{label}</b><br>"
                "%{value:,.0f} orang<br>"
                "%{percentRoot:.1%} dari total"
                "<extra></extra>"
            ),
            tiling={"pad": 3},
            pathbar={"visible": False},
        )
    )

    figure.update_layout(
        **_base_layout(
            330,
            margin={
                "l": 10,
                "r": 10,
                "t": 10,
                "b": 10,
            },
        ),
        uniformtext={
            "minsize": 10,
            "mode": "show",
        },
    )

    figure.update_traces(
        textfont={
            "size": 14,
            "color": "white",
        }
    )

    return figure


def gender_pyramid(
    data: pd.DataFrame,
) -> go.Figure:
    grouped = data.groupby(
        ["kelompok", "jenis_kelamin"]
    )["jumlah"].sum()

    male = [
        float(
            grouped.get(
                (group, "Laki-laki"),
                0,
            )
        )
        for group in GROUPS
    ]

    female = [
        float(
            grouped.get(
                (group, "Perempuan"),
                0,
            )
        )
        for group in GROUPS
    ]

    labels = [
        "Dokter",
        "Perawat",
        "Nakes Lainnya",
    ]

    max_value = max(male + female + [1])

    if max_value >= 100:
        axis_limit = (
            math.ceil(max_value / 100) * 100
        )
    else:
        axis_limit = (
            math.ceil(max_value / 10) * 10
        )

    tick_step = max(
        1,
        math.ceil(axis_limit / 4),
    )

    tick_values = list(
        range(
            -axis_limit,
            axis_limit + 1,
            tick_step,
        )
    )

    figure = go.Figure()

    figure.add_bar(
        y=labels,
        x=[-value for value in male],
        name="Laki-laki",
        orientation="h",
        marker={
            "color": GENDER_COLORS["Laki-laki"],
            "line": {"width": 0},
        },
        customdata=male,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Laki-laki: %{customdata:,.0f}"
            "<extra></extra>"
        ),
    )

    figure.add_bar(
        y=labels,
        x=female,
        name="Perempuan",
        orientation="h",
        marker={
            "color": GENDER_COLORS["Perempuan"],
            "line": {"width": 0},
        },
        customdata=female,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Perempuan: %{customdata:,.0f}"
            "<extra></extra>"
        ),
    )

    figure.update_layout(
        **_base_layout(
            330,
            barmode="relative",
            bargap=0.38,
            legend={
                "orientation": "h",
                "y": -0.12,
                "x": 0.5,
                "xanchor": "center",
            },
            xaxis={
                "range": [
                    -axis_limit,
                    axis_limit,
                ],
                "tickvals": tick_values,
                "ticktext": [
                    f"{abs(value):,.0f}"
                    for value in tick_values
                ],
                "gridcolor": "#E2E8F0",
                "zerolinecolor": "#94A3B8",
                "title": None,
            },
            yaxis={
                "categoryorder": "array",
                "categoryarray": labels,
                "title": None,
            },
        )
    )

    return figure


def format_period(period_str: str) -> str:
    s = str(period_str)
    if "-S1" in s or "-s1" in s:
        return s.replace("-S1", " Semester 1").replace("-s1", " Semester 1")
    elif "-S2" in s or "-s2" in s:
        return s.replace("-S2", " Semester 2").replace("-s2", " Semester 2")
    elif "S1" in s:
        return s.replace("S1", "Semester 1")
    elif "S2" in s:
        return s.replace("S2", "Semester 2")
    return s


def trend_chart(
    trend: pd.DataFrame,
    indexed: bool,
) -> go.Figure:
    figure = go.Figure()

    for group in GROUPS:
        part = (
            trend[
                trend["kelompok"] == group
            ]
            .sort_values("urutan")
            .copy()
        )

        if part.empty:
            continue

        part["periode_formatted"] = part["periode"].apply(format_period)

        values = part["jumlah"].astype(float)

        if indexed:
            nonzero = values[values > 0]

            baseline = (
                float(nonzero.iloc[0])
                if not nonzero.empty
                else 1.0
            )

            display = values / baseline * 100
            custom = values
        else:
            display = values
            custom = values

        figure.add_trace(
            go.Scatter(
                x=part["periode_formatted"],
                y=display,
                customdata=custom,
                mode="lines+markers",
                name={
                    "Dokter": "Dokter",
                    "Tenaga Kesehatan Lainnya": (
                        "Nakes Lainnya"
                    ),
                }.get(group, group),
                line={
                    "color": (
                        PROFESSION_COLORS[group]
                    ),
                    "width": 3,
                    "shape": "spline",
                    "smoothing": 0.7,
                },
                marker={
                    "size": 7,
                    "line": {
                        "color": "white",
                        "width": 1.5,
                    },
                },
                hovertemplate=(
                    (
                        "<b>%{x}</b><br>"
                        "Indeks: %{y:.1f}<br>"
                        "Jumlah: "
                        "%{customdata:,.0f} orang"
                        "<extra></extra>"
                    )
                    if indexed
                    else (
                        "<b>%{x}</b><br>"
                        "Jumlah: %{y:,.0f} orang"
                        "<extra></extra>"
                    )
                ),
            )
        )

    y_title = (
        "Indeks (periode awal = 100)"
        if indexed
        else "Jumlah orang"
    )

    figure.update_layout(
        **_base_layout(
            390,
            margin={
                "l": 28,
                "r": 28,
                "t": 18,
                "b": 42,
            },
            hovermode="x unified",
            legend={
                "orientation": "h",
                "y": 1.08,
                "x": 0.5,
                "xanchor": "center",
            },
            xaxis={
                "title": None,
                "gridcolor": "#F1F5F9",
                "fixedrange": True,
            },
            yaxis={
                "title": y_title,
                "gridcolor": "#E2E8F0",
                "zeroline": False,
                "fixedrange": True,
            },
        )
    )

    return figure


def hospital_lollipop(
    ranking: pd.DataFrame,
) -> go.Figure:
    frame = (
        ranking
        .sort_values(
            "jumlah",
            ascending=True,
        )
        .copy()
    )

    frame["nama_pendek"] = (
        frame["nama_rs"].map(short_name)
    )

    maximum = max(
        (
            frame["jumlah"].max()
            if not frame.empty
            else 1
        ),
        1,
    )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=frame["jumlah"],
            y=frame["nama_pendek"],
            orientation="h",
            text=[
                f"  {value:,.0f}"
                for value in frame["jumlah"]
            ],
            textposition="outside",
            textfont={
                "size": 12,
                "color": "#1E3A8A",
            },
            marker={
                "color": frame["jumlah"],
                "colorscale": [
                    [0.0, "#93C5FD"],
                    [0.35, "#3B82F6"],
                    [0.75, "#2563EB"],
                    [1.0, "#1D4ED8"],
                ],
                "line": {
                    "color": "#1E40AF",
                    "width": 1,
                },
            },
            customdata=frame["nama_rs"],
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                "Jumlah: <b>%{x:,.0f} orang</b>"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        **_base_layout(
            max(
                380,
                len(frame) * 34,
            ),
            margin={
                "l": 12,
                "r": 55,
                "t": 12,
                "b": 35,
            },
            showlegend=False,
            xaxis={
                "title": "Jumlah orang",
                "range": [
                    0,
                    maximum * 1.18,
                ],
                "gridcolor": "#F1F5F9",
                "zeroline": False,
            },
            yaxis={
                "title": None,
                "automargin": True,
            },
        )
    )

    return figure


hospital_bar_chart = hospital_lollipop


def profession_radar(
    selected: pd.Series,
    benchmark: pd.Series,
    hospital_name: str,
) -> go.Figure:
    labels = [
        "Dokter",
        "Perawat",
        "Nakes Lainnya",
    ]

    selected = (
        selected
        .reindex(
            GROUPS,
            fill_value=0,
        )
        .astype(float)
    )

    benchmark = (
        benchmark
        .reindex(
            GROUPS,
            fill_value=0,
        )
        .astype(float)
    )

    selected_share = (
        selected
        / max(selected.sum(), 1)
        * 100
    )

    benchmark_share = (
        benchmark
        / max(benchmark.sum(), 1)
        * 100
    )

    theta = labels + [labels[0]]

    figure = go.Figure()

    figure.add_trace(
        go.Scatterpolar(
            r=(
                selected_share.tolist()
                + [selected_share.iloc[0]]
            ),
            theta=theta,
            fill="toself",
            name=short_name(hospital_name),
            line={
                "color": "#2563EB",
                "width": 3,
            },
            fillcolor="rgba(37,99,235,.18)",
            customdata=(
                selected.tolist()
                + [selected.iloc[0]]
            ),
            hovertemplate=(
                "<b>%{theta}</b><br>"
                "%{customdata:,.0f} orang<br>"
                "%{r:.1f}% komposisi"
                "<extra></extra>"
            ),
        )
    )

    figure.add_trace(
        go.Scatterpolar(
            r=(
                benchmark_share.tolist()
                + [benchmark_share.iloc[0]]
            ),
            theta=theta,
            name="Rata-rata RS",
            line={
                "color": "#10B981",
                "width": 2,
                "dash": "dash",
            },
            customdata=(
                benchmark.tolist()
                + [benchmark.iloc[0]]
            ),
            hovertemplate=(
                "<b>%{theta}</b><br>"
                "Rata-rata "
                "%{customdata:,.0f} orang<br>"
                "%{r:.1f}% komposisi"
                "<extra></extra>"
            ),
        )
    )

    maximum = max(
        float(selected_share.max()),
        float(benchmark_share.max()),
        10,
    )

    figure.update_layout(
        **_base_layout(
            430,
            margin={
                "l": 42,
                "r": 42,
                "t": 26,
                "b": 58,
            },
            polar={
                "radialaxis": {
                    "visible": True,
                    "range": [
                        0,
                        math.ceil(
                            maximum / 10
                        ) * 10,
                    ],
                    "ticksuffix": "%",
                    "gridcolor": "#E2E8F0",
                },
                "angularaxis": {
                    "gridcolor": "#E2E8F0",
                },
                "bgcolor": (
                    "rgba(0,0,0,0)"
                ),
            },
            legend={
                "orientation": "h",
                "x": 0.5,
                "xanchor": "center",
                "y": -0.08,
            },
        )
    )

    return figure


def gender_heatmap(
    data: pd.DataFrame,
    gender: str,
    color_scale: list[list[object]],
) -> go.Figure:
    grouped = data.groupby(
        [
            "nama_rs",
            "kelompok",
            "jenis_kelamin",
        ],
        as_index=False,
    )["jumlah"].sum()

    known = grouped[
        grouped["jenis_kelamin"].isin(
            [
                "Laki-laki",
                "Perempuan",
            ]
        )
    ].copy()

    totals = known.groupby(
        [
            "nama_rs",
            "kelompok",
        ]
    )["jumlah"].transform("sum")

    known["persentase"] = (
        known["jumlah"]
        .div(
            totals.where(
                totals > 0
            )
        )
        .mul(100)
    )

    selected = known[
        known["jenis_kelamin"] == gender
    ]

    pivot = (
        selected
        .pivot(
            index="nama_rs",
            columns="kelompok",
            values="persentase",
        )
        .reindex(columns=GROUPS)
    )

    pivot.index = [
        short_name(name)
        for name in pivot.index
    ]

    labels = [
        "Dokter",
        "Perawat",
        "Nakes Lainnya",
    ]

    text = pivot.map(
        lambda value: (
            "-"
            if pd.isna(value)
            else f"{value:.0f}%"
        )
    )

    figure = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=labels,
            y=pivot.index.tolist(),
            zmin=0,
            zmax=100,
            colorscale=color_scale,
            text=text.values,
            texttemplate="%{text}",
            textfont={"size": 10},
            colorbar={
                "title": "%",
                "thickness": 10,
                "len": 0.8,
            },
            hovertemplate=(
                "<b>%{y}</b><br>"
                "%{x}: %{z:.1f}%"
                "<extra></extra>"
            ),
            xgap=3,
            ygap=3,
        )
    )

    figure.update_layout(
        **_base_layout(
            max(
                410,
                len(pivot) * 28 + 90,
            ),
            margin={
                "l": 8,
                "r": 22,
                "t": 14,
                "b": 34,
            },
            yaxis={
                "autorange": "reversed",
                "title": None,
                "automargin": True,
            },
        )
    )

    return figure


def nakes_composition_heatmap(
    data: pd.DataFrame,
    color_scale: list[list[object]] | None = None,
) -> go.Figure:
    if color_scale is None:
        color_scale = [
            [0.0, "#EFF6FF"],
            [0.2, "#BFDBFE"],
            [0.5, "#3B82F6"],
            [0.8, "#1D4ED8"],
            [1.0, "#1E3A8A"],
        ]

    grouped = data.groupby(
        [
            "nama_rs",
            "kelompok",
        ],
        as_index=False,
    )["jumlah"].sum()

    rs_totals = grouped.groupby("nama_rs")["jumlah"].transform("sum")
    grouped["persentase"] = (
        grouped["jumlah"]
        .div(rs_totals.where(rs_totals > 0))
        .mul(100)
    )

    pivot_pct = (
        grouped.pivot(
            index="nama_rs",
            columns="kelompok",
            values="persentase",
        )
        .reindex(columns=GROUPS)
    )

    pivot_cnt = (
        grouped.pivot(
            index="nama_rs",
            columns="kelompok",
            values="jumlah",
        )
        .reindex(columns=GROUPS)
    )

    pivot_pct.index = [
        short_name(name)
        for name in pivot_pct.index
    ]
    pivot_cnt.index = pivot_pct.index

    labels = [
        "Dokter",
        "Perawat",
        "Nakes Lainnya",
    ]

    text = pivot_pct.map(
        lambda value: (
            "-"
            if pd.isna(value) or value == 0
            else f"{value:.0f}%"
        )
    )

    cnt_vals = pivot_cnt.fillna(0).values
    pct_vals = pivot_pct.fillna(0).values

    customdata = [
        [
            [cnt_vals[r][c], pct_vals[r][c]]
            for c in range(len(labels))
        ]
        for r in range(len(pivot_pct))
    ]

    figure = go.Figure(
        go.Heatmap(
            z=pivot_pct.values,
            x=labels,
            y=pivot_pct.index.tolist(),
            zmin=0,
            zmax=100,
            colorscale=color_scale,
            text=text.values,
            texttemplate="%{text}",
            textfont={
                "size": 11,
                "weight": "bold",
            },
            colorbar={
                "title": "%",
                "thickness": 12,
                "len": 0.85,
            },
            customdata=customdata,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "%{x}: <b>%{customdata[1]:.1f}%</b> (%{customdata[0]:,.0f} orang)"
                "<extra></extra>"
            ),
            xgap=4,
            ygap=4,
        )
    )

    figure.update_layout(
        **_base_layout(
            max(
                380,
                len(pivot_pct) * 34 + 60,
            ),
            margin={
                "l": 10,
                "r": 20,
                "t": 14,
                "b": 35,
            },
            xaxis={
                "side": "bottom",
                "title": None,
            },
            yaxis={
                "autorange": "reversed",
                "title": None,
                "automargin": True,
            },
        )
    )

    return figure


def classify_dokter_kualifikasi(val: str) -> str:
    s = str(val).upper().strip()
    if "GIGI SPESIALIS" in s:
        return "Dokter Gigi Spesialis"
    elif "GIGI" in s:
        return "Dokter Gigi"
    elif "SPES" in s or "SPESIALIS" in s:
        return "Dokter Spesialis"
    elif "UMUM" in s or "S1" in s or "S2" in s or "S-1" in s or "S-2" in s:
        return "Dokter Umum"
    elif s in ["TIDAK DIRINCI", "NAN", "NONE", ""]:
        return "Lainnya / Tidak Dirinci"
    else:
        return s.title()


DOKTER_CAT_COLORS = {
    "Dokter Spesialis": "#1E40AF",
    "Dokter Umum": "#38BDF8",
    "Dokter Gigi": "#10B981",
    "Dokter Gigi Spesialis": "#F59E0B",
    "Lainnya / Tidak Dirinci": "#94A3B8",
}


def dokter_kategori_donut(data: pd.DataFrame) -> go.Figure:
    dokter_data = data[data["kelompok"] == "Dokter"].copy()
    if dokter_data.empty:
        return go.Figure()

    dokter_data["kategori_dokter"] = dokter_data["kualifikasi"].apply(classify_dokter_kualifikasi)
    summary = dokter_data.groupby("kategori_dokter")["jumlah"].sum().reset_index()

    colors = [DOKTER_CAT_COLORS.get(cat, "#64748B") for cat in summary["kategori_dokter"]]

    figure = go.Figure(
        go.Pie(
            labels=summary["kategori_dokter"],
            values=summary["jumlah"],
            hole=0.55,
            marker={"colors": colors},
            textinfo="percent+label",
            hoverinfo="label+value+percent",
            hovertemplate="<b>%{label}</b><br>%{value:,.0f} orang (%{percent})<extra></extra>",
            textposition="outside",
        )
    )

    figure.update_layout(
        **_base_layout(
            360,
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
            showlegend=False,
        )
    )
    return figure


def dokter_kategori_bar(data: pd.DataFrame) -> go.Figure:
    dokter_data = data[data["kelompok"] == "Dokter"].copy()
    if dokter_data.empty:
        return go.Figure()

    dokter_data["kategori_dokter"] = dokter_data["kualifikasi"].apply(classify_dokter_kualifikasi)
    dokter_data["nama_pendek"] = dokter_data["nama_rs"].map(short_name)

    pivot = (
        dokter_data.groupby(["nama_pendek", "kategori_dokter"])["jumlah"]
        .sum()
        .unstack(fill_value=0)
    )

    h_totals = pivot.sum(axis=1)
    pivot = pivot.loc[h_totals[h_totals > 0].index]

    # Calculate 100% stacked proportions
    row_sums = pivot.sum(axis=1)
    pivot_pct = pivot.div(row_sums, axis=0) * 100

    figure = go.Figure()

    for cat in [
        "Dokter Spesialis",
        "Dokter Umum",
        "Dokter Gigi",
        "Dokter Gigi Spesialis",
        "Lainnya / Tidak Dirinci",
    ]:
        if cat in pivot_pct.columns:
            figure.add_trace(
                go.Bar(
                    x=pivot_pct[cat],
                    y=pivot_pct.index,
                    customdata=pivot[cat],
                    name=cat,
                    orientation="h",
                    marker={"color": DOKTER_CAT_COLORS.get(cat, "#64748B")},
                    hovertemplate=f"<b>%{{y}}</b><br>{cat}: <b>%{{x:.1f}}%</b> (%{{customdata:,.0f}} orang)<extra></extra>",
                )
            )

    figure.update_layout(
        **_base_layout(
            max(380, len(pivot_pct) * 34),
            barmode="stack",
            margin={"l": 10, "r": 25, "t": 20, "b": 95},
            legend={
                "orientation": "h",
                "x": 0.5,
                "xanchor": "center",
                "y": -0.32,
                "font": {"size": 11},
            },
            xaxis={
                "title": {"text": "Proporsi (% Total Dokter)", "standoff": 10},
                "range": [0, 100],
                "ticksuffix": "%",
                "gridcolor": "#F1F5F9",
            },
            yaxis={"title": None, "automargin": True},
        )
    )
    return figure