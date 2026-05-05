import os
import sys
import pytest
import logging
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

env_path = os.path.join(os.path.dirname(__file__), '..', '.env.test')
load_dotenv(env_path, override=True)

# 配置日志
log_dir = os.path.join(os.path.dirname(__file__), '..', 'test_results', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, 'test.log')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)8s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file_path, mode='w', encoding='utf-8'),
    ]
)

logger = logging.getLogger(__name__)


def pytest_configure(config):
    """动态生成带时间戳的测试报告文件名"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = os.path.join(os.path.dirname(__file__), '..', 'test_results', 'reports')
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f'report_{timestamp}.html')
    config.option.htmlpath = report_path
    config.option.self_contained_html = True


@pytest.fixture(scope="session", autouse=True)
def log_test_session():
    """自动记录测试会话开始和结束"""
    logger.info("=" * 50)
    logger.info("测试会话开始")
    yield
    logger.info("测试会话结束")
    logger.info("=" * 50)

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
