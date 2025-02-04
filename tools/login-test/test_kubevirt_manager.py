import os
import pytest
from playwright.sync_api import expect


@pytest.mark.skipif(not os.getenv("kubevirt_manager_url"), reason="Kubevirt Manager URL not provided", all=True)
def test_kubevirt_manager(browser, kubevirt_manager_url):
    username = os.getenv('KUBEVERT_USERNAME')
    password = os.getenv('KUBEVERT_PASSWORD')
    context = browser.new_context(
        ignore_https_errors=True, locale='en-US',
        http_credentials={"username": username, "password": password}
    )
    page = context.new_page()
    response = page.goto(kubevirt_manager_url)
    assert response.status == 200, f"Expected status 200, but got {response.status}"

    expect(page).to_have_title("kubevirt-manager")
