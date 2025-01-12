import re
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import ilgibunseog
from emotion_compute import calculate_final_emotion
import json
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

app = FastAPI()

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 구체적인 오리진을 지정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
    app.database = app.mongodb_client[os.getenv("DB_NAME", "diary_db")]
    print("MongoDB에 연결되었습니다!")

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()
    print("MongoDB 연결이 종료되었습니다.")

class DiaryEntry(BaseModel):
    content: str

cached_analysis_results = {}

@app.post("/analyze")
async def analyze_diary(entry: DiaryEntry):
    try:
        content = entry.content
        print(f"Received content: {content}")

        # 감정, 장소, 키워드 분석 수행
        emotion_analysis = ilgibunseog.emotion_anal(content)
        place_extraction = ilgibunseog.extract_places(content)
        object_keywords = ilgibunseog.extract_object_keywords(content)

        # 분석 결과 캐싱
        cached_analysis_results["content"] = content
        cached_analysis_results["emotion_analysis"] = emotion_analysis

        # MongoDB에 저장할 데이터 구성
        analysis_data = {
            "content": content,
            "emotion_analysis": emotion_analysis,
            "place_extraction": place_extraction,
            "object_keywords": object_keywords,
            "timestamp": datetime.now()
        }

        # MongoDB에 저장
        await app.database.diary_entries.insert_one(analysis_data)

        # 분석 결과 로깅
        print(f"Emotion analysis response: {emotion_analysis}")
        print(f"Place extraction response: {place_extraction}")
        print(f"Object keywords response: {object_keywords}")

        return {
            "emotion_analysis": emotion_analysis,
            "place_extraction": place_extraction,
            "object_keywords": object_keywords
        }

    except ValueError as ve:
        print(f"Value error occurred: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/entries")
async def get_entries():
    try:
        entries = await app.database.diary_entries.find().to_list(length=100)
        # ObjectId를 문자열로 변환
        for entry in entries:
            entry["_id"] = str(entry["_id"])
        return entries
    except Exception as e:
        print(f"Error fetching entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/final-emotions")
async def get_final_emotions():
    try:
        if "emotion_analysis" not in cached_analysis_results:
            raise HTTPException(status_code=400, detail="No analysis data found. Please analyze the diary first.")

        emotion_analysis = cached_analysis_results["emotion_analysis"]
        final_emotions = calculate_final_emotion(emotion_analysis)

        return final_emotions

    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)