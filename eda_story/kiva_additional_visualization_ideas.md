# Kiva Lending Patterns: Threshold-Based Hierarchical Treemap

## 1. Objective

Create an interactive Plotly treemap to explore how Kiva loans are distributed across sectors and countries. Instead of displaying a fixed number of top sectors or countries, use a dynamic threshold to decide which categories should be shown individually and which should be grouped into **Other**.

The goal is to reveal important lending patterns without hiding the overall distribution or overcrowding the chart.

## 2. Treemap Hierarchy

The treemap has three conceptual levels:

1. **All Loans** — the full dataset.
2. **Sector** — individual sectors that meet the display rule, plus an aggregated **Other sectors** group when necessary.
3. **Country** — within every sector, including **Other sectors**, show individual countries that meet the display rule and group the remaining countries into **Other countries**.

The **Other sectors** group must also have its own country-level breakdown.

## 3. Rectangle Size and Percentages

- **Rectangle size:** Number of loans in the corresponding sector, country, or sector-country combination.
- **Overall share:** Category loan count divided by the total number of loans in the dataset.
- **Parent share:** Category loan count divided by the loan count of its immediate parent.

The chart's hover information should clearly distinguish overall share from parent share.

## 4. Dynamic 10% Aggregation Rule

Use a **parent-relative threshold**, rather than a fixed top-five rule.

### Sector level

1. Rank sectors by loan count in descending order.
2. Add sectors individually, starting with the largest.
3. Calculate the percentage of all loans represented by the remaining sectors.
4. Continue adding sectors while the remaining share is greater than 10%.
5. Group any remaining sectors into **Other sectors**.

### Country level

Apply the same logic separately within every displayed sector and within **Other sectors**:

1. Rank countries by loan count within the parent group.
2. Add countries individually, starting with the largest.
3. Calculate the share of the parent's loans represented by the countries not yet shown individually.
4. Continue adding countries while the remaining share is greater than 10%.
5. Group any remaining countries into **Other countries**.

The number of displayed sectors and countries is determined by the data. Five is not a fixed limit.

**Stopping condition:** The remaining Other group should represent at most 10% of its parent. If its share is exactly 10%, the algorithm can stop.

## 5. Data Integrity and Aggregation

- Preserve the original sector and country values in the source dataset.
- Create separate aggregated counts for the treemap. Do not overwrite the original categories with **Other sectors** or **Other countries**.
- Preserve the underlying records so aggregated groups can be inspected or explored further.
- Treat **Other sectors** as a visualization group, not as a real business sector.
- A country breakdown inside **Other sectors** combines countries across the grouped sectors. It does not show each original sector separately unless further drill-down is implemented.

## 6. Suggested Visual Design

- **Chart type:** Plotly Express treemap.
- **Hierarchy:** Sector → Country.
- **Rectangle area:** Number of loans.
- **Color:** Optionally use sector to distinguish major groups.
- **Hover information:** Loan count, parent share, and overall share.
- **Interactivity:** Support hover inspection and, if practical, drill-down into grouped categories.

## 7. Critical Considerations

1. **Comparability:** Treemaps are useful for visualizing composition, but bar charts are generally better for precise comparisons.
2. **Aggregation can hide detail:** Other sectors combines different sectors. Preserve the original data and label the group clearly.
3. **Country distributions can conceal sector differences:** A country may be prominent within Other sectors without being prominent in every individual sector.
4. **Crowding:** Even with a 10% threshold, several categories may need to be displayed individually. If the chart becomes crowded, consider interactive drill-down or a complementary bar chart.
5. **Interpretation:** Loan counts measure lending activity by number of loans. They do not measure monetary volume, repayment success, or the reasons behind sector and country differences.

## 8. Validation Before Finalizing

Before using the treemap as one of the project's assessed visualizations:

- Verify that sector and country counts reconcile to the total loan count.
- Confirm that each parent's displayed children plus its Other group equal the parent total.
- Confirm that each remaining Other group represents at most 10% of its parent.
- Check whether the treemap reveals insights that are not already communicated more clearly by the sector and country bar charts.
- If it replaces one of those charts, explain why the combined hierarchical view adds analytical value.

## 9. Proposed Chart Title

**Kiva Loan Distribution Across Sectors and Countries**

## 10. Implementation Note

Plotly Express supports hierarchical treemaps, but it does not automatically apply this custom threshold-based aggregation policy. The category selection and Other group calculations must be implemented in pandas before creating the chart.