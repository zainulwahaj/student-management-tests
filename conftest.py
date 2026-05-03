import os
import time
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

BASE_URL    = os.environ.get('APP_URL', 'http://localhost:5000')
TEST_RUN_ID = str(int(time.time()))


@pytest.fixture(scope='session')
def base_url():
    return BASE_URL

@pytest.fixture(scope='session')
def run_id():
    return TEST_RUN_ID

@pytest.fixture(scope='session')
def test_user(run_id):
    return {
        'username': f'qa_user_{run_id}',
        'email':    f'qa_user_{run_id}@example.com',
        'password': 'TestPass123!',
    }

@pytest.fixture(scope='session')
def test_student(run_id):
    return {
        'name':       f'Ada Lovelace {run_id}',
        'email':      f'ada_{run_id}@example.com',
        'department': 'Computer Science',
        'semester':   '5',
        'cgpa':       '3.85',
    }

@pytest.fixture(scope='session')
def driver():
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--no-zygote')          # required for Docker/ARM64
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('--disable-extensions')
    opts.add_argument('--disable-software-rasterizer')

    chrome_bin = os.environ.get('CHROME_BIN')
    if chrome_bin:
        opts.binary_location = chrome_bin

    chromedriver_bin = os.environ.get('CHROMEDRIVER_BIN')
    svc = Service(chromedriver_bin) if chromedriver_bin else Service()

    drv = webdriver.Chrome(service=svc, options=opts)
    drv.implicitly_wait(10)
    drv.set_page_load_timeout(30)
    yield drv
    drv.quit()

def pytest_collection_modifyitems(items):
    items.sort(key=lambda item: item.name)
