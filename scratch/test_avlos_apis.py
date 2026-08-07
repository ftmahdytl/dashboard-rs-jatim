import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ENDPOINTS = {
    "RSPJ": ("RS Paru Jember", "https://opendata.jatimprov.go.id/api/cleaned-bigdata/rumah_sakit_paru_jember/avlos_average_length_of_stay_7"),
    "RSMNO": ("RSUD Mohammad Noer Pamekasan", "https://opendata.jatimprov.go.id/api/cleaned-bigdata/rumah_sakit_umum_daerah_mohammad_noer_pamekasan/avlos_average_length_of_stay_9"),
    "RSMM": ("RS Mata Masyarakat Jatim", "https://opendata.jatimprov.go.id/api/cleaned-bigdata/rumah_sakit_mata_masyarakat_jawa_timur/avlos_average_length_of_stay"),
    "RSSM": ("RSUD dr. Soedono Madiun", "https://opendata.jatimprov.go.id/api/cleaned-bigdata/rumah_sakit_umum_daerah_dr_soedono_madiun_provinsi_jawa_timur/avlos_average_length_of_stay_2"),
    "RSDH": ("RSUD Daha Husada Kediri", "https://opendata.jatimprov.go.id/api/cleaned-bigdata/rumah_sakit_umum_daerah_daha_husada/avlos_avarage_length_of_stay"),
    "RSDS": ("RSUD Dr. Soetomo Surabaya", "https://opendata.jatimprov.go.id/api/cleaned-bigdata/rumah_sakit_umum_daerah_dr_soetomo_surabaya_provinsi_jawa_tim/avlos_average_length_of_stay_4"),
    "RSSA": ("RSUD Dr. Saiful Anwar Malang", "https://opendata.jatimprov.go.id/api/cleaned-bigdata/rumah_sakit_umum_daerah_dr_saiful_anwar_malang_provinsi_jawa_/avlos_average_length_of_stay_6"),
    "RSHJ": ("RSUD Haji Surabaya", "https://opendata.jatimprov.go.id/api/cleaned-bigdata/rumah_sakit_umum_daerah_haji_provinsi_jawa_timur/avlos_average_length_of_stay_3"),
    "RSPM": ("RS Paru Manguharjo Madiun", "https://opendata.jatimprov.go.id/api/cleaned-bigdata/rumah_sakit_paru_manguharjo_madiun/avlos_average_length_of_stay_5"),
}

results = {}
for code, (name, url) in ENDPOINTS.items():
    try:
        r = requests.get(url, params={"per_page": 200}, verify=False, timeout=10)
        if r.status_code == 200:
            res_json = r.json()
            data = res_json.get("data", [])
            print(f"[OK] {code} ({name}): {len(data)} baris")
            if data:
                print(f"   Sample keys: {list(data[0].keys())}")
                print(f"   Sample row: {data[0]}")
            results[code] = data
        else:
            print(f"[FAIL] {code}: HTTP {r.status_code}")
    except Exception as e:
        print(f"[ERROR] {code}: {e}")

with open("scratch/avlos_cache.json", "w") as f:
    json.dump(results, f, indent=2)
print("Finished testing all 9 AVLOS endpoints.")
