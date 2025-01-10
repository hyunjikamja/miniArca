import requests
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import torch

# 감정 카테고리 정의
categories = {
    "긍정적/고활성": ["기쁨", "흥분"],
    "긍정적/저활성": ["만족", "평온"],
    "부정적/고활성": ["분노", "공포"],
    "부정적/저활성": ["슬픔", "지루함"]
}

# GPU 최적화
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-augSTS', device=device) #모델에 대한 설명 발표 때 필요(유사도 상관관계)

# FastAPI 서버에서 감정 분석 결과 가져오기
def fetch_emotion_analysis(text):
    try:
        url = "http://localhost:8000/analyze"  # FastAPI 서버 URL
        payload = {"content": text}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
        return response.json()["emotion_analysis"]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching emotion analysis: {e}")
        return None

def calculate_final_emotion(input_data):
    emotion_expressions = [input_data["주요 감정"]] + [item["감정"] for item in input_data["세부 감정"]]
    emotion_weights = [input_data["감정 강도"]] + [item["강도"] for item in input_data["세부 감정"]]

    # 감정 표현과 카테고리 임베딩 계산
    emotion_embeddings = model.encode(emotion_expressions)
    category_embeddings = {key: model.encode(value) for key, value in categories.items()}

    # 카테고리별 유사도 계산
    category_scores = {}
    category_top_emotions = {}
    for category, embeddings in category_embeddings.items():
        similarity_matrix = cosine_similarity(emotion_embeddings, embeddings)
        weighted_similarity = np.average(similarity_matrix, axis=0, weights=emotion_weights)
        category_scores[category] = np.mean(weighted_similarity)  # 평균 유사도 사용

        # 각 카테고리에서 가장 관련 높은 감정 선택
        max_index = np.argmax(np.mean(similarity_matrix, axis=0))
        category_top_emotions[category] = categories[category][max_index]

    # 상위 2개 카테고리 선택
    sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
    top_categories = sorted_categories[:2]

    # 최종 출력: 상위 카테고리와 관련 높은 감정
    final_results = [
        (category, category_scores[category], category_top_emotions[category])
        for category, _ in top_categories
    ]

    return final_results

# 통합 워크플로우
def analyze_and_compute_final_emotion(text):
    # FastAPI 서버로부터 감정 분석 결과 가져오기
    emotion_result = fetch_emotion_analysis(text)
    if emotion_result is None:
        return "Failed to fetch emotion analysis."
    final_emotions = analyze_and_compute_final_emotion(text)
    return final_emotions
