from concurrent import futures
import grpc
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
from dotenv import load_dotenv
from datetime import datetime
import os
import logging

import weather_microservice_pb2
import weather_microservice_pb2_grpc

load_dotenv()
DEBUG_MODE = os.getenv("DEBUG", "False").lower() == "true"

log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
log_format = (
    "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    if DEBUG_MODE
    else "%(levelname)s: %(message)s"
)

logging.basicConfig(level=log_level, format=log_format)
logger = logging.getLogger(__name__)

if DEBUG_MODE:
    logger.debug("Debug mode enabled — verbose logging active.")
else:
    logger.info("Running in production mode — minimal logging.")


def weather_response_to_dict(resp):
    return {
        "city": resp.city,
        "country": resp.country,
        "coordinates": {"lon": resp.coord.lon, "lat": resp.coord.lat},
        "temperature": resp.temperature,
        "feels_like": resp.feels_like,
        "temp_min": resp.temp_min,
        "temp_max": resp.temp_max,
        "pressure": resp.pressure,
        "humidity": resp.humidity,
        "wind_speed": resp.wind_speed,
        "wind_deg": resp.wind_deg,
        "wind_gust": resp.wind_gust,
        "main_condition": resp.main_condition,
        "description": resp.description,
        "rain_1h": resp.rain_1h,
        "clouds": resp.clouds,
        "timestamp": resp.timestamp,
        "datetime": datetime.utcfromtimestamp(resp.timestamp),
        "api_timestamp": getattr(resp, "api_timestamp", None),
        "api_datetime": datetime.utcfromtimestamp(getattr(resp, "api_timestamp", 0))
            if getattr(resp, "api_timestamp", 0) else None,
        "request_timestamp": getattr(resp, "request_timestamp", None),
        "request_datetime": datetime.utcfromtimestamp(getattr(resp, "request_timestamp", 0))
            if getattr(resp, "request_timestamp", 0) else None,
    }



class WeatherServiceServicer(weather_microservice_pb2_grpc.WeatherServiceServicer):
    def __init__(self):
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        db_name = os.getenv("MONGO_DB", "weather_db")
        collection_name = os.getenv("MONGO_COLLECTION", "weather_logs")
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.expected_grpc_key = os.getenv("GRPC_API_KEY")

        if not self.api_key:
            raise ValueError("Missing OPENWEATHER_API_KEY in environment variables or .env file")

        try:
            self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000, tz_aware=True)
            self.db = self.mongo_client[db_name]
            self.collection = self.db[collection_name]
            logger.info(f"Connected to MongoDB at {mongo_uri}")
        except ServerSelectionTimeoutError:
            logger.warning("Could not connect to MongoDB. Continuing without DB connection.")
            self.collection = None

    def GetWeather(self, request, context):
        metadata = dict(context.invocation_metadata())
        api_key = metadata.get("x-api-key")
        if not api_key or api_key != self.expected_grpc_key:
            logger.warning("Unauthorized request: invalid or missing API key.")
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("Invalid or missing API key.")
            return weather_microservice_pb2.WeatherResponse()
        


        city = request.city.strip()
        logger.info(f"Received gRPC request for city: {city}")

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric"
        }

        try:
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
            except Timeout:
                context.set_code(grpc.StatusCode.DEADLINE_EXCEEDED)
                context.set_details("Request to weather API timed out.")
                return weather_microservice_pb2.WeatherResponse()
            except ConnectionError:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("Failed to connect to weather API.")
                return weather_microservice_pb2.WeatherResponse()
            except HTTPError as e:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"City '{city}' not found or API error: {str(e)}")
                return weather_microservice_pb2.WeatherResponse()
            except RequestException as e:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"Unexpected error calling weather API: {str(e)}")
                return weather_microservice_pb2.WeatherResponse()

            try:
                data = response.json()
                coord = data.get("coord", {})
                main = data.get("main", {})
                wind = data.get("wind", {})
                weather = data.get("weather", [{}])[0]
                rain = data.get("rain", {}).get("1h", 0)
                clouds = data.get("clouds", {}).get("all", 0)
                sys_data = data.get("sys", {})
                api_timestamp = data.get("dt", 0)
                request_timestamp = int(datetime.now().timestamp())

                weather_response = weather_microservice_pb2.WeatherResponse(
                    city=data.get("name", ""),
                    country=sys_data.get("country", ""),
                    coord=weather_microservice_pb2.Coordinates(
                        lon=coord.get("lon", 0.0),
                        lat=coord.get("lat", 0.0)
                    ),
                    temperature=main.get("temp", 0.0),
                    feels_like=main.get("feels_like", 0.0),
                    temp_min=main.get("temp_min", 0.0),
                    temp_max=main.get("temp_max", 0.0),
                    pressure=main.get("pressure", 0),
                    humidity=main.get("humidity", 0),
                    wind_speed=wind.get("speed", 0.0),
                    wind_deg=wind.get("deg", 0),
                    wind_gust=wind.get("gust", 0.0),
                    main_condition=weather.get("main", ""),
                    description=weather.get("description", ""),
                    rain_1h=rain,
                    clouds=clouds,
                    timestamp=api_timestamp,
                    api_timestamp=api_timestamp,
                    request_timestamp=request_timestamp
                )

            except (ValueError, KeyError, TypeError) as e:
                context.set_code(grpc.StatusCode.DATA_LOSS)
                context.set_details(f"Failed to parse weather data: {str(e)}")
                return weather_microservice_pb2.WeatherResponse()

            if self.collection is not None:
                try:
                    self.collection.insert_one(weather_response_to_dict(weather_response))
                    logger.info(f"Weather data for {city} saved to MongoDB")
                except (ServerSelectionTimeoutError, PyMongoError) as e:
                    logger.warning(f"MongoDB error while saving data: {e}")
            else:
                logger.warning("Skipping MongoDB save (no connection).")

            logger.info(f"Successfully processed weather data for {city}")
            return weather_response
        except Exception as e:
            logger.exception(f"Unexpected error while processing request for {city}: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected server error: {str(e)}")
            return weather_microservice_pb2.WeatherResponse()


def serve():
    port = os.getenv("GRPC_PORT", "50051")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    weather_microservice_pb2_grpc.add_WeatherServiceServicer_to_server(
        WeatherServiceServicer(), server
    )
    server.add_insecure_port(f"[::]:{port}")
    logger.info(f"Weather gRPC server running on port {port} ...")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
