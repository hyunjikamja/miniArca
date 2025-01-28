from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

    @classmethod
    async def connect_to_mongo(cls):
        cls.client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
        cls.database = cls.client[os.getenv("DB_NAME")]
        print("MongoDB에 연결되었습니다!")
        return cls.database

    @classmethod
    async def close_mongo_connection(cls):
        if cls.client is not None:
            cls.client.close()
            print("MongoDB 연결이 종료되었습니다.")

    @classmethod
    def get_database(cls):
        return cls.database