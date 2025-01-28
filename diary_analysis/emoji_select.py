import json
import torch
from sentence_transformers import SentenceTransformer, util
import os
from googletrans import Translator

# Sentence Transformer 모델 로드
model = SentenceTransformer('all-MiniLM-L6-v2')

# emoji_list.json 파일의 경로
json_path = os.path.join(os.path.dirname(__file__), 'emoji_list.json')

# emoji_list.json 파일 로드
with open(json_path, 'r', encoding='utf-8') as f:
    emoji_list = json.load(f)

# Translator 객체 생성
translator = Translator()

def translate_to_english(text):
    try:
        return translator.translate(text, dest='en').text
    except:
        return text

def get_emoji(input_word):
    # 입력 단어를 영어로 번역
    input_word_en = translate_to_english(input_word)
    
    # 입력 단어와 이모지 리스트의 임베딩 생성
    input_embedding = model.encode(input_word_en, convert_to_tensor=True)
    emoji_embeddings = model.encode(emoji_list, convert_to_tensor=True)

    # 코사인 유사도 계산
    cosine_scores = util.pytorch_cos_sim(input_embedding, emoji_embeddings)[0]

    # 가장 유사한 이모지 선택
    top_result = torch.topk(cosine_scores, k=1)
    top_index = top_result.indices.item()

    return emoji_list[top_index]

def get_emojis(emotion_analysis, object_keywords):
    emojis = []

    # 주요 감정에 대한 이모지 선택
    if '주요 감정' in emotion_analysis:
        emojis.append(get_emoji(emotion_analysis['주요 감정']))

    # 세부 감정들에 대한 이모지 선택
    if '세부 감정' in emotion_analysis and isinstance(emotion_analysis['세부 감정'], list):
        for detail in emotion_analysis['세부 감정']:
            if isinstance(detail, dict) and '감정' in detail:
                emojis.append(get_emoji(detail['감정']))

    # 사물 키워드에 대한 이모지 선택 (최대 5개)
    if 'object_keywords' in object_keywords and isinstance(object_keywords['object_keywords'], list):
        for keyword in object_keywords['object_keywords'][:5]:
            emojis.append(get_emoji(keyword))

    return emojis

