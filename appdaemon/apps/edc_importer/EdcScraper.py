import platform
import subprocess
from datetime import datetime as dt
import os,glob
import shutil
import time
from datetime import datetime as dt
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import calendar
import logging
from pathlib import Path
from Colors import Colors


class EdcScraper:
    
    username = 'undefined'
    password = 'undefined'
    downloadDirectory = 'undefined'
    browserExecutable = 'undefined'
    exportGroup = 'undefined'
    exportedFile = "automatic-export" 
    
    def __init__(self, browserExecutable, username, password, exportGroup, downloadDirectory):
        self.browserExecutable = browserExecutable
        self.username = username
        self.password = password
        self.exportGroup = exportGroup
        self.downloadDirectory = downloadDirectory
        
        os.makedirs(self.downloadDirectory, exist_ok=True)
        os.makedirs(self.downloadDirectory + "/debug", exist_ok=True)
        print(dt.now().strftime("%Y-%m-%d %H:%M:%S") + ": EDC Initialized")
        
    
    def printInstalledModules(self):
        print("\nInstalled Python Modules:")
        result = subprocess.run(['pip', 'list'], stdout=subprocess.PIPE, text=True)
        print(result.stdout)
    
    def getChromedriverVersion(self):
        try:
            result = subprocess.run(['chromedriver', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                version_info = result.stdout.strip()
                print(f"ChromeDriver Version: {version_info}")
            else:
                print(f"Error: {result.stderr.strip()}")
        except FileNotFoundError:
            print("ChromeDriver is not installed or not found in the system PATH.")
    
    def scrapeData(self, month, year):
        scrapeStartTime = dt.now()
        print(dt.now().strftime("%Y-%m-%d %H:%M:%S") + f": {Colors.CYAN}********************* Scraping EDC data  *********************{Colors.RESET}")
        self.cleanUpDirectory(self.downloadDirectory+"/")
        self.cleanUpDirectory(self.downloadDirectory+"/debug/")
        driver = self.initializeChromeDriver()
        try:
            self.loadMainPage(driver)
            self.login(driver)
            self.exportMonth(driver, month, year)
            downloadedFile = self.downloadExport(driver)
            return Path(downloadedFile)
        except Exception as e:
            print(dt.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + f"{Colors.RED}ERROR: Unable to scrape data - exiting {e} {Colors.RESET}")
            raise Exception("Unable to scrape EDC data")
        finally:
            self.logout(driver)
            scrapeEndTime = dt.now()
            scrapoeDuration = scrapeEndTime - scrapeStartTime
            print(dt.now().strftime("%Y-%m-%d %H:%M:%S") + f": {Colors.CYAN}********************* Finished in {scrapoeDuration} *********************{Colors.RESET}")
        
    def initializeChromeDriver(self):
        chrome_options = Options()
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": self.downloadDirectory,  # Set download folder
            "download.prompt_for_download": False,          # Disable download prompt
            "download.directory_upgrade": True,             # Manage download directory
            "plugins.always_open_pdf_externally": False      # Automatically open PDFs
        })
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument("--log-level=3")  # Disable logging
        #load service
        service = Service(self.browserExecutable)#load service
        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print(dt.now().strftime("%Y-%m-%d %H:%M:%S") + ": Driver Loaded")
        except:
            print(dt.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + f"{Colors.RED}ERROR: Unable to initialize Chrome Driver - exitting{Colors.RESET}")
            raise Exception("Unable to initialize Chrome Driver - exitting")
        # Open a website
        driver.set_window_size(1920, 1080)
        return driver

    def loadMainPage(self, driver):
        try:
            driver.get("https://portal.edc-cr.cz/")  # Change to the website's login page
            print(dt.now().strftime("%Y-%m-%d %H:%M:%S") + ": EDC Website loaded")
        except:
            print(dt.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + f"{Colors.RED}ERROR: Unable to load website - exitting{Colors.RESET}")
            raise Exception("Unable to open website - exitting")
        time.sleep(2)  # Allow time for the page to load
        
    def login(self, driver):
        print(dt.now().strftime("%Y-%m-%d %H:%M:%S") + ": Loding login page")
        try:
            loginLink = driver.find_element(By.XPATH, "//div[contains(@class, 'MuiBox-root')]//button[contains(text(), 'Přihlášení')]")
            loginLink.click()
            time.sleep(3)  # Allow time for the page to load
                       
            username_field = driver.find_element(By.XPATH, "//input[@id='email']")
            password_field = driver.find_element(By.XPATH, "//input[@id='password']")
            loginButton = driver.find_element(By.XPATH, "//button[@id='kc-login']")
            # Enter login credentials and click the button
            username_field.send_keys(self.username)
            password_field.send_keys(self.password)
            # Wait until the login button is clickable
            wait = WebDriverWait(driver, 10)  # 10-second timeout
            loginButton = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@id='kc-login']")))
            
            self.createScreenshot(driver, "login")
            loginButton.click()
            time.sleep(2)
            self.createScreenshot(driver, "logged")
        except:
            print(dt.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + f"{Colors.RED}ERROR: Failed to enter login details or find and click the login button{Colors.RESET}")
            raise Exception("Failed to find or click the login button")
        # Allow time for login processing
        time.sleep(2)
        
    def exportMonth(self, driver, month=dt.now().month, year=dt.now().year):
        print(dt.now().strftime("%Y-%m-%d %H:%M:%S") + f": Exporting data {year}/{month}")
        lastDay = calendar.monthrange(year, month)[1]
        try:
            driver.get("https://portal.edc-cr.cz/sprava-dat/zobrazeni-dat")
            time.sleep(2)
            self.createScreenshot(driver, "export_page")
            self.clickOnElement(driver, "//label[@title='Výběr dat pro skupinu sdílení.']")
            time.sleep(3)
            self.createScreenshot(driver, "export_group")
            
            self.clickOnElement(driver, "//span[normalize-space()='Vyberte']/..")
            self.clickOnElement(driver, f"//li[@role='option' and text() = '{self.exportGroup}']")
            exportTypeXpath = "//span[normalize-space()='Denní hodnoty']"
            if (self.useMonthExport(month)):
                exportTypeXpath = "//span[normalize-space()='Měsíční hodnoty']"
                
            self.clickOnElement(driver, exportTypeXpath)
            fromField = driver.find_element(By.XPATH, "//input[@name='dateFrom']")
            toField = driver.find_element(By.XPATH, "//input[@name='dateTo']")
            #fromField.clear()
            #toField.clear()
            fromField.click()
            fromField.send_keys(Keys.ARROW_LEFT*5)
            fromField.send_keys("01")
            fromField.send_keys(f"{month}")
            fromField.send_keys(f"{year}")
            
            toField.click()
            toField.send_keys(Keys.ARROW_LEFT*5)
            toField.send_keys(f"{lastDay}")
            toField.send_keys(f"{month}")
            toField.send_keys(f"{year}")
            self.createScreenshot(driver, "export_data")
            self.clickOnElement(driver, "//button[normalize-space()='Export']")
            self.createScreenshot(driver, "export_confirm")
            fileNameField = driver.find_element(By.XPATH, "//input[@id='fileName']")
            fileNameField.clear()
            fileNameField.send_keys(self.exportedFile)
            #confirm export dialog
            self.clickOnElement(driver, "//button[normalize-space()='Exportovat']")
            time.sleep(10) # wait for export
            #go to reports
            self.createScreenshot(driver, "report_dialog")
            self.clickOnElement(driver, "//button[normalize-space()='Přejít na reporty']")
        except:
            print(dt.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + f"{Colors.RED}ERROR: Failed to export data{Colors.RESET}")
            logging.exception("Failed")
            raise Exception("Failed to export data")
        # Allow time for login processing
        time.sleep(5)
        
    def useMonthExport(self, month)-> bool:
        now = dt.now()
        if (((now.month -1) == month) and (now.day <= 5)) or (month == now.month):
            #there is 5 days period to adjust month data
            return False
        return True

    def downloadExport(self, driver):
        self.clickOnElement(driver, "//table[contains(@class,'MuiTable-root')]//tr[1]//p[text()='Stáhnout']")
        
        files = glob.glob(self.downloadDirectory + '/*')
        maxFile = max(files, key=os.path.getctime)
        path = Path(maxFile)
        newPath = path.rename(Path(path.parent, f"{self.exportedFile}.csv"))
        return newPath

    def clickOnElement(self, driver, xpath):
        print(f"   :clicking on xpath[{xpath}]")
        link = driver.find_element(By.XPATH, xpath)
        link.click()
        time.sleep(1)
        

    def logout(self, driver, failInError=False):
        print(dt.now().strftime("%Y-%m-%d %H:%M:%S") + f": Logging out")
        try:
            #self.loadMainPage(driver) #just in case reload the app
            menuLink = driver.find_element(By.XPATH, "//button[@title='Menu']")
            self.createScreenshot(driver, "before_logout")
            menuLink.click()
            time.sleep(1)
            
            logoutLink = driver.find_element(By.XPATH, "//p[contains(text(), 'Odhlásit')]")
            logoutLink.click()
            time.sleep(1)
            self.createScreenshot(driver, "after_logout")
        except:
            if (failInError == False):
                self.logout(driver, True)
                
    def createScreenshot(self, driver, page):
        body = driver.find_element(By.TAG_NAME, 'body')
        body.screenshot(self.downloadDirectory+f"/debug/{page}.png")
            
    def cleanUpDirectory(self, folderPath):
        print(f"Clean-up directory {folderPath}")
        for filename in os.listdir(folderPath):
            file_path = os.path.join(folderPath, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # Removes each file.
                #elif os.path.isdir(file_path):
                    #shutil.rmtree(file_path)  # Removes directories and their contents recursively.
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")




