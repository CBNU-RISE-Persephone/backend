import os
from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS
import pymysql

app = Flask(__name__)

CORS(app)

app.json.ensure_ascii = False

HEATMAP_DIR = "/data/WiMANS/heatmaps"
VIDEOS_DIR = "/data/WiMANS/videos"


def get_connection(database):
    return pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="admin",
        password="Qlalfqjsgh2@",
        database=database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

def get_dynamic_samples():
    """
    VIDEOS_DIR 폴더를 스캔하여 'act_nn_mm.mp4' 형식의 파일을 찾고,
    해당 파일과 매칭되는 히트맵 GIF 경로를 묶어 동적으로 리스트를 반환합니다.
    """
    samples = []
    
    if not os.path.exists(VIDEOS_DIR):
        return samples

    file_list = sorted(os.listdir(VIDEOS_DIR))
    
    idx = 1
    for filename in file_list:
        if filename.endswith(".mp4") and filename.startswith("act_"):
            name_without_ext = filename.replace(".mp4", "")
            parts = name_without_ext.split("_")
            
            if len(parts) == 3:
                nn, mm = parts[1], parts[2]
                heatmap_filename = f"act_{nn}_{mm}_heatmap.gif"
                
                samples.append({
                    "id": idx,
                    "sample_id": f"WI-MANS-{nn}-{mm}",
                    "subTitle": f"식물 생장 데이터 샘플 (act_{nn}_{mm})",
                    "environment": "실제 환경 데이터 (자동 로드됨)",
                    "wifi_band": "측정 환경에 따름",
                    "number_of_users": "N/A",
                    "user_1_activity": "N/A",
                    "user_2_activity": "N/A",
                    "video_path": os.path.join(VIDEOS_DIR, filename),
                    "amp_npy_path": os.path.join(HEATMAP_DIR, heatmap_filename),
                    "video_url": f"/static/videos/{filename}",
                    "heatmap_url": f"/static/heatmaps/{heatmap_filename}"
                })
                idx += 1
                
    return samples

@app.route("/")
def home():
    return jsonify({
        "message": "Persephone backend server is running"
    })

@app.route('/static/heatmaps/<path:filename>')
def serve_heatmap(filename):
    if not os.path.exists(os.path.join(HEATMAP_DIR, filename)):
        abort(404, description="Heatmap file not found")
    return send_from_directory(HEATMAP_DIR, filename)

@app.route('/static/videos/<path:filename>')
def serve_video(filename):
    if not os.path.exists(os.path.join(VIDEOS_DIR, filename)):
        abort(404, description="Video file not found")
    return send_from_directory(VIDEOS_DIR, filename)

@app.route('/api/samples', methods=['GET'])
def get_samples():
    samples = get_dynamic_samples()
    summary_list = [{"id": item["id"], "subTitle": item["subTitle"]} for item in samples]
    return jsonify(summary_list)

@app.route('/api/samples/<int:sample_id>', methods=['GET'])
def get_sample_detail(sample_id):
    samples = get_dynamic_samples()
    sample = next((item for item in samples if item["id"] == sample_id), None)
    if sample is None:
        abort(404, description="해당 샘플을 찾을 수 없습니다.")
    return jsonify(sample)

@app.route("/api/team-members", methods=["GET"])
def get_team_members():
    try:
        conn = get_connection("persephone_web")
        with conn.cursor() as cursor:
            sql = """
                SELECT id, name, role, image, github_url
                FROM team_members
                ORDER BY FIELD(id, 'song', 'mic', 'kim')
            """
            cursor.execute(sql)
            members = cursor.fetchall()
        return jsonify(members), 200
    except Exception as e:
        print("팀원 조회 오류:", repr(e))
        return jsonify({
            "error": "팀원 정보를 불러오지 못했습니다.",
            "detail": str(e)
        }), 500
    finally:
        if "conn" in locals():
            conn.close()

@app.route("/api/questions", methods=["POST"])
def create_question():
    try:
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        contents = data.get("contents")

        if not name or not email or not contents:
            return jsonify({"error": "name, email, contents는 필수입니다."}), 400

        conn = get_connection("questions")
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO questions (name, email, contents)
                VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (name, email, contents))
            conn.commit()

        return jsonify({"message": "문의가 저장되었습니다."}), 201

    except Exception as e:
        print("문의 저장 오류:", repr(e))
        return jsonify({
            "error": "문의 저장에 실패했습니다.",
            "detail": str(e)
        }), 500
    finally:
        if "conn" in locals():
            conn.close()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)