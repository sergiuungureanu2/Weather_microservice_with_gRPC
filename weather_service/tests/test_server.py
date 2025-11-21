import os
import grpc
import pytest
from datetime import datetime
import weather_microservice_pb2
import weather_microservice_pb2_grpc


def test_grpc_valid_response(grpc_server_address):
    api_key = os.getenv("GRPC_API_KEY", "testkey")
    with grpc.insecure_channel(grpc_server_address) as channel:
        stub = weather_microservice_pb2_grpc.WeatherServiceStub(channel)
        metadata = [("x-api-key", api_key)]
        request = weather_microservice_pb2.WeatherRequest(city="Iasi")

        response = stub.GetWeather(request, metadata=metadata, timeout=10)
        assert response.city.lower() == "iasi"
        assert response.api_timestamp > 0
        assert response.request_timestamp > 0
