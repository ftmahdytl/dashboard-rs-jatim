from __future__ import annotations

from html import escape
from typing import Iterable

import streamlit as st


PROFESSION_COLORS = {
    "Dokter/Tenaga Medis": "#2563EB",
    "Perawat": "#10B981",
    "Tenaga Kesehatan Lainnya": "#8B5CF6",
}

GENDER_COLORS = {
    "Laki-laki": "#2563EB",
    "Perempuan": "#EC4899",
    "Tidak dirinci": "#94A3B8",
}


def fmt_number(value: float | int) -> str:
    return f"{int(round(value)):,}".replace(",", ".")


def short_name(name: str) -> str:
    replacements = {
        "RSUD Dr. Soetomo": "Dr. Soetomo",
        "RSUD Dr. Saiful Anwar": "Dr. Saiful Anwar",
        "RSUD dr. Soedono Madiun": "dr. Soedono",
        "RSUD Haji Provinsi Jawa Timur": "RSUD Haji",
        "RS Jiwa Menur Provinsi Jawa Timur": "RS Jiwa Menur",
        "RSUD Karsa Husada Batu": "Karsa Husada",
        "RSUD Sumberglagah": "Sumberglagah",
        "RSU Mohammad Noer Pamekasan": "Mohammad Noer",
        "RSUD Dungus Madiun": "Dungus",
        "RSUD Daha Husada Kediri": "Daha Husada",
        "RSUD Husada Prima": "Husada Prima",
        "RS Paru Jember": "Paru Jember",
        "RS Mata Masyarakat Jawa Timur": "RS Mata",
        "RS Paru Manguharjo Madiun": "Paru Manguharjo",
    }

    return replacements.get(name, name)


def inject_nakes_style() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1500px !important;
            padding-top: 2.4rem !important;
        }

        .nakes-filter-note {
            padding: 10px 14px;
            background: #eff6ff;
            border: 1px solid #dbeafe;
            border-radius: 12px;
            color: #1e3a8a;
            font-size: .82rem;
            margin: 4px 0 14px;
        }

        .nakes-kpi-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 10px;
            margin: 8px 0 14px;
        }

        .nakes-kpi {
            position: relative;
            overflow: hidden;
            background: #fff;
            border: 1px solid #e2e8f0;
            border-radius: 15px;
            padding: 12px 14px;
            min-height: 92px;
            box-shadow: 0 6px 18px rgba(30, 64, 175, .06);
        }

        .nakes-kpi::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: var(--accent);
        }

        .nakes-kpi-label {
            font-size: .69rem;
            font-weight: 750;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: .035em;
        }

        .nakes-kpi-value {
            font-size: 1.48rem;
            line-height: 1.08;
            color: #0f2f6b;
            font-weight: 820;
            margin: 6px 0 4px;
        }

        .nakes-kpi-note {
            font-size: .72rem;
            color: #64748b;
            line-height: 1.2;
            max-width: 72%;
        }

        .nakes-spark {
            position: absolute;
            right: 10px;
            bottom: 11px;
            width: 72px;
            height: 25px;
        }

        .nakes-insights {
            display: grid;
            grid-template-columns: 170px repeat(4, minmax(0, 1fr));
            gap: 8px;
            padding: 10px;
            background: linear-gradient(125deg, #102a66, #1d4ed8);
            border-radius: 16px;
            box-shadow: 0 12px 28px rgba(30, 64, 175, .18);
            margin: 4px 0 18px;
            color: white;
        }

        .nakes-insight-title {
            padding: 7px 9px;
            font-size: .79rem;
            font-weight: 800;
            display: flex;
            align-items: center;
        }

        .nakes-insight {
            background: rgba(255, 255, 255, .11);
            border: 1px solid rgba(255, 255, 255, .12);
            border-radius: 11px;
            padding: 8px 10px;
            font-size: .7rem;
            line-height: 1.32;
            color: #fff;
        }

        .nakes-insight b {
            display: block;
            color: #bfdbfe;
            font-size: .62rem;
            margin-bottom: 3px;
            letter-spacing: .04em;
        }

        .nakes-section {
            margin: 14px 0 2px;
        }

        .nakes-section h3 {
            font-size: 1.14rem;
            color: #0f2f6b;
            margin: 0 0 3px;
        }

        .nakes-section p {
            font-size: .8rem;
            color: #64748b;
            margin: 0 0 8px;
        }

        div[data-testid="stPlotlyChart"] {
            background: #fff;
            border: 1px solid #e2e8f0;
            border-radius: 18px;
            padding: 5px;
            box-shadow: 0 7px 20px rgba(30, 64, 175, .055);
        }

        @media (max-width: 1000px) {
            .nakes-kpi-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .nakes-insights {
                grid-template-columns: 1fr 1fr;
            }

            .nakes-insight-title {
                grid-column: 1 / -1;
            }
        }

        @media (max-width: 620px) {
            .nakes-kpi-grid,
            .nakes-insights {
                grid-template-columns: 1fr;
            }

            .nakes-insight-title {
                grid-column: auto;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _sparkline_svg(
    values: Iterable[float],
    color: str,
) -> str:
    clean = [float(value) for value in values]

    if not clean:
        clean = [0.0, 0.0]

    if len(clean) == 1:
        clean *= 2

    low = min(clean)
    high = max(clean)
    span = high - low or 1.0
    points = []

    for index, value in enumerate(clean):
        x = 2 + index * 68 / (len(clean) - 1)
        y = 22 - (value - low) * 18 / span
        points.append(f"{x:.1f},{y:.1f}")

    return (
        '<svg class="nakes-spark" '
        'viewBox="0 0 72 26" '
        'aria-hidden="true">'
        f'<polyline points="{" ".join(points)}" '
        'fill="none" '
        f'stroke="{color}" '
        'stroke-width="2" '
        'stroke-linecap="round" '
        'stroke-linejoin="round"/>'
        f'<circle cx="{points[-1].split(",")[0]}" '
        f'cy="{points[-1].split(",")[1]}" '
        f'r="2.5" fill="{color}"/>'
        "</svg>"
    )


def render_kpi_grid(
    cards: list[dict[str, object]],
) -> None:
    html = ['<div class="nakes-kpi-grid">']

    for card in cards:
        color = str(card["color"])

        html.append(
            f'<div class="nakes-kpi" '
            f'style="--accent:{color}">'
            f'<div class="nakes-kpi-label">'
            f'{escape(str(card["label"]))}'
            "</div>"
            f'<div class="nakes-kpi-value">'
            f'{escape(str(card["value"]))}'
            "</div>"
            f'<div class="nakes-kpi-note">'
            f'{escape(str(card["note"]))}'
            "</div>"
            f'{_sparkline_svg(card.get("trend", []), color)}'
            "</div>"
        )

    html.append("</div>")

    st.markdown(
        "".join(html),
        unsafe_allow_html=True,
    )


def render_insights(items: list[str]) -> None:
    html = [
        '<div class="nakes-insights">',
        '<div class="nakes-insight-title">'
        "✦ Insight otomatis"
        "</div>",
    ]

    for index, item in enumerate(
        items[:4],
        start=1,
    ):
        html.append(
            '<div class="nakes-insight">'
            f"<b>0{index}</b>"
            f"{escape(item)}"
            "</div>"
        )

    html.append("</div>")

    st.markdown(
        "".join(html),
        unsafe_allow_html=True,
    )


def section_heading(
    title: str,
    subtitle: str,
) -> None:
    st.markdown(
        '<div class="nakes-section">'
        f"<h3>{escape(title)}</h3>"
        f"<p>{escape(subtitle)}</p>"
        "</div>",
        unsafe_allow_html=True,
    )