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
from selenium.webdriver.common.by import By


BASE_URL = os.environ.get('APP_URL', 'http://localhost:5000')
TEST_RUN_ID = str(int(time.time()))


def _reports_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')


def _failure_artifact_basename(nodeid):
    return nodeid.replace('::', '__').replace(os.sep, '_')[:220]


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
    opts.page_load_strategy = 'none'
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-setuid-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('--disable-extensions')
    opts.add_argument('--disable-background-networking')
    opts.add_argument('--disable-component-update')
    opts.add_argument('--disable-default-apps')
    opts.add_argument('--disable-features=MediaRouter,OptimizationHints,Translate')
    opts.add_argument('--disable-sync')
    opts.add_argument('--metrics-recording-only')
    opts.add_argument('--no-first-run')
    opts.add_argument('--remote-debugging-port=0')

    chrome_bin = os.environ.get('CHROME_BIN')
    if chrome_bin:
        opts.binary_location = chrome_bin

    chromedriver_bin = os.environ.get('CHROMEDRIVER_BIN')
    svc = Service(chromedriver_bin) if chromedriver_bin else Service()

    drv = webdriver.Chrome(service=svc, options=opts)
    drv.implicitly_wait(2)
    drv.set_page_load_timeout(30)
    yield drv
    drv.quit()


def pytest_collection_modifyitems(items):
    """Force tests to run in their declared order so the workflow is coherent."""
    items.sort(key=lambda item: item.name)


def pytest_sessionstart(session):
    rd = _reports_dir()
    os.makedirs(rd, exist_ok=True)
    env_path = os.path.join(rd, 'session-env.txt')
    with open(env_path, 'w', encoding='utf-8') as fh:
        fh.write(f'APP_URL={os.environ.get("APP_URL")!r}\n')
        fh.write(f'CHROME_BIN={os.environ.get("CHROME_BIN")!r}\n')
        fh.write(f'CHROMEDRIVER_BIN={os.environ.get("CHROMEDRIVER_BIN")!r}\n')
    print(f'[pytest] Wrote {env_path}', flush=True)
    print(f'[pytest] APP_URL={os.environ.get("APP_URL")!r}', flush=True)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when != 'call' or not rep.failed:
        return

    rd = _reports_dir()
    os.makedirs(rd, exist_ok=True)
    base = _failure_artifact_basename(item.nodeid)
    txt_path = os.path.join(rd, f'failure-{base}.txt')

    long_msg = getattr(rep, 'longreprtext', None) or str(getattr(rep, 'longrepr', ''))
    lines = [
        f'nodeid={item.nodeid}',
        f'APP_URL={os.environ.get("APP_URL")!r}',
        '',
        '--- pytest failure / traceback ---',
        long_msg,
        '',
    ]

    drv = getattr(item, 'funcargs', {}).get('driver')
    if drv is not None:
        lines.append('--- WebDriver ---')
        try:
            lines.append(f'current_url: {drv.current_url}')
            lines.append(f'title: {drv.title!r}')
            try:
                body_el = drv.find_element(By.TAG_NAME, 'body')
                lines.append('body[:4000]:')
                lines.append(body_el.text[:4000])
            except Exception as body_exc:
                lines.append(f'(body text unavailable: {body_exc!r})')
            try:
                src = drv.page_source
                lines.append('page_source[:12000]:')
                lines.append(src[:12000])
            except Exception as src_exc:
                lines.append(f'(page_source unavailable: {src_exc!r})')
        except Exception as drv_exc:
            lines.append(f'WebDriver snapshot error: {drv_exc!r}')
        png_path = os.path.join(rd, f'failure-{base}.png')
        try:
            drv.save_screenshot(png_path)
            lines.append('')
            lines.append(f'screenshot: {png_path}')
        except Exception as png_exc:
            lines.append(f'screenshot failed: {png_exc!r}')
    else:
        lines.append('(no driver in funcargs; skipping browser snapshot)')

    text = '\n'.join(lines)
    with open(txt_path, 'w', encoding='utf-8') as fh:
        fh.write(text)

    summary_path = os.path.join(rd, 'failures-summary.log')
    with open(summary_path, 'a', encoding='utf-8') as fh:
        fh.write('\n')
        fh.write('=' * 80)
        fh.write('\n')
        fh.write(text)
        fh.write('\n')

    print('\n=== TEST FAILURE (see artifacts under tests/reports/) ===', flush=True)
    print(f'Written: {txt_path}', flush=True)
    for preview in lines[:40]:
        print(preview, flush=True)
    if len(lines) > 40:
        print(f'... ({len(lines) - 40} more lines in {txt_path})', flush=True)
