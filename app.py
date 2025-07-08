import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
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
    summary = trending_summary(df)
    return render_template('dashboard.html', tables=df.to_dict(orient='records'), summary=summary)


@app.route('/api/data/<parsed_file>')
def api_data(parsed_file):
    path = os.path.join(app.config['PARSED_FOLDER'], parsed_file)
    df = pd.read_json(path)
    return df.to_json(orient='records', force_ascii=False)


if __name__ == '__main__':
    app.run(debug=True)
