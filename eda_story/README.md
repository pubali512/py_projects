# Kiva Lending Patterns

Exploratory data analysis of historical Kiva loan records, covering data cleaning, three assessed visualizations, and two interactive Dash dashboards.

## Project Structure

```
eda_story/
├── data/
│   ├── data_abschlussprojekt.csv   # Raw dataset (# separator)
│   └── kiva_cleaned.csv            # Cleaned dataset (produced by notebooks)
└── src/
    ├── kiva_dataclean.ipynb        # Data loading, inspection, and cleaning
    ├── kiva_eda.ipynb              # Three assessed visualizations + Dashboard 1
    └── kiva_eda_dash.ipynb         # Combined notebook: cleaning + EDA + dashboards
```

## Notebooks

### `kiva_dataclean.ipynb`
Loads the raw dataset, inspects it, applies 13 cleaning steps, and saves `kiva_cleaned.csv`.
Key steps: whitespace stripping, duplicate removal, missing value handling, funding gap derivation.

### `kiva_eda.ipynb`
Three assessed visualizations:
1. **Loan Count by Country** -- horizontal bar chart
2. **Sector Distribution for Top N Countries** -- 100% stacked bar
3. **Loan Activity vs Typical Loan Size by Country** -- bubble scatter

Includes Dashboard 1 (Kiva Sector Explorer, port 8050).

### `kiva_eda_dash.ipynb`
All-in-one notebook. Runs the full pipeline from loading to dashboards.

Three assessed visualizations (same as above with funding completeness replacing Chart 3):
1. **Loan Count by Country**
2. **Sector Distribution for Top N Countries**
3. **Funding Completeness by Sector** -- bubble scatter (% fully funded vs loan count)

Two dashboards:
- **Dashboard 1 -- Kiva Sector Explorer** (port 8050): sector dropdown, top N countries bar + loan amount histogram
- **Dashboard 2 -- Kiva Sector Lens** (port 8051): sector dropdown, top N input, bubble scatter colored by dominant repayment interval

## Setup

Run the first cell of any notebook to install dependencies:

```bash
pip install --upgrade pandas numpy seaborn plotly dash psutil
```

## Data

The raw dataset uses `#` as the column separator and contains ~670k Kiva loan records with columns: `funded_amount`, `loan_amount`, `activity`, `sector`, `use`, `country_code`, `country`, `region`, `currency`, `term_in_months`, `lender_count`, `borrower_genders`, `repayment_interval`.

The derived column `funding_gap = loan_amount - funded_amount` is added during cleaning.
