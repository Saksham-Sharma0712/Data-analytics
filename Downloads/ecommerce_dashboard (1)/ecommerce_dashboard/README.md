# E-Commerce Admin Dashboard

A data-driven dashboard for monitoring e-commerce performance: sales, revenue, orders, profit,
customers and products. Data flows **Data -> Cleaning -> Database -> Analysis -> Dashboard -> Insights**.

| Layer | What it does | File |
|---|---|---|
| Data sources | Generates a realistic *synthetic* dataset (1,200 customers, 48 products, 6,500 orders, Jan 2025 - Sep 2026) with deliberate quality problems | `generate_data.py` |
| Processing | Pandas cleaning: duplicates, missing values, inconsistent spelling, invalid emails, recomputed order totals | `clean_data.py` |
| Database | SQLAlchemy schema with PK/FK. SQLite by default, MySQL via env var | `database.py`, `load_to_db.py`, `schema.sql` |
| Analytics | EDA, KPIs, monthly/category/product/region analysis, RFM customer segmentation, Excel + CSV export | `analytics.py`, `analysis.py`, `queries.sql` |
| Dashboard | One interactive HTML file: KPI strip, slicers, drill-down, charts, tables, auto-generated insights, CSV export | `build_dashboard.py`, `dashboard_template.html` |
| Power BI | Flat tables + DAX measures to recreate the dashboard in Power BI | `output/powerbi/`, `powerbi_guide.md` |

## Run it

```bash
pip install -r requirements.txt
python run_all.py        # runs all 5 steps, takes a few seconds
python verify.py         # 10 integrity checks
```
Then open **`output/dashboard.html`** in a browser (needs internet once per load for Chart.js and fonts).

Outputs: `output/ecommerce_analysis.xlsx`, `output/csv/*.csv`, `output/kpis.json`, `output/powerbi/*.csv`.

## Using MySQL instead of SQLite

```sql
CREATE DATABASE ecommerce;
```
```bash
export DATABASE_URL="mysql+pymysql://USER:PASSWORD@localhost:3306/ecommerce"   # Windows: set DATABASE_URL=...
python load_to_db.py && python analysis.py && python build_dashboard.py && python verify.py
```
`queries.sql` holds example queries you can run directly in MySQL Workbench.

## Using your own data
Replace the four CSVs in `data/raw/` (same columns: see `database.py`), skip `generate_data.py`, and run
`clean_data.py`, `load_to_db.py`, `analysis.py`, `build_dashboard.py`.
If your categories, regions or cities differ, edit `CITY_REGION` in `config.py`.

## Definitions
- **Valid sales** = orders with status Delivered, Shipped or Processing. Cancelled and Returned are excluded from KPIs (the dashboard's status chips let you include them).
- **Revenue** = quantity x unit price x (1 - discount). **Profit** = revenue - quantity x product cost.
- **RFM segments**: Champions, Loyal, Promising, Needs attention, At risk, Lost (rules in `analytics.py`).

## Deploy on Render (free Static Site)

1. Push this folder to a new GitHub repo (`git init && git add . && git commit -m "dashboard" && git branch -M main && git remote add origin <your-repo-url> && git push -u origin main`).
2. On https://render.com: **New > Blueprint**, pick the repo. Render reads `render.yaml`, runs `python run_all.py`, and serves `output/`.
   (Manual alternative: **New > Static Site**, Build Command `pip install -r requirements.txt && python run_all.py`, Publish Directory `output`.)
3. Your dashboard is live at `https://ecommerce-admin-dashboard.onrender.com` (the name may differ).

The deployed site is a static snapshot of the data at build time. Redeploy to refresh it.
