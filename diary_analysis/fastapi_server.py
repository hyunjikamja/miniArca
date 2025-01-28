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
import subprocess
import asyncio
from bson import ObjectId
import emoji_select
import traceback

# 환경 변수 로드
load_dotenv()

app = FastAPI()

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(os.getenv("MONGODB_URL","mongodb+srv://20220767:duksung2022@path22.64mkm.mongodb.net/?retryWrites=true&w=majority&appName=path22"))
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
        result = await app.database.diary_entries.insert_one(analysis_data)
        entry_id = str(result.inserted_id)
        inserted_id = str(result.inserted_id)


        # 분석 결과 로깅
        print(f"Emotion analysis response: {emotion_analysis}")
        print(f"Place extraction response: {place_extraction}")
        print(f"Object keywords response: {object_keywords}")

        # 이모지 선택 및 저장 실행
        emojis = await select_and_save_emoji(inserted_id)

        # 배경 생성 작업 시작
        await run_generate_background(entry_id)

        return {
            "emotion_analysis": emotion_analysis,
            "place_extraction": place_extraction,
            "object_keywords": object_keywords,
            "entry_id": entry_id,
            "emojis": emojis
        }

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

async def run_generate_background(entry_id: str):
    try:
        print(f"Starting background generation for entry_id: {entry_id}")
        script_path = r"C:\Users\DS\miniArca\stable-diffusion-webui\scripts\generate_background.py"
        result = await asyncio.to_thread(subprocess.run,
            ["python", script_path, entry_id],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Background generation completed for entry_id: {entry_id}")
    except Exception as e:
        print(f"Error in background generation: {e}")

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
    
async def select_and_save_emoji(id: str):
    try:
        document = await app.database.diary_entries.find_one({"_id": ObjectId(id)})
        
        if not document:
            print(f"Document not found for id: {id}")
            return
        
        emotion_analysis = document.get("emotion_analysis", {})
        object_keywords = document.get("object_keywords", {})
        
        print(f"Emotion analysis: {emotion_analysis}")
        print(f"Object keywords: {object_keywords}")
        
        # emoji_select.py의 get_emojis 함수 호출
        try:
            emojis = emoji_select.get_emojis(emotion_analysis, object_keywords)
            print(f"Selected emojis: {emojis}")
        except Exception as emoji_error:
            print(f"Error in emoji selection: {emoji_error}")
            print(f"Traceback: {traceback.format_exc()}")
            return None
        
        # 결과를 MongoDB에 저장
        try:
            update_result = await app.database.diary_entries.update_one(
                {"_id": ObjectId(id)},
                {"$set": {"이모지": emojis}}
            )
            
            if update_result.modified_count == 0:
                print(f"Failed to update document {id}")
            else:
                print(f"Successfully updated document {id} with emojis: {emojis}")
        except Exception as db_error:
            print(f"Error updating database: {db_error}")
            print(f"Traceback: {traceback.format_exc()}")
            return None
        
        return emojis
    except Exception as e:
        print(f"Error selecting and saving emoji: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
