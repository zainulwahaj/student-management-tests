"""
Selenium UI tests for the Student Management System.

22 test cases covering:
  * Public page rendering & navigation
  * User registration (success, duplicate username, duplicate email,
    server-side empty-field validation)
  * Login (success, invalid credentials)
  * Authenticated dashboard
  * Student CRUD (create, list, search, edit, delete)
  * Logout & protected-route redirect

All tests run against headless Chromium.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


def navigate(driver, url, timeout=20):
    driver.get(url)
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )


# ─── Helpers ────────────────────────────────────────────────────────────────

def wait_for(driver, locator, timeout=10):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))


def wait_visible(driver, locator, timeout=10):
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))


def disable_html5_validation(driver):
    """Strip the `required` attribute so server-side validation can be tested."""
    driver.execute_script(
        "document.querySelectorAll('[required]').forEach(e => e.removeAttribute('required'));"
        "document.querySelectorAll('form').forEach(f => f.setAttribute('novalidate', ''));"
    )


def flash_text(driver, timeout=10):
    el = wait_visible(driver, (By.ID, 'flash-message'), timeout)
    return el.text


# ─── 1. Public pages ─────────────────────────────────────────────────────────

def test_01_homepage_loads_with_correct_title(driver, base_url):
    navigate(driver, base_url + '/')
    WebDriverWait(driver, 15).until(
        lambda d: 'Student Management System' in d.title
    )
    hero = wait_visible(driver, (By.ID, 'hero-title'))
    assert 'Student Management System' in hero.text


def test_02_homepage_shows_login_and_register_buttons(driver, base_url):
    navigate(driver, base_url + '/')
    assert wait_visible(driver, (By.ID, 'btn-login')).is_displayed()
    assert wait_visible(driver, (By.ID, 'btn-register')).is_displayed()


def test_03_navbar_shows_login_and_register_when_logged_out(driver, base_url):
    navigate(driver, base_url + '/')
    nav = wait_visible(driver, (By.ID, 'main-nav'))
    assert nav.find_element(By.ID, 'nav-login').is_displayed()
    assert nav.find_element(By.ID, 'nav-register').is_displayed()


def test_04_login_page_loads(driver, base_url):
    navigate(driver, base_url + '/login')
    heading = wait_visible(driver, (By.ID, 'login-heading'))
    assert heading.text in ('Login', 'Sign in')
    assert driver.find_element(By.ID, 'username').is_displayed()
    assert driver.find_element(By.ID, 'password').is_displayed()


def test_05_register_page_loads(driver, base_url):
    navigate(driver, base_url + '/register')
    heading = wait_visible(driver, (By.ID, 'register-heading'))
    assert 'Create Account' in heading.text


# ─── 2. Registration ─────────────────────────────────────────────────────────

def test_06_register_with_empty_fields_shows_server_error(driver, base_url):
    navigate(driver, base_url + '/register')
    disable_html5_validation(driver)
    driver.find_element(By.ID, 'btn-submit-register').click()
    msg = flash_text(driver)
    assert 'All fields are required' in msg


def test_07_register_new_user_succeeds(driver, base_url, test_user):
    navigate(driver, base_url + '/register')
    driver.find_element(By.ID, 'username').send_keys(test_user['username'])
    driver.find_element(By.ID, 'email').send_keys(test_user['email'])
    driver.find_element(By.ID, 'password').send_keys(test_user['password'])
    driver.find_element(By.ID, 'btn-submit-register').click()

    WebDriverWait(driver, 10).until(EC.url_contains('/login'))
    assert 'Registration successful' in flash_text(driver)


def test_08_register_duplicate_username_shows_error(driver, base_url, test_user, run_id):
    navigate(driver, base_url + '/register')
    driver.find_element(By.ID, 'username').send_keys(test_user['username'])
    driver.find_element(By.ID, 'email').send_keys(f'different_{run_id}@example.com')
    driver.find_element(By.ID, 'password').send_keys('AnotherPass1!')
    driver.find_element(By.ID, 'btn-submit-register').click()
    assert 'Username already taken' in flash_text(driver)


def test_09_register_duplicate_email_shows_error(driver, base_url, test_user, run_id):
    navigate(driver, base_url + '/register')
    driver.find_element(By.ID, 'username').send_keys(f'other_{run_id}')
    driver.find_element(By.ID, 'email').send_keys(test_user['email'])
    driver.find_element(By.ID, 'password').send_keys('AnotherPass1!')
    driver.find_element(By.ID, 'btn-submit-register').click()
    assert 'Email already registered' in flash_text(driver)


# ─── 3. Login ────────────────────────────────────────────────────────────────

def test_10_login_with_invalid_password_shows_error(driver, base_url, test_user):
    navigate(driver, base_url + '/login')
    driver.find_element(By.ID, 'username').send_keys(test_user['username'])
    driver.find_element(By.ID, 'password').send_keys('wrongpassword')
    driver.find_element(By.ID, 'btn-submit-login').click()
    assert 'Invalid username or password' in flash_text(driver)


def test_11_login_with_unknown_username_shows_error(driver, base_url):
    navigate(driver, base_url + '/login')
    driver.find_element(By.ID, 'username').send_keys('no_such_user_xyz')
    driver.find_element(By.ID, 'password').send_keys('whatever')
    driver.find_element(By.ID, 'btn-submit-login').click()
    assert 'Invalid username or password' in flash_text(driver)


def test_12_login_with_empty_fields_shows_server_error(driver, base_url):
    navigate(driver, base_url + '/login')
    disable_html5_validation(driver)
    driver.find_element(By.ID, 'btn-submit-login').click()
    msg = flash_text(driver)
    assert 'enter both username and password' in msg.lower()


def test_13_login_with_valid_credentials_redirects_to_dashboard(driver, base_url, test_user):
    navigate(driver, base_url + '/login')
    driver.find_element(By.ID, 'username').send_keys(test_user['username'])
    driver.find_element(By.ID, 'password').send_keys(test_user['password'])
    driver.find_element(By.ID, 'btn-submit-login').click()
    WebDriverWait(driver, 10).until(EC.url_contains('/dashboard'))
    heading = wait_visible(driver, (By.ID, 'dashboard-heading'))
    assert 'Dashboard' in heading.text


# ─── 4. Authenticated state ──────────────────────────────────────────────────

def test_14_navbar_shows_logout_when_authenticated(driver, base_url):
    nav = driver.find_element(By.ID, 'main-nav')
    assert nav.find_element(By.ID, 'nav-logout').is_displayed()
    assert nav.find_element(By.ID, 'nav-students').is_displayed()
    assert nav.find_element(By.ID, 'nav-add-student').is_displayed()


def test_15_navigate_to_add_student_via_navbar(driver, base_url):
    driver.find_element(By.ID, 'nav-add-student').click()
    WebDriverWait(driver, 10).until(EC.url_contains('/students/add'))
    assert wait_visible(driver, (By.ID, 'add-student-heading')).text == 'Add New Student'


# ─── 5. Student CRUD ─────────────────────────────────────────────────────────

def test_16_add_student_with_valid_data(driver, base_url, test_student):
    navigate(driver, base_url + '/students/add')
    driver.find_element(By.ID, 'name').send_keys(test_student['name'])
    driver.find_element(By.ID, 'email').send_keys(test_student['email'])
    Select(driver.find_element(By.ID, 'department')).select_by_visible_text(test_student['department'])
    driver.find_element(By.ID, 'semester').send_keys(test_student['semester'])
    driver.find_element(By.ID, 'cgpa').send_keys(test_student['cgpa'])
    driver.find_element(By.ID, 'btn-submit-student').click()

    WebDriverWait(driver, 10).until(EC.url_contains('/students'))
    assert 'Student added successfully' in flash_text(driver)


def test_17_add_student_empty_form_shows_server_error(driver, base_url):
    navigate(driver, base_url + '/students/add')
    disable_html5_validation(driver)
    driver.find_element(By.ID, 'btn-submit-student').click()
    assert 'All fields are required' in flash_text(driver)


def test_18_students_list_contains_added_student(driver, base_url, test_student):
    navigate(driver, base_url + '/students')
    table = wait_visible(driver, (By.ID, 'students-table'))
    assert test_student['name'] in table.text
    assert test_student['email'] in table.text


def test_19_search_students_by_name_finds_match(driver, base_url, test_student):
    navigate(driver, base_url + '/students')
    search = driver.find_element(By.ID, 'search-input')
    search.clear()
    search.send_keys(test_student['name'].split()[0])  # search "Ada"
    driver.find_element(By.ID, 'btn-search').click()

    wait_visible(driver, (By.ID, 'students-table'))
    # Re-query from driver (not cached table ref) to avoid stale element after page reload
    rows = driver.find_elements(By.CSS_SELECTOR, '#students-table tbody tr.student-row')
    assert len(rows) >= 1
    assert any(test_student['name'] in r.text for r in rows)


def test_20_search_with_no_match_shows_empty_message(driver, base_url):
    navigate(driver, base_url + '/students?q=zzzzz_no_match_zzzzz')
    msg = wait_visible(driver, (By.ID, 'no-students-msg'))
    assert 'No students found' in msg.text


def test_21_edit_student_updates_record(driver, base_url, test_student):
    navigate(driver, base_url + '/students')
    rows = driver.find_elements(By.CSS_SELECTOR, 'tr.student-row')
    target = next(r for r in rows if test_student['name'] in r.text)
    target.find_element(By.CSS_SELECTOR, '.btn-edit').click()

    WebDriverWait(driver, 10).until(EC.url_contains('/students/edit/'))
    cgpa = driver.find_element(By.ID, 'cgpa')
    cgpa.clear()
    cgpa.send_keys('3.95')
    driver.find_element(By.ID, 'btn-update-student').click()

    WebDriverWait(driver, 10).until(EC.url_contains('/students'))
    assert 'Student updated successfully' in flash_text(driver)
    table = wait_visible(driver, (By.ID, 'students-table'))
    assert '3.95' in table.text


def test_22_delete_student_removes_row(driver, base_url, test_student):
    navigate(driver, base_url + '/students')

    # Bypass the JS confirm() dialog so the form submits cleanly.
    driver.execute_script(
        "document.querySelectorAll('form').forEach(f => f.removeAttribute('onsubmit'));"
    )
    rows = driver.find_elements(By.CSS_SELECTOR, 'tr.student-row')
    target = next(r for r in rows if test_student['name'] in r.text)
    target.find_element(By.CSS_SELECTOR, '.btn-delete').click()

    WebDriverWait(driver, 10).until(EC.url_contains('/students'))
    assert 'Student deleted' in flash_text(driver)
    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert test_student['name'] not in body_text


# ─── 6. Logout & protected route ─────────────────────────────────────────────

def test_23_logout_clears_session_and_redirects(driver, base_url):
    navigate(driver, base_url + '/dashboard')
    driver.find_element(By.ID, 'nav-logout').click()
    WebDriverWait(driver, 10).until(EC.url_matches(r'.*/$|.*/index'))
    nav = driver.find_element(By.ID, 'main-nav')
    assert nav.find_element(By.ID, 'nav-login').is_displayed()


def test_24_protected_route_redirects_when_not_authenticated(driver, base_url):
    navigate(driver, base_url + '/dashboard')
    WebDriverWait(driver, 10).until(EC.url_contains('/login'))
    assert 'Please log in first' in flash_text(driver)
