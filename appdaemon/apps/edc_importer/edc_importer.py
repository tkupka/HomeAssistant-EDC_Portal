version = "1.1.0"

import hassapi as hass
import platform
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
import time
from EdcScraper import EdcScraper
import edc
from EdcExporter import EdcExporter
from Colors import Colors
from typing import List
from edc import GroupingOptions



class EDCImporter(hass.Hass):
    
    edcScraper = 'undefined'
    edcExporter = 'undefined'
    defaultGroupings = ["1h", "1d", "1m"]
    
    def initialize(self):
        self.log("Initializing...")
        
        self.edcScraper = EdcScraper("/usr/bin/chromedriver", self.args["username"], self.args["password"], self.args["exportGroup"], self.args["dataDirectory"])
        self.edcExporter = EdcExporter(self.args["dataDirectory"], self)
        
        self.listen_event(self.importEdcDataEventHandler, "edc_import")
        self.listen_event(self.importEdcDailyDataEventHandler, "edc_import_daily")
        self.listen_event(self.importEdcMonthltdataEventHandler, "edc_import_month")
        self.listen_event(self.printScraperInfo, "edc_scraper_info")
        
        self.run_daily(self.runDailCallback, "10:15:00")
        self.set_state("input_text.edc_version", state=version,attributes={
            "name": "EDC Version",
        })

        self.printSystemInfo()
        self.log("EDC Initialized")
        
    def printSystemInfo(self):
        print("System Information:")
        print(f"Platform: {platform.system()}")
        print(f"Platform Release: {platform.release()}")
        print(f"Platform Version: {platform.version()}")
        print(f"Architecture: {platform.machine()}")
        print(f"Processor: {platform.processor()}")
        print(f"Python Version: {platform.python_version()}")
        
    def importEdcDailyDataEventHandler(self, event_name, data, kwargs):
        self.executeEdcImportDailyData()
        
    def runDailCallback(self, **kwargs):
        self.executeEdcImportDailyData()
        
    def executeEdcImportDailyData(self):
        ##Works only with latest AppDaemon
        year = dt.now().year
        month = dt.now().month
        day = dt.now().day
        if (day == 1):
            ## still last month required
            month = month - 1
            
        try:
            self.executeEdcImport(month, year, self.defaultGroupings)
        except Exception:
            time.sleep(30)
            # call it again in case of failure
            self.executeEdcImport(month, year, self.defaultGroupings)
        if (day >=6 and day <=8):
            #download whole previous month.
            month = month - 1
            if (month <= 0):
                month = 12
                year = year - 1
            try:
                self.executeEdcImport(month, year, self.defaultGroupings)
            except Exception:
                time.sleep(30)
                self.executeEdcImport(month, year, self.defaultGroupings)
        
    def printScraperInfo(self, data, **kwargs):
        self.edcScraper.printInstalledModules()
        self.edcScraper.getChromedriverVersion()

        
    def importEdcDataForDefaultInterval(self):
        downloadIntervals= self.getLastMonths(dt.today(), 2)[::-1]
        for downloadInterval in downloadIntervals:
            year = downloadInterval[0]
            month = downloadInterval[1]
            self.executeEdcImport(month, year, self.defaultGroupings) 
    
    def importEdcDataEventHandler(self, event_name, data, kwargs):
        self.importEdcDataForDefaultInterval()
    
    def importEdcMonthltdataEventHandler(self, event_name, data, kwargs):
       

        if 'month' in data:
            month = int(data['month'])
        else:
            month = dt.now().month
            
        if 'grouping' in data:
            groupings = [data['grouping']]
        else:
            groupings = ["1h", "1d", "1m"]
        
        if 'year' in data:
            year = int(data['year'])
        else:
            year = dt.now().year
        
        self.executeEdcImport(month, year, groupings)
        
        
    def executeEdcImport(self, month, year, groupings: List[GroupingOptions]):
        edcStartTime = dt.now()
        groupingsNames =  "[%s]"%','.join(map(lambda grouping: self.edcExporter.convertGroupinToName(grouping), groupings))
        scriptParameters = f"Interval [{year}/{month}] :: Grouping [{groupingsNames}]"
        print(dt.now().strftime("%Y-%m-%d %H:%M:%S") + f": {Colors.CYAN}********************* Starting EDC data load [{year}/{month}::{groupingsNames}]  *********************{Colors.RESET}")
        try:
            self.set_state("binary_sensor.edc_running", state="on")
            
            self.set_state("input_text.edc_script_parameters", state=scriptParameters)
            dataFile = self.edcScraper.scrapeData(month, year)

            csvDataFromFile = dataFile.read_text()
            if (len(csvDataFromFile) < 200):
                #approx 2 lines
                return
            
            parsedCsv = edc.parse_csv(csvDataFromFile, dataFile.name)
            for grouping in groupings:
                self.edcExporter.exportData(parsedCsv, grouping)

            self.set_state("input_text.edc_script_status", state=f"OK")

        except Exception as e:
            self.set_state("input_text.edc_script_status", state=f"Failed")
            print(dt.now().strftime("%Y-%m-%d %H:%M:%S") + f": {Colors.RED}********************* Script failed : {str(e)} *********************{Colors.RESET}")
            raise Exception("Unable to scrape EDC data")
        finally:
            edcEndTime = dt.now()
            edcDuration = edcEndTime - edcStartTime
            
            self.set_state("input_text.edc_script_duration", state=f"{str(edcDuration).split('.')[0]} :: {edcEndTime:%d/%m/%Y}",
                attributes={
                    "script_parameters": scriptParameters
                })
            self.set_state("binary_sensor.edc_running", state="off")
            print(dt.now().strftime("%Y-%m-%d %H:%M:%S") + f": {Colors.CYAN}********************* Finished in {edcDuration} *********************{Colors.RESET}")
        

    def getLastMonths(self, start_date, months) -> List[tuple]:
        return [i for i in self.getLastMonthsImpl(start_date, months)]
    
    def getLastMonthsImpl(self, start_date, months):
        for i in range(months):
            yield (start_date.year,start_date.month)
            start_date += relativedelta(months = -1)

