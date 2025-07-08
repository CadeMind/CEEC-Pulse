import pandas as pd


def _parse_sales_period(series: pd.Series) -> pd.Series:
    """Parse Sales Period handling YYYYMM strings."""
    col = series.astype(str).str.strip()
    parsed = pd.to_datetime(col, errors='coerce')
    mask = parsed.isna() & col.str.match(r'^\d{6}$')
    if mask.any():
        parsed.loc[mask] = pd.to_datetime(col[mask], format='%Y%m', errors='coerce')
    return parsed

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
    df['Sales Period'] = _parse_sales_period(df['Sales Period'])
    df = df.dropna(subset=['Sales Period'])

    # Convert numeric columns that may use comma as decimal separator
    if df['Units'].dtype == 'object':
        df['Units'] = df['Units'].astype(str).str.replace(',', '.').astype(float)

    df['Royalty Amount Customer'] = (
        df['Royalty Amount Customer']
        .astype(str)
        .str.replace(',', '.')
        .astype(float)
    )
    return df


def parse_excel(path: str) -> pd.DataFrame:
    """Parse an Excel report (.xlsx) using the same rules as CSV."""
    df = pd.read_excel(path, engine='openpyxl')
    if 'Unnamed: 13' in df.columns:
        df = df.drop(columns=['Unnamed: 13'])
    df = df.dropna(how='all')
    df = df.fillna('')
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f'Missing columns: {missing_cols}')
    df['Sales Period'] = _parse_sales_period(df['Sales Period'])
    df = df.dropna(subset=['Sales Period'])

    if df['Units'].dtype == 'object':
        df['Units'] = df['Units'].astype(str).str.replace(',', '.').astype(float)

    df['Royalty Amount Customer'] = (
        df['Royalty Amount Customer']
        .astype(str)
        .str.replace(',', '.')
        .astype(float)
    )
    return df


def parse_file(path: str) -> pd.DataFrame:
    """Parse a report in CSV or XLSX format."""
    if path.lower().endswith('.csv'):
        return parse_csv(path)
    if path.lower().endswith('.xlsx'):
        return parse_excel(path)
    raise ValueError('Unsupported file format')
