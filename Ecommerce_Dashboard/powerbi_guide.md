# Building the Power BI version

Power BI reports are `.pbix` files made inside Power BI Desktop (Windows), so they can't be generated from code.
This guide gets you from the project output to the same dashboard in Power BI in about 30 minutes.
`output/dashboard.html` is the working, finished dashboard; this is the Power BI recreation of it.

## 1. Import the data
Run `python run_all.py`, then in Power BI Desktop: **Get data > Text/CSV** and load
- `output/powerbi/fact_sales.csv` (one row per order line, with `revenue`, `profit`, `is_valid`, `customer_segment`)
- `output/powerbi/dim_customer_rfm.csv` (optional, RFM scores per customer)

To read from MySQL instead: **Get data > MySQL database**, server `localhost`, database `ecommerce`.
(The MySQL route needs the MySQL connector installed, and you recompute revenue/profit as DAX columns.)

In Power Query make sure `order_date` is type **Date** and `is_valid` is **True/False**.

## 2. Date table
Modeling > New table:
```DAX
dim_date = CALENDARAUTO()
```
Add columns `Year = YEAR(dim_date[Date])`, `Month = FORMAT(dim_date[Date], "MMM yy")`,
`MonthSort = YEAR(dim_date[Date]) * 100 + MONTH(dim_date[Date])` (set Month to sort by MonthSort).
Relate `dim_date[Date]` to `fact_sales[order_date]` (one-to-many, single direction).

## 3. DAX measures
```DAX
Total Revenue    = CALCULATE ( SUM ( fact_sales[revenue] ), fact_sales[is_valid] = TRUE () )
Total Profit     = CALCULATE ( SUM ( fact_sales[profit] ),  fact_sales[is_valid] = TRUE () )
Total Orders     = CALCULATE ( DISTINCTCOUNT ( fact_sales[order_id] ), fact_sales[is_valid] = TRUE () )
Customers        = CALCULATE ( DISTINCTCOUNT ( fact_sales[customer_id] ), fact_sales[is_valid] = TRUE () )
Units Sold       = CALCULATE ( SUM ( fact_sales[quantity] ), fact_sales[is_valid] = TRUE () )
Avg Order Value  = DIVIDE ( [Total Revenue], [Total Orders] )
Profit Margin %  = DIVIDE ( [Total Profit], [Total Revenue] )
Revenue Prev Month = CALCULATE ( [Total Revenue], DATEADD ( dim_date[Date], -1, MONTH ) )
Revenue MoM %    = DIVIDE ( [Total Revenue] - [Revenue Prev Month], [Revenue Prev Month] )
Cancel/Return Rate =
    DIVIDE (
        CALCULATE ( DISTINCTCOUNT ( fact_sales[order_id] ), fact_sales[is_valid] = FALSE () ),
        DISTINCTCOUNT ( fact_sales[order_id] )
    )
```
Check: with no filters, `Total Revenue` should equal `total_revenue` in `output/kpis.json`.

## 4. Report page layout
| Visual | Fields |
|---|---|
| KPI cards (x5) | Total Revenue, Total Profit, Total Orders, Avg Order Value, Customers |
| Combo chart (columns + line) | Axis: `dim_date[Month]`; columns: Total Revenue; line: Total Profit |
| Bar chart | Axis: `category`; value: Total Revenue |
| Bar chart | Axis: `region`; value: Total Revenue |
| Donut | Legend: `payment_method`; value: Total Orders |
| Table (Top N filter = 10 by Total Revenue) | `product_name`, `category`, Total Revenue, Profit Margin % |
| Table (Top N = 10 customers) | `customer_name`, `location`, `customer_segment`, Total Revenue |
| Slicers | `dim_date[Date]` (Between), `category`, `region`, `order_status` |

Drill-down: add `category` then `product_name` to the bar chart axis and turn on drill mode.
Cross-filtering between visuals is automatic. Use **File > Export > Export data** for CSV/Excel exports.
