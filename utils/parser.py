import pandas as pd

REQUIRED_COLUMNS = [
    'Labelname', 'ISRC', 'EAN/UPC', 'Artist', 'Producttitle',
    'Tracktitle', 'ArtNo', 'Outletname', 'Format', 'Territory',
    'Sales Period', 'Units', 'Royalty Amount Customer'
]


def parse_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=';', encoding='cp1251', on_bad_lines='skip')
    if 'Unnamed: 13' in df.columns:
        df = df.drop(columns=['Unnamed: 13'])
    df = df.dropna(how='all')
    df = df.fillna('')
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f'Missing columns: {missing_cols}')
    df['Sales Period'] = pd.to_datetime(df['Sales Period'], errors='coerce')
    df = df.dropna(subset=['Sales Period'])
    return df
