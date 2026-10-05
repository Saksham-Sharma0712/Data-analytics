"""Run the whole pipeline:  python run_all.py"""
import generate_data, clean_data, load_to_db, analysis, build_dashboard

steps = [("1/5 Generate raw data", generate_data.main), ("2/5 Clean data", clean_data.main),
         ("3/5 Load database", load_to_db.main), ("4/5 Analyse & export reports", analysis.main),
         ("5/5 Build dashboard", build_dashboard.main)]
for title, fn in steps:
    print(f"\n=== {title} ===")
    fn()
print("\nDone. Open output/dashboard.html in your browser.")
