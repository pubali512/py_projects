# Business Case: Kiva Lending Patterns

## 1. Goal and Problem Statement

### Original assignment requirements
The assignment asks for an exploratory data analysis (EDA) of the historical Kiva loan dataset.

The goals are to:
- Understand the dataset's structure and contents.
- Inspect and clean the data where necessary.
- Identify interesting patterns and anomalies without trying to discover every possible insight.
- Create at least three visualizations using Seaborn, object-oriented Matplotlib, or Plotly/Plotly Express.
- Explain what each visualization shows and describe the insights or unusual patterns it reveals.
- Build a Dash dashboard with a heading, a selection/filter control, and a chart that updates automatically when the selection changes.
- Submit a structured Jupyter Notebook that runs from top to bottom without errors, documents data cleaning, clearly marks at least three assessed visualizations, and includes an interpretation for each.
- Prepare a presentation of three selected visualizations lasting approximately five minutes (per the assignment timeline).

### Business context and assumptions
Kiva operates a platform that connects people and small businesses seeking loans with lenders who want to support them. Borrowers use the funding for activities such as agriculture, education, and other projects.

The assignment states that:
- The loans in the dataset have completed their funding phase.
- Funds were disbursed even if the original requested amount was not fully reached.
- The dataset represents historical Kiva platform activity over several years.

Important interpretation: completion of the funding phase does not establish that a loan was fully repaid. Do not claim repayment success or loan performance unless the dataset supports it.

## 2. Proposed Solution, Ideas, and Discussion

### Main approach
**Approach 1: Explore Kiva's historical lending patterns across sectors and countries.**

Suggested title:
**Business Case: Kiva Lending Patterns — An Exploratory Data Analysis**

Main analytical questions:
1. Which sectors account for the largest number of loan records?
2. Which countries have the largest number of loan records?
3. How does the distribution of loan amounts differ across sectors?

### Three main assessed visualizations
1. **Loan distribution by sector** — horizontal bar chart showing the top sectors by loan count.
2. **Geographic distribution of loans** — horizontal bar chart showing the top countries by loan count.
3. **Loan amount distribution by sector** — box plot comparing loan-amount distributions across sectors.

Each visualization must have a clear objective, an explanation of what it displays, and a concise interpretation based on the actual results.

### Additional analysis: Repayment arrangements and duration
Investigate the `repayment_interval` categories (Bullet, irregular, monthly, weekly) and `term_in_months`.

Potential questions:
- Does the distribution of repayment intervals differ across sectors?
- Do repayment arrangements vary across countries?
- Does loan duration differ across sectors or selected countries?

Preferred additional visualization: a 100% stacked bar chart showing repayment-interval percentages across selected sectors. Include counts or sample sizes because categories and sectors may differ substantially in size.

Potential secondary analysis: a box plot of `term_in_months` by sector. Investigate unusual values rather than automatically removing them.

Critical limitation: repayment interval and term describe loan structure; they do not show whether borrowers repaid successfully or whether one arrangement is better.

### Bonus analysis: Requested versus funded amounts
Compare:
- `loan_amount`: amount requested.
- `funded_amount`: amount funded/disbursed according to the supplied data dictionary.

Create a derived measure:
`funding_gap = loan_amount - funded_amount`

Investigate the distribution of the gap and differences by sector. Validate unusual cases, including records where the funded amount exceeds the requested amount. Do not automatically remove partially funded loans; the assignment explicitly says funds were disbursed even when the requested amount was not fully reached.

### Dashboard proposal
Build a Dash application called **Kiva Sector Explorer**:
- Heading/title.
- Dropdown to select a sector.
- Plotly chart that updates when the selection changes.
- Recommended chart: percentage distribution of repayment intervals for the selected sector.
- Show the number of records represented where practical.

This connects the main sector analysis with the additional repayment analysis while satisfying the dashboard requirement.

### Data preparation and implementation notes
- Use Python in a Jupyter Notebook in VS Code.
- Pandas, NumPy, Seaborn, Matplotlib, and Plotly Express are already installed.
- Load the CSV using the user's exact file path and the correct `#` separator.
- Inspect dimensions, columns, data types, summary statistics, missing values, duplicates, and numerical validity before deciding on cleaning.
- Document every cleaning decision and its reason; avoid dropping records or imputing values without justification.
- Use Plotly Express for the main interactive charts and Dash dashboard, while Seaborn can be used for additional exploration if useful.

### Scope and priorities
1. Complete data inspection and defensible cleaning first.
2. Keep the three required visualizations focused on sector distribution, country distribution, and loan amounts by sector.
3. Explore repayment arrangements and duration as additional analysis; promote the repayment-interval chart if the actual results are clear and useful.
4. Keep requested-versus-funded comparison as the bonus analysis.
5. Build and test the Dash callback.
6. Restart the notebook kernel and run all cells from top to bottom before submission.
7. Prepare a concise presentation focused on the three strongest visualizations.

### Working agreement
Proceed one step at a time. After each step, ask the user for confirmation before continuing, so they can review the work or request changes.
