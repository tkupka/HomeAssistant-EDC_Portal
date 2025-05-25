import hassapi as hass
from edc import Csv, Interval, GroupingOptions, Ean, Measurement
from typing import List, Dict, Any, Optional, Set, Literal, TypedDict, AnyStr
from pathlib import Path
from datetime import datetime
from functools import partial
from datetime import datetime as dt
import json
class EdcExporter:

	hass = 'undefined'
	dataDirectory = 'undefined'
	exportHeader = "statistic_id;unit;start;state;sum"

	def __init__(self, dataDirectory, hass = 'undefined'):
		self.hass = hass
		self.dataDirectory = Path(f"{dataDirectory}/")
		
	def exportData(self, parsedData: Csv, grouping: GroupingOptions = "1m"):
		print(f"Exporting data {grouping}")
		intervals = parsedData.getGroupedIntervals(grouping)
		
		self.exportSharedEnergy(parsedData, intervals, grouping)
		self.exportProducerMissed(parsedData, intervals, grouping)
		self.exportProducerSoldToNetwork(parsedData, intervals, grouping)
		self.exportConsumerMissed(parsedData, intervals, grouping)
		self.exportConsumerPurchaseFromNetwork(parsedData, intervals, grouping)
		self.exportProducerEans(parsedData)
		self.exportConsumerEans(parsedData)
		
		
	def exportSharedEnergy(self, parsedData: Csv, intervals: List[Interval], grouping: GroupingOptions):
		#create sensors
		print(f"Exporting Shared energy for producer between EANS.")
		#it might be consumer resolver....
		dataResolver = partial(self.resolveProducer)
		#dataResolver = partial(self.resolveConsumer)
		calculator = partial(self.calculateBeforeAfterDifference)
		self.exportConsumptionForEans(intervals, parsedData.consumerEans, "shared", grouping, dataResolver, calculator)
		
	
	def exportProducerMissed(self, parsedData: Csv, intervals: List[Interval], grouping: GroupingOptions):
		print(f"Exporting missed opportunity for producer by EANs.")
		dataResolver = partial(self.resolveProducer)
		calculator = partial(self.calculateMissed)
		self.exportConsumptionForEans(intervals, parsedData.distributionEans, "producer_missed", grouping, dataResolver, calculator)
	
	def exportProducerSoldToNetwork(self, parsedData: Csv, intervals: List[Interval], grouping: GroupingOptions):
		print(f"Exporting sold energy to network by producer.")
		dataResolver = partial(self.resolveProducer)
		calculator = partial(self.calculateAfterMissedDifference)
		self.exportConsumptionForEans(intervals, parsedData.distributionEans, "producer_sold_network", grouping, dataResolver, calculator)

	def exportConsumerMissed(self, parsedData: Csv, intervals: List[Interval], grouping: GroupingOptions):
		print(f"Exporting missed opportunity for consumer by EANs.")
		dataResolver = partial(self.resolveConsumer)
		calculator = partial(self.calculateMissed)
		self.exportConsumptionForEans(intervals, parsedData.consumerEans, "consumer_missed", grouping, dataResolver, calculator)

	def exportConsumerPurchaseFromNetwork(self, parsedData: Csv, intervals: List[Interval], grouping: GroupingOptions):
		print(f"Exporting purchased energy from network by consumer.")
		dataResolver = partial(self.resolveConsumer)
		calculator = partial(self.calculateAfter)
		self.exportConsumptionForEans(intervals, parsedData.consumerEans, "consumer_purchased", grouping, dataResolver, calculator)



	def exportConsumptionForEans(self, intervals: List[Interval], eans: List[Ean], dataType: AnyStr, grouping: GroupingOptions, dataResolver: partial, calculator: partial):
		for i, ean in enumerate(eans):
			print(f"Exporting {dataType} EAN  [{ean.name}].")
			sensorName = self.createSensor("edc_data", dataType, self.convertGroupinToName(grouping), ean.name)
			file = self.exportFile(i, ean.name, sensorName, intervals, dataResolver, calculator, dataType, grouping)
			self.uploadFile(file)
		
	#dataType: producer/consumer
	#interval: hour/day/month
	def createSensor(self, sensorBaseName: AnyStr, dataType: AnyStr, interval: AnyStr, ean: AnyStr):
		completeSensorName = f"{sensorBaseName}_{dataType}_{ean}_{interval}"
		if (self.hass != 'undefined'):
			print(f"Creating sensor [{completeSensorName}")
			
			self.hass.set_state(f"sensor.{completeSensorName}",state=f"{dt.now().strftime('%Y/%m/%d')}",attributes={
				"unique_id": f"{completeSensorName}",
				"friendly_name": f"EDC {dataType.capitalize()} {interval.capitalize()} for EAN: {ean}",
				"icon" : "mdi:database-arrow-down",
#				"state_class": "measurement",
#				"unit_of_measurement": "kWh"
			})
		return completeSensorName


	def exportFile(self, i, ean, sensorName, intervals: List[Interval], dataResolver, calculator: partial, dataType: AnyStr, grouping: GroupingOptions):
		fileName = f"{dataType}_export_{ean}_{grouping}.csv"
		fileName = (self.dataDirectory / fileName)
		print(f"Exporting file [{fileName.resolve()}]")
		exportFile = fileName.open("w", encoding ="utf-8")
		exportFile.write(f"{self.exportHeader}\n")
		
		for interval in intervals:
			dateObj = datetime.strptime(f"{interval.start}", "%Y-%m-%d %H:%M:%S")
			convertedStart = dateObj.strftime('%d.%m.%Y %H:%M')
			data = dataResolver(interval)
			value = calculator(data[i])
			exportFile.write(f"sensor:{sensorName};kWh;{convertedStart};{(value):.2f};0\n")
		exportFile.close()
		return fileName
	
	def uploadFile(self, file: Path):
		if (self.hass != 'undefined'):
			relativePath = str(file.resolve()).replace("/homeassistant/", "")
			print(f"Uploading statistic file [{relativePath}]")
			self.hass.call_service(
				"import_statistics/import_from_file",
				filename=relativePath,
				timezone_identifier="Europe/Vienna",
				delimiter=";",
				decimal="false"
				
			)
			
	def exportProducerEans(self, parsedData: Csv):
		eans = ';'.join(map(lambda ean: ean.name, parsedData.distributionEans))
		print(f"Exporting producer EANs [{eans}]")
		self.exportEans(parsedData.distributionEans, "edc_producer_eans")
		
		
	def exportConsumerEans(self, parsedData: Csv):
		eans = ';'.join(map(lambda ean: ean.name, parsedData.consumerEans))
		print(f"Exporting consumer EANs [{eans}]")
		self.exportEans(parsedData.consumerEans, "edc_consumer_eans")
		
	def exportEans(self, eans: List[Ean], sensorName: AnyStr):
		if (self.hass != 'undefined'):
			existingEansStr = self.hass.get_state(f"sensor.{sensorName}")
			existingEans: set = set(json.loads(existingEansStr))
			
			for ean in eans:
				existingEans.add(ean.name)
			existingEansStr = json.dumps(list(existingEans))
			
			self.hass.set_state(f"sensor.{sensorName}", state = existingEansStr)
		
		
		
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