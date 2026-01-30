import pytest
from app.core.config import settings


@pytest.fixture
def skip_if_no_openai():
    if not getattr(settings, "OPENAI_API_KEY", None):
        pytest.skip("需要OPENAI_API_KEY环境变量")


@pytest.fixture
def skip_if_no_oss():
    required_oss_configs = [
        "ALIYUN_ACCESS_KEY_ID",
        "ALIYUN_ACCESS_KEY_SECRET",
        "ALIYUN_OSS_ENDPOINT",
        "ALIYUN_OSS_BUCKET",
    ]

    missing_configs = [
        config for config in required_oss_configs if not getattr(settings, config, None)
    ]
    if missing_configs:
        pytest.skip(f"需要OSS配置: {', '.join(missing_configs)}")


def pytest_collection_modifyitems(config, items):
    run_external = str(getattr(settings, "RUN_EXTERNAL_TESTS", "") or "").strip().lower()
    run_external_enabled = run_external in {"1", "true", "yes", "on"}
    skip_external = pytest.mark.skip(
        reason="external tests disabled (set RUN_EXTERNAL_TESTS=1 to enable)"
    )

    for item in items:
        if "test_diagnostic" in item.nodeid:
            item.add_marker(pytest.mark.diagnostic)
        if "test_openai" in item.nodeid or "openai" in item.nodeid:
            item.add_marker(pytest.mark.openai)
            item.add_marker(pytest.mark.external)
        if "test_oss" in item.nodeid or "oss" in item.nodeid:
            item.add_marker(pytest.mark.oss)
            item.add_marker(pytest.mark.external)
        if "test_database" in item.nodeid or "database" in item.nodeid:
            item.add_marker(pytest.mark.database)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        if "e2e" in item.nodeid or "end_to_end" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)

        if not run_external_enabled and "external" in item.keywords:
            item.add_marker(skip_external)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if exitstatus == 0:
        terminalreporter.write_line(
            "\n🎉 所有测试通过！AI图像生成系统运行正常。", green=True
        )
    else:
        terminalreporter.write_line("\n❌ 部分测试失败，请检查上述错误信息。", red=True)
