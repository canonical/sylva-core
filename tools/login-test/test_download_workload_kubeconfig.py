import os
import pytest
from playwright.sync_api import Page
from test_sso_playwright import login_to_sso


@pytest.fixture
def workload_name():
    return os.getenv("WORKLOAD_CLUSTER_NAME")


@pytest.mark.skipif(not os.getenv("WORKLOAD_CLUSTER_NAME"), reason="Workload cluster name not provided")
def test_rancher_download_workload_kubeconfig(page: Page, rancher_url, workload_name):
    response = page.goto(rancher_url)
    assert response.status == 200, f"Expected status 200, but got {response.status}"

    page.get_by_text("Log in with OIDC").click()
    login_to_sso(page)

    page.locator("a", has=page.get_by_text(f"{workload_name}")).click()

    with page.expect_download() as download_info:
        page.get_by_test_id("btn-download-kubeconfig").click()
    download = download_info.value

    download.save_as(f"{workload_name}-rancher.yaml")
