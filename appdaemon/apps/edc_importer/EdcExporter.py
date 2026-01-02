from typing import List, AnyStr
from pathlib import Path
from functools import partial
import json
import calendar
from datetime import datetime
from edc import Csv, Interval, GroupingOptions, Ean, Measurement
from EdcLogger import EdcLogger

class EdcExporter:

	hass = 'undefined'
	dataDirectory = 'undefined'
	uiLogger: EdcLogger = 'undefined'
	exportHeader = "statistic_id;unit;start;state;sum"

	def __init__(self, dataDirectory, logger: EdcLogger, hass = 'undefined'):
		self.hass = hass
		self.uiLogger = logger
		self.dataDirectory = Path(f"{dataDirectory}/")
		self.uiLogger.logAndPrint("EDC Exporter Initialized")
		
	def exportData(self, parsedData: Csv, grouping: GroupingOptions = "1m"):
		self.uiLogger.logAndPrint(f"Exporting data {grouping}")
		intervals = parsedData.getGroupedIntervals(grouping)
		
		self.exportProducerSharedEnergy(parsedData, intervals, grouping)
		self.exportConsumerSharedEnergy(parsedData, intervals, grouping)
		self.exportProducerMissed(parsedData, intervals, grouping)
		self.exportProducerSoldToNetwork(parsedData, intervals, grouping)
		self.exportConsumerMissed(parsedData, intervals, grouping)
		self.exportConsumerPurchaseFromNetwork(parsedData, intervals, grouping)
		self.exportProducerEans(parsedData)
		self.exportConsumerEans(parsedData)
		
		
	def exportProducerSharedEnergy(self, parsedData: Csv, intervals: List[Interval], grouping: GroupingOptions):
		#create entities
		self.uiLogger.logAndPrint(f"Exporting Shared energy for producer between EANs.")
		#it might be consumer resolver....
		dataResolver = partial(self.resolveProducer)
		#dataResolver = partial(self.resolveConsumer)
		calculator = partial(self.calculateBeforeAfterDifference)
		self.exportConsumptionForEans(intervals, parsedData.distributionEans, "shared", grouping, dataResolver, calculator)

	def exportConsumerSharedEnergy(self, parsedData: Csv, intervals: List[Interval], grouping: GroupingOptions):
		#create entities
		self.uiLogger.logAndPrint(f"Exporting Shared energy for consumer between EANs.")
		#it might be consumer resolver....
		dataResolver = partial(self.resolveConsumer)
		calculator = partial(self.calculateBeforeAfterDifference)
		self.exportConsumptionForEans(intervals, parsedData.consumerEans, "shared", grouping, dataResolver, calculator)
		
	
	def exportProducerMissed(self, parsedData: Csv, intervals: List[Interval], grouping: GroupingOptions):
		self.uiLogger.logAndPrint(f"Exporting missed opportunity for producer by EANs.")
		dataResolver = partial(self.resolveProducer)
		calculator = partial(self.calculateMissed)
		self.exportConsumptionForEans(intervals, parsedData.distributionEans, "producer_missed", grouping, dataResolver, calculator)
	
	def exportProducerSoldToNetwork(self, parsedData: Csv, intervals: List[Interval], grouping: GroupingOptions):
		self.uiLogger.logAndPrint(f"Exporting sold energy to network by producer.")
		dataResolver = partial(self.resolveProducer)
		calculator = partial(self.calculateAfterMissedDifference)
		self.exportConsumptionForEans(intervals, parsedData.distributionEans, "producer_sold_network", grouping, dataResolver, calculator)

	def exportConsumerMissed(self, parsedData: Csv, intervals: List[Interval], grouping: GroupingOptions):
		self.uiLogger.logAndPrint(f"Exporting missed opportunity for consumer by EANs.")
		dataResolver = partial(self.resolveConsumer)
		calculator = partial(self.calculateMissed)
		self.exportConsumptionForEans(intervals, parsedData.consumerEans, "consumer_missed", grouping, dataResolver, calculator)

	def exportConsumerPurchaseFromNetwork(self, parsedData: Csv, intervals: List[Interval], grouping: GroupingOptions):
		self.uiLogger.logAndPrint(f"Exporting purchased energy from network by consumer.")
		dataResolver = partial(self.resolveConsumer)
		calculator = partial(self.calculateAfter)
		self.exportConsumptionForEans(intervals, parsedData.consumerEans, "consumer_purchased", grouping, dataResolver, calculator)



	def exportConsumptionForEans(self, intervals: List[Interval], eans: List[Ean], dataType: AnyStr, grouping: GroupingOptions, dataResolver: partial, calculator: partial):
		for eanIndex, ean in enumerate(eans):
			self.uiLogger.logAndPrint(f"Exporting {dataType} EAN  [{ean.name}].")
			entityName = self.createEntity("edc_data", dataType, self.convertGroupinToName(grouping), ean.name)
			file = self.exportFile(eanIndex, ean.name, entityName, intervals, dataResolver, calculator, dataType, grouping)
			self.uploadFile(file)
			
			if (grouping == "1m"):
				#update current state just for monthly interval
				self.updateEntityState(entityName, ean, eanIndex, intervals, dataResolver, calculator)
	
	def updateEntityState(self, entityName: AnyStr, ean: AnyStr, eanIndex: int, intervals: List[Interval], dataResolver: partial, calculator: partial):
		year = datetime.now().year
		month = datetime.now().month

		for interval in intervals:
			statisticDate: datetime = self.parseIntervalStart(interval)
			#just current month
			if ((statisticDate.month == month) and (statisticDate.year == year)):
				completeEntityName = f"input_number.{entityName}"
				data = dataResolver(interval)
				value = calculator(data[eanIndex])
				if (value == 0):
					value = 0.1
				self.uiLogger.logAndPrint(f"Updating monthly [{statisticDate.year}::{statisticDate.month}] entity [{completeEntityName}] sate to [{value}]")
				if (self.hass != 'undefined'):
					self.hass.set_state(completeEntityName,state=value)
		
	#dataType: producer/consumer
	#interval: hour/day/month
	def createEntity(self, entityBaseName: AnyStr, dataType: AnyStr, interval: AnyStr, ean: AnyStr):
		completeEntityName = f"{entityBaseName}_{dataType}_{ean}_{interval}"
		fullEntityName = f"input_number.{completeEntityName}"
		if (self.hass != 'undefined'):
			existingState = self.hass.get_state(fullEntityName)
			#if (existingState == None):
			self.uiLogger.logAndPrint(f"Creating entity [{fullEntityName}, existing state: [{existingState}]")

			self.hass.set_state(fullEntityName, state=0.1,attributes={
				"unique_id": f"{fullEntityName}",
				"name": f"EDC {dataType.capitalize()} {interval.capitalize()} for EAN: {ean}",
				"icon" : "mdi:database-arrow-down",
				"state_class": "measurement",
				"unit_of_measurement": "kWh"
			})
			#else: 
		#		self.uiLogger.logAndPrint(f"Entity exists [{fullEntityName}, with state: [{existingState}]")
		return completeEntityName


	def exportFile(self, i, ean: AnyStr, entityName, intervals: List[Interval], dataResolver, calculator: partial, dataType: AnyStr, grouping: GroupingOptions):
		fileName = f"{dataType}_export_{ean}_{grouping}.csv"
		fileName = (self.dataDirectory / fileName)
		self.uiLogger.logAndPrint(f"Exporting file [{fileName.resolve()}]")
		exportFile = fileName.open("w", encoding ="utf-8")
		exportFile.write(f"{self.exportHeader}\n")
		
		for interval in intervals:
			statisticDate: datetime = self.parseIntervalStart(interval)
			data = dataResolver(interval)
			value = calculator(data[i])

			self.writeData(exportFile, entityName, statisticDate, value)
			#in case on month statistic we need to set end date otherwise sometimes HA screw up last day of the month
			if (grouping == "1m"):
				lastDay = calendar.monthrange(statisticDate.year, statisticDate.month)[1]
				statisticDate = statisticDate.replace(day = lastDay)
				self.writeData(exportFile, entityName, statisticDate, value)
			
		exportFile.close()
		return fileName
	
	def parseIntervalStart(self, interval: Interval) -> datetime:
		return datetime.strptime(f"{interval.start}", "%Y-%m-%d %H:%M:%S")
	
	def writeData(self, exportFile, entityName, statisticDate, value):
		statisticDateStr = statisticDate.strftime('%d.%m.%Y %H:%M')
		exportFile.write(f"input_number.{entityName};kWh;{statisticDateStr};{(value):.2f};0\n")
		
	
	def uploadFile(self, file: Path):
		if (self.hass != 'undefined'):
			relativePath = str(file.resolve()).replace("/homeassistant/", "")
			self.uiLogger.logAndPrint(f"Uploading statistic file [{relativePath}]")
			self.hass.call_service(
				"import_statistics/import_from_file",
				filename=relativePath,
				timezone_identifier="Europe/Vienna",
				delimiter=";",
				decimal="false"
				
			)
			
	def exportProducerEans(self, parsedData: Csv):
		eans = ';'.join(map(lambda ean: ean.name, parsedData.distributionEans))
		self.uiLogger.logAndPrint(f"Exporting producer EANs [{eans}]")
		self.exportEans(parsedData.distributionEans, "edc_producer_eans")
		
		
	def exportConsumerEans(self, parsedData: Csv):
		eans = ';'.join(map(lambda ean: ean.name, parsedData.consumerEans))
		self.uiLogger.logAndPrint(f"Exporting consumer EANs [{eans}]")
		self.exportEans(parsedData.consumerEans, "edc_consumer_eans")
		
	def exportEans(self, eans: List[Ean], entityName: AnyStr):
		if (self.hass != 'undefined'):
			existingEansStr = self.hass.get_state(f"input_text.{entityName}")
			try:
				existingEans: set = set(json.loads(existingEansStr))
			except:
				existingEans: set = set([])			
			
			for ean in eans:
				existingEans.add(ean.name)
			existingEansStr = json.dumps(list(existingEans))
			
			self.hass.set_state(f"input_text.{entityName}", state = existingEansStr)
		
		
		
	def resolveProducer(self, interval: Interval) -> List[Measurement]:
		return interval.distributions
	
	def resolveConsumer(self, interval: Interval) -> List[Measurement]:
		return interval.consumers
	
	def calculateBeforeAfterDifference(self, measurement: Measurement):
		return measurement.before - measurement.after
	
	def calculateMissed(self, measurement: Measurement):
		return measurement.missed

	def calculateAfter(self, measurement: Measurement):
		return measurement.after

	def calculateAfterMissedDifference(self, measurement: Measurement):
		return measurement.after - measurement.missed

		
	def convertGroupinToName(self, grouping: GroupingOptions):
		if grouping == "15m":
			return "fluent"
		elif grouping == "1h":
			return "hourly"
		elif grouping == "1d":
			return "daily"
		elif grouping == "1m":
			return "monthly"
		else:
			raise ValueError("Unknown grouping option")  # TS throw new Error()
