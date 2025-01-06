from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pathlib import Path
from colorama import Fore, Style
import time
import os

user = os.getenv("USER_SSO")
password = os.getenv("PASSWORD_SSO")
rancher_url = os.getenv("rancher_url")
vault_url = os.getenv("vault_url")
flux_url = os.getenv("flux_url")
harbor_url = os.getenv("harbor_url")
neuvector_url = os.getenv("neuvector_url")
grafana_url = os.getenv("grafana_url")
gitea_url = os.getenv("gitea_url")
mgmt_only = os.getenv("ONLY_DEPLOY_MGMT")
workload_name = os.getenv("WORKLOAD_CLUSTER_NAME")
download_dir = os.getenv("PWD")
screenshots_dir = os.getenv("SCREENSHOTS")

options = FirefoxOptions()
options.set_preference("browser.download.dir", download_dir)
options.set_preference("browser.download.folderList", 2)
options.set_preference("browser.download.manager.useWindow", False)
options.add_argument("-headless")


def login_to_sso(browser, username, password, delay):
    try:
        element_present = EC.presence_of_element_located((By.ID, "username"))
        WebDriverWait(browser, delay).until(element_present)
    except TimeoutException:
        print("Cannot access SSO Sign In page")
        browser.save_screenshot(screenshots_dir + '/login_to_sso.png')
        return None
    print(browser.title)
    print(browser.current_url)
    browser.find_element(By.ID, "username").send_keys(username)
    browser.find_element(By.ID, "password").send_keys(password)
    browser.find_element(By.ID, "kc-login").click()
    print(browser.current_url)


def rancher_sso(endpoint, username, password, workload_name):
    print("--------------------------------")
    print("Checking SSO auth Rancher")
    browser = webdriver.Firefox(options=options)
    url = "https://" + endpoint
    browser.get(url)
    time.sleep(15)
    print(browser.current_url)
    print(browser.title)
    browser.implicitly_wait(10)
    delay = 30
    try:
        element_present = EC.presence_of_element_located(
            (By.XPATH, '//button[@class="btn bg-primary"]')
        )
        WebDriverWait(browser, delay).until(element_present)
    except TimeoutException:
        print("Cannot access SSO option")
        browser.save_screenshot(screenshots_dir + '/rancher-mgmt.png')
        return None
    browser.find_element(By.XPATH, '//button[@class="btn bg-primary"]').click()
    print("Redirect to SSO")
    login_to_sso(browser, username, password, delay)
    retry = 0
    while retry < 7:
        try:
            retry += 1
            local_cluster = browser.find_element(By.LINK_TEXT, "local").is_displayed()
            print(local_cluster)
            if local_cluster is True:
                break
            else:
                print(
                    "didn't find local cluster link text yet (but no was exception raised), retrying..."
                    + str(retry)
                )
        except Exception:
            print("didn't find local cluster link text yet, retrying..." + str(retry))
            actual_url = browser.current_url
            if "login?err" in actual_url:
                print("An error occurs during SSO auth:" + actual_url)
                break
            else:
                browser.get(actual_url)
    print("Waiting to be redirect towards rancher UI home page")
    try:
        mgmt_present = EC.presence_of_element_located(
            (By.XPATH, '//a[@href="/dashboard/c/local/explorer"]')
        )
        WebDriverWait(browser, delay).until(mgmt_present)
        mgmt_clickable = EC.element_to_be_clickable(
            (By.XPATH, '//a[@href="/dashboard/c/local/explorer"]')
        )
        WebDriverWait(browser, delay).until(mgmt_clickable)
    except TimeoutException:
        print("Cannot access the Rancher UI")
        browser.save_screenshot(screenshots_dir + '/rancher-mgmt.png')
        return None
    print("Redirect to rancher UI home page")
    print(browser.current_url)
    if mgmt_only == "TRUE":
        print("No workload cluster present on this configuration")
        print(Fore.GREEN + "Rancher SSO check done")
        print(Style.RESET_ALL)
        browser.delete_all_cookies()
        browser.quit()
        return True
    else:
        cluster = workload_name + "-capi"
        try:
            workload_present = EC.presence_of_element_located((By.LINK_TEXT, cluster))
            WebDriverWait(browser, delay).until(workload_present)
            workload_clickable = EC.element_to_be_clickable((By.LINK_TEXT, cluster))
            WebDriverWait(browser, delay).until(workload_clickable)
        except TimeoutException:
            print("Cannot access workload cluster in Rancher UI")
            browser.save_screenshot(screenshots_dir + '/rancher-' + workload_name + '.png')
            return None
        print("Switch to workload cluster " + workload_name)
        browser.find_element(By.LINK_TEXT, cluster).click()
        time.sleep(15)
        print(browser.current_url)
        print("Getting kubeconfig for " + workload_name)
        browser.find_elements(
            By.XPATH, '//button[@data-testid="btn-download-kubeconfig"]'
        )[0].click()
        rancher_config = workload_name + "-rancher" + ".yaml"
        file = cluster + ".yaml"
        while not os.path.exists(file):
            print("Waiting until kubeconfig is successfully downloaded")
            time.sleep(5)
        os.rename(file, rancher_config)
        print("Check if the kubeconfig has been downloaded")
        path_to_file = rancher_config
        path = Path(path_to_file)
        if path.is_file():
            print("The kubeconfig exists")
        else:
            print("The kubeconfig does not exist")
        print(Fore.GREEN + "Rancher SSO check done")
        print(Style.RESET_ALL)
        browser.delete_all_cookies()
        browser.quit()
        return True


def vault_sso(endpoint, username, password):
    print("--------------------------------")
    print("Checking SSO auth Vault")
    browser = webdriver.Firefox(options=options)
    url = "https://" + endpoint
    browser.get(url)
    print(browser.current_url)
    print(browser.title)
    browser.implicitly_wait(10)
    browser.find_element(
        By.XPATH, '//select[@id="select-ember36"]/option[text()="OIDC"]'
    ).click()
    browser.find_element(By.ID, "role").send_keys(username)
    browser.find_element(By.ID, "auth-submit").click()
    browser.find_element(By.XPATH, '//button[@id="auth-submit"]').click()
    browser.implicitly_wait(20)
    time.sleep(25)
    print(browser.current_url)
    windows = browser.window_handles
    vault = windows[0]
    sso = windows[1]
    print("Redirect to SSO")
    delay = 30
    browser.switch_to.window(sso)
    login_to_sso(browser, username, password, delay)
    print("Waiting to be redirect towards vault UI home page")
    time.sleep(10)
    print("Redirect to vault UI home")
    browser.switch_to.window(vault)
    try:
        element_present = EC.presence_of_element_located((By.ID, "ember70"))
        WebDriverWait(browser, delay).until(element_present)
        print(browser.current_url)
        print(Fore.GREEN + "Vault SSO check done")
        print(Style.RESET_ALL)
    except TimeoutException:
        print("Cannot access the Vault UI")
        browser.save_screenshot(screenshots_dir + '/vault.png')
        return None
    browser.delete_all_cookies()
    browser.quit()
    return True


def flux_sso(endpoint, username, password):
    print("--------------------------------")
    print("Checking SSO auth Flux")
    browser = webdriver.Firefox(options=options)
    url = "https://" + endpoint
    browser.get(url)
    print(browser.current_url)
    print(browser.title)
    browser.implicitly_wait(10)
    delay = 40
    try:
        element_present = EC.presence_of_element_located(
            (By.XPATH, '//span[@class="MuiButton-label"]')
        )
        WebDriverWait(browser, delay).until(element_present)
    except TimeoutException:
        print("Cannot access SSO option")
        browser.save_screenshot(screenshots_dir + '/flux.png')
        return None
    # force to retry
    retry = 0
    while retry < 25:
        try:
            browser.find_element(By.XPATH, '//span[@class="MuiButton-label"]').click()
            if browser.title == "Sign in to Sylva":
                break
            retry += 1
        except Exception:
            browser.get(url)
    print("Redirect to SSO")
    login_to_sso(browser, username, password, delay)
    print(browser.current_url)
    print("Waiting to be redirect towards flux UI home page")
    time.sleep(25)
    print("Redirect to flux UI home page")
    try:
        element_present = EC.presence_of_element_located(
            (By.XPATH, '//a[@href="/applications"]')
        )
        WebDriverWait(browser, delay).until(element_present)
        print(browser.current_url)
        print(Fore.GREEN + "Flux SSO check done")
        print(Style.RESET_ALL)
    except TimeoutException:
        print("Cannot access the Flux UI")
        browser.save_screenshot(screenshots_dir + '/flux.png')
        return None
    browser.delete_all_cookies()
    browser.quit()
    return True


def neuvector_sso(endpoint, username, password):
    if not endpoint:
        print("-----------------------------------------------")
        print("Neuvector is not defined in this configuration")
        return True
    else:
        print("--------------------------------")
        browser = webdriver.Firefox(options=options)
        url = "https://" + endpoint
        browser.get(url)
        print(browser.current_url)
        print(browser.title)
        time.sleep(40)
        browser.implicitly_wait(10)
        delay = 30  # seconds
        try:
            print("Agree to the End User License Agreement on first login")
            element_present = EC.presence_of_element_located(
                (By.XPATH, '//mat-checkbox[@id="mat-checkbox-1"]')
            )
            WebDriverWait(browser, delay).until(element_present)
            browser.find_element(
                By.XPATH, '//mat-checkbox[@id="mat-checkbox-1"]'
            ).click()
        except TimeoutException:
            print("Not first login continue to SSO")
        try:
            element_present = EC.presence_of_element_located(
                (By.XPATH, '//button[normalize-space()="Login with OpenID"]')
            )
            WebDriverWait(browser, delay).until(element_present)
        except TimeoutException:
            print("Cannot access SSO option")
            browser.save_screenshot(screenshots_dir + '/neuvector.png')
            return None
        browser.find_element(
            By.XPATH, '//button[normalize-space()="Login with OpenID"]'
        ).click()
        print("Redirect to SSO")
        login_to_sso(browser, username, password, delay)
        print("Waiting to be redirect toward neuvector UI home page")
        time.sleep(50)
        print("Redirected to neuvector home page")
        delay = 25  # seconds
        try:
            element_present = EC.presence_of_element_located(
                (By.XPATH, '//a[@href="#/dashboard"]')
            )
            WebDriverWait(browser, delay).until(element_present)
            print(browser.current_url)
            print(Fore.GREEN + "Neuvector SSO check done")
            print(Style.RESET_ALL)
        except TimeoutException:
            print("Cannot access the Neuvector UI")
            browser.save_screenshot(screenshots_dir + '/neuvector.png')
            return None
        browser.delete_all_cookies()
        browser.quit()
        return True


def harbor_sso(endpoint, username, password):
    if not endpoint:
        print("---------------------------------------------")
        print("Harbor is not defined in this configuration")
        return True
    else:
        print("--------------------------------")
        print("Checking SSO auth Harbor")
        browser = webdriver.Firefox(options=options)
        url = "https://" + endpoint
        browser.get(url)
        print(browser.current_url)
        print(browser.title)
        browser.implicitly_wait(10)
        delay = 30
        try:
            element_present = EC.presence_of_element_located(
                (By.XPATH, '//button[@id="log_oidc"]')
            )
            WebDriverWait(browser, delay).until(element_present)
        except TimeoutException:
            print("Cannot access SSO option")
            browser.save_screenshot(screenshots_dir + '/harbor.png')
            return None
        browser.find_element(By.XPATH, '//button[@id="log_oidc"]').click()
        print("Redirect to SSO")
        login_to_sso(browser, username, password, delay)
        print("Waiting to be redirect towards harbor UI home page")
        time.sleep(25)
        print("Redirect to harbor UI home page")
        try:
            element_present = EC.presence_of_element_located(
                (By.XPATH, '//a[@href="/harbor/registries"]')
            )
            WebDriverWait(browser, delay).until(element_present)
            print(browser.current_url)
            print(Fore.GREEN + "Harbor SSO check done")
            print(Style.RESET_ALL)
        except TimeoutException:
            print("Cannot access the Harbor UI")
            browser.save_screenshot(screenshots_dir + '/harbor.png')
            return None
        browser.delete_all_cookies()
        browser.quit()
        return True


def grafana_sso(endpoint, username, password):
    if not endpoint:
        print("--------------------------------------------")
        print("Grafana is not defined in this configuration")
        return True
    else:
        print("--------------------------------")
        print("Checking SSO auth Grafana")
        browser = webdriver.Firefox(options=options)
        url = "https://" + endpoint
        browser.get(url)
        print(browser.current_url)
        print(browser.title)
        browser.implicitly_wait(10)
        delay = 30
        try:
            element_present = EC.presence_of_element_located(
                (By.XPATH, '//a[@href="login/generic_oauth"]')
            )
            WebDriverWait(browser, delay).until(element_present)
        except TimeoutException:
            print("Cannot access SSO option")
            browser.save_screenshot(screenshots_dir + '/grafana.png')
            return None
        browser.find_element(By.XPATH, '//a[@href="login/generic_oauth"]').click()
        print("Redirect to SSO")
        login_to_sso(browser, username, password, delay)
        print("Waiting to be redirect towards grafana UI home page")
        time.sleep(25)
        print("Redirect to grafana UI home page")
        try:
            print(browser.title)
            print(browser.current_url)
            print("Accessing dashboards")
            element_clickable = EC.element_to_be_clickable((By.XPATH, '//button[@id="mega-menu-toggle"]'))
            WebDriverWait(browser, delay).until(element_clickable)
            browser.find_element(By.XPATH, '//button[@id="mega-menu-toggle"]').click()
            element_clickable = EC.element_to_be_clickable((By.XPATH, '//a[@href="/dashboards"]'))
            WebDriverWait(browser, delay).until(element_clickable)
            browser.find_element(By.XPATH, '//a[@href="/dashboards"]').click()
            print(browser.title)
            print(browser.current_url)
            print(Fore.GREEN + "Grafana SSO check done")
            print(Style.RESET_ALL)
        except TimeoutException:
            print("Cannot access the Grafana UI")
            browser.save_screenshot(screenshots_dir + '/grafana.png')
            return None
        finally:
            browser.delete_all_cookies()
            browser.quit()
        return True


def gitea_sso(endpoint, username, password):
    if not endpoint:
        print("---------------------------------------------")
        print("Gitea is not defined in this configuration")
        return True
    else:
        print("--------------------------------")
        print("Checking SSO auth Gitea")
        browser = webdriver.Firefox(options=options)
        url = "https://" + endpoint
        browser.get(url)
        print(browser.current_url)
        print(browser.title)
        browser.implicitly_wait(10)
        delay = 30
        try:
            element_present = EC.presence_of_element_located(
                (By.XPATH, '//a[@rel="nofollow"]')
            )
            WebDriverWait(browser, delay).until(element_present)
        except TimeoutException:
            print("Cannot access SignIn option")
            browser.save_screenshot(screenshots_dir + '/gitea.png')
            return None
        browser.find_element(By.XPATH, '//a[@rel="nofollow"]').click()
        print(browser.title)
        try:
            element_present = EC.presence_of_element_located(
                (By.XPATH, '//a[@href="/user/oauth2/keycloak-sylva"]')
            )
            WebDriverWait(browser, delay).until(element_present)
        except TimeoutException:
            print("Cannot access SSO option")
            browser.save_screenshot(screenshots_dir + '/gitea.png')
            return None
        browser.find_element(
            By.XPATH, '//a[@href="/user/oauth2/keycloak-sylva"]'
        ).click()
        login_to_sso(browser, username, password, delay)
        print("Waiting to be redirect towards gitea UI home page")
        time.sleep(20)
        print("Redirect to gitea UI home page")
        try:
            element_present = EC.presence_of_element_located(
                (By.XPATH, '//button[@class="ui green button"]')
            )
            WebDriverWait(browser, delay).until(element_present)
            print("Complete account on first login")
            browser.find_element(By.XPATH, '//button[@class="ui green button"]').click()
        except Exception:
            print("Not first Login")
        try:
            element_present = EC.presence_of_element_located(
                (By.XPATH, '//a[@class="item active"]')
            )
            WebDriverWait(browser, delay).until(element_present)
            print(browser.title)
            print(Fore.GREEN + "Gitea SSO check done")
            print(Style.RESET_ALL)
        except TimeoutException:
            print("Cannot access the Gitea UI")
            browser.save_screenshot(screenshots_dir + '/gitea.png')
            return None
        browser.delete_all_cookies()
        browser.quit()
        return True


all_tests = 0
passed_tests = 0
retry = 0

# dict with keys app name and value 1 for OK/passed and 0 for KO/failed, initial value 0
test = {}

env_vars = os.environ
for key, value in env_vars.items():
    if key.endswith("_url"):
        test[key.split("_")[0]] = 0
        all_tests += 1

# a function is True when the sso test passed
if rancher_sso(rancher_url, user, password, workload_name):
    test["rancher"] = 1
    passed_tests += 1

if vault_sso(vault_url, user, password):
    test["vault"] = 1
    passed_tests += 1

if flux_sso(flux_url, user, password):
    test["flux"] = 1
    passed_tests += 1

if neuvector_sso(neuvector_url, user, password):
    test["neuvector"] = 1
    passed_tests += 1

if harbor_sso(harbor_url, user, password):
    test["harbor"] = 1
    passed_tests += 1

if grafana_sso(grafana_url, user, password):
    test["grafana"] = 1
    passed_tests += 1

if gitea_sso(gitea_url, user, password):
    test["gitea"] = 1
    passed_tests += 1

while all_tests > passed_tests:
    if test["rancher"] != 1:
        if rancher_sso(rancher_url, user, password, workload_name):
            test["rancher"] = 1
            passed_tests += 1
        else:
            retry += 1

    if test["vault"] != 1:
        if vault_sso(vault_url, user, password):
            test["vault"] = 1
            passed_tests += 1
        else:
            retry += 1

    if test["flux"] != 1:
        if flux_sso(flux_url, user, password):
            test["flux"] = 1
            passed_tests += 1
        else:
            retry += 1

    if test["neuvector"] != 1:
        if neuvector_sso(neuvector_url, user, password):
            test["neuvector"] = 1
            passed_tests += 1
        else:
            retry += 1

    if test["harbor"] != 1:
        if harbor_sso(harbor_url, user, password):
            test["harbor"] = 1
            passed_tests += 1
        else:
            retry += 1

    if test["grafana"] != 1:
        if grafana_sso(grafana_url, user, password):
            test["grafana"] = 1
            passed_tests += 1
        else:
            retry += 1

    if test["gitea"] != 1:
        if gitea_sso(gitea_url, user, password):
            test["gitea"] = 1
            passed_tests += 1
        else:
            retry += 1
    if retry > 20:
        print("The maximum number of retries was reached")
        exit(1)
