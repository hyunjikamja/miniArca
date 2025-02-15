import sys
import os

# analysis 폴더를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from model import ilgibunseog
from model.emotion_compute import calculate_final_emotion
from model.generate_background import generate_anime_background
import json
from dotenv import load_dotenv
from model import emoji_select
import traceback
from model.analyze import analyze_image

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(os.getenv("MONGODB_URL", "mongodb+srv://20220784:duksung2022@path22.64mkm.mongodb.net/?retryWrites=true&w=majority&appName=path22"))
    app.database = app.mongodb_client[os.getenv("DB_NAME", "diary_db")]
    print("MongoDB에 연결되었습니다!")

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()
    print("MongoDB 연결이 종료되었습니다.")

class DiaryEntry(BaseModel):
    content: str
    analysis_id: str

cached_analysis_results = {}

@app.post("/analyzePhoto")
async def analyze_photo(file: UploadFile = File(...)):
    try:
        inserted_id = str(uuid.uuid4())
        user_directory = os.path.join("C:/Users/DS/miniArca/analysis/model/Pictures", inserted_id)
        os.makedirs(user_directory, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"photo_{timestamp}.jpg"
        filepath = os.path.join(user_directory, filename)

        with open(filepath, "wb") as buffer:
            buffer.write(await file.read())

        analysis_result = analyze_image(inserted_id)

        new_diary_entry = {
            "_id": inserted_id,
            "photo_analysis_result": analysis_result,
            "file_path": filepath
        }
        await app.database.diary_entries.insert_one(new_diary_entry)

        return {
            "message": "사진 분석 완료 및 결과 저장됨",
            "analysis_id": inserted_id,
            "analysis_result": analysis_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사진 분석 중 오류 발생: {str(e)}")

@app.post("/analyzeDiary")
async def analyze_diary(entry: DiaryEntry):
    try:
        content = entry.content
        analysis_id = entry.analysis_id
        print(f"Received content: {content}")
        print(f"Received analysis_id: {analysis_id}")

        document = await app.database.diary_entries.find_one({"_id": analysis_id})
        if not document:
            raise HTTPException(status_code=400, detail="사진 분석을 먼저 수행해야 합니다.")

        emotion_analysis = ilgibunseog.emotion_anal(content)
        place_extraction = ilgibunseog.extract_places(content)
        object_keywords = ilgibunseog.extract_object_keywords(content)
        final_emotions = calculate_final_emotion(emotion_analysis)

        cached_analysis_results["content"] = content
        cached_analysis_results["emotion_analysis"] = emotion_analysis

        update_data = {
            "$set": {
                "content": content,
                "emotion_analysis": emotion_analysis,
                "final_emotions": final_emotions,
                "place_extraction": place_extraction,
                "object_keywords": object_keywords,
                "timestamp": datetime.now()
            }
        }

        await app.database.diary_entries.update_one({"_id": analysis_id}, update_data)

        location = place_extraction.get("장소")
        if location:
            image_path = generate_anime_background(analysis_id, location)
            await app.database.diary_entries.update_one(
                {"_id": analysis_id},
                {"$set": {"background_image_path": image_path}}
            )

        print(f"Emotion analysis response: {emotion_analysis}")
        print(f"Final emotions response: {final_emotions}")
        print(f"Place extraction response: {place_extraction}")
        print(f"Object keywords response: {object_keywords}")
        print(f"Generated background image path: {image_path}")

        emojis = await select_and_save_emoji(analysis_id)

        return {
            "id": analysis_id,
            "emotion_analysis": emotion_analysis,
            "final_emotions": final_emotions,
            "place_extraction": place_extraction,
            "object_keywords": object_keywords,
            "background_image_path": image_path,
            "emojis": emojis
        }

    except ValueError as ve:
        print(f"Value error occurred: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        raise HTTPException(status_code=500, detail="Invalid JSON format")
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/entries")
async def get_entries():
    try:
        entries = await app.database.diary_entries.find().to_list(length=100)
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

async def select_and_save_emoji(id: str):
    try:
        document = await app.database.diary_entries.find_one({"_id": id})
        
        if not document:
            print(f"Document not found for id: {id}")
            return
        
        emotion_analysis = document.get("emotion_analysis", {})
        object_keywords = document.get("object_keywords", {})
        
        print(f"Emotion analysis: {emotion_analysis}")
        print(f"Object keywords: {object_keywords}")
        
        try:
            emojis = emoji_select.get_emojis(emotion_analysis, object_keywords)
            print(f"Selected emojis: {emojis}")
        except Exception as emoji_error:
            print(f"Error in emoji selection: {emoji_error}")
            print(f"Traceback: {traceback.format_exc()}")
            return None
        
        try:
            update_result = await app.database.diary_entries.update_one(
                {"_id": id},
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
