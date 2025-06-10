import unittest
from EdcScraper import EdcScraper
from datetime import datetime as dt
from pathlib import Path
import json
from EdcLogger import EdcLogger


class TestScraper(unittest.TestCase):

    def test_checkScraper(self):
        
        configFile = Path("config.json")
        print(f"Reading config from:  {configFile.resolve()}")
        configuration = json.loads(configFile.read_text())
       
        month = dt.now().month
        month = 5
        year = 2025
        dataDirectory = str((Path.cwd() / "../data").resolve())
        logger = EdcLogger()
        scraper = EdcScraper(configuration['chromeDriverPath'], configuration['user'], configuration['password'], configuration['group'], dataDirectory, logger)
        result = scraper.scrapeData(month, year)
        print(f"Report file: {result}")


if __name__ == '__main__':
    unittest.main()


#It's required to create a file config.json to run the test
#{
#    "user": "XXXX",
#    "password": "XXXX",
#    "group": "XXXXX"
#}