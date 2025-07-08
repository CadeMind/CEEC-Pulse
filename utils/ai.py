import pandas as pd


def trending_summary(df: pd.DataFrame) -> str:
    """Return a short sales trend summary with track hints."""
    if df.empty:
        return 'No data available.'

    # Ensure datetime and numeric types
    df['Sales Period'] = pd.to_datetime(df['Sales Period'], errors='coerce')
    df = df.dropna(subset=['Sales Period'])

    df_sorted = df.sort_values('Sales Period')
    df_sorted['Units'] = pd.to_numeric(df_sorted['Units'], errors='coerce').fillna(0)

    latest = df_sorted['Sales Period'].max()
    prev = latest - pd.Timedelta(days=7)
    prev_prev = prev - pd.Timedelta(days=7)

    current_df = df_sorted[df_sorted['Sales Period'] > prev]
    previous_df = df_sorted[(df_sorted['Sales Period'] > prev_prev) & (df_sorted['Sales Period'] <= prev)]

    current = current_df['Units'].sum()
    previous = previous_df['Units'].sum()

    if previous == 0:
        overall_part = 'Недостаточно данных для анализа динамики.'
    else:
        change = (current - previous) / previous * 100
        overall_part = f'Изменение Units за последнюю неделю: {change:.2f}%.'

    # Track level growth calculation
    track_cur = current_df.groupby('Tracktitle')['Units'].sum()
    track_prev = previous_df.groupby('Tracktitle')['Units'].sum()

    hints = []
    for track, cur_val in track_cur.items():
        prev_val = track_prev.get(track, 0)
        if prev_val > 0:
            growth = (cur_val - prev_val) / prev_val * 100
            if growth > 0:
                hints.append((growth, f'Трек {track} показывает рост {growth:.1f}%'))
        elif cur_val > 0:
            hints.append((0, f'Трек {track} впервые получил {int(cur_val)} продаж'))

    hints.sort(key=lambda x: x[0], reverse=True)
    hints_text = ' '.join(h[1] for h in hints[:3])

    artist_report = ''
    if df_sorted['Artist'].nunique() == 1:
        artist = df_sorted['Artist'].iloc[0]
        total_units = int(df_sorted['Units'].sum())
        top_track = df_sorted.groupby('Tracktitle')['Units'].sum().idxmax()
        artist_report = f'Артист {artist} суммарно продал {total_units} Units. Лидирующий трек: {top_track}.'

    summary_parts = [artist_report, overall_part, hints_text]
    return ' '.join(p for p in summary_parts if p)
