import pandas as pd


def trending_summary(df: pd.DataFrame) -> str:
    """Return a short sales trend summary."""
    if df.empty:
        return 'No data available.'

    # Ensure Sales Period is in datetime format for timedelta arithmetic
    df['Sales Period'] = pd.to_datetime(df['Sales Period'], errors='coerce')
    df = df.dropna(subset=['Sales Period'])

    df_sorted = df.sort_values('Sales Period')

    latest_period = df_sorted['Sales Period'].max()
    prev_period = latest_period - pd.Timedelta(days=7)

    current = df_sorted[df_sorted['Sales Period'] > prev_period]['Units'].sum()
    previous = df_sorted[df_sorted['Sales Period'] <= prev_period]['Units'].sum()

    if previous == 0:
        return 'Недостаточно данных для анализа динамики.'

    change = (current - previous) / previous * 100
    return f'Изменение Units за последнюю неделю: {change:.2f}%.'
