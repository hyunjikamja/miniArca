from flask import Flask, request, jsonify, render_template, session
from pymongo import MongoClient
from capture import capture_photo
from analyze import analyze_image
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 세션을 위한 비밀키 설정

# MongoDB 연결
client = MongoClient('mongodb+srv://20220968:duksung2022@path22.64mkm.mongodb.net/?retryWrites=true&w=majority&appName=path22')
db = client['photo_analysis']
collection = db['analysis_results']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_name', methods=['POST'])
def submit_name():
    name = request.form['name']
    session['user_name'] = name
    return jsonify(success=True)

@app.route('/capture')
def capture_page():
    return render_template('capture.html')

@app.route('/capture', methods=['POST'])
def capture():
    user_name = session.get('user_name', 'unknown')
    result = capture_photo(user_name)
    return jsonify(result)

@app.route('/analyze', methods=['POST'])
def analyze():
    user_name = session.get('user_name', 'unknown')
    result = analyze_image(user_name)
    
    # MongoDB에 분석 결과 저장
    analysis_data = {
        "user_name": user_name,
        "output_image": result.get('output_image'),
        "output_txt": result.get('output_txt'),
        "results": result.get('results')
    }
    collection.insert_one(analysis_data)
    
    return jsonify(result)

@app.route('/analysis_results/<user_name>', methods=['GET'])
def get_analysis_results(user_name):
    results = collection.find_one({"user_name": user_name})
    if results:
        # MongoDB의 ObjectId는 JSON 직렬화가 불가능하므로 제거
        results.pop('_id', None)
        return jsonify(results)
    else:
        return jsonify({"error": "결과를 찾을 수 없습니다."}), 404

if __name__ == '__main__':
    app.run(debug=True)
