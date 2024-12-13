import pandas as pd
import sys

FOLDER = "../weather-exports/"


if len(sys.argv) < 1:
    print("python concat_w.py [measurement1, measurement2, ...]")
    exit(-1)
else:
    MEASUREMENTS = sys.argv[1:]

df = pd.read_csv(f"{FOLDER}{MEASUREMENTS[0]}.csv")
df['time'] = pd.to_datetime(df['time'])
df_comb = df[['time', 'data']].rename(columns={'data': MEASUREMENTS[0]}) 

for measurement in MEASUREMENTS[1:]:
    df = pd.read_csv(f"{FOLDER}{measurement}.csv")
    df['time'] = pd.to_datetime(df['time'])
    df_comb = df_comb.merge(df[['time', 'data']].rename(columns={'data': measurement}), on='time')

df_comb.to_csv(f'{FOLDER}weather.csv', index=False)