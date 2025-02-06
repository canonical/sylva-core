import pytest
import os
from playwright.sync_api import Page, expect


@pytest.mark.skipif(not os.getenv("thanos_url"), reason="Thanos URL not provided", all=True)
@pytest.mark.skipif(not os.getenv("thanos_user"), reason="Thanos login not provided")
@pytest.mark.skipif(not os.getenv("thanos_password"), reason="Thanos password not provided")
def test_thanos_basic_auth(page_thanos: Page, thanos_url):
    response = page_thanos.goto(thanos_url)
    assert response.status == 200, f"Expected status 200, but got {response.status}"

    page_thanos.locator("a[href=\"/stores\"]").click()

    expect(page_thanos.locator("a", has=page_thanos.get_by_text("Rules"))).to_be_attached()
    expect(page_thanos).to_have_url(thanos_url + '/stores')
