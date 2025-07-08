import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd

from utils.parser import parse_csv
from utils.ai import trending_summary

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PARSED_FOLDER'] = 'parsed_data'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PARSED_FOLDER'], exist_ok=True)


@app.route('/', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            filename = datetime.utcnow().strftime('%Y%m%d%H%M%S_') + file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            data = parse_csv(filepath)
            parsed_path = os.path.join(app.config['PARSED_FOLDER'], filename + '.json')
            data.to_json(parsed_path, orient='records', force_ascii=False)
            return redirect(url_for('view_data', parsed_file=filename + '.json'))
    return render_template('dashboard.html')


@app.route('/data/<parsed_file>')
def view_data(parsed_file):
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
        parsed_file=parsed_file
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

    outlet = request.args.get('outlet')
    if outlet and outlet != 'all':
        df = df[df['Outletname'] == outlet]

    start_date = request.args.get('start_date')
    if start_date:
        df = df[df['Sales Period'] >= pd.to_datetime(start_date)]

    end_date = request.args.get('end_date')
    if end_date:
        df = df[df['Sales Period'] <= pd.to_datetime(end_date)]

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


if __name__ == '__main__':
    app.run(debug=True)
