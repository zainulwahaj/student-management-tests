"""
Shared pytest fixtures for Selenium tests.

Tests run sequentially against a single browser session (faster, and the test
sequence builds on prior steps — register a user, log in with that user,
add a student, edit it, delete it). Uses headless Chromium.
"""
import os
import time
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


BASE_URL = os.environ.get('APP_URL', 'http://localhost:5000')
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
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-extensions')

    chrome_bin = os.environ.get('CHROME_BIN')
    if chrome_bin:
        options.binary_location = chrome_bin

    chromedriver_bin = os.environ.get('CHROMEDRIVER_BIN')
    if chromedriver_bin:
        service = Service(chromedriver_bin)
    else:
        service = Service()

    drv = webdriver.Chrome(service=service, options=options)
    drv.implicitly_wait(5)
    yield drv
    drv.quit()


def pytest_collection_modifyitems(items):
    """Force tests to run in their declared order so the workflow is coherent."""
    items.sort(key=lambda item: item.name)
