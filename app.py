import os
import json
import io
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    jsonify, send_file, Response
)
import pandas as pd
import weasyprint

from utils.parser import parse_csv
from utils.ai import trending_summary

TRANSLATIONS = {
    'ru': {
        'title': 'CEEC Pulse Dashboard',
        'upload_csv': 'Загрузить CSV',
        'all_artists': 'Все артисты',
        'all_outlets': 'Все платформы',
        'reset_filters': 'Сбросить фильтры',
        'ai_analysis': 'AI анализ',
        'data': 'Данные',
        'export_csv': 'Экспорт CSV',
        'export_excel': 'Экспорт Excel',
        'export_pdf': 'Экспорт PDF',
        'dark_mode': 'Тёмная тема'
    },
    'en': {
        'title': 'CEEC Pulse Dashboard',
        'upload_csv': 'Upload CSV',
        'all_artists': 'All artists',
        'all_outlets': 'All outlets',
        'reset_filters': 'Reset filters',
        'ai_analysis': 'AI analysis',
        'data': 'Data',
        'export_csv': 'Export CSV',
        'export_excel': 'Export Excel',
        'export_pdf': 'Export PDF',
        'dark_mode': 'Dark mode'
    }
}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PARSED_FOLDER'] = 'parsed_data'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PARSED_FOLDER'], exist_ok=True)


@app.route('/', methods=['GET', 'POST'])
def dashboard():
    lang = request.args.get('lang', 'ru')
    if lang not in TRANSLATIONS:
        lang = 'ru'
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            filename = datetime.utcnow().strftime('%Y%m%d%H%M%S_') + file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            data = parse_csv(filepath)
            parsed_path = os.path.join(app.config['PARSED_FOLDER'], filename + '.json')
            data.to_json(parsed_path, orient='records', force_ascii=False)
            return redirect(url_for('view_data', parsed_file=filename + '.json', lang=lang))
    return render_template('dashboard.html', lang=lang, t=TRANSLATIONS[lang])


@app.route('/data/<parsed_file>')
def view_data(parsed_file):
    lang = request.args.get('lang', 'ru')
    if lang not in TRANSLATIONS:
        lang = 'ru'
    path = os.path.join(app.config['PARSED_FOLDER'], parsed_file)
    df = pd.read_json(path)

    # Normalize numeric columns that may have comma decimal separator
    if df['Units'].dtype == 'object':
        df['Units'] = df['Units'].astype(str).str.replace(',', '.').astype(float)
    df['Royalty Amount Customer'] = (
        df['Royalty Amount Customer'].astype(str).str.replace(',', '.').astype(float)
    )
    summary = trending_summary(df)

    artists = sorted(df['Artist'].dropna().unique().tolist())
    outlets = sorted(df['Outletname'].dropna().unique().tolist())
    units_min = int(df['Units'].min())
    units_max = int(df['Units'].max())
    royalty_min = float(df['Royalty Amount Customer'].min())
    royalty_max = float(df['Royalty Amount Customer'].max())

    return render_template(
        'dashboard.html',
        tables=df.to_dict(orient='records'),
        summary=summary,
        artists=artists,
        outlets=outlets,
        units_min=units_min,
        units_max=units_max,
        royalty_min=royalty_min,
        royalty_max=royalty_max,
        parsed_file=parsed_file,
        lang=lang,
        t=TRANSLATIONS[lang]
    )


@app.route('/api/data/<parsed_file>')
def api_data(parsed_file):
    path = os.path.join(app.config['PARSED_FOLDER'], parsed_file)
    df = pd.read_json(path)
    return df.to_json(orient='records', force_ascii=False)


@app.route('/filter_data/<parsed_file>')
def filter_data(parsed_file):
    path = os.path.join(app.config['PARSED_FOLDER'], parsed_file)
    df = pd.read_json(path)

    if df['Units'].dtype == 'object':
        df['Units'] = df['Units'].astype(str).str.replace(',', '.').astype(float)
    df['Royalty Amount Customer'] = (
        df['Royalty Amount Customer'].astype(str).str.replace(',', '.').astype(float)
    )

    artist = request.args.get('artist')
    if artist and artist != 'all':
        df = df[df['Artist'] == artist]

@@ -100,27 +142,61 @@ def filter_data(parsed_file):

    units_min = request.args.get('units_min')
    if units_min:
        df = df[df['Units'] >= int(units_min)]

    units_max = request.args.get('units_max')
    if units_max:
        df = df[df['Units'] <= int(units_max)]

    royalty_min = request.args.get('royalty_min')
    if royalty_min:
        df = df[df['Royalty Amount Customer'] >= float(royalty_min)]

    royalty_max = request.args.get('royalty_max')
    if royalty_max:
        df = df[df['Royalty Amount Customer'] <= float(royalty_max)]

    summary = trending_summary(df)

    return jsonify({
        'data': df.to_dict(orient='records'),
        'summary': summary
    })


@app.route('/export/<fmt>/<parsed_file>')
def export_data(fmt, parsed_file):
    path = os.path.join(app.config['PARSED_FOLDER'], parsed_file)
    df = pd.read_json(path)

    if fmt == 'csv':
        csv_data = df.to_csv(index=False)
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={parsed_file[:-5]}.csv'}
        )
    elif fmt == 'xlsx':
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=parsed_file[:-5] + '.xlsx'
        )
    elif fmt == 'pdf':
        html = df.to_html(index=False)
        pdf_bytes = weasyprint.HTML(string=html).write_pdf()
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=parsed_file[:-5] + '.pdf'
        )
    return 'Unsupported format', 400


if __name__ == '__main__':
    app.run(debug=True)
