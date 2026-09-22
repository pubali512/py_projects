"""
One-time setup script: fetches all PLZ codes for the 75 target German cities
from the OpenPLZ API and writes data/plz_city_mapping.csv.

Run once before data generation:
    python python/00_prepare_plz_data.py

Output columns: PostalCode, City, FederalState
"""

import csv
import time
import urllib.request
import urllib.parse
import json
import pathlib
# 75 German cities distributed across all 16 federal states.
# Tuple: (City name as used in OpenPLZ API, FederalState)
CITIES = [
    # Baden-Wuerttemberg (5)
    ("Stuttgart",               "Baden-Wuerttemberg"),
    ("Karlsruhe",               "Baden-Wuerttemberg"),
    ("Freiburg im Breisgau",    "Baden-Wuerttemberg"),
    ("Heidelberg",              "Baden-Wuerttemberg"),
    ("Ulm",                     "Baden-Wuerttemberg"),
    # Bayern (6)
    ("Muenchen",                 "Bayern"),
    ("Nuernberg",                "Bayern"),
    ("Augsburg",                "Bayern"),
    ("Regensburg",              "Bayern"),
    ("Wuerzburg",                "Bayern"),
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
    ("Osnabrueck",               "Niedersachsen"),
    ("Oldenburg",               "Niedersachsen"),
    ("Goettingen",               "Niedersachsen"),
    ("Wolfsburg",               "Niedersachsen"),
    ("Hildesheim",              "Niedersachsen"),
    # Nordrhein-Westfalen (11)
    ("Koeln",                    "Nordrhein-Westfalen"),
    ("Duesseldorf",              "Nordrhein-Westfalen"),
    ("Dortmund",                "Nordrhein-Westfalen"),
    ("Essen",                   "Nordrhein-Westfalen"),
    ("Duisburg",                "Nordrhein-Westfalen"),
    ("Bochum",                  "Nordrhein-Westfalen"),
    ("Wuppertal",               "Nordrhein-Westfalen"),
    ("Bielefeld",               "Nordrhein-Westfalen"),
    ("Bonn",                    "Nordrhein-Westfalen"),
    ("Muenster",                 "Nordrhein-Westfalen"),
    ("Aachen",                  "Nordrhein-Westfalen"),
    # Rheinland-Pfalz (4)
    ("Mainz",                   "Rheinland-Pfalz"),
    ("Ludwigshafen am Rhein",   "Rheinland-Pfalz"),
    ("Koblenz",                 "Rheinland-Pfalz"),
    ("Trier",                   "Rheinland-Pfalz"),
    # Saarland (3)
    ("Saarbruecken",             "Saarland"),
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
    ("Dessau-Rosslau",           "Sachsen-Anhalt"),
    ("Lutherstadt Wittenberg",  "Sachsen-Anhalt"),
    # Schleswig-Holstein (4)
    ("Kiel",                    "Schleswig-Holstein"),
    ("Luebeck",                  "Schleswig-Holstein"),
    ("Flensburg",               "Schleswig-Holstein"),
    ("Neumuenster",              "Schleswig-Holstein"),
    # Thueringen (4)
    ("Erfurt",                  "Thueringen"),
    ("Jena",                    "Thueringen"),
    ("Gera",                    "Thueringen"),
    ("Weimar",                  "Thueringen"),
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
    "Neumuenster":       ("Neumuenster", "Schleswig-Holstein",
                         ["24534", "24536", "24537", "24539"]),
}


def fetch_plz_for_city(city_name: str) -> list[dict]:
    """Return list of {PostalCode, City, FederalState} dicts for a City."""
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
            rows.append({"PostalCode": plz, "City": name, "FederalState": state})
    return rows


def main():
    out_path = pathlib.Path(__file__).parent.parent / "data" / "plz_city_mapping.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict] = []
    seen: set[str] = set()

    for City, state in CITIES:
        print(f"Fetching PLZ for {City} ({state}) ...", end=" ")

        # Use fallback if known to fail via API
        if City in FALLBACK_PLZ:
            canon_city, canon_state, plz_list = FALLBACK_PLZ[City]
            added = 0
            for plz in plz_list:
                if plz not in seen:
                    seen.add(plz)
                    all_rows.append({"PostalCode": plz, "City": canon_city, "FederalState": canon_state})
                    added += 1
            print(f"{added} PLZ codes added (fallback)")
            continue

        rows = fetch_plz_for_city(City)
        added = 0
        for row in rows:
            key = row["PostalCode"]
            if key not in seen:
                seen.add(key)
                # Use the supplied state as ground truth (API may differ slightly)
                row["FederalState"] = state
                all_rows.append(row)
                added += 1
        print(f"{added} PLZ codes added")
        time.sleep(DELAY_SECONDS)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["PostalCode", "City", "FederalState"])
        writer.writeheader()
        writer.writerows(sorted(all_rows, key=lambda r: r["PostalCode"]))

    print(f"\nDone. {len(all_rows)} PLZ rows written to {out_path}")


if __name__ == "__main__":
    main()
