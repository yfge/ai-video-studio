import pytest


@pytest.fixture
def driver():
    """Provide Selenium WebDriver; skip if missing."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except Exception:
        pytest.skip("Selenium 未安装，跳过依赖 WebDriver 的测试")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    try:
        driver_instance = webdriver.Chrome(options=options)
    except Exception:
        pytest.skip("Chrome WebDriver 不可用，跳过相关测试")
        return

    try:
        yield driver_instance
    finally:
        driver_instance.quit()
