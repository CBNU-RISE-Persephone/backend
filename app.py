
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import pymysql

app = Flask(__name__)
CORS(app)

app.json.ensure_ascii = False


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


@app.route("/")
def home():
    return jsonify({
        "message": "Persephone backend server is running"
    })


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

@app.route("/videos/<path:filename>")
def stream_video(filename):
	video_dir = os.path.join(app.root_path, 'static/videos')
	return send_from_directory(video_dir, filename)

@app.route("/heatmaps/<path:filename>")
def stream_heatmap(filename):
	heatmap_dir = os.path.join(app.root_path, 'static/heatmaps')
	return send_from_directory(heatmap_dir, filename)

@app.route("/api/questions", methods=["POST"])
def create_question():
    try:
        data = request.get_json()

        name = data.get("name")
        email = data.get("email")
        contents = data.get("contents")

        if not name or not email or not contents:
            return jsonify({
                "error": "name, email, contents는 필수입니다."
            }), 400

        conn = get_connection("questions")

        with conn.cursor() as cursor:
            sql = """
                INSERT INTO questions (name, email, contents)
                VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (name, email, contents))
            conn.commit()

        return jsonify({
            "message": "문의가 저장되었습니다."
        }), 201

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
    app.run(debug=True, port=5000)
