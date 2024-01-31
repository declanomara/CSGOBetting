import time
import random
import json

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import json
from json.decoder import JSONDecodeError


# Constants
STEAM_BASE_URL = "https://steamcommunity.com"
LOGIN_REDIRECT_URL = "https://steamcommunity.com/openid/login?openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&openid.mode=checkid_setup&openid.return_to=https%3A%2F%2Fdota2.net%2Flogin%2Findex.php%3Fgetmid%3Dcsgolounge%26login%3D1&openid.realm=https%3A%2F%2Fdota2.net&openid.ns.sreg=http%3A%2F%2Fopenid.net%2Fextensions%2Fsreg%2F1.1&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select"
LOGIN_URL = "https://csgolounge.com/login/"
LOUNGE_URL = "https://csgolounge.com/"
STEAM_LOGIN_BUTTON_ID = "imageLogin"


class CSGOLoungeAuth:
    def __init__(self, steam_cookies_path="cookies.json", save_file=None, headless=True):
        self.steam_timeout = 10

        self._headless = headless
        self._driver = self._setup_driver()
        self._lounge_session = None
        self._steam_cookies_path = steam_cookies_path
        self._save_file = save_file

        if self._save_file is not None:
            try:
                with open(save_file, "r") as f:
                    try:
                        self._lounge_session = json.load(f)
                    except JSONDecodeError as e:
                        print(f"Error decoding JSON: {e}")
            except FileNotFoundError:
                pass

    def _setup_driver(self):
        # Set up chrome webdriver
        chrome_options = webdriver.ChromeOptions()
        if self._headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--window-size=1280,720")
            chrome_options.add_argument("--disable-gpu")

        return webdriver.Chrome(options=chrome_options)
    
    def _login_to_csgolounge(self):
        # Load Steam home page before injecting Steam cookies
        self._driver.get(STEAM_BASE_URL)

        print("Loading cookies...")
        # Load cookies from file
        with open(self._steam_cookies_path, "r") as f:
            cookies = json.load(f)

        print("Injecting cookies...")
        # Add cookies to driver
        for cookie in cookies:
            self._driver.add_cookie(cookie)

        print("Redirecting to login...")
        self._driver.get(LOGIN_REDIRECT_URL)

        # Wait for the login button to appear
        WebDriverWait(self._driver, self.steam_timeout).until(
            expected_conditions.element_to_be_clickable((By.ID, STEAM_LOGIN_BUTTON_ID))
        )

        # Wait a random amount of time before clicking the login button
        time.sleep(random.randint(1, 6) / 2)

        print("Clicking login button")
        # Click the login button
        self._driver.find_element(By.ID, STEAM_LOGIN_BUTTON_ID).click()

        # Wait for the login to complete
        # TODO: Wait for the login to complete instead of sleeping
        time.sleep(5)

        # Redirect to lounge login endpoint (sometimes this is unnecessary)
        self._driver.get(LOGIN_URL)

    def _get_lounge_session_token(self):
        # Token is stored as javascript variable GetSessionToken
        if self._driver.current_url != LOUNGE_URL:
            self._driver.get(LOUNGE_URL)

        token = self._driver.execute_script("return GetSessionToken")
        return token
    
    def _get_lounge_session_cookie(self):
        if not self._driver.current_url.startswith(LOUNGE_URL):
            print(f"Driver url: {self._driver.current_url} \n redirecting to {LOUNGE_URL}")
            self._driver.get(LOUNGE_URL)

        return {"PHPSESSID": self._driver.get_cookie("PHPSESSID")["value"]}
    
    def _get_lounge_session(self):
        lounge_session = {
            "cookie": self._get_lounge_session_cookie(),
            "token": self._get_lounge_session_token()
        }

        return lounge_session

    def _authenticate(self):
        # Make sure we have a driver
        if self._driver is None:
            self._driver = self._setup_driver()
        
        # Login to csgolounge
        self._login_to_csgolounge()

        # Get session cookie and token
        self._lounge_session = self._get_lounge_session()

        # Save cookies for next time
        self._driver.get(STEAM_BASE_URL)
        cookies = self._driver.get_cookies()
        with open(self._steam_cookies_path, "w+") as f:
            json.dump(cookies, f)

        self._driver.quit()
        self._driver = None

    def reauthenticate(self):
        try:
            self._authenticate()
        except Exception as e:
            self._driver.save_screenshot("error.png")
            raise e
        
        if self._save_file is not None:
            with open(self._save_file, "w+") as f:
                json.dump(self._lounge_session, f)

    def get_session(self):
        if self._lounge_session is None:
            self.reauthenticate()

        return self._lounge_session
    
if __name__ == "__main__":
    auth = CSGOLoungeAuth(steam_cookies_path="/Users/declan/Documents/Programs/CSGOBetting/notebooks/cookies.json",
                           save_file="authentication.json",
                           headless=True)
    
    print(auth.get_session())


# def authenticate():
#     driver = setup_driver()

#     try:
#         # Login to csgolounge
#         print("Logging in...", end="")
#         login_to_csgolounge(driver)
#         print("Done")

#         # Get session cookie and token
#         print("Getting session...", end="")
#         lounge_session = get_lounge_session(driver)
#         print(lounge_session)

#         # Save cookies for next time
#         driver.get(STEAM_BASE_URL)
#         cookies = driver.get_cookies()
#         with open("cookies.json", "w+") as f:
#             json.dump(cookies, f)

#         driver.quit()
#     except Exception as e:
#         driver.save_screenshot("error.png")
#         driver.quit()
#         raise e
    
#     return lounge_session

