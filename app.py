from flask import Flask, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# MySQL 연결 설정 
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:Qlalfqjsgh2@@localhost:13306/WiMANS'
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
        # 데이터베이스의 samples 테이블에서 상위 50개 데이터를 가져옵니다.
        samples_list = Sample.query.limit(50).all()
        
        result = []
        for s in samples_list:
            # 💡 중요: 리액트 Data.jsx 코드가data.id, data.subTitle을 사용하고 있으므로 key 이름을 정확히 맞춰줍니다.
            result.append({
                "id": s.sample_id,  # 리액트의 data.id와 매핑
                "title": f"Sample {s.sample_id}",
                # 사용자가 요구한 sample_id, environment, wifi_band를 한눈에 볼 수 있도록 구성
                "subTitle": f"ID: {s.sample_id} | Env: {s.environment} | Band: {s.wifi_band}"
            })
        return jsonify(result)
    except Exception as e:
        # 에러가 나면 콘솔에 출력하여 디버깅하기 쉽게 만듭니다.
        print("백엔드 에러 발생:", str(e))
        return jsonify({"error": str(e)}), 500


# [API 2] 특정 샘플을 클릭했을 때 우측 공간에 비디오 경로(video_path), CSI 경로(amp_npy_path) 반환하기
@app.route('/api/samples/<string:sample_id>', methods=['GET'])
def get_sample_detail(sample_id):
    try:
        sample = Sample.query.get(sample_id)
        if not sample:
            return jsonify({"error": "해당 샘플을 찾을 수 없습니다."}), 404
        
        # 외래키로 연결된 video_data와 csi_data 테이블 조회
        video = VideoData.query.filter_by(sample_id=sample_id).first()
        csi = CsiData.query.filter_by(sample_id=sample_id).first()

        # 💡 사용자의 요청사항인 실제 DB 내부의 video_path와 amp_npy_path 원본 문자열을 그대로 담아 보냅니다.
        return jsonify({
            "sample_id": sample.sample_id,
            "environment": sample.environment,
            "wifi_band": sample.wifi_band,
            "number_of_users": sample.number_of_users,
            "user_1_activity": sample.user_1_activity or "None",
            
            # 리액트에서 보여줄 원본 DB 경로 문자열 처리
            "video_path": video.video_path if video else "등록된 video_path가 없습니다.",
            "amp_npy_path": csi.amp_npy_path if csi else "등록된 amp_npy_path가 없습니다."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# [API 2] 특정 샘플을 클릭했을 때 비디오 주소, CSI 정보 등 상세 데이터 가져오기
@app.route('/api/samples/<string:sample_id>', methods=['GET'])
def get_sample_detail(sample_id):
    try:
        # 1. 메인 샘플 데이터 조회
        sample = Sample.query.get(sample_id)
        if not sample:
            return jsonify({"error": "해당 샘플을 찾을 수 없습니다."}), 404
        
        # 2. 외래키(sample_id)로 연결된 CSI 데이터와 비디오 데이터 조회
        csi = CsiData.query.filter_by(sample_id=sample_id).first()
        video = VideoData.query.filter_by(sample_id=sample_id).first()

        # 💡 [정적 파일 경로 매핑 설정]
        # DB에 적힌 파일명(예: act_1_1.mp4)만 추출하여 웹 브라우저가 접근 가능한 URL 주소로 만들어줍니다.
        video_filename = os.path.basename(video.video_path) if video else ""
        
        # 💡 전처리팀(진우혁 팀원)이 만든 .npy 기반의 시각화 히트맵/그래프 파일명 예측 매핑
        # 만약 이미지가 생성되어 static/csi_plots 폴더에 저장된다고 가정한 파일 이름입니다.
        heatmap_filename = f"{sample_id}_heatmap.png"
        graph_filename = f"{sample_id}_graph.png"

        return jsonify({
            "sample_id": sample.sample_id,
            "environment": sample.environment,
            "wifi_band": sample.wifi_band,
            "number_of_users": sample.number_of_users,
            "user_1_activity": sample.user_1_activity or "None",
            "user_2_activity": sample.user_2_activity or "None",
            
            # 리액트 태그(video src, img src)가 가져갈 수 있는 백엔드 주소 형태 구성
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