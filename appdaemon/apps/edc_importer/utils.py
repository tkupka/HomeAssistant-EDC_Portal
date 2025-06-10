from dateutil.relativedelta import relativedelta
from typing import List

def getLastMonths(start_date, months) -> List[tuple]:
    return [i for i in getLastMonthsImpl(start_date, months)]

def getLastMonthsImpl(start_date, months):
    for i in range(months):
        yield (start_date.year,start_date.month)
        start_date += relativedelta(months = -1)

