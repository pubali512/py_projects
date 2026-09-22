"""
One-time setup script: fetches all PLZ codes for the 75 target German cities
from the OpenPLZ API and writes data/plz_city_mapping.csv.

Run once before data generation:
    python python/00_prepare_plz_data.py

Output columns: postal_code, city, federal_state
"""

import csv
import time
import urllib.request
import urllib.parse
import json
import pathlib
# 75 German cities distributed across all 16 federal states.
# Tuple: (city name as used in OpenPLZ API, federal_state)
CITIES = [
    # Baden-Württemberg (5)
    ("Stuttgart",               "Baden-Württemberg"),
    ("Karlsruhe",               "Baden-Württemberg"),
    ("Freiburg im Breisgau",    "Baden-Württemberg"),
    ("Heidelberg",              "Baden-Württemberg"),
    ("Ulm",                     "Baden-Württemberg"),
    # Bayern (6)
    ("München",                 "Bayern"),
    ("Nürnberg",                "Bayern"),
    ("Augsburg",                "Bayern"),
    ("Regensburg",              "Bayern"),
    ("Würzburg",                "Bayern"),
    ("Ingolstadt",              "Bayern"),
    # Berlin (3)
    ("Berlin",                  "Berlin"),
    # Brandenburg (4)
    ("Potsdam",                 "Brandenburg"),
    ("Cottbus",                 "Brandenburg"),
    ("Brandenburg an der Havel","Brandenburg"),
    ("Frankfurt (Oder)",        "Brandenburg"),
    # Bremen (2)
    ("Bremen",                  "Bremen"),
    ("Bremerhaven",             "Bremen"),
    # Hamburg (3)
    ("Hamburg",                 "Hamburg"),
    # Hessen (6)
    ("Frankfurt am Main",       "Hessen"),
    ("Wiesbaden",               "Hessen"),
    ("Kassel",                  "Hessen"),
    ("Darmstadt",               "Hessen"),
    ("Offenbach am Main",       "Hessen"),
    ("Marburg",                 "Hessen"),
    # Mecklenburg-Vorpommern (4)
    ("Rostock",                 "Mecklenburg-Vorpommern"),
    ("Schwerin",                "Mecklenburg-Vorpommern"),
    ("Greifswald",              "Mecklenburg-Vorpommern"),
    ("Stralsund",               "Mecklenburg-Vorpommern"),
    # Niedersachsen (7)
    ("Hannover",                "Niedersachsen"),
    ("Braunschweig",            "Niedersachsen"),
    ("Osnabrück",               "Niedersachsen"),
    ("Oldenburg",               "Niedersachsen"),
    ("Göttingen",               "Niedersachsen"),
    ("Wolfsburg",               "Niedersachsen"),
    ("Hildesheim",              "Niedersachsen"),
    # Nordrhein-Westfalen (11)
    ("Köln",                    "Nordrhein-Westfalen"),
    ("Düsseldorf",              "Nordrhein-Westfalen"),
    ("Dortmund",                "Nordrhein-Westfalen"),
    ("Essen",                   "Nordrhein-Westfalen"),
    ("Duisburg",                "Nordrhein-Westfalen"),
    ("Bochum",                  "Nordrhein-Westfalen"),
    ("Wuppertal",               "Nordrhein-Westfalen"),
    ("Bielefeld",               "Nordrhein-Westfalen"),
    ("Bonn",                    "Nordrhein-Westfalen"),
    ("Münster",                 "Nordrhein-Westfalen"),
    ("Aachen",                  "Nordrhein-Westfalen"),
    # Rheinland-Pfalz (4)
    ("Mainz",                   "Rheinland-Pfalz"),
    ("Ludwigshafen am Rhein",   "Rheinland-Pfalz"),
    ("Koblenz",                 "Rheinland-Pfalz"),
    ("Trier",                   "Rheinland-Pfalz"),
    # Saarland (3)
    ("Saarbrücken",             "Saarland"),
    ("Neunkirchen",             "Saarland"),
    ("Homburg",                 "Saarland"),
    # Sachsen (5)
    ("Leipzig",                 "Sachsen"),
    ("Dresden",                 "Sachsen"),
    ("Chemnitz",                "Sachsen"),
    ("Zwickau",                 "Sachsen"),
    ("Plauen",                  "Sachsen"),
    # Sachsen-Anhalt (4)
    ("Halle (Saale)",           "Sachsen-Anhalt"),
    ("Magdeburg",               "Sachsen-Anhalt"),
    ("Dessau-Roßlau",           "Sachsen-Anhalt"),
    ("Lutherstadt Wittenberg",  "Sachsen-Anhalt"),
    # Schleswig-Holstein (4)
    ("Kiel",                    "Schleswig-Holstein"),
    ("Lübeck",                  "Schleswig-Holstein"),
    ("Flensburg",               "Schleswig-Holstein"),
    ("Neumünster",              "Schleswig-Holstein"),
    # Thüringen (4)
    ("Erfurt",                  "Thüringen"),
    ("Jena",                    "Thüringen"),
    ("Gera",                    "Thüringen"),
    ("Weimar",                  "Thüringen"),
]

API_BASE = "https://openplzapi.org/de/Localities"
PAGE_SIZE = 50  # max per request; most cities fit in one page
DELAY_SECONDS = 0.15  # polite rate-limit between requests

# Hardcoded fallback PLZ for cities the API does not match by name
FALLBACK_PLZ: dict[str, tuple[str, str, list[str]]] = {
    "Frankfurt (Oder)": ("Frankfurt (Oder)", "Brandenburg",
                         ["15230", "15232", "15234", "15236"]),
    "Halle (Saale)":    ("Halle (Saale)", "Sachsen-Anhalt",
                         ["06108", "06110", "06112", "06114", "06116",
                          "06118", "06120", "06122", "06124", "06126",
                          "06128", "06130", "06132"]),
    "Lutherstadt Wittenberg": ("Lutherstadt Wittenberg", "Sachsen-Anhalt",
                               ["06886", "06888", "06889"]),
    "Neumünster":       ("Neumünster", "Schleswig-Holstein",
                         ["24534", "24536", "24537", "24539"]),
}


def fetch_plz_for_city(city_name: str) -> list[dict]:
    """Return list of {postal_code, city, federal_state} dicts for a city."""
    params = urllib.parse.urlencode({"name": city_name, "pageSize": PAGE_SIZE})
    url = f"{API_BASE}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"  WARNING: could not fetch '{city_name}': {exc}")
        return []

    rows = []
    for item in data:
        plz = item.get("postalCode") or item.get("zipCode") or item.get("key", "")
        name = item.get("name", city_name)
        state = (
            item.get("federalState", {}).get("name", "")
            if isinstance(item.get("federalState"), dict)
            else item.get("federalState", "")
        )
        if plz:
            rows.append({"postal_code": plz, "city": name, "federal_state": state})
    return rows


def main():
    out_path = pathlib.Path(__file__).parent.parent / "data" / "plz_city_mapping.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict] = []
    seen: set[str] = set()

    for city, state in CITIES:
        print(f"Fetching PLZ for {city} ({state}) ...", end=" ")

        # Use fallback if known to fail via API
        if city in FALLBACK_PLZ:
            canon_city, canon_state, plz_list = FALLBACK_PLZ[city]
            added = 0
            for plz in plz_list:
                if plz not in seen:
                    seen.add(plz)
                    all_rows.append({"postal_code": plz, "city": canon_city, "federal_state": canon_state})
                    added += 1
            print(f"{added} PLZ codes added (fallback)")
            continue

        rows = fetch_plz_for_city(city)
        added = 0
        for row in rows:
            key = row["postal_code"]
            if key not in seen:
                seen.add(key)
                # Use the supplied state as ground truth (API may differ slightly)
                row["federal_state"] = state
                all_rows.append(row)
                added += 1
        print(f"{added} PLZ codes added")
        time.sleep(DELAY_SECONDS)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["postal_code", "city", "federal_state"])
        writer.writeheader()
        writer.writerows(sorted(all_rows, key=lambda r: r["postal_code"]))

    print(f"\nDone. {len(all_rows)} PLZ rows written to {out_path}")


if __name__ == "__main__":
    main()
