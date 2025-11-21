import os
import grpc
import pytest
import weather_microservice_pb2
import weather_microservice_pb2_grpc

def test_valid_api_key_allows_access(grpc_server_address):
    api_key = os.getenv("GRPC_API_KEY", "testkey")
    with grpc.insecure_channel(grpc_server_address) as channel:
        stub = weather_microservice_pb2_grpc.WeatherServiceStub(channel)
        metadata = [("x-api-key", api_key)]
        request = weather_microservice_pb2.WeatherRequest(city="Iasi")

        response = stub.GetWeather(request, metadata=metadata, timeout=5)
        assert response.city != ""


def test_invalid_api_key_is_rejected(grpc_server_address):
    with grpc.insecure_channel(grpc_server_address) as channel:
        stub = weather_microservice_pb2_grpc.WeatherServiceStub(channel)
        metadata = [("x-api-key", "wrong-key")]
        request = weather_microservice_pb2.WeatherRequest(city="Iasi")
        with pytest.raises(grpc.RpcError) as exc_info:
            stub.GetWeather(request, metadata=metadata, timeout=5)
        assert exc_info.value.code() == grpc.StatusCode.PERMISSION_DENIED


def test_missing_api_key_is_rejected(grpc_server_address):
    with grpc.insecure_channel(grpc_server_address) as channel:
        stub = weather_microservice_pb2_grpc.WeatherServiceStub(channel)
        request = weather_microservice_pb2.WeatherRequest(city="Iasi")
        with pytest.raises(grpc.RpcError) as exc_info:
            stub.GetWeather(request, timeout=5)
        assert exc_info.value.code() == grpc.StatusCode.PERMISSION_DENIED
