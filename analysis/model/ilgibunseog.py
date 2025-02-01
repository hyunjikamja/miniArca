# -*- coding: utf-8 -*-
import json
import hashlib
import logging
import re
import time
import google.generativeai as genai


logging.basicConfig(level=logging.WARNING)

response_cache = {}

GOOGLE_API_KEY = 'AIzaSyApiC9CGNOyrYtHXhee_qP2O0hbnQpKyQI'

genai.configure(api_key=GOOGLE_API_KEY)

# 기본 재시도 설정
MAX_RETRIES = 10
RETRY_DELAY = 1  # 초 단위 지연 시간

# 감정 분석 함수
def emotion_anal(text):
    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    
    if text_hash in response_cache:
        return response_cache[text_hash]
    
    model = genai.GenerativeModel('gemini-pro')
    
    instructions = """
    주어진 한국어 텍스트에서 전반적인 내용을 깊이 있게 이해하여 감정을 분석해주세요.
    가장 높은 강도를 가지는 감정을 주요 감정으로 선택해주세요.
    세부감정은 높은 강도순대로 나열해주세요.
    다음 형식으로 정확하게 결과를 제공해주세요:
    {
        "주요 감정": "감정 이름",
        "감정 강도": 숫자 (0~100),
        "세부 감정": [
            {
                "감정": "감정 이름",
                "강도": 숫자 (0~100)
            },
            {
                "감정": "감정 이름",
                "강도": 숫자 (0~100)
            },
            {
                "감정": "감정 이름",
                "강도": 숫자 (0~100)
            }
        ]
    }
    """
    
    prompt = f"텍스트: {text}\n분석 결과:"
    full_prompt = f"{instructions}\n{prompt}"

    for attempt in range(MAX_RETRIES):
        try:
            response = model.generate_content(full_prompt)
            response_text = response.text.encode('utf-8').decode('utf-8').strip()
            parsed_response = json.loads(response_text)
            response_cache[text_hash] = parsed_response
            return parsed_response
        except json.JSONDecodeError as e:
            logging.error(f"Attempt {attempt + 1} failed: Invalid JSON format received: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                logging.error("Maximum retries reached. Returning default response.")
                parsed_response = {
                    "주요 감정": "알 수 없음",
                    "감정 강도": 0,
                    "세부 감정": [
                        {"감정": "알 수 없음", "강도": 0},
                        {"감정": "알 수 없음", "강도": 0},
                        {"감정": "알 수 없음", "강도": 0}
                    ]
                }
                response_cache[text_hash] = parsed_response
                return parsed_response

# 장소 추출 함수
def extract_places(text):
    text_hash = hashlib.md5((text + "_places").encode('utf-8')).hexdigest()
    
    if text_hash in response_cache:
        return response_cache[text_hash]
    
    model = genai.GenerativeModel('gemini-pro')
    
    instructions = """
    장소: 텍스트에서 장소를 하나만 선택해주세요.
    장소와 관련된 단어들은 도시, 나라, 건물, 지역 등을 포함합니다.
    만약 장소가 없다면 텍스트에서 장소를 분석해서 선택해주세요.
    다음 형식으로 정확하게 결과를 제공해주세요:
    {
        "장소": "장소 이름"
    }
    """
    
    prompt = f"텍스트: {text}\n장소 추출:"
    full_prompt = f"{instructions}\n{prompt}"

    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            response = model.generate_content(full_prompt)
            response_text = response.text.encode('utf-8').decode('utf-8').strip()
            parsed_response = json.loads(response_text)

            # 만약 "장소" 값이 "알 수 없음"이라면, 다시 시도
            if parsed_response.get("장소") and parsed_response["장소"] != "알 수 없음":
                response_cache[text_hash] = parsed_response
                return parsed_response
            else:
                logging.warning(f"Attempt {attempt + 1}: Invalid or unknown place received, retrying...")

        except json.JSONDecodeError as e:
            logging.error(f"Attempt {attempt + 1} failed: Invalid JSON format received: {e}")

        # 재시도 대기
        attempt += 1
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)

    # 최대 재시도 후 기본값 반환
    logging.error("Maximum retries reached. Returning default response.")
    parsed_response = {"장소": "알 수 없음"}
    response_cache[text_hash] = parsed_response
    return parsed_response

# 사물 키워드 추출 함수
def extract_object_keywords(text, excluded_keywords=None):
    text_hash = hashlib.md5((text + "_object_keywords").encode('utf-8')).hexdigest()
    
    if text_hash in response_cache:
        return response_cache[text_hash]
    
    model = genai.GenerativeModel('gemini-pro')
    
    instructions = """
    중요: 장소와 관련된 단어들은 포함하지 마세요. 예를 들어, 도시, 나라, 건물, 지역, 공원과 같은 장소와 관련된 단어는 결과에서 제외해주세요.
    주어진 한국어 텍스트에서 주요 감정 또는 세부 감정과 관련된 사물, 상황 또는 개념을 중심으로 명사를 5개 추출해주세요. 명사와 관련된 키워드는 물건, 도구, 기계, 자연물, 추상적인 것 등을 포함합니다.
    다음 형식으로 정확하게 결과를 제공해주세요:
    {
        "사물 키워드": ["명사1", "명사2", "명사3", "명사4", "명사5"]
    }
    """
    
    if excluded_keywords:
        excluded_string = ", ".join(excluded_keywords)
        instructions += f"\n단, 다음 키워드는 결과에서 제외해주세요: {excluded_string}."
    
    prompt = f"텍스트: {text}\n사물 키워드 추출 결과:"
    full_prompt = f"{instructions}\n{prompt}"

    for attempt in range(MAX_RETRIES):
        try:
            response = model.generate_content(full_prompt)
            response_text = response.text.encode('utf-8').decode('utf-8').strip()
            parsed_response = json.loads(response_text)
            object_keywords = parsed_response.get('사물 키워드', [])

            if excluded_keywords:
                object_keywords = [keyword for keyword in object_keywords if keyword not in excluded_keywords]

            final_object_keywords = object_keywords[:5]
            parsed_response['사물 키워드'] = final_object_keywords

            response_cache[text_hash] = parsed_response
            return parsed_response
        except json.JSONDecodeError as e:
            logging.error(f"Attempt {attempt + 1} failed: Invalid JSON format received: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                logging.error("Maximum retries reached. Returning empty response.")
                parsed_response = {"사물 키워드": []}
                response_cache[text_hash] = parsed_response
                return parsed_response

# 통합 사용 예시
def analyze_text(text):
    place_result = extract_places(text)
    excluded_keywords = [place_result.get("장소")] if place_result.get("장소") else []
    object_keywords_result = extract_object_keywords(text, excluded_keywords=excluded_keywords)
    return {
        "place": place_result,
        "object_keywords": object_keywords_result
    }


