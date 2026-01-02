import math
import random
import datetime
import time
import copy
import functools
import threading
import sys

# Define types/interfaces as classes or TypedDicts for structure and type hinting
# Python doesn't have direct interface equivalents, using classes for data structures
# Union types are represented using typing.Literal

from typing import List, Dict, Any, Optional, Set, Literal, TypedDict

DisplayUnit = Literal["kWh", "kW"]
ProduceConsume = Literal["produce", "consume"]
GroupingOptions = Literal["15m", "1h", "1d", "1m"]
OptimizationAlgorithm = Literal["gradientDescend", "random"]


class EanStats:
    def __init__(self):
        self.original_balance = 0
        self.adjusted_balance = 0
        self.missed_due_to_allocation = 0

    def shared(self) -> float:
        return self.original_balance - self.adjusted_balance
    
class Summary:
    def __init__(self, distributionStats: List[EanStats], consumerStats: List[EanStats]):
        self.distributionStats = distributionStats
        self.consumerStats = consumerStats


class Measurement:

    def __init__(self, before: float, after: float, missed: float):
        self.before = before
        self.after = after
        self.missed = missed


class Interval:

    def __init__(self, start: datetime.datetime, sumSharing: float, sumMissed: float, sumProduction: float, distributions: List[Measurement], consumers: List[Measurement], errors: List[str]):
        self.start = start
        self.sumSharing = sumSharing
        self.sumMissed = sumMissed
        self.sumProduction = sumProduction
        self.distributions = distributions
        self.consumers = consumers
        self.errors = errors


class OptimizedAllocation(TypedDict):
    weights: List[float]
    sharing: List[float]
    profit: List[float]


class SharingSimulationResult(TypedDict):
    profitPerEan: List[float]
    sharingPerEan: List[float]
    sharingPerRoundPerEan: List[List[float]]  # list[iterations][eans]


class Ean:

    def __init__(self, name: str, csvIndex: int):
        self.name = name
        self.csvIndex = csvIndex


# Helper function for console logging (mapping TS console to Python print)
def console_log(*args):
    print(*args)


def console_error(*args):
    print("ERROR:", *args, file=sys.stderr)


def console_info(*args):
    print("INFO:", *args)


# Helper for performance.now()
def performance_now():
    return time.perf_counter() * 1000  # Convert to milliseconds

# Helper for alert (no direct equivalent in standard Python, omit or simulate)
# Omitting alert as it's browser-specific

# Helper for debugger (no direct equivalent in standard Python, omit)
# Omitting debugger as it's environment-specific


# Helper for structuredClone (using copy.deepcopy)
def structured_clone(obj):
    return copy.deepcopy(obj)


# Helper for Array.prototype.reduce
def array_reduce(arr, func, initial_value):
    return functools.reduce(func, arr, initial_value)


# Helper for Array.prototype.fill
def array_fill(size, value):
    return [value] * size


# Helper for Array.prototype.splice (simulating in-place modification)
def array_splice(arr, start, delete_count, *items):
    deleted_items = arr[start:start + delete_count]
    arr[start:start + delete_count] = list(items)
    return deleted_items  # TS splice returns deleted items


# Helper for Array.prototype.push
def array_push(arr, *items):
    arr.extend(items)
    return len(arr)  # TS push returns new length


# Helper for Array.prototype.map
def array_map(arr, func):
    return list(map(func, arr))


# Helper for Array.prototype.has
def set_has(s: Set, item: Any) -> bool:
    return item in s


# Helper for Math.trunc
def math_trunc(x: float) -> int:
    return int(x)


# Helper for Math.round
def math_round(x: float) -> int:
    return round(x)


# Helper for Math.min
def math_min(*args) -> float:
    return min(*args)


# Helper for Math.max
def math_max(*args) -> float:
    return max(*args)


# Helper for Math.random
def math_random() -> float:
    return random.random()


# Helper for Math.sqrt
def math_sqrt(x: float) -> float:
    return math.sqrt(x)


# Helper for Math.log
def math_log(x: float) -> float:
    return math.log(x)


# Helper for Math.cos
def math_cos(x: float) -> float:
    return math.cos(x)


# Helper for Math.PI
math_pi = math.pi


# Helper for isNaN
def is_nan(x: float) -> bool:
    return math.isnan(x)


# Helper for toFixed
def to_fixed(x: float, digits: int) -> str:
    return f"{x:.{digits}f}"


# Helper for replaceAll (using str.replace)
def replace_all(s: str, old: str, new: str) -> str:
    return s.replace(old, new)


# Helper for padStart (using str.zfill or f-string)
def pad_start(s: str, length: int, fillchar: str) -> str:
    return s.zfill(length)  # zfill only works for numeric strings with '0'


# More general padStart
def pad_start_general(s: str, length: int, fillchar: str) -> str:
    if len(s) >= length:
        return s
    return fillchar * (length - len(s)) + s


def last(container: List):
    return container[len(container) - 1]


# asserts condition
def assert_condition(condition: bool, *loggingArgs: Any):
    if not condition:
        # const errorMsg = `Assert failed: ${loggingArgs.toString()}`; # TS toString on array
        errorMsg = f"Assert failed: {', '.join(map(str, loggingArgs))}"  # Python equivalent
        console_error("Assert failed", *loggingArgs)
        # eslint-disable-next-line no-debugger
        # debugger; # Omitted - browser/Node.js specific
        # alert(errorMsg); # Omitted - browser specific
        raise AssertionError(errorMsg)

# Renaming to avoid conflict with Python's built-in assert


def logWarning(warning: str, date: datetime.datetime):
    console_info(warning)


def gaussianRandom(mean: float=0, stdev: float=1) -> float:
    u = 1 - math_random()  # Converting [0,1) to (0,1]
    v = math_random()
    z = math_sqrt(-2.0 * math_log(u)) * math_cos(2.0 * math_pi * v)
    # Transform to the desired mean and standard deviation:
    return z * stdev + mean


def parseKwh(data: str) -> float:
    if len(data) == 0:
        return 0.0
    adj = replace_all(data, ",", ".")
    result = float(adj)
    assert(not is_nan(result))
    return result


def getDate(explodedLine: List[str]) -> datetime.datetime:
    assert_condition(len(explodedLine) > 3, f'Cannot extract date - whole line is: "{";".join(explodedLine)}"')
    day, month, year = explodedLine[0].split(".")
    hour, minute = explodedLine[1].split(":")
    # Note: Python month is 1-12, TS month is 0-11
    return datetime.datetime(
        int(year),
        int(month),  # No -1 needed for Python month
        int(day),
        int(hour),
        int(minute),
    )


class Settings:
    displayUnit: DisplayUnit = "kWh"
    anonymizeEans = False
    filterValue = 0
    grouping: GroupingOptions = "1d"
    groupGraph = True
    graphExtra: ProduceConsume = "produce"

    hiddenEans: Set[str] = set()

    minDayFilter = 0
    maxDayFilter = 0

    def useFiltering(self) -> bool:
        return self.grouping == "15m" or self.grouping == "1h"


gSettings = Settings()


def sumContainer(container: List[float]) -> float:
    return array_reduce(container, lambda acc, val: acc + val, 0)


def accumulateInterval(to: Interval, from_interval: Interval):
    assert_condition(
        len(to.distributions) == len(from_interval.distributions) and
            len(to.consumers) == len(from_interval.consumers),
    )
    to.sumSharing += from_interval.sumSharing
    to.sumMissed += from_interval.sumMissed
    to.sumProduction += from_interval.sumProduction

    for i in range(len(to.distributions)):
        accumulateMeasurement(to.distributions[i], from_interval.distributions[i])
    for i in range(len(to.consumers)):
        accumulateMeasurement(to.consumers[i], from_interval.consumers[i])
    # to.errors.push(...from.errors); # TS spread syntax
    array_push(to.errors, *from_interval.errors)


def accumulateMeasurement(to: Measurement, from_measurement: Measurement):
    to.before += from_measurement.before
    to.after += from_measurement.after
    to.missed += from_measurement.missed


class PrintKWhOptions(TypedDict, total=False):
    alwaysKwh: bool  # Default false
    nbsp: bool  # Default false


def printKWh(input_value: float, options: Optional[PrintKWhOptions]=None) -> str:
    assert_condition(not is_nan(input_value), "NaN in printKWh!")
    # const alwaysKWh = options?.alwaysKwh ?? false; # TS nullish coalescing
    alwaysKWh = options.get('alwaysKwh', False) if options is not None else False
    # const nsbsp = (options?.nbsp ?? false) ? "&nbsp;" : " "; # TS nullish coalescing and ternary
    nsbsp = "&nbsp;" if (options.get('nbsp', False) if options is not None else False) else " "

    if (
        gSettings.displayUnit == "kW" and
        not alwaysKWh and
        (gSettings.grouping == "15m" or gSettings.grouping == "1h")
    ):
        multiplier = 4 if gSettings.grouping == "15m" else 1
        # return `${(input * multiplier).toFixed(2)}${nsbsp}kW`; # TS template literal
        return f"{to_fixed(input_value * multiplier, 2)}{nsbsp}kW"
    else:
        # return `${input.toFixed(2)}${nsbsp}kWh`; # TS template literal
        return f"{to_fixed(input_value, 2)}{nsbsp}kWh"


class Csv:
    distributionEans: List[Ean] = []
    consumerEans: List[Ean] = []

    filename: str
    dateFrom: datetime.datetime
    dateTo: datetime.datetime

    # readonly #intervals: Interval[]; # TS private field
    _Csv__intervals: List[Interval]  # Python name mangling for private

    # Used for optimizing sharing
    # readonly #flatConsumed: Uint32Array; # TS private field, commented out
    # _Csv__flatConsumed: List[int] # Python equivalent, commented out

    def __init__(self, filename: str, intervals: List[Interval], distributionEans: List[Ean], consumerEans: List[Ean]):
        self.filename = filename
        self._Csv__intervals = intervals
        self.dateFrom = intervals[0].start
        # self.dateTo = structuredClone(last(intervals).start); # TS structuredClone
        self.dateTo = structured_clone(last(intervals).start)
        self.dateTo = self.dateTo + datetime.timedelta(minutes=14)  # TS setMinutes

        # Copy EAN lists before sorting
        self.distributionEans = list(distributionEans)
        self.consumerEans = list(consumerEans)

        # Sort columns
        newDistributionEans: List[Ean] = []
        newConsumerEans: List[Ean] = []

        def findSmallestEan(eans: List[Ean]) -> int:
            result = 0
            for i in range(1, len(eans)):
                if eans[i].name < eans[result].name:
                    result = i
            if result != 0:
                console_log("Swapping EANs: ", eans[result].name, eans[0].name)
            return result

        while len(self.distributionEans) > 0:
            index = findSmallestEan(self.distributionEans)
            newDistributionEans.append(self.distributionEans[index])
            for i in self._Csv__intervals:
                # i.distributions.push(i.distributions[index]); # TS push
                array_push(i.distributions, i.distributions[index])
                # i.distributions.splice(index, 1); # TS splice
                array_splice(i.distributions, index, 1)
            # this.distributionEans.splice(index, 1); # TS splice
            array_splice(self.distributionEans, index, 1)

        while len(self.consumerEans) > 0:
            index = findSmallestEan(self.consumerEans)
            newConsumerEans.append(self.consumerEans[index])
            for i in self._Csv__intervals:
                # i.consumers.push(i.consumers[index]); # TS push
                array_push(i.consumers, i.consumers[index])
                # i.consumers.splice(index, 1); # TS splice
                array_splice(i.consumers, index, 1)
            # this.consumerEans.splice(index, 1); # TS splice
            array_splice(self.consumerEans, index, 1)

        self.distributionEans = newDistributionEans
        self.consumerEans = newConsumerEans

        # this.#flatConsumed = new Uint32Array(this.intervals.length * this.consumerEans.length); # Commented out
        # self._Csv__flatConsumed = array_fill(len(self._Csv__intervals) * len(self.consumerEans), 0) # Python equivalent, commented out
        # for (let i = 0; i < this.intervals.length; ++i) { # Commented out
        #    for (let j = 0; j < this.consumerEans.length; ++j) { # Commented out
        #        this.#flatConsumed[i * this.consumerEans.length + j] = Math.round( # Commented out
        #            this.intervals[i].consumers[j].before * 100, # Commented out
        #        ); # Commented out
        #    } # Commented out
        # } # Commented out

    def getGroupedIntervals(self, grouping: GroupingOptions) -> List[Interval]:
        #dateFrom, dateTo = self._Csv__getDayFilterDates()
        timer = performance_now()
        result: List[Interval] = []
        for i in range(len(self._Csv__intervals)):
            #if self._Csv__intervals[i].start < dateFrom or self._Csv__intervals[i].start > dateTo:
            #    continue

            mergeToLast = False
            if len(result) > 0:
                dateLast = self._Csv__intervals[i - 1].start
                dateThis = self._Csv__intervals[i].start
                if grouping == "15m":
                    mergeToLast = False
                elif grouping == "1h":
                    mergeToLast = dateThis.hour == dateLast.hour
                elif grouping == "1d":
                    mergeToLast = dateThis.day == dateLast.day
                elif grouping == "1m":
                    mergeToLast = dateThis.month == dateLast.month
                else:
                    raise ValueError("Unknown grouping option")  # TS throw new Error()

            if mergeToLast:
                accumulateInterval(last(result), self._Csv__intervals[i])
            else:
                # result.push(structuredClone(this.#intervals[i])); # TS push, structuredClone
                array_push(result, structured_clone(self._Csv__intervals[i]))

        console_log(
            "Merging intervals",
            len(self._Csv__intervals),
            "=>",
            len(result),
            "elapsed",
            performance_now() - timer,
            "ms",
        )
        return result
    
    def calculateSummary(self, grouping: GroupingOptions) -> Summary:
        grouped_intervals: List[Interval] = self.getGroupedIntervals(grouping)
        distributionStats = [EanStats() for _ in range(len(self.distributionEans))]
        consumerStats = [EanStats() for _ in range(len(self.consumerEans))]
    
        def accumulate(to: EanStats, from_: 'Measurement') -> None:
            to.original_balance += from_.before
            to.adjusted_balance += from_.after
            to.missed_due_to_allocation += from_.missed
    
        for interval in grouped_intervals:
            for i in range(len(interval.distributions)):
                accumulate(distributionStats[i], interval.distributions[i])
            for i in range(len(interval.consumers)):
                accumulate(consumerStats[i], interval.consumers[i])
        return Summary(distributionStats, consumerStats)

    # return number of days in the data
    def getNumDays(self) -> int:
        # TS Date.UTC uses 0-11 for month, Python datetime uses 1-12
        # TS Date.UTC returns milliseconds since epoch
        # Python datetime objects can be subtracted to get timedelta
        # Need to create date-only objects for day difference calculation

        utc1 = datetime.datetime(self.dateTo.year, self.dateTo.month, self.dateTo.day)
        utc2 = datetime.datetime(self.dateFrom.year, self.dateFrom.month, self.dateFrom.day)
        # console.log(utc1 - utc2); # This will print timedelta object in Python
        delta = utc1 - utc2
        # TS calculates difference in milliseconds and divides by ms per day
        # Python timedelta has days attribute
        return delta.days + 1

    def simulateSharing(
        self,
        allocations: List[float],
        costsPerKwh: List[float],
        iterations: int,
    ) -> SharingSimulationResult:
        # const startTime = Date.now(); # Commented out
        assert_condition(sumContainer(allocations) <= 100, "Allocations are over 100", allocations, sumContainer(allocations))
        assert_condition(len(self.distributionEans) == 1)

        # We will run everything in integers multiplier by 100 to get fixed point 2 decimal places exact arithmetic

        # const resultDetailed = [] as number[][]; # TS array initialization
        resultDetailed: List[List[float]] = []
        for i in range(iterations):
            # resultDetailed.push(Array<number>(allocations.length).fill(0)); # TS push, Array.fill
            array_push(resultDetailed, array_fill(len(allocations), 0.0))

        # Filter the intervals by time by calling getGroupedIntervals
        for interval in self.getGroupedIntervals("15m"):
            # To fixed point. Note that the rounding is necessary even here. 0.07*100 = 7.000000000000001
            toShare = math_round(interval.distributions[0].before * 100)
            # const consumed: number[] = interval.consumers.map((c) => Math.round(c.before * 100)); # TS map, Math.round
            consumed: List[int] = array_map(interval.consumers, lambda c: math_round(c.before * 100))

            for iteration in range(iterations):
                energyThisRound = toShare
                for i in range(len(consumed)):
                    # Allocations are in %, so we need to divide by 100. The EDC manual explicitly says they truncate down here
                    # const shared = Math.min( # TS Math.min
                    #    consumed[i],
                    #    Math.trunc(energyThisRound * (allocations[i] / 100)), # TS Math.trunc
                    # );
                    shared = math_min(
                       consumed[i],
                       math_trunc(energyThisRound * (allocations[i] / 100)),
                    )
                    consumed[i] -= shared
                    toShare -= shared
                    resultDetailed[iteration][i] += shared
                    assert_condition(shared >= 0)
                    assert_condition(toShare >= 0)
                    assert_condition(consumed[i] >= 0)

        # Go back from fixed point to floats
        # const resultEan = Array<number>(allocations.length).fill(0); # TS Array.fill
        resultEan: List[float] = array_fill(len(allocations), 0.0)
        for i in range(iterations):
            for j in range(len(allocations)):
                resultDetailed[i][j] /= 100
                resultEan[j] += resultDetailed[i][j]

        # console.log("simulateSharing TOTAL took ", Date.now() - startTime, " ms"); # Commented out
        return {
            # profitPerEan: resultEan.map((value, index) => costsPerKwh[index] * value), # TS map
            'profitPerEan': array_map(list(enumerate(resultEan)), lambda item: costsPerKwh[item[0]] * item[1]),
            'sharingPerEan': resultEan,
            'sharingPerRoundPerEan': resultDetailed,
        }

    # Fast version computing only final profit
    def simulateSharingFast(
        self,
        filteredIntervals: List[Interval],
        allocations: List[float],
        costsPerKwh: List[float],
        iterations: int,
    ) -> float:
        # const startTime = Date.now(); # Commented out
        assert_condition(sumContainer(allocations) <= 100, "Allocations are over 100", allocations, sumContainer(allocations))
        assert_condition(len(self.distributionEans) == 1)

        # const allocationsFraction = allocations.map((i) => i / 100); # TS map
        allocationsFraction: List[float] = array_map(allocations, lambda i: i / 100)
        # const allocationsFraction = new Uint32Array(allocations.length); # Commented out
        # for (let i = 0; i < allocations.length; ++i) { # Commented out
        #    allocationsFraction[i] = allocations[i] / 100; # Commented out
        # } # Commented out

        # We will run everything in integers multiplier by 100 to get fixed point 2 decimal places exact arithmetic

        # const flatConsumed = new Uint32Array(this.#flatConsumed); # Commented out
        # flatConsumed = list(self._Csv__flatConsumed) # Python equivalent, commented out

        # const profitPerEan = Array<number>(allocations.length).fill(0); # TS Array.fill
        profitPerEan: List[float] = array_fill(len(allocations), 0.0)
        for interval in filteredIntervals:
            # To fixed point. Note that the rounding is necessary even here. 0.07*100 = 7.000000000000001
            toShare = math_round(interval.distributions[0].before * 100)

            # const consumed = interval.consumers.map((c) => Math.round(c.before * 100)); # TS map, Math.round
            consumed: List[int] = array_map(interval.consumers, lambda c: math_round(c.before * 100))

            for iteration in range(iterations):
                energyThisRound = toShare
                for i in range(len(consumed)):
                    # Allocations are in %, so we need to divide by 100. The EDC manual explicitly says they truncate down here
                    # const shared = Math.min( # TS Math.min
                    #    consumed[i],
                    #    Math.trunc(energyThisRound * allocationsFraction[i]), # TS Math.trunc
                    # );
                    shared = math_min(
                        consumed[i],
                        math_trunc(energyThisRound * allocationsFraction[i]),
                    )
                    consumed[i] -= shared
                    toShare -= shared
                    profitPerEan[i] += shared * costsPerKwh[i]
                    # console.log(shared); # Commented out

        return sumContainer(profitPerEan) / 100

    # progressCallback is called at the end with final value
    def optimizeAllocation(
        self,
        sharingRounds: int,
        costsPerKwh: List[float],
        algorithm: OptimizationAlgorithm,
        maxFails: int,
        restarts: int,
        progressCallback: callable,  # (resultSoFar: OptimizedAllocation, iteration: number) => void
    ):
        startTime = time.time()  # Using time.time() for wall clock time as in TS Date.now()
        result = self._Csv__optimizeAllocationIteration(sharingRounds, costsPerKwh, algorithm, maxFails)

        progress = 0

        def iterate():
            nonlocal progress, result  # Allow modifying outer scope variables
            progress += 1
            newResult = self._Csv__optimizeAllocationIteration(
                sharingRounds,
                costsPerKwh,
                algorithm,
                maxFails,
            )
            console_log(
                f"Restart {progress} Achieved sharing {sumContainer(newResult['sharing'])} yielding {sumContainer(newResult['profit'])} CZK",
            )
            if sumContainer(newResult['profit']) > sumContainer(result['profit']):
                result = newResult

            # progressCallback(result, progress); # Call the callback
            progressCallback(result, progress)

            if progress < restarts:
                # setTimeout(iterate, 0); # TS setTimeout
                # Use threading.Timer to simulate non-blocking scheduling
                threading.Timer(0, iterate).start()
            else:
                console_log("optimizeAllocation TOTAL took ", time.time() - startTime, " s")  # Using seconds for time.time()

        # setTimeout(iterate, 0); # TS setTimeout
        threading.Timer(0, iterate).start()  # Start the first iteration

    def getFilteredCsv(self) -> str:
        timeStart = datetime.datetime.now().timestamp() * 1000  # Get milliseconds timestamp
        result = "Datum;Cas od;Cas do;"
        hasConsumer = False
        for ean in self.consumerEans:
            # if (!gSettings.hiddenEans.has(ean.name)) { # TS Set.has
            if not set_has(gSettings.hiddenEans, ean.name):
                result += f"IN-{ean.name}-O;OUT-{ean.name}-O;"
                hasConsumer = True

        assert_condition(hasConsumer, "Pro export CSV musí být zobrazen aspoň jeden odběratelský EAN")
        result += "IN-859182400000000000-D;OUT-859182400000000000-D\n"  # Virtual EANs that will be the inverse of consumption

        # const printNumberCzech = (x: number): string => x.toFixed(2).replaceAll(".", ","); # TS arrow function, toFixed, replaceAll
        def printNumberCzech(x: float) -> str:
            return replace_all(to_fixed(x, 2), ".", ",")

        for interval in self.getGroupedIntervals("15m"):
            # result += `${String(interval.start.getDate()).padStart(2, "0")}.${String(interval.start.getMonth() + 1).padStart(2, "0")}.${interval.start.getFullYear()};`; # TS template literal, padStart, getMonth (0-11)
            # Python datetime month is 1-12
            result += f"{pad_start_general(str(interval.start.day), 2, '0')}.{pad_start_general(str(interval.start.month), 2, '0')}.{interval.start.year};"

            # const intervalEnd = structuredClone(interval.start); # TS structuredClone
            intervalEnd = structured_clone(interval.start)
            # intervalEnd.setMinutes(intervalEnd.getMinutes() + 15); # TS setMinutes
            intervalEnd = intervalEnd + datetime.timedelta(minutes=15)

            for time_obj in [interval.start, intervalEnd]:
                # result += `${String(time.getHours()).padStart(2, "0")}:${String(time.getMinutes()).padStart(2, "0")};`; # TS template literal, padStart
                result += f"{pad_start_general(str(time_obj.hour), 2, '0')}:{pad_start_general(str(time_obj.minute), 2, '0')};"

            sumShared = 0.0
            for i in range(len(self.consumerEans)):
                # if (!gSettings.hiddenEans.has(this.consumerEans[i].name)) { # TS Set.has
                if not set_has(gSettings.hiddenEans, self.consumerEans[i].name):
                    result += f"{printNumberCzech(-interval.consumers[i].before)};"
                    result += f"{printNumberCzech(-interval.consumers[i].after)};"
                    sumShared += interval.consumers[i].before - interval.consumers[i].after

            result += f"{printNumberCzech(sumShared)};0;\n"

        console_log("getFilteredCsv took", datetime.datetime.now().timestamp() * 1000 - timeStart, "ms")
        return result

    # private #getDayFilterDates(): [Date, Date] { # TS private method
    def _Csv__getDayFilterDates(self) -> List[datetime.datetime]:  # Python name mangling
        # const dateFrom = structuredClone(this.dateFrom); # TS structuredClone
        dateFrom = structured_clone(self.dateFrom)
        # dateFrom.setDate(dateFrom.getDate() + gSettings.minDayFilter); # TS setDate
        dateFrom = dateFrom + datetime.timedelta(days=gSettings.minDayFilter)

        # const dateTo = structuredClone(this.dateFrom); # TS structuredClone
        dateTo = structured_clone(self.dateFrom)
        # dateTo.setDate(dateTo.getDate() + gSettings.maxDayFilter + 1); # TS setDate
        dateTo = dateTo + datetime.timedelta(days=gSettings.maxDayFilter + 1)
        # dateTo.setMinutes(dateTo.getMinutes() - 1); # TS setMinutes
        dateTo = dateTo + datetime.timedelta(minutes=-1)

        return [dateFrom, dateTo]

    # private #optimizeAllocationIteration( # TS private method
    def _Csv__optimizeAllocationIteration(# Python name mangling
        self,
        sharingRounds: int,
        costsPerKwh: List[float],
        algorithm: OptimizationAlgorithm,
        maxFails: int,
    ) -> OptimizedAllocation:

        # const clampTo2 = (num: number): number => Math.trunc(num * 100) / 100; # TS arrow function, Math.trunc
        def clampTo2(num: float) -> float:
            return math_trunc(num * 100) / 100.0

        timeStart = time.time()  # Using time.time() for wall clock time
        # let weights = Array<number>(this.consumerEans.length); # TS Array initialization
        weights: List[float] = array_fill(len(self.consumerEans), 0.0)
        for i in range(len(weights)):
            weights[i] = math_random() * 100

        sumInitial = sumContainer(weights)
        for i in range(len(weights)):
            weights[i] /= sumInitial / 99.99

        # console.log("initial random weights", weights); # Commented out

        # const bumpConsumer = (index: number, amount: number): number[] => { # TS arrow function
        def bumpConsumer(index: int, amount: float) -> List[float]:
            # const result = structuredClone(weights); # TS structuredClone
            result = structured_clone(weights)
            # const eligibleUp = Math.min(amount, 100 - result[index]); # TS Math.min
            eligibleUp = math_min(amount, 100 - result[index])
            eligibleDown = 0.0
            desiredDownIndividual = eligibleUp / (len(result) - 1) if len(result) > 1 else 0.0  # Handle division by zero if only one consumer
            for i in range(len(result)):
                if i != index:
                    # eligibleDown += Math.min(desiredDownIndividual, result[i]); # TS Math.min
                    eligibleDown += math_min(desiredDownIndividual, result[i])

            # const change = Math.min(eligibleUp, eligibleDown); # TS Math.min
            change = math_min(eligibleUp, eligibleDown)
            assert_condition(change >= 0)  # Change can be 0 if eligibleUp or eligibleDown is 0
            if change > 0:  # Only apply changes if there's something to change
                result[index] = clampTo2(result[index] + change)
                for i in range(len(result)):
                    if i != index:
                        # result[i] = Math.max(0, clampTo2(result[i] - desiredDownIndividual)); # TS Math.max
                        result[i] = math_max(0.0, clampTo2(result[i] - desiredDownIndividual))

                # Finally, add the unallocated amount to the consumer which we are bumping:
                result[index] = clampTo2(result[index] + 99.99 - sumContainer(result))

            return result

        filteredIntervals = self.getGroupedIntervals("15m")

        bestSharingProfit = self.simulateSharingFast(
            filteredIntervals,
            weights,
            costsPerKwh,
            sharingRounds,
        )
        failedInRow = 0
        iterations = 0
        # let bestWeights = structuredClone(weights); # TS structuredClone
        bestWeights = structured_clone(weights)

        while failedInRow < maxFails:
            iterations += 1

            thisTotalProfit = 0.0
            if algorithm == "gradientDescend":
                # This gradient descend implementation in TS seems incomplete or simplified.
                # It calculates differences but doesn't use them to update weights.
                # Translating as is, but noting this discrepancy.
                STEP = 1
                # const differences = [] as number[]; # TS array initialization
                differences: List[float] = []
                for i in range(len(self.consumerEans)):
                    resultProfit = self.simulateSharingFast(
                        filteredIntervals,
                        bumpConsumer(i, STEP),
                        costsPerKwh,
                        sharingRounds,
                    )
                    differences.append(resultProfit - bestSharingProfit)

                # console.log(differences); # Commented out
                max_index = 0
                for i in range(1, len(differences)):
                    if differences[i] > differences[max_index]:
                        max_index = i

                # The original TS code calculates thisTotalProfit here but doesn't use it
                # to update weights in the gradientDescend branch.
                # Keeping the calculation for exact translation, but noting it's unused.
                thisTotalProfit = self.simulateSharingFast(
                    filteredIntervals,
                    weights,  # Uses current weights, not the bumped ones
                    costsPerKwh,
                    sharingRounds,
                )
                # The logic below (checking thisTotalProfit <= bestSharingProfit)
                # will likely always increment failedInRow in the gradientDescend branch
                # because thisTotalProfit is calculated using the *current* weights,
                # not the weights that yielded the 'max' difference.
                # This suggests the gradientDescend part might be unfinished or incorrect
                # in the original TS code. Translating the logic as written.

            else:  # algorithm == "random"
                randomIndex = math_trunc(math_random() * len(self.consumerEans))
                # const randomAmount = Math.abs(gaussianRandom(0, 5)); # TS Math.abs
                randomAmount = math_abs(gaussianRandom(0, 5))
                # console.log("random amount", randomAmount); # Commented out
                proposedWeights = bumpConsumer(randomIndex, randomAmount)
                proposedProfit = self.simulateSharingFast(
                    filteredIntervals,
                    proposedWeights,
                    costsPerKwh,
                    sharingRounds,
                )
                if proposedProfit > bestSharingProfit:
                    weights = proposedWeights
                    # console.log(proposedWeights); # Commented out
                    thisTotalProfit = proposedProfit  # Update thisTotalProfit only if proposedProfit is better
                else:
                    # If random step didn't improve, thisTotalProfit remains 0.0 from initialization
                    # or the value from the previous successful step.
                    # The check `thisTotalProfit <= bestSharingProfit` below will handle this.
                    pass  # No change to weights or thisTotalProfit if not improved

            # Check if the current iteration's profit (thisTotalProfit) is not better than the best found so far.
            # Note: In the 'gradientDescend' branch, thisTotalProfit is calculated using the *current* weights,
            # not the weights from the 'bumpConsumer' call that found the max difference.
            # This makes the 'gradientDescend' logic here potentially flawed as per the original TS.
            if thisTotalProfit <= bestSharingProfit:
                failedInRow += 1
            else:
                # console.log(thisTotal); # Commented out
                bestSharingProfit = thisTotalProfit
                # bestWeights = structuredClone(weights); # TS structuredClone
                bestWeights = structured_clone(weights)
                failedInRow = 0

        # After the loop finishes (maxFails reached), run simulateSharing with the best weights found
        final = self.simulateSharing(bestWeights, costsPerKwh, sharingRounds)

        # assert_condition( # TS assert
        #    Math.abs( # TS Math.abs
        #        sumContainer(final.profitPerEan) -
        #            this.simulateSharingFast(filteredIntervals, bestWeights, costsPerKwh, sharingRounds),
        #    ) < 0.01,
        #    sumContainer(final.profitPerEan),
        #    this.simulateSharingFast(filteredIntervals, bestWeights, costsPerKwh, sharingRounds),
        # );
        assert_condition(
            math_abs(
                sumContainer(final['profitPerEan']) - 
                    self.simulateSharingFast(filteredIntervals, bestWeights, costsPerKwh, sharingRounds),
            ) < 0.01,
            sumContainer(final['profitPerEan']),
            self.simulateSharingFast(filteredIntervals, bestWeights, costsPerKwh, sharingRounds),
        )

        console_log(
            f"Optimize Weights iteration took {iterations} iterations and {time.time() - timeStart} s. Sharing achieved: {sumContainer(final['sharingPerEan'])} kWh, {sumContainer(final['profitPerEan'])} CZK",
        )
        # console.log(`Sum weights ${bestWeights.reduce((w, a) => w + a, 0)}`); # Commented out
        # assert_condition(bestWeights.reduce((w, a) => w + a, 0) <= 100); # TS reduce
        assert_condition(array_reduce(bestWeights, lambda w, a: w + a, 0) <= 100)

        return { 'profit': final['profitPerEan'], 'weights': bestWeights, 'sharing': final['sharingPerEan'] }



# Helper for Math.abs
def math_abs(x: float) -> float:
    return abs(x)


def parse_csv(csv: str, filename: str) -> Csv:
    csv = csv.replace("\r\n", "\n")
    lines = csv.split("\n")
    assert_condition(len(lines) > 0, "CSV file is empty")
    header = lines[0].split(";")
    assert_condition(
        len(header) > 3,
        f"CSV file has invalid header - less than 3 elements. Is there an extra empty line? The entire line is \"{lines[0]}\"",
    )
    assert_condition(header[0] == "Datum" and header[1] == "Cas od" and header[2] == "Cas do")
    assert_condition(
        len(header) % 2 == 1,
        f"Wrong number of CSV header fields - must be 3 + 2* number of EANs. Got {len(header)}",
    )

    distributor_eans: List[Ean] = []
    consumer_eans: List[Ean] = []

    for i in range(3, len(header), 2):
        before = header[i].strip()
        after = header[i + 1].strip()
        assert_condition(before[2:] == after[3:], "Mismatched IN- and OUT-", before, after)

        is_distribution = before.endswith("-D")
        # Calculate end index for substring: len(before) - 2
        ean_number = before[3:len(before) - 2]
        if is_distribution:
            distributor_eans.append(Ean(ean_number, i))
        else:
            assert_condition(before.endswith("-O"), before)
            consumer_eans.append(Ean(ean_number, i))
        assert_condition(before.startswith("IN-") and after.startswith("OUT-"), before, after)

    # Maps from time to missing sharing for that time slot
    intervals: List[Interval] = []

    for i in range(1, len(lines)):
        if len(lines[i].strip()) == 0:
            continue
        exploded_line = lines[i].split(";")

        expected_length = 3 + (len(consumer_eans) + len(distributor_eans)) * 2
        # In some reports there is an empty field at the end of the line
        assert_condition(
            len(exploded_line) == expected_length or
                (len(exploded_line) == expected_length + 1 and last(exploded_line) == ""),
            f"Wrong number of items: {len(exploded_line)}, expected: {expected_length}, line number: {i}. Last item on line is \"{last(exploded_line)}\"",
        )
        date_start = getDate(exploded_line)

        if len(intervals) > 0:
            last_start = last(intervals).start
            minutes_this = date_start.hour * 60 + date_start.minute
            minutes_last = last_start.hour * 60 + last_start.minute
            minutes_diff = minutes_this - minutes_last

            # Using if/elif/else to translate switch
            if minutes_diff == -1425:  # Day break
                pass  # break
            elif minutes_diff == 15:  # 15 minutes - regular
                pass  # break
            elif minutes_diff == 75:  # 1:15 - missing 1 hour (4 entries) due to DST adjustment
                assert_condition(date_start.hour == 3)
                print("DST!!!!!!!!!!!!!!!!!!!!!!!!!!", date_start)
                pass  # break
            elif minutes_diff == -45:  # -0:45 - missing 1 hour due to DST adjustment
                assert_condition(date_start.hour == 2)
                print("DST!!!!!!!!!!!!!!!!!!!!!!!!!!", date_start)
                pass  # break
            else:
                assert_condition(False, f"Unexpected time difference: {minutes_diff} minutes at line {i}", date_start)

        distributed: List[Measurement] = []
        consumed: List[Measurement] = []

        errors: List[str] = []

        def parse_pair(cell_before: str, cell_after: str, ean: Ean) -> tuple[float, float]:
            before = parseKwh(cell_before)
            # In "Aktuální hodnoty", the after value could be missing while before value is present. Let's assume no sharing in that case
            if cell_after == "" and cell_before != "":
                error = f"Pro EAN {ean.name} chybí hodnota pro ponížená data. Sdílení pro tento časový úsek bude nastaveno na 0."
                logWarning(error, date_start)
                errors.append(error)
                return (before, before)
            else:
                # When EAN is added in the middle of the report time frame, both before and after are missing. We will return zeroes
                return (before, parseKwh(cell_after))

        for ean in distributor_eans:
            before, after = parse_pair(exploded_line[ean.csvIndex], exploded_line[ean.csvIndex + 1], ean)
            if after > before:
                error = f"Výroba zdroje {ean.name} je po započítání sdílení VYŠŠÍ o {after - before} kWh. Sdílení pro tento časový úsek bude nastaveno na 0."
                logWarning(error, date_start)
                errors.append(error)
                after = before
            if before < 0 or after < 0:
                # Note: The original TS code had before / after here, which is likely a typo
                # and should probably be just the values themselves or a difference.
                # Translating literally but noting the potential issue.
                error = f"Výrobní zdroj {ean.name} odebírá energii ze sítě ({before} / {after} kWh). Odběr/výroba pro tento časový úsek bude nastavena na 0."
                logWarning(error, date_start)
                errors.append(error)
                before = max(0.0, before)
                after = max(0.0, after)
            distributed.append(Measurement(before=before, after=after, missed=0.0))

        for ean in consumer_eans:
            before, after = parse_pair(exploded_line[ean.csvIndex], exploded_line[ean.csvIndex + 1], ean)
            before *= -1
            after *= -1
            if after > before:
                error = f"Odběrovému EAN {ean.name} se po započítání sdílení ZVÝŠILA spotřeba o {after - before} kWh. Sdílení pro tento časový úsek bude nastaveno na 0."
                logWarning(error, date_start)
                errors.append(error)
                after = before
            if before < 0 or after < 0:
                # Note: The original TS code had before / after here, which is likely a typo
                # and should probably be just the values themselves or a difference.
                # Translating literally but noting the potential issue.
                error = f"Odběrový EAN {ean.name} dodává energii do sítě ({before} / {after} kWh). Odběr/výroba pro tento časový úsek bude nastavena na 0."
                logWarning(error, date_start)
                errors.append(error)
                before = max(0.0, before)
                after = max(0.0, after)
            consumed.append(Measurement(before=before, after=after, missed=0.0))

        sum_distributors_after = sumContainer(val.after for val in distributed)
        sum_distributors_before = sumContainer(val.before for val in distributed)
        sum_consumers_after = sumContainer(val.after for val in consumed)
        sum_consumers_before = sumContainer(val.before for val in consumed)
        sum_shared = sum_distributors_before - sum_distributors_after
        assert_condition(sum_shared >= 0, sum_shared, "Line", i)

        if abs(sum_shared - (sum_consumers_before - sum_consumers_after)) > 0.0001:
            sum_shared_consumers = sum_consumers_before - sum_consumers_after
            error = f"Energie nasdílená od výrobních zdrojů ({printKWh(sum_shared)}) neodpovídá energii nasdílené do odběratelských míst ({printKWh(sum_shared_consumers)})!. V reportu se použije nižší z hodnot."
            logWarning(error, date_start)
            errors.append(error)
            if sum_shared > sum_shared_consumers:
                # Avoid division by zero if sum_shared is 0
                fix_distributors = sum_shared_consumers / sum_shared if sum_shared != 0 else 0.0
                print("Fixing distributors", fix_distributors)
                assert_condition(
                    fix_distributors <= 1 and fix_distributors >= 0 and not math.isnan(fix_distributors),
                    sum_shared_consumers,
                    sum_shared,
                )
                for j in distributed:
                    j.after *= fix_distributors
            else:
                # Avoid division by zero if sum_shared_consumers is 0
                fix_consumers = sum_shared / sum_shared_consumers if sum_shared_consumers != 0 else 0.0
                print("Fixing consumers", fix_consumers)
                assert_condition(
                    fix_consumers <= 1 and fix_consumers >= 0 and not math.isnan(fix_consumers),
                    sum_shared,
                    sum_shared_consumers,
                )
                for j in consumed:
                    j.after *= fix_consumers

                # Different attempt to fix it:
                # Coefficient is sum of missed consumption / sum of consumed
                # const coefficient = (sumSharedConsumers - sumShared) / sumConsumersBefore;
                # console.log("Fixing consumers", coefficient);
                # assert_condition(coefficient > 0, sumShared, sumSharedConsumers);
                # for (const j of consumed) {
                #    j.after += j.before * coefficient;
                # }

        # If there is still some power left after sharing, we check that all consumers have 0 adjusted power.
        # If there was some consumer left with non-zero power, it means there was energy that could have been
        # shared, but wasn't due to bad allocation.
        sum_missed = 0.0

        def any_over_threshold(measurements: List[Measurement]) -> bool:
            for measurement in measurements:
                # There are plenty of intervals where distribution before and after are both 0.01 and no sharing is performed...:
                if measurement.after > 0:
                    return True
            return False

        # Recalculate sums after potential fixing
        sum_consumers_after_fixed = sumContainer(val.after for val in consumed)
        sum_distributors_after_fixed = sumContainer(val.after for val in distributed)

        if any_over_threshold(distributed) and any_over_threshold(consumed):
            sum_missed = min(sum_consumers_after_fixed, sum_distributors_after_fixed)
            # Avoid division by zero
            if sum_consumers_after_fixed != 0:
                for c in consumed:
                    c.missed = (c.after / sum_consumers_after_fixed) * sum_missed
                    assert_condition(not math.isnan(c.missed))
            else:
                for c in consumed:
                    c.missed = 0.0  # If sum is 0, all after values must be 0, so missed is 0

            # Avoid division by zero
            if sum_distributors_after_fixed != 0:
                for p in distributed:
                    p.missed += (p.after / sum_distributors_after_fixed) * sum_missed
                    assert_condition(not math.isnan(p.missed))
            else:
                for p in distributed:
                    p.missed += 0.0  # If sum is 0, all after values must be 0, so missed is 0

        intervals.append(Interval(
            start=date_start,
            sumSharing=sum_shared,
            sumMissed=sum_missed,
            sumProduction=sum_distributors_before,
            distributions=distributed,
            consumers=consumed,
            errors=errors,
        ))

    return Csv(filename, intervals, distributor_eans, consumer_eans)

