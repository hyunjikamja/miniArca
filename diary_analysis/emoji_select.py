import json
import torch
from sentence_transformers import SentenceTransformer, util


# 입력 단어 지정
input_word = " "

# emoji_list.json 파일의 절대 경로 지정
# 여기서 'DS'는 사용자 이름이므로, 실제 경로에 맞게 수정해야 합니다.
json_path = r'C:\Users\DS\miniArca\diary_analysis\emoji_list.json'

# emoji_list.json 파일 로드
with open(json_path, 'r', encoding='utf-8') as f:
    emoji_list = json.load(f)

# Sentence Transformer 모델 로드
model = SentenceTransformer('all-MiniLM-L6-v2')

# 입력 단어와 이모지 리스트의 임베딩 생성
input_embedding = model.encode(input_word, convert_to_tensor=True)
emoji_embeddings = model.encode(emoji_list, convert_to_tensor=True)

# 코사인 유사도 계산
cosine_scores = util.pytorch_cos_sim(input_embedding, emoji_embeddings)[0]

# 가장 유사한 이모지 선택
top_result = torch.topk(cosine_scores, k=1)
top_score = top_result.values.item()
top_index = top_result.indices.item()

# 결과 출력
print(f"입력 단어: {input_word}")
print(f"가장 유사한 이모지: {emoji_list[top_index]}")
print(f"유사도 점수: {top_score:.4f}")
