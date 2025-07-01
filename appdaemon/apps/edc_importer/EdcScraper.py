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
from EdcLogger import EdcLogger
import utils


class EdcScraper:
    
    username = 'undefined'
    password = 'undefined'
    downloadDirectory = 'undefined'
    browserExecutable = 'undefined'
    exportGroup = 'undefined'
    exportedFile = "automatic-export"
    uiLogger: EdcLogger = 'undefined' 
    
    def __init__(self, browserExecutable, username, password, exportGroup, downloadDirectory, logger: EdcLogger):
        self.browserExecutable = browserExecutable
        self.username = username
        self.password = password
        self.exportGroup = exportGroup
        self.downloadDirectory = downloadDirectory
        self.uiLogger = logger
        
        self.prepareDataDirectories()
        self.uiLogger.logAndPrint("EDC Scraper Initialized")
        
    def prepareDataDirectories(self):
        os.makedirs(self.downloadDirectory, exist_ok=True)
        self.cleanUpDirectory(self.downloadDirectory+"/")
        os.makedirs(self.downloadDirectory + "/debug", exist_ok=True)
        
    def printInstalledModules(self):
        self.uiLogger.print("\nInstalled Python Modules:")
        result = subprocess.run(['pip', 'list'], stdout=subprocess.PIPE, text=True)
        self.uiLogger.print(result.stdout)
    
    def getChromedriverVersion(self):
        try:
            result = subprocess.run(['chromedriver', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                version_info = result.stdout.strip()
                self.uiLogger.print(f"ChromeDriver Version: {version_info}")
            else:
                self.uiLogger.print(f"Error: {result.stderr.strip()}")
        except FileNotFoundError:
            self.uiLogger.print("ChromeDriver is not installed or not found in the system PATH.")
    
    def scrapeData(self, month, year):
        scrapeStartTime = dt.now()
        self.uiLogger.logAndPrint("********************* Scraping EDC data  *********************", Colors.CYAN)
        self.prepareDataDirectories()
        
        driver = self.initializeChromeDriver()
        try:
            self.loadMainPage(driver)
            self.login(driver)
            self.exportMonth(driver, month, year)
            downloadedFile = self.downloadExport(driver)
            return Path(downloadedFile)
        except Exception as e:
            self.uiLogger.logAndPrint(f"ERROR: Unable to scrape data - exiting {str(e)}", Colors.RED)
            raise Exception("Unable to scrape EDC data")
        finally:
            self.logout(driver)
            scrapeEndTime = dt.now()
            scrapoeDuration = scrapeEndTime - scrapeStartTime
            self.uiLogger.logAndPrint(f"********************* Finished in {scrapoeDuration} *********************", Colors.CYAN)
        
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
            self.uiLogger.logAndPrint("Driver Loaded")
        except:
            self.uiLogger.logAndPrint(f"RROR: Unable to initialize Chrome Driver - exitting", Colors.RED)
            raise Exception("Unable to initialize Chrome Driver - exitting")
        # Open a website
        driver.set_window_size(1920, 1080)
        return driver

    def loadMainPage(self, driver):
        try:
            driver.get("https://portal.edc-cr.cz/")  # Change to the website's login page
            self.uiLogger.logAndPrint("EDC Website loaded")
        except:
            self.uiLogger.logAndPrint(f"ERROR: Unable to load website - exitting", Colors.RED)
            raise Exception("Unable to open website - exitting")
        time.sleep(2)  # Allow time for the page to load
        
    def login(self, driver):
        self.uiLogger.logAndPrint("Loading login page")
        try:
            loginLink = driver.find_element(By.XPATH, "//div[contains(@class, 'MuiBox-root')]//button[contains(text(), 'Přihlášení')]")
            loginLink.click()
            time.sleep(3)  # Allow time for the page to load
            self.createScreenshot(driver, "pre_login")
                       
            username_field = driver.find_element(By.XPATH, "//input[@id='username']")
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
            self.uiLogger.logAndPrint(f"ERROR: Failed to enter login details or find and click the login button", Colors.RED)
            raise Exception("Failed to find or click the login button")
        # Allow time for login processing
        time.sleep(2)
        
    def exportMonth(self, driver, month=dt.now().month, year=dt.now().year):
        self.uiLogger.logAndPrint(f"Exporting data {year}/{month}")
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
            #for now use only daily since month values are crappy 
            if (self.useMonthExport(month, year)):
                exportTypeXpath = "//span[normalize-space()='Měsíční hodnoty']"
                
            self.clickOnElement(driver, exportTypeXpath)
            fromField = driver.find_element(By.XPATH, "//input[@name='dateFrom']")
            toField = driver.find_element(By.XPATH, "//input[@name='dateTo']")
            #fromField.clear()
            #toField.clear()
            fromField.click()
            fromField.send_keys(Keys.ARROW_LEFT*5)
            fromField.send_keys("01")
            fromField.send_keys(f"{month:02d}")
            fromField.send_keys(f"{year}")
            
            toField.click()
            toField.send_keys(Keys.ARROW_LEFT*5)
            toField.send_keys(f"{lastDay}")
            toField.send_keys(f"{month:02d}")
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
            self.uiLogger.logAndPrint(f"ERROR: Failed to export data", Colors.RED)
            logging.exception("Failed")
            raise Exception("Failed to export data")
        # Allow time for login processing
        time.sleep(5)
        
    def useMonthExport(self, month: int, year: int)-> bool:
        now = dt.now()
        lastMonthsInterval = utils.getLastMonths(dt.today(), 2)[::-1]
        lastMonthYear = lastMonthsInterval[0][0]
        lastMonth = lastMonthsInterval[0][1]
        #if (((now.month -1) == month) and (now.day <= 9)) or (month == now.month):
        if ((month == now.month and now.year == year) or (month == lastMonth and year == lastMonthYear and now.day <=9)):
            #there is 5 days period to adjust month data plus a Bulgarian constant
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
        self.uiLogger.logAndPrint(f"   :clicking on xpath[{xpath}]", Colors.YELLOW, False)
        link = driver.find_element(By.XPATH, xpath)
        link.click()
        time.sleep(1)
        

    def logout(self, driver, failInError=False):
        self.uiLogger.logAndPrint(f"Logging out")
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
        self.uiLogger.logAndPrint(f"Clean-up directory {folderPath}")
        for filename in os.listdir(folderPath):
            file_path = os.path.join(folderPath, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # Removes each file.
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Removes directories and their contents recursively.
            except Exception as e:
                self.uiLogger.logAndPrint(f"Failed to delete {file_path}. Reason: {e}")




