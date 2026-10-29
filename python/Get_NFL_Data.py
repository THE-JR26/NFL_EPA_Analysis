from sqlalchemy import create_engine
from nflreadRpy import nflreadR
import pandas as pd

print("Pandas connected successfully!")

seasons = [2023,2024,2025,2026]
pbp = nflreadR.import_pbp(seasons)

pbp.to_parquet("pbp_2023_2026.parquet")
print("Download PBP:", pbp.shape)

engine = create_engine("mysql+pymysql://root:password?@localhost:3306/nfl_analytics")

try:
    engine.connect()
    print("Connected Successfully!")
except Exception as e:
    print("Connection failed:", e)
