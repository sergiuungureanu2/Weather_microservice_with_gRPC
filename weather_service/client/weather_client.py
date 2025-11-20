import grpc
import os
from dotenv import load_dotenv
from datetime import datetime
from pymongo import MongoClient
import weather_microservice_pb2
import weather_microservice_pb2_grpc

load_dotenv()

GRPC_SERVER = os.getenv("GRPC_SERVER", "localhost")
GRPC_PORT = os.getenv("GRPC_PORT", "50051")
DEBUG_MODE = os.getenv("DEBUG", "False").lower() == "true"

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "weather_db")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "weather_logs")

def get_current_weather(city_name: str):

    target = f"{GRPC_SERVER}:{GRPC_PORT}"

    try:
        with grpc.insecure_channel(target) as channel:
            stub = weather_microservice_pb2_grpc.WeatherServiceStub(channel)
            request = weather_microservice_pb2.WeatherRequest(city=city_name)
            response = stub.GetWeather(request, timeout=10)

            if not response.city:
                return {"error": "Empty response from server"}

            return {
                    "city": response.city,
                    "country": response.country,
                    "temperature": round(response.temperature, 2),
                    "feels_like": round(response.feels_like, 2),
                    "humidity": response.humidity,
                    "wind_speed": response.wind_speed,
                    "description": response.description.capitalize(),
                    "clouds": response.clouds,
                    "timestamp": response.timestamp,
                    "api_timestamp": getattr(response, "api_timestamp", None),
                    "request_timestamp": getattr(response, "request_timestamp", None)
                }

    except grpc.RpcError as e:
        return {"error": f"{e.code().name}: {e.details()}"}
    except Exception as e:
        return {"error": str(e)}


def get_weather_history(city: str, limit: int = 10):

    try:
        client = MongoClient(MONGO_URI, tz_aware=True)
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]

        query = {"city": {"$regex": f"^{city}$", "$options": "i"}}

        results = list(collection.find(query).sort("datetime", -1).limit(limit))
        client.close()

        history = []
        for entry in results:
            history.append({
                "city": entry.get("city", ""),
                "country": entry.get("country", ""),
                "temperature": entry.get("temperature"),
                "feels_like": entry.get("feels_like"),
                "humidity": entry.get("humidity"),
                "description": entry.get("description"),
                "datetime": entry.get("datetime"),
            })

        return history[::-1]

    except Exception as e:
        if DEBUG_MODE:
            print(f"MongoDB query error: {e}")
        return []


def get_full_weather(city_name: str, history_limit: int = 10):
    current_data = get_current_weather(city_name)

    if "error" in current_data:
        return {"error": current_data["error"]}

    history_data = get_weather_history(city_name, limit=history_limit)

    return {
        "city": city_name,
        "current": current_data,
        "history": history_data
    }