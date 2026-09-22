# Project Description (Aufgabenstellung)

## 1. Motivation

A German online furniture retailer (comparable to home24) sells furniture and home
accessories to private customers throughout Germany. The operational shop database is
designed for processing individual orders — it answers *"what is in order 41725?"*
quickly, but it cannot answer *"how did revenue per product category develop over the
last two years?"* without expensive joins and aggregations over the live system.

This project builds a small but complete data warehouse for that retailer: a normalized
operational source database, a dimensional target model, and an ETL process connecting
the two.

## 2. Objective

1. Design and implement a relational **Business DB** in 3NF that represents the
   order-taking process of the shop.
2. Populate it with synthetic but plausible data covering a two-year period.
3. Design and implement a **data warehouse** as a star schema.
4. Implement an **ETL process** in Python that loads the Business DB into the star schema.
5. Analyse **slowly changing dimensions** and show which attributes require which SCD type.
6. Answer the defined analytical questions with SQL against the warehouse.

## 3. Scope

The **order-taking process**: a customer places an order that contains one or more
order lines, each referring to a product belonging to a category.

The Business DB consists of five entities:

| Entity | Content |
|---|---|
| `customer` | Name, e-mail, address, postal code, city, federal state, customer since |
| `order_header` | Order date, payment method, shipping cost, reference to customer |
| `order_line` | Quantity, unit price, discount; reference to order and product |
| `product` | Product name, list price, colour, material, reference to category |
| `category` | Category name and optional parent category (two-level hierarchy) |


## 4. Data Basis

No production data is available, so the Business DB is filled with **synthetic data
generated in Python** using the `Faker` library. 

## 5. Analytical Questions

The warehouse is designed to answer the following two questions:

**Question 1 — Revenue and discount by category over time**
How does net revenue develop per top-level product category and quarter, and which
category carries the highest discount share?

**Question 2 — Regional differences in order value**
Which postal code regions generate the highest average order value, and does the
product category mix differ between them?

Neither question can be answered from a single dimension. Question 1 requires the date
and product dimensions; question 2 requires the customer and product dimensions.
Together they exercise all three dimensions of the model and thereby justify the schema.

**Optional**

Additional questions can be added if time permits: 

- Discount effectiveness Do products with a higher average discount share also show higher unit volumes, per category? Two measures against one dimension. Good because it produces a genuine finding rather than a ranking.

- Price segment mix How does revenue split across price segments (budget / mid / premium), and does the mix differ by postal code zone? Requires a derived band from list_price in the ETL — one CASE expression. Demonstrates a transformation rule in your mapping table, which is a plus.

- New vs. returning customers What share of revenue comes from customers in their first year versus later years? Uses customer_since in dim_customer. Attractive, but at 500 customers the cohorts get small — skip it under your revised volumes.

- Basket size How many lines does an average order contain, and does it vary by category or zone? Forces aggregation from line grain up to order_number. Pedagogically the strongest of the five, because it shows you understand your own grain.

## 6. Target Model

A **star schema** with one fact table and three dimensions.

**Grain of the fact table: one row per order line.**

| Table | Role | Content |
|---|---|---|
| `fact_sales` | Fact | Quantity, gross amount, discount amount, net amount; order number as degenerate dimension |
| `dim_date` | Dimension | Day, month, quarter, year, weekday, calendar week |
| `dim_customer` | Dimension | Name, address, postal code plus derived `plz_region` and `plz_zone`, city, federal state |
| `dim_product` | Dimension | Product name, colour, material, list price, category and top-level category (denormalized) |

The category hierarchy is normalized in the Business DB and deliberately denormalized
into `dim_product` in the warehouse. The postal code hierarchy
(zone → region → postal code) is stored in `dim_customer` and provides the drill-down
path for question 2.

## 7. ETL

A Python process reads the Business DB, transforms the data and loads the star schema.
The transformation rules are documented in a **mapping table** giving, for every target
column, the source column and the applied transformation rule.

Core transformations:

- Generation of surrogate keys for all dimensions
- Derivation of `dim_date` from the order date range
- Derivation of `plz_region` (first two digits) and `plz_zone` (first digit) from the postal code
- Flattening of the two-level category hierarchy into `dim_product`
- Calculation of the measures: `gross_amount`, `discount_amount`, `net_amount`

## 8. Slowly Changing Dimensions

Three scenarios are analysed and justified:

| Type | Example attribute | Justification |
|---|---|---|
| SCD 0 | `customer_id`, order date | Immutable by definition; must never be overwritten |
| SCD 1 | Product name (typo correction) | History has no analytical value; overwrite |
| SCD 2 | Customer address / postal code | A relocation changes the region a customer belongs to |

SCD 2 on the customer address is not an academic exercise here: without it, a customer's
relocation would retroactively reassign all historical orders to the new postal code
region, which directly falsifies analytical question 2.

The required changes to the logical model (`customer_sk`, `valid_from`, `valid_to`,
`is_current`) are documented as `ALTER` statements.

