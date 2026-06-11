import os
from flask import Flask, jsonify, send_from_directory, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

HEATMAP_DIR = "/data/WiMANS/heatmaps"
VIDEOS_DIR = "/data/WiMANS/videos"

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


# 데이터베이스를 대신할 샘플 가상 데이터 (nn, mm 조합 예시)
# 실제 환경에서는 DB에서 조회한 nn, mm 값으로 파일명을 동적 매핑하시면 됩니다.
SAMPLES_DATA = [
    {
        "id": 1,
        "sample_id": "WI-MANS-01",
        "subTitle": "식물 생장 데이터 샘플 01 (act_01_01)",
        "environment": "연구실 옥상 온실 (Zone A)",
        "wifi_band": "5 GHz",
        "number_of_users": 1,
        "user_1_activity": "식물 수분 공급",
        "user_2_activity": "없음",
        "video_path": os.path.join(VIDEOS_DIR, "act_01_01.mp4"),
        "amp_npy_path": os.path.join(HEATMAP_DIR, "act_01_01_heatmap.gif"),
        "video_url": "http://localhost:5000/static/videos/act_01_01.mp4",
        "heatmap_url": "http://localhost:5000/static/heatmaps/act_01_01_heatmap.gif"
    },
    {
        "id": 2,
        "sample_id": "WI-MANS-02",
        "subTitle": "식물 생장 데이터 샘플 02 (act_02_15)",
        "environment": "실내 스마트팜 큐브 (Zone B)",
        "wifi_band": "2.4 GHz",
        "number_of_users": 2,
        "user_1_activity": "잎 측정 및 이동",
        "user_2_activity": "노트북 제어",
        "video_path": os.path.join(VIDEOS_DIR, "act_02_15.mp4"),
        "amp_npy_path": os.path.join(HEATMAP_DIR, "act_02_15_heatmap.gif"),
        "video_url": "http://localhost:5000/static/videos/act_02_15.mp4",
        "heatmap_url": "http://localhost:5000/static/heatmaps/act_02_15_heatmap.gif"
    }
]

@app.route('/api/samples', methods=['GET'])
def get_samples():
    summary_list = [{"id": item["id"], "subTitle": item["subTitle"]} for item in SAMPLES_DATA]
    return jsonify(summary_list)

@app.route('/api/samples/<int:sample_id>', methods=['GET'])
def get_sample_detail(sample_id):
    sample = next((item for item in SAMPLES_DATA if item["id"] == sample_id), None)
    if sample is None:
        abort(404, description="해당 샘플을 찾을 수 없습니다.")
    return jsonify(sample)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)