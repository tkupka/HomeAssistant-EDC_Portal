version = "1.0.0"

import hassapi as hass
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from itertools import filterfalse
from EdcScraper import EdcScraper
import edc
from pathlib import Path
from EdcExporter import EdcExporter
from Colors import Colors
from typing import List, Dict, Any, Optional, Set, Literal, TypedDict
from edc import GroupingOptions



class EDCImporter(hass.Hass):
    
    edcScraper = 'undefined'
    edcExporter = 'undefined'
    
    def initialize(self):
        self.log("Initializing...")
        
        self.edcScraper = EdcScraper("/usr/bin/chromedriver", self.args["username"], self.args["password"], self.args["exportGroup"], self.args["dataDirectory"])
        self.edcExporter = EdcExporter(self.args["dataDirectory"], self)
        
        self.listen_event(self.edcStart, "edc_start")
        self.listen_event(self.edcStartMonth, "edc_start_month")
        self.run_daily(self.run_daily_callback, "08:00:00")
        
        self.log("Initialized")
        
    def run_daily_callback(self, data, **kwargs):
        year = dt.now().year
        month = dt.now().month
        groupings = ["15m", "1d", "1m"]
        self.executeEDC(month, year, groupings)
        
    def edcExecuteDefaultDataLoad(self):
        downloadIntervals= self.getLastMonths(dt.today(), 2)[::-1]
        groupings = ["15m", "1d", "1m"]
        for downloadInterval in downloadIntervals:
            year = downloadInterval[0]
            month = downloadInterval[1]
            self.executeEDC(month, year, groupings) 
    
    def edcStart(self, event_name, data, kwargs):
        self.edcExecuteDefaultDataLoad()
    
    def edcStartMonth(self, event_name, data, kwargs):
       

        if 'month' in data:
            month = int(data['month'])
        else:
            month = dt.now().month
            
        if 'grouping' in data:
            grouping = data['grouping']
        else:
            grouping ="1m"
        
        if 'year' in data:
            year = int(data['year'])
        else:
            year = dt.now().year
        
        self.executeEDC(month, year, [grouping])
        
        
    def executeEDC(self, month, year, groupings: List[GroupingOptions]):
        self.set_state("input_text.edc_version", state=version,attributes={
            "friendly_name": "EDC Version",
        })
        edcStartTime = dt.now()
        try:
            groupingsNames =  "[%s]"%','.join(map(lambda grouping: self.edcExporter.convertGroupinToName(grouping), groupings))
            print(dt.now().strftime("%Y-%m-%d %H:%M:%S") + f": {Colors.CYAN}********************* Starting EDC data load [{year}/{month}::{groupingsNames}]  *********************{Colors.RESET}")
            self.set_state("binary_sensor.edc_running", state="on")
            
            self.set_state("input_text.edc_script_parameters", state=f"Time [{year}/{month}] :: Grouping [{groupingsNames}]")
            dataFile = self.edcScraper.scrapeData(month, year)
            if (dataFile is None):
                return
            
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
            
            self.set_state("input_text.edc_script_duration", state=f"{str(edcDuration).split('.')[0]}")
            self.set_state("binary_sensor.edc_running", state="off")
            print(dt.now().strftime("%Y-%m-%d %H:%M:%S") + f": {Colors.CYAN}********************* Finished in {edcDuration} *********************{Colors.RESET}")


        

    def getLastMonths(self, start_date, months) -> List[tuple]:
        return [i for i in self.getLastMonthsImpl(start_date, months)]
    
    def getLastMonthsImpl(self, start_date, months):
        for i in range(months):
            yield (start_date.year,start_date.month)
            start_date += relativedelta(months = -1)

