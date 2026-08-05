from __future__ import annotations

from zoneinfo import ZoneInfo

from scraper_soetomo import URL_SOETOMO, scrape_soetomo
from scraper_saiful_anwar import (
    URL_SAIFUL_ANWAR,
    scrape_saiful_anwar,
)
from scraper_soedono import URL_SOEDONO, scrape_soedono
from scraper_haji import URL_HAJI, scrape_haji
from scraper_menur import URL_MENUR, scrape_menur
from scraper_mohammad_noer import (
    URL_MOHAMMAD_NOER,
    scrape_mohammad_noer,
)
from scraper_dungus import URL_DUNGUS, scrape_dungus
from scraper_daha_husada import (
    URL_DAHA_HUSADA,
    scrape_daha_husada,
)
from scraper_paru_jember import (
    URL_PARU_JEMBER,
    scrape_paru_jember,
)
from scraper_sumberglagah import URL_SUMBERGLAGAH, scrape_sumberglagah
from scraper_rsmm import URL_RSMM, scrape_rsmm
from scraper_manguharjo import URL_MANGUHARJO_SOURCE, scrape_manguharjo
from scraper_karsa_husada import URL_KARSA_HUSADA, scrape_karsa_husada


from scraper_husada_prima import URL_HUSADA_PRIMA, scrape_husada_prima


JAKARTA = ZoneInfo("Asia/Jakarta")

# Registry tunggal seluruh 14 rumah sakit yang dipantau Pemprov Jatim beserta koordinat lokasinya.
HOSPITALS: dict[str, dict[str, object]] = {
    "RSUD Dr. Soetomo": {
        "kode_rs": "RSDS",
        "url": URL_SOETOMO,
        "scraper": scrape_soetomo,
        "lat": -7.2687,
        "lon": 112.7583,
        "kota": "Kota Surabaya",
    },
    "RSUD Dr. Saiful Anwar": {
        "kode_rs": "RSSA",
        "url": URL_SAIFUL_ANWAR,
        "scraper": scrape_saiful_anwar,
        "lat": -7.9723,
        "lon": 112.6318,
        "kota": "Kota Malang",
    },
    "RSUD dr. Soedono Madiun": {
        "kode_rs": "RSSM",
        "url": URL_SOEDONO,
        "scraper": scrape_soedono,
        "lat": -7.6288,
        "lon": 111.5244,
        "kota": "Kota Madiun",
    },
    "RSUD Haji Provinsi Jawa Timur": {
        "kode_rs": "RSHJ",
        "url": URL_HAJI,
        "scraper": scrape_haji,
        "lat": -7.2847,
        "lon": 112.7840,
        "kota": "Kota Surabaya",
    },
    "RS Jiwa Menur Provinsi Jawa Timur": {
        "kode_rs": "RSMN",
        "url": URL_MENUR,
        "scraper": scrape_menur,
        "lat": -7.2853,
        "lon": 112.7626,
        "kota": "Kota Surabaya",
    },
    "RSU Mohammad Noer Pamekasan": {
        "kode_rs": "RSMNO",
        "url": URL_MOHAMMAD_NOER,
        "scraper": scrape_mohammad_noer,
        "lat": -7.1611,
        "lon": 113.4831,
        "kota": "Kabupaten Pamekasan",
    },
    "RSUD Dungus Madiun": {
        "kode_rs": "RSDG",
        "url": URL_DUNGUS,
        "scraper": scrape_dungus,
        "lat": -7.6744,
        "lon": 111.5833,
        "kota": "Kabupaten Madiun",
    },
    "RSUD Daha Husada Kediri": {
        "kode_rs": "RSDH",
        "url": URL_DAHA_HUSADA,
        "scraper": scrape_daha_husada,
        "lat": -7.8164,
        "lon": 112.0118,
        "kota": "Kota Kediri",
    },
    "RS Paru Jember": {
        "kode_rs": "RSPJ",
        "url": URL_PARU_JEMBER,
        "scraper": scrape_paru_jember,
        "lat": -8.1672,
        "lon": 113.7011,
        "kota": "Kabupaten Jember",
    },
    "RSUD Sumberglagah": {
        "kode_rs": "RSSG",
        "url": URL_SUMBERGLAGAH,
        "scraper": scrape_sumberglagah,
        "lat": -7.5855,
        "lon": 112.5117,
        "kota": "Kabupaten Mojokerto",
    },
    "RS Mata Masyarakat Jawa Timur": {
        "kode_rs": "RSMM",
        "url": URL_RSMM,
        "scraper": scrape_rsmm,
        "lat": -7.3168,
        "lon": 112.7354,
        "kota": "Kota Surabaya",
    },
    "RS Paru Manguharjo Madiun": {
        "kode_rs": "RSPM",
        "url": URL_MANGUHARJO_SOURCE,
        "scraper": scrape_manguharjo,
        "lat": -7.6083,
        "lon": 111.5234,
        "kota": "Kota Madiun",
    },
    "RSUD Karsa Husada Batu": {
        "kode_rs": "RSKH",
        "url": URL_KARSA_HUSADA,
        "scraper": scrape_karsa_husada,
        "lat": -7.8683,
        "lon": 112.5261,
        "kota": "Kota Batu",
    },
    "RSUD Husada Prima": {
        "kode_rs": "RSHP",
        "url": URL_HUSADA_PRIMA,
        "scraper": scrape_husada_prima,
        "lat": -7.2345,
        "lon": 112.7489,
        "kota": "Kota Surabaya",
    },
}
