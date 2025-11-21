import os
import pytest
from pymongo import MongoClient
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

@pytest.fixture(scope="session")
def grpc_server_address():
    return f"{os.getenv('GRPC_SERVER', 'localhost')}:{os.getenv('GRPC_PORT', '50051')}"

@pytest.fixture(scope="session")
def mongo_client():
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    client = MongoClient(uri)
    yield client
    client.close()
