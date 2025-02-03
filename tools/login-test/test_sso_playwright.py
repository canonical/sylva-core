import os
import pytest
import base64
from playwright.sync_api import Page, expect


def login_to_sso(page: Page):
    page.locator("input[name=\"username\"]").fill(os.getenv("USER_SSO"))
    page.locator("input[name=\"password\"]").fill(os.getenv("PASSWORD_SSO"))
    page.locator("input[name=\"login\"]").click()


@pytest.mark.skipif(not os.getenv("rancher_url"), reason="Rancher URL not provided", all=True)
def test_rancher_sso(page: Page, rancher_url):
    response = page.goto(rancher_url)
    assert response.status == 200, f"Expected status 200, but got {response.status}"

    page.get_by_text("Log in with OIDC").click()
    login_to_sso(page)

    expect(page.get_by_test_id("banner-title")).to_have_text("Welcome to Rancher")

    expect(page.get_by_test_id("sortable-cell-0-0")).to_have_text("Active")


@pytest.mark.skipif(not os.getenv("vault_url"), reason="Vault URL not provided", all=True)
def test_vault_sso(page: Page, vault_url):
    response = page.goto(vault_url)
    assert response.status == 200, f"Expected status 200, but got {response.status}"

    page.locator("select[data-test-select=\"auth-method\"]").select_option('OIDC')
    page.locator("input[id=\"role\"]").fill("sylva-admin")

    page.wait_for_event("requestfinished", lambda event: event.url == f"{vault_url}/v1/auth/oidc/oidc/auth_url" and event.response().status == 200)

    with page.expect_popup() as popup_info:
        page.locator("button[id=\"auth-submit\"]").click()
    popup = popup_info.value
    login_to_sso(popup)

    expect(page.get_by_text("Secrets Engine")).to_be_visible()


@pytest.mark.skipif(not os.getenv("flux_url"), reason="Flux URL not provided", all=True)
def test_flux_sso(page: Page, flux_url):
    response = page.goto(flux_url)
    assert response.status == 200, f"Expected status 200, but got {response.status}"

    page.locator("button", has=page.get_by_text("Log in with Keycloak")).click()
    login_to_sso(page)

    expect(page.get_by_title("Applications")).to_have_text("Applications")


@pytest.mark.skipif(not os.getenv("neuvector_url"), reason="Neuvector URL not provided", all=True)
def test_neuvector_sso(page: Page, neuvector_url):
    response = page.goto(neuvector_url)
    assert response.status == 200, f"Expected status 200, but got {response.status}"

    oidc_login = page.get_by_text("Login with OpenID")

    if oidc_login.is_disabled():
        page.locator(".checkbox-wrapper") \
            .filter(has=page.get_by_text("I have read and agree")) \
            .locator("mat-checkbox").click()

    oidc_login.click()
    login_to_sso(page)

    expect(page).to_have_title("NeuVector")
    expect(page.locator("a[href=\"http://www.neuvector.com\"]")).to_have_text("NeuVector")


@pytest.mark.skipif(not os.getenv("harbor_url"), reason="Harbor URL not provided", all=True)
def test_harbor_sso(page: Page, harbor_url):
    response = page.goto(harbor_url)
    assert response.status == 200, f"Expected status 200, but got {response.status}"

    page.locator("button[id=\"log_oidc\"]").click()
    login_to_sso(page)

    expect(page.locator("a", has=page.get_by_text("Registrie"))).to_be_attached()


@pytest.mark.skipif(not os.getenv("grafana_url"), reason="Grafana URL not provided", all=True)
def test_grafana_sso(page: Page, grafana_url):
    response = page.goto(grafana_url)
    assert response.status == 200, f"Expected status 200, but got {response.status}"

    page.locator("a[href=\"login/generic_oauth\"]").click()

    login_to_sso(page)

    page.locator("button[id=\"mega-menu-toggle\"]").click()
    page.locator("a[href=\"/dashboards\"]").click()

    expect(page).to_have_title("Dashboards - Grafana")


@pytest.mark.skipif(not os.getenv("gitea_url"), reason="Gitea URL not provided", all=True)
def test_gitea_sso(page: Page, gitea_url):
    response = page.goto(gitea_url)
    assert response.status == 200, f"Expected status 200, but got {response.status}"

    page.locator("a").filter(has=page.get_by_text("Sign In")).click()

    page.locator("a").filter(has=page.get_by_text("keycloak-sylva")).click()

    login_to_sso(page)

    expect(page.get_by_text("Complete New Account")).to_be_visible()


@pytest.mark.skipif(not os.getenv("thanos_url"), reason="Thanos URL not provided", all=True)
def test_thanos_basic_auth(page: Page, thanos_url):
    thanos_user = os.getenv("thanos_user")
    thanos_password = os.getenv("thanos_password")
    auth_string = f"{thanos_user}:{thanos_password}".encode("ascii")
    base64_bytes = base64.b64encode(auth_string)
    base64_string = base64_bytes.decode("ascii")
    auth_header = f"Basic {base64_string}"
    page.set_extra_http_headers({"Authorization": auth_header})

    response = page.goto(thanos_url)
    assert response.status == 200, f"Expected status 200, but got {response.status}"
    page.locator("a[href=\"/stores\"]").click()

    expect(page.locator("a", has=page.get_by_text("Rules"))).to_be_attached()
    expect(page).to_have_url(thanos_url + '/stores')
