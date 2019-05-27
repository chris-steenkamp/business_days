import datetime as dt
from functools import singledispatch
from locale import getdefaultlocale

__holidays = {}
__cache = set()

__min_year = None
__max_year = None
__current_locale = None

class _Holiday(object):
    '''Container for public holiday meta information.

    Most holidays recur on the same day every year so these
    only require the month and day. Once-off holidays occur
    at a fixed point in time so they require the exact date
    to be specified. The exact date of other holidays (such
    as Easter) is based on a formula and will differ each
    year. These types of holidays can be specified either as
    once-off holidays or by specfiying actual the formula.
    '''
    def __init__(self, name, type_cd, value, locale):
        self.__name = name
        self.__type_cd = type_cd
        self.__value = value
        self.__locale = locale

    def __str__(self):
        return f'{self.__locale} - {self.__name} with type code {self.__type_cd} with value {self.__value}'

    def get_type_cd(self):
        return self.__type_cd

    def get_name(self):
        return self.__name

    def get_locale(self):
        return self.__locale

    def get_effective_date(self, year=dt.datetime.today().year):
        '''Get the effective date of the holiday (adjusted if the actual date
        falls on Sunday).
        '''
        return self.__get_date(year, True)

    def get_actual_date(self, year=dt.datetime.today().year):
        '''Get the actual date of the holiday, as specified in the source file.'''
        return self.__get_date(year)

    def __get_date(self, year, effective=False):
        '''Get the date of the holiday, optionally adjusted to reflect the
        effective date, if the actual date falls on a Sunday.'''
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


def is_business_day(date):
    '''Return true if the given date is a valid business day.'''
    __check_and_update(date.year)

    return date not in __cache and date.weekday() < 5


def get_business_days(start_date, end_date=dt.datetime.today()):
    '''Gets the list of business days between to dates (inclusive).

    The end date defaults to the current day.
    '''
    __check_and_update(start_date.year)
    __check_and_update(end_date.year)

    dates = list({start_date + dt.timedelta(s) for s in range((end_date - start_date).days + 1)
                  if (start_date + dt.timedelta(s)).weekday() < 5} - __cache)
    dates.sort()

    return dates


def get_holidays(year=dt.datetime.today().year):
    '''Return the list of named holidays and their corresponding dates.

    Defaults to the list of holidays for the current year.
    '''
    __check_and_update(year)

    holidays = list({(h.get_actual_date(year), h.get_name())
                     for h in __holidays if h.get_actual_date(year).year == year and h.get_locale() == __current_locale})
    holidays.sort()
    return holidays


def get_holiday_effective_dates(year=dt.datetime.today().year):
    '''Get the list of effective public holiday dates for the given year.

    Defaults to the list of holidays for the current year.

    The effective date can differ if the public holiday falls on a Sunday,
    where the following Monday is then given as the holiday date.
    '''
    __check_and_update(year)

    dates = list({h.get_effective_date(year)
                  for h in __holidays if h.get_effective_date(year).year == year and h.get_locale() == __current_locale})
    dates.sort()

    return dates

def get_previous_business_day(date_val=dt.date.today(), *args):
    '''Return business day prior to the date specified. 

    If called without args then returns the date of the most recent
    business day.

    The date_val can be either a datetime/date object or a string.
    If date_val is a string, then you can optionally pass the format
    string as the second parameter (default is ISO 8601 %Y-%m-%d).
    '''
    return __get_previous_business_day_date(date_val, args)

@singledispatch
def __get_previous_business_day_date(date_val, *args):
    '''Internal method to handle date/datetime objects.'''
    prev_day = date_val
    while True:
        prev_day -= dt.timedelta(1)

        if is_business_day(prev_day):
            break

    return prev_day


@__get_previous_business_day_date.register(str)
def _get_previous_business_day_str(date_val, *args):
    '''Internal method to handle dates passed as a string.'''
    if len(args) and len(args[0]):
        date_fmt = args[0][0]
    else:
        date_fmt = '%Y-%m-%d'

    return __get_previous_business_day_date(dt.datetime.strptime(date_val, date_fmt)).strftime(date_fmt)


def __check_year(year):
    '''Check whether the given year in is within cached range.'''
    return year >= __min_year and year <= __max_year


def __check_and_update(year):
    '''Load holidays for year into cache if given year is not within cached range.'''
    if not __check_year(year):
        __load_holidays_for_year(year)


def __load_holidays_for_year(year):
    '''Load holidays for year into cache.'''
    global __min_year
    __min_year = min(year, __min_year)
    global __max_year
    __max_year = max(year, __max_year)
    for i in range(__max_year - __min_year + 1):
        for h in [h for h in __holidays if h.get_locale() == __current_locale]:
            __cache.add(h.get_effective_date(__min_year + i))


def __process_line(line):
    parts = line.split(',')

    return _Holiday(parts[0], parts[1], parts[2], parts[3])

def init(locale=getdefaultlocale()[0], year=dt.datetime.today().year):
    '''Initialize list of holidays for the specified year and locale'''
    global __holidays
    global __min_year
    global __max_year
    global __current_locale

    __min_year = year
    __max_year = __min_year
    __current_locale = locale

    __holidays.clear()
    __cache.clear()

    with open('public_holidays.csv', 'r') as f:
        f.readline()
        __holidays = [__process_line(l.strip())
                      for l in f.readlines() if l.strip()]

    __load_holidays_for_year(dt.datetime.today().year)


'''Initialize default values when importing the business_days module'''
init()
