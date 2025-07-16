import os
import time
import pandas as pd
import requests
from flask import Flask, render_template, jsonify, abort
from dotenv import load_dotenv

# ✅ 환경 변수 로드 (카카오 API 키 저장)
load_dotenv()

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

# ✅ 카카오 맵 API 키 가져오기 (없으면 None)
KAKAO_MAP_API_KEY = os.getenv("KAKAO_MAP_API_KEY")

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html", kakao_api_key=KAKAO_MAP_API_KEY)

@app.route("/parking")
def parking():
    return render_template("parking.html")

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
