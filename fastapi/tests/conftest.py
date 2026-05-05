import os
import sys
import pytest
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

env_path = os.path.join(os.path.dirname(__file__), '..', '.env.test')
load_dotenv(env_path)

pytest_plugins = [
    "test_data.fixtures.database",
    "test_data.fixtures.api",
    "test_data.fixtures.mocks",
]

@pytest.fixture(scope="session")
def test_db_config():
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": os.getenv("DB_PORT", "3307"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASS", "test123"),
        "database": os.getenv("DB_NAME", "movie_test"),
    }

@pytest.fixture(scope="session")
def test_api_config():
    return {
        "api_key": os.getenv("API_KEY"),
        "model_name": os.getenv("MODEL_NAME"),
        "api_base": os.getenv("API_BASE"),
    }
