import unittest
from EdcScraper import EdcScraper
from datetime import datetime as dt
from pathlib import Path
import json


class TestScraper(unittest.TestCase):

    def test_checkScraper(self):
        
        configFile = Path("config.json")
        print(f"Reading config from:  {configFile.resolve()}")
        configuration = json.loads(configFile.read_text())
       
        month = dt.now().month
        month = 4
        year = 2025
        scraper = EdcScraper("c:\\Java\\chromedriver-win64\\chromedriver.exe", configuration['user'], configuration['password'], configuration['group'], "..\\data")
        result = scraper.scrapeData(month, year)
        print(f"Clean-up directory {result}")


if __name__ == '__main__':
    unittest.main()


#It's required to create a file config.json to run the test
#{
#    "user": "XXXX",
#    "password": "XXXX",
#    "group": "XXXXX"
#}