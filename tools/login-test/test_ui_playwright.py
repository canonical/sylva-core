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


# Test for Kepler Dashboard reachability
@pytest.mark.skipif(os.getenv("kepler_unit_enabled") != 'true', reason="Kepler unit is not enabled", all=True)
@pytest.mark.skipif(not os.getenv("grafana_url"), reason="Grafana URL not provided", all=True)
@pytest.mark.skipif(not os.getenv("grafana_user"), reason="Grafana login not provided")
@pytest.mark.skipif(not os.getenv("grafana_password"), reason="Grafana password not provided")
def test_kepler_dashboard(page: Page, grafana_url):
    response = page.goto(grafana_url + "/dashboards")
    assert response.status == 200, f"Expected status 200, but got {response.status}"
    page.locator("input[name=\"user\"]").fill(os.getenv("grafana_user"))
    page.locator("input[name=\"password\"]").fill(os.getenv("grafana_password"))
    page.get_by_text('Log in').click()
    expect(page.get_by_role("heading", level=1)).to_have_text('Dashboards')
    page.locator('a[href*="kepler-exporter-dashboard"]').click()
    expect(page.locator('span[title="Kepler Exporter Dashboard"]')).to_be_visible()
