from flask import Flask, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
# 1. 주소 인코딩을 위한 라이브러리 추가
import urllib.parse

app = Flask(__name__)
CORS(app)

# 2. 비밀번호를 안전하게 인코딩 처리
password = urllib.parse.quote_plus("Qlalfqjsgh2@")

# 3. 인코딩된 비밀번호를 문자열 포맷팅(f-string)으로 삽입
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://admin:{password}@localhost:13306/WiMANS'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
# ==========================================
# 1. DB 모델 정의 (제공해주신 SQL 스크립트 기반)
# ==========================================

class Sample(db.Model):
    __tablename__ = 'samples'
    sample_id = db.Column(db.String(50), primary_key=True)
    environment = db.Column(db.String(100), nullable=False)
    wifi_band = db.Column(db.String(10), nullable=False)
    number_of_users = db.Column(db.Integer, nullable=False)
    user_1_activity = db.Column(db.String(100))
    user_2_activity = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class CsiData(db.Model):
    __tablename__ = 'csi_data'
    csi_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sample_id = db.Column(db.String(50), db.ForeignKey('samples.sample_id', ondelete='CASCADE'), nullable=False)
    raw_mat_path = db.Column(db.String(500), nullable=False)
    amp_npy_path = db.Column(db.String(500), nullable=False)

class VideoData(db.Model):
    __tablename__ = 'video_data'
    video_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sample_id = db.Column(db.String(50), db.ForeignKey('samples.sample_id', ondelete='CASCADE'), nullable=False)
    video_path = db.Column(db.String(500), nullable=False)


# ==========================================
# 2. 리액트 연동을 위한 API 엔드포인트
# ==========================================

# [API 1] 좌측 사이드바에 뿌려줄 데이터셋 전체 목록 가져오기
@app.route('/api/samples', methods=['GET'])
def get_samples():
    try:
        samples_list = Sample.query.limit(50).all()
        
        result = []
        for s in samples_list:
            result.append({
                "id": s.sample_id,
                "title": f"Sample {s.sample_id}",
                "subTitle": f"ID: {s.sample_id} | Env: {s.environment} | Band: {s.wifi_band}"
            })
        return jsonify(result)
    except Exception as e:
        print("백엔드 에러 발생:", str(e))
        return jsonify({"error": str(e)}), 500


# [API 2] 중복되던 두 함수를 하나로 깔끔하게 통합했습니다!
@app.route('/api/samples/<string:sample_id>', methods=['GET'])
def get_sample_detail(sample_id):
    try:
        # 1. 메인 샘플 데이터 조회
        sample = Sample.query.get(sample_id)
        if not sample:
            return jsonify({"error": "해당 샘플을 찾을 수 없습니다."}), 404
        
        # 2. 외래키로 연결된 video_data와 csi_data 테이블 조회
        video = VideoData.query.filter_by(sample_id=sample_id).first()
        csi = CsiData.query.filter_by(sample_id=sample_id).first()

        # 3. 파일명 추출 및 정적 파일 URL 구성
        video_filename = os.path.basename(video.video_path) if video else ""
        heatmap_filename = f"{sample_id}_heatmap.png"
        graph_filename = f"{sample_id}_graph.png"

        # 4. 원본 경로 정보와 웹 URL 주소를 모두 포함하여 하나의 JSON으로 반환
        return jsonify({
            "sample_id": sample.sample_id,
            "environment": sample.environment,
            "wifi_band": sample.wifi_band,
            "number_of_users": sample.number_of_users,
            "user_1_activity": sample.user_1_activity or "None",
            "user_2_activity": sample.user_2_activity or "None",
            
            # 원본 DB 내부 경로 문자열
            "video_path": video.video_path if video else "등록된 video_path가 없습니다.",
            "amp_npy_path": csi.amp_npy_path if csi else "등록된 amp_npy_path가 없습니다.",
            
            # 리액트 UI 태그(video src, img src)용 URL 주소 형태
            "video_url": f"http://localhost:5000/static/videos/{video_filename}" if video_filename else None,
            "heatmap_url": f"http://localhost:5000/static/csi_plots/{heatmap_filename}",
            "graph_url": f"http://localhost:5000/static/csi_plots/{graph_filename}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# [기존 연결 체크 기능 유지]
@app.route('/')
def home():
    return "페르세포네 Flask 서버가 정상적으로 작동 중입니다!"

@app.route('/api/db-check')
def db_check():
    try:
        db.session.execute('SELECT 1')
        return jsonify({"status": "success", "message": "MySQL 데이터베이스 연결 성공!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)