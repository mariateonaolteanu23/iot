
import pandas as pd
import sys

RIDS=["66", "111", "23", "57", "1"]
FOLDER = "../vehicle-exports/"

if len(sys.argv) < 1:
    print("python concat_v.py [measurement1, measurement2, ...]")
    exit(-1)
else:
    MEASUREMENTS = sys.argv[1:]

for rid in RIDS:
    df = pd.read_csv(f"{FOLDER}{MEASUREMENTS[0]}_route_{rid}.csv")
    df['time'] = pd.to_datetime(df['time'])
    df = df.rename(columns={'data': MEASUREMENTS[0]})
    df_comb = df.drop(columns=["name", "tags"])
    for measurement in MEASUREMENTS[1:]:
        df = pd.read_csv(f"{FOLDER}{measurement}_route_{rid}.csv")
        df['time'] = pd.to_datetime(df['time'])
        df = df.rename(columns={'data': measurement})
        df = df.drop(columns=["name", "tags"])
        df['trip'] = df['trip'].astype(str)
        df_comb['trip'] = df_comb['trip'].astype(str)
        df_comb = df_comb.merge(df, on=["time", "revenue", "occupancy_status", "current_status", "current_stop_sequence", "id", "route", "trip", "stop"]) 
    df_comb = df_comb.dropna()
    df_comb.to_csv(f'{FOLDER}route_{rid}.csv', index=False)