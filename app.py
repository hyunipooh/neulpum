import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
from dotenv import load_dotenv

# ✅ 환경 변수 로드 (카카오 API 키 저장)
load_dotenv()

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = 'neulpum_vet_secret_key_2024'  # 세션을 위한 시크릿 키
app.config['PERMANENT_SESSION_LIFETIME'] = 30 * 24 * 60 * 60  # 30일 (초 단위)

# ✅ 카카오 맵 API 키 가져오기 (없으면 None)
KAKAO_MAP_API_KEY = os.getenv("KAKAO_MAP_API_KEY")

# 파일 업로드 설정
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 업로드 폴더 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 관리자 계정 정보 (실제 운영시에는 환경변수로 관리)
ADMIN_USERNAME = 'hyunipooh'
ADMIN_PASSWORD = 'smfvna3130@'

# 공지사항 데이터 파일
NOTICES_FILE = 'notices.json'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_notices():
    if os.path.exists(NOTICES_FILE):
        with open(NOTICES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_notices(notices):
    with open(NOTICES_FILE, 'w', encoding='utf-8') as f:
        json.dump(notices, f, ensure_ascii=False, indent=2)

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html", kakao_api_key=KAKAO_MAP_API_KEY)

@app.route("/parking")
def parking():
    return render_template("parking.html")

@app.route("/notice")
def notice():
    notices = load_notices()
    return render_template("notice.html", notices=notices)

@app.route("/notice/<notice_id>")
def notice_detail(notice_id):
    notices = load_notices()
    notice = next((n for n in notices if n['id'] == notice_id), None)
    if notice:
        return render_template("notice_detail.html", notice=notice)
    return redirect(url_for('notice'))

@app.route("/admin/login", methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            
            # 로그인 유지 체크박스가 체크된 경우 세션을 영구적으로 설정
            if remember:
                session.permanent = True
            
            return redirect(url_for('admin_dashboard'))
        else:
            flash('아이디 또는 비밀번호가 올바르지 않습니다.')
    
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('notice'))

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    notices = load_notices()
    return render_template("admin_dashboard.html", notices=notices)

@app.route("/admin/write", methods=['GET', 'POST'])
def admin_write():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if title and content:
            notice_id = str(uuid.uuid4())
            notice = {
                'id': notice_id,
                'title': title,
                'content': content,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'images': []
            }
            
            # 이미지 업로드 처리
            if 'images' in request.files:
                files = request.files.getlist('images')
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        # 고유한 파일명 생성
                        unique_filename = f"{notice_id}_{uuid.uuid4().hex}_{filename}"
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                        file.save(filepath)
                        
                        # 이미지 리사이즈 (선택사항)
                        try:
                            with Image.open(filepath) as img:
                                if img.size[0] > 1200 or img.size[1] > 1200:
                                    img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                                    img.save(filepath, quality=85, optimize=True)
                        except Exception as e:
                            print(f"이미지 리사이즈 오류: {e}")
                        
                        notice['images'].append(unique_filename)
            
            notices = load_notices()
            notices.insert(0, notice)  # 최신 글이 맨 위에 오도록
            save_notices(notices)
            
            return redirect(url_for('admin_dashboard'))
    
    return render_template("admin_write.html")

@app.route("/admin/edit/<notice_id>", methods=['GET', 'POST'])
def admin_edit(notice_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    notices = load_notices()
    notice = next((n for n in notices if n['id'] == notice_id), None)
    
    if not notice:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if title and content:
            notice['title'] = title
            notice['content'] = content
            notice['date'] = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            # 새 이미지 업로드 처리
            if 'images' in request.files:
                files = request.files.getlist('images')
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        unique_filename = f"{notice_id}_{uuid.uuid4().hex}_{filename}"
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                        file.save(filepath)
                        
                        try:
                            with Image.open(filepath) as img:
                                if img.size[0] > 1200 or img.size[1] > 1200:
                                    img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                                    img.save(filepath, quality=85, optimize=True)
                        except Exception as e:
                            print(f"이미지 리사이즈 오류: {e}")
                        
                        notice['images'].append(unique_filename)
            
            save_notices(notices)
            return redirect(url_for('admin_dashboard'))
    
    return render_template("admin_edit.html", notice=notice)

@app.route("/admin/delete/<notice_id>")
def admin_delete(notice_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    notices = load_notices()
    notice = next((n for n in notices if n['id'] == notice_id), None)
    
    if notice:
        # 이미지 파일 삭제
        for image in notice.get('images', []):
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image))
            except:
                pass
        
        notices = [n for n in notices if n['id'] != notice_id]
        save_notices(notices)
    
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/delete_image/<notice_id>/<image_name>")
def admin_delete_image(notice_id, image_name):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    notices = load_notices()
    notice = next((n for n in notices if n['id'] == notice_id), None)
    
    if notice and image_name in notice.get('images', []):
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image_name))
            notice['images'].remove(image_name)
            save_notices(notices)
        except:
            pass
    
    return redirect(url_for('admin_edit', notice_id=notice_id))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
