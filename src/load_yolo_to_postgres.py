import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:"
    f"{os.getenv('POSTGRES_PORT')}/"
    f"{os.getenv('POSTGRES_DB')}"
)

CSV_PATH = "data/processed/yolo_detections.csv"

def main():
    engine = create_engine(DB_URL)
    df = pd.read_csv(CSV_PATH)

    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS raw_yolo_detections;"))
        conn.commit()

    df.to_sql("raw_yolo_detections", engine, if_exists="replace", index=False)
    print(f"Loaded {len(df)} rows into raw_yolo_detections")

if __name__ == "__main__":
    main()