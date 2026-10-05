"""Step 3 - Load cleaned CSVs into the relational database."""
import pandas as pd

from config import CLEAN
from database import DATE_COLUMNS, LOAD_ORDER, get_engine, metadata


def main():
    engine = get_engine()
    metadata.drop_all(engine)       # rebuild from scratch so the script is re-runnable
    metadata.create_all(engine)
    for name in LOAD_ORDER:
        df = pd.read_csv(CLEAN / f"{name}.csv")
        for col in DATE_COLUMNS.get(name, []):
            df[col] = pd.to_datetime(df[col]).dt.date
        df.to_sql(name, engine, if_exists="append", index=False, chunksize=500, method="multi")
        print(f"  loaded {name:<12}{len(df):>7,} rows")
    print("Database ready:", engine.url.render_as_string(hide_password=True))


if __name__ == "__main__":
    main()
