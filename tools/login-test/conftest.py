import pytest
import os


@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context(ignore_https_errors=True, locale='en-US')
    page = context.new_page()
    yield page
    page.close()
    context.close()


@pytest.fixture(scope="function")
def page_thanos(browser):
    thanos_user = os.getenv("thanos_user")
    thanos_password = os.getenv("thanos_password")
    context = browser.new_context(ignore_https_errors=True, locale='en-US', http_credentials={'username': thanos_user, 'password': thanos_password})
    page = context.new_page()
    yield page
    page.close()
    context.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        try:
            page = item.funcargs["page"]
            screenshot_path = f"screenshots/{item.name}.png"
            os.makedirs("screenshots", exist_ok=True)
            page.screenshot(path=screenshot_path)
        except Exception as e:
            print(f"Failed to take screenshot: {e}")


def add_scheme(url):
    if url.startswith("http"):
        return url
    return f'https://{url}'


@pytest.fixture
def rancher_url():
    return add_scheme(os.getenv("rancher_url", "https://rancher.sylva"))


@pytest.fixture
def vault_url():
    return add_scheme(os.getenv("vault_url", "https://vault.sylva"))


@pytest.fixture
def flux_url():
    return add_scheme(os.getenv("flux_url", "https://flux.sylva"))


@pytest.fixture
def harbor_url():
    return add_scheme(os.getenv("harbor_url", "https://harbor.sylva"))


@pytest.fixture
def neuvector_url():
    return add_scheme(os.getenv("neuvector_url", "https://neuvector.sylva"))


@pytest.fixture
def kubevirt_url():
    return add_scheme(os.getenv("kubevirt_url", "https://kubevirt-manager.sylva"))


@pytest.fixture
def grafana_url():
    return add_scheme(os.getenv("grafana_url", "https://grafana.sylva"))


@pytest.fixture
def gitea_url():
    return add_scheme(os.getenv("gitea_url", "https://gitea.sylva"))


@pytest.fixture
def thanos_url():
    return add_scheme(os.getenv("thanos_url", "https://thanos.sylva"))


def pytest_addoption(parser):
    parser.addoption("--all", action="store_true", default=False, help="Run all tests")


# Allow running all tests using default values provided by the preceding fixtures
#   or run only tests for which parameters are provided as environment variables
def pytest_collection_modifyitems(config, items):
    if config.getoption("--all"):
        for item in items:
            for marker in item.own_markers:
                # Remove all conditional markers which have all=True as attribute
                if marker.name == "skipif" and "all" in marker.kwargs and marker.kwargs["all"] is True:
                    item.own_markers.remove(marker)
