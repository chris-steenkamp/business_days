import datetime as dt

__holidays = {}
__recurring = set()

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

    def get_value(self, year=dt.datetime.today().year):
        if self.__type_cd == 'ONCE':
            return dt.datetime.strptime(self.__value, '%Y%m%d')
        elif self.__type_cd == 'RECUR':
            date = dt.datetime.strptime(f'{year}{self.__value}', '%Y%m%d')
            if date.weekday() == 6:
                date = date + dt.timedelta(1)
            return date
        else:
            return dt.datetime.strptime(f'{year}0101', '%Y%m%d')

    def __lt__(self, value):
        return self.get_value() < value.get_value()

    def __eq__(self, value):
        return self.get_value() == value.get_value()


def _process_line(line):
    parts = line.split(',')

    return _Holiday(parts[0], parts[1], parts[2])

def is_business_day(date):
    _check_and_update(date.year)

    return date not in __recurring and date.weekday() < 5

def get_business_days(start_date, end_date=dt.datetime.today()):
    _check_and_update(start_date.year)
    _check_and_update(end_date.year)

    return {start_date + dt.timedelta(s) for s in range((end_date - start_date).days + 1) if (start_date + dt.timedelta(s)).weekday() < 5} - __recurring

def get_holiday_dates(year=dt.datetime.today().year):
    _check_and_update(year)

    return {h.get_value(year) for h in __holidays}

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
            __recurring.add(h.get_value(__min_year + i))
    

with open('public_holidays.csv', 'r') as f:
    f.readline()
    __holidays = [_process_line(l.strip()) for l in f.readlines() if l.strip()]

__holidays.sort()

__min_year = dt.datetime.today().year
__max_year = __min_year

_load_holidays_for_year(dt.datetime.today().year)