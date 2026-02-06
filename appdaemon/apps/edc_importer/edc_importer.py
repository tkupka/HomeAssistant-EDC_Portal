version = "1.5.0"

from EdcLogger import EdcLogger
import utils
from appdaemon.plugins.hass import Hass
import platform
from datetime import datetime as dt
import time
import random
from EdcScraper import EdcScraper
import edc
from EdcExporter import EdcExporter
from Colors import Colors
from typing import List
from edc import GroupingOptions


class EDCImporter(Hass):

    edcScraper = 'undefined'
    edcExporter = 'undefined'
    defaultGroupings = ["1h", "1d", "1m"]
    uiLogger: EdcLogger = 'undefined'
    daily_handle = None
    
    def initialize(self):
        self.log("Initializing...")
        logger = EdcLogger(self)
        self.uiLogger = logger

        self.edcScraper = EdcScraper("/usr/bin/chromedriver", self.args["username"], self.args["password"], self.args["exportGroup"], self.args["dataDirectory"], logger)
        self.edcExporter = EdcExporter(self.args["dataDirectory"], logger, self)

        self.listen_event(self.importEdcDataEventHandler, "edc_import")
        self.listen_event(self.importEdcDailyDataEventHandler, "edc_import_daily")
        self.listen_event(self.importEdcMonthlyDataEventHandler, "edc_import_month")
        self.listen_event(self.printScraperInfo, "edc_scraper_info")
        self.listen_event(self.printServicesEventHandler, "edc_print_services")

        # Set default values for scheduling entities if not already set
        # Note: initial values are defined in packages/edc_importer.yaml
        base_time_state = self.get_state("input_datetime.edc_daily_base_run_time")
        if base_time_state in [None, "unknown", "unavailable", ""]:
            self.call_service("input_datetime/set_datetime", entity_id="input_datetime.edc_daily_base_run_time", time="10:15:00")

        randomization_state = self.get_state("input_number.edc_daily_run_randomization")
        if randomization_state in [None, "unknown", "unavailable", ""]:
            self.call_service("input_number/set_value", entity_id="input_number.edc_daily_run_randomization", value=45)

        # Schedule daily run with configurable time
        self.schedule_daily_run()

        # Listen for configuration changes to reschedule automatically
        self.listen_state(self.on_schedule_config_change, "input_datetime.edc_daily_base_run_time")
        self.listen_state(self.on_schedule_config_change, "input_number.edc_daily_run_randomization")

        self.set_state("input_text.edc_version", state=version,attributes={
            "name": "EDC Version",
        })
        self.set_state("input_number.edc_data_Y_consumer_missed_859182400504099833_min", state=1,attributes={
            "unique_id": "input_number.edc_data_Y_consumer_missed_859182400504099833_min",
            "name": "TMP",
        })

        self.printSystemInfo()
        self.log("EDC Initialized")
        
    def printSystemInfo(self):
        self.uiLogger.print("System Information:")
        self.uiLogger.print(f"Platform: {platform.system()}")
        self.uiLogger.print(f"Platform Release: {platform.release()}")
        self.uiLogger.print(f"Platform Version: {platform.version()}")
        self.uiLogger.print(f"Architecture: {platform.machine()}")
        self.uiLogger.print(f"Processor: {platform.processor()}")
        self.uiLogger.print(f"Python Version: {platform.python_version()}")

    def schedule_daily_run(self):
        """Schedule or reschedule the daily scraper run."""
        # Cancel existing schedule if any
        if self.daily_handle:
            self.cancel_timer(self.daily_handle)

        # Read configuration from HA entities (with defaults)
        base_time_str = self.get_state("input_datetime.edc_daily_base_run_time")
        if base_time_str in [None, "unknown", "unavailable", ""]:
            base_time_str = "10:15:00"

        randomization_str = self.get_state("input_number.edc_daily_run_randomization")
        if randomization_str in [None, "unknown", "unavailable", ""]:
            randomization_minutes = 45
        else:
            randomization_minutes = int(float(randomization_str))

        # Parse base time
        time_parts = base_time_str.split(":")
        base_hour = int(time_parts[0])
        base_minute = int(time_parts[1])

        # Calculate randomized time
        random_minutes_offset = random.randint(0, randomization_minutes) if randomization_minutes > 0 else 0
        total_minutes = base_hour * 60 + base_minute + random_minutes_offset
        scheduled_hour = (total_minutes // 60) % 24
        scheduled_minute = total_minutes % 60
        scheduled_second = random.randint(0, 59)
        scheduled_time = f"{scheduled_hour:02d}:{scheduled_minute:02d}:{scheduled_second:02d}"
        self.call_service("input_datetime/set_datetime", entity_id="input_datetime.edc_daily_execution_time", time=f"{scheduled_time}")

        self.uiLogger.logAndPrint(f"Daily scraper scheduled at {scheduled_time}", Colors.CYAN)
        self.daily_handle = self.run_daily(self.runDailCallback, scheduled_time)

    def on_schedule_config_change(self, entity, attribute, old, new, kwargs):
        """Handle changes to scheduling configuration."""
        self.uiLogger.logAndPrint(f"Schedule configuration changed ({entity}), rescheduling...", Colors.CYAN)
        self.schedule_daily_run()
        

    def printServicesEventHandler(self, event_name, data, kwargs):
        availableServices = self.list_services(namespace="global")
        self.uiLogger.print("HA services:")
        self.uiLogger.print('\n'.join(list(map(lambda service: str(service), availableServices))))        
        
    def importEdcDailyDataEventHandler(self, event_name, data, kwargs):
        self.executeEdcImportDailyData()
        
    def runDailCallback(self, **kwargs):
        self.executeEdcImportDailyData()
        
    def executeEdcImportDailyData(self):
        ##Works only with latest AppDaemon
        year = dt.now().year
        month = dt.now().month
        day = dt.now().day
        lastMonthsInterval = utils.getLastMonths(dt.today(), 2)[::-1]
        lastMonthYear = lastMonthsInterval[0][0]
        lastMonth = lastMonthsInterval[0][1]

        if (day == 1):
            ## still last month required
            month = lastMonth
            year = lastMonthYear
            
        try:
            self.executeEdcImport(month, year, self.defaultGroupings)
        except Exception:
            time.sleep(30)
            # call it again in case of failure
            self.executeEdcImport(month, year, self.defaultGroupings)
        
        if (day >=8 and day <=10):
            #download whole previous month. God knows when it's ready in EDC
            try:
                self.executeEdcImport(lastMonth, lastMonthYear, self.defaultGroupings)
            except Exception:
                time.sleep(30)
                self.executeEdcImport(lastMonth, lastMonthYear, self.defaultGroupings)
        
    def printScraperInfo(self, data, **kwargs):
        self.edcScraper.printInstalledModules()
        self.edcScraper.getChromedriverVersion()

        
    def importEdcDataForDefaultInterval(self):
        downloadIntervals= utils.getLastMonths(dt.today(), 2)[::-1]
        for downloadInterval in downloadIntervals:
            year = downloadInterval[0]
            month = downloadInterval[1]
            self.executeEdcImport(month, year, self.defaultGroupings) 
    
    def importEdcDataEventHandler(self, event_name, data, kwargs):
        self.importEdcDataForDefaultInterval()
    
    def importEdcMonthlyDataEventHandler(self, event_name, data, kwargs):

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
        self.uiLogger.logAndPrint(f"******************** Starting EDC data load [{year}/{month}::{groupingsNames}]  *********************", Colors.CYAN)
        importError = ""
        try:
            self.set_state("binary_sensor.edc_running", state="on")
            
            self.set_state("input_text.edc_script_parameters", state=scriptParameters)
            dataFile = self.edcScraper.scrapeData(month, year)

            csvDataFromFile = dataFile.read_text()
            fileLenght = len(csvDataFromFile)
            if (fileLenght < 200):
                #approx 2 lines
                self.uiLogger.logAndPrint(f"EDC export contains no data len[{fileLenght}]. Ignoring....")
                return
            
            parsedCsv = edc.parse_csv(csvDataFromFile, dataFile.name)
            for grouping in groupings:
                self.edcExporter.exportData(parsedCsv, grouping)

            self.set_state("input_text.edc_script_status", state=f"OK")

        except Exception as e:
            importError = str(e)
            self.set_state("input_text.edc_script_status", state=f"Failed",
                attributes={
                    "error": importError
                })
            
            self.uiLogger.logAndPrint(f"******************** Script failed : {importError} *********************", Colors.RED)
            raise Exception("Unable to scrape EDC data")
        finally:
            edcEndTime = dt.now()
            edcDuration = edcEndTime - edcStartTime
            
            self.set_state("input_text.edc_script_duration", state=f"{str(edcDuration).split('.')[0]} :: {edcEndTime:%d/%m/%Y}",
                attributes={
                    "script_parameters": scriptParameters,
                    "error": importError
                })
            self.set_state("binary_sensor.edc_running", state="off")
            self.uiLogger.logAndPrint(f"********************* Finished in {edcDuration} *********************", Colors.CYAN)
        

