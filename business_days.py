import datetime as dt
from functools import singledispatch

__holidays = {}
__cache = set()

__min_year = None
__max_year = None


class _Holiday(object):
    def __init__(self, name, type_cd, value):
        self.__name = name
        self.__type_cd = type_cd
        self.__value = value

    def __str__(self):
        return f'{self.__name} with type code {self.__type_cd} with value {self.__value}'

    def get_type_cd(self):
        return self.__type_cd

    def get_effective_date(self, year=dt.datetime.today().year):
        return self.__get_date(year, True)

    def get_actual_date(self, year=dt.datetime.today().year):
        return self.__get_date(year)

    def __get_date(self, year, effective=False):
        if self.__type_cd == 'ONCE':
            date = dt.datetime.strptime(self.__value, '%Y%m%d')
        elif self.__type_cd == 'RECUR':
            date = dt.datetime.strptime(f'{year}{self.__value}', '%Y%m%d')
        else:
            date = dt.datetime.strptime(f'{year}0101', '%Y%m%d')

        if effective:
            if date.weekday() == 6:
                date = date + dt.timedelta(1)

        return date

    def __lt__(self, value):
        return self.get_actual_date() < value.get_actual_date()

    def __eq__(self, value):
        return self.get_effective_date() == value.get_effective_date()


def _process_line(line):
    parts = line.split(',')

    return _Holiday(parts[0], parts[1], parts[2])


def is_business_day(date):
    _check_and_update(date.year)

    return date not in __cache and date.weekday() < 5


def get_business_days(start_date, end_date=dt.datetime.today()):
    _check_and_update(start_date.year)
    _check_and_update(end_date.year)

    return {start_date + dt.timedelta(s) for s in range((end_date - start_date).days + 1) if (start_date + dt.timedelta(s)).weekday() < 5} - __cache

def get_holiday_dates(year=dt.datetime.today().year):
    _check_and_update(year)

    return {h.get_actual_date(year) for h in __holidays if h.get_actual_date(year).year == year}

def get_holiday_effective_dates(year=dt.datetime.today().year):
    _check_and_update(year)

    return {h.get_effective_date(year) for h in __holidays if h.get_effective_date(year).year == year}

@singledispatch
def get_previous_business_day(date_val=dt.date.today(), *args):
    prev_day = date_val
    while True:
        prev_day -= dt.timedelta(1)

        if is_business_day(prev_day):
            break

    return prev_day


@get_previous_business_day.register(str)
def _get_prev_business_day_str(date_val, date_fmt='%Y%m%d'):
    return get_previous_business_day(dt.datetime.strptime(date_val, date_fmt)).strftime(date_fmt)


def _check_year(year):
    return year >= __min_year and year <= __max_year


def _check_and_update(year):
    if not _check_year(year):
        _load_holidays_for_year(year)


def _load_holidays_for_year(year):
    global __min_year
    __min_year = min(year, __min_year)
    global __max_year
    __max_year = max(year, __max_year)
    for i in range(__max_year - __min_year + 1):
        for h in [h for h in __holidays]:
            __cache.add(h.get_effective_date(__min_year + i))

with open('public_holidays.csv', 'r') as f:
    f.readline()
    __holidays = [_process_line(l.strip()) for l in f.readlines() if l.strip()]

__holidays.sort()

__min_year = dt.datetime.today().year
__max_year = __min_year

_load_holidays_for_year(dt.datetime.today().year)