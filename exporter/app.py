#!/usr/bin/env python3
import rancher_exporter
from flask import Flask, make_response

app = Flask(__name__)
@app.route('/metrics')
def metrics():
    response = make_response(rancher_exporter.metrics(), 200)
    response.mimetype = "text/plain"
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=12009)