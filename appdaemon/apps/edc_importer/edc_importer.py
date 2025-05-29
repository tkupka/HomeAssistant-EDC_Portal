version = "1.0.0"


import hassapi as hass
import platform
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from EdcScraper import EdcScraper
import edc
from EdcExporter import EdcExporter
from Colors import Colors
from typing import List, Dict, Any, Optional, Set, Literal, TypedDict
from edc import GroupingOptions



class EDCImporter(hass.Hass):
    
    edcScraper = 'undefined'
    edcExporter = 'undefined'
    defaultGroupings = ["1h", "1d", "1m"]
    
    def initialize(self):
        self.log("Initializing...")
        
        self.edcScraper = EdcScraper("/usr/bin/chromedriver", self.args["username"], self.args["password"], self.args["exportGroup"], self.args["dataDirectory"])
        self.edcExporter = EdcExporter(self.args["dataDirectory"], self)
        
        self.listen_event(self.edcStart, "edc_start")
        self.listen_event(self.edcStartMonth, "edc_start_month")
        self.listen_event(self.printScraperInfo, "edc_scraper_info")
        
        self.run_daily(self.runDailCallback, "08:00:00")
        self.set_state("input_text.edc_version", state=version,attributes={
            "friendly_name": "EDC Version",
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
        
        
    def runDailCallback(self, **kwargs):
        ##Works only with latest AppDaemon
        year = dt.now().year
        month = dt.now().month
        self.executeEDC(month, year, self.defaultGroupings)
        
    def printScraperInfo(self, data, **kwargs):
        self.edcScraper.printInstalledModules()
        self.edcScraper.getChromedriverVersion()

        
    def edcExecuteDefaultDataLoad(self):
        downloadIntervals= self.getLastMonths(dt.today(), 2)[::-1]
        for downloadInterval in downloadIntervals:
            year = downloadInterval[0]
            month = downloadInterval[1]
            self.executeEDC(month, year, self.defaultGroupings) 
    
    def edcStart(self, event_name, data, kwargs):
        self.edcExecuteDefaultDataLoad()
    
    def edcStartMonth(self, event_name, data, kwargs):
       

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
        
        self.executeEDC(month, year, groupings)
        
        
    def executeEDC(self, month, year, groupings: List[GroupingOptions]):
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

