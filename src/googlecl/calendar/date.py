# Copyright (C) 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Classes and functions for manipulating strings into dates.

Some parts are specific to Google Calendar."""

__author__ = 'thmiller@google.com (Tom Miller)'
import datetime
import re
import googlecl.base

QUERY_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.000Z'

ACCEPTED_DAY_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
ACCEPTED_DAY_FORMATS = [googlecl.base.DATE_FORMAT,
                        '%m/%d',
                        '%m/%d/%Y',
                        '%m/%d/%y',
                        '%b %d',
                        '%B %d',
                        '%b %d %Y',
                        '%B %d %Y']
ACCEPTED_TIME_FORMATS = ['%I%p',
                         '%I %p',
                         '%I:%M%p',
                         '%I:%M %p',
                         '%H:%M']
# Regular expression for strings that specify a time that could be afternoon or
# morning. First group will be the hour, second the minutes.
AMBIGUOUS_TIME_REGEX = '((?:1[0-2])|(?:[1-9]))?(?::([0-9]{2}))?$'

_DAY_TIME_TOKENIZERS = ['@', ' at ']
_RANGE_TOKENIZERS = [',']


class Error(Exception):
  """Base error for this module."""
  pass


def datetime_today():
  """Creates a datetime object with zeroed-out time parameters."""
  return datetime.datetime.now().replace(hour=0,
                                         minute=0,
                                         second=0,
                                         microsecond=0)


def determine_duration(duration_token):
  """Determines a duration from a non-time token.

  Args:
    duration_token: String of hours and minutes.

  Returns:
    Timedelta object representing positive offset of hours and minutes.
  """
  hour, minute = parse_ambiguous_time(duration_token)
  if not (hour or minute):
    raise ValueError('Duration must be in form of [hours][:minutes]')
  return datetime.timedelta(hours=hour, minutes=minute)


def get_utc_timedelta():
  """Return the UTC offset of local zone at present time as a timedelta."""
  import time
  if time.localtime().tm_isdst and time.daylight:
    return datetime.timedelta(hours=time.altzone/3600)
  else:
    return datetime.timedelta(hours=time.timezone/3600)


def parse_ambiguous_time(time):
  """Parses an ambiguous time into an hour and minute value.

  Args:
    time: Ambiguous time to be parsed. "Ambiguous" means it could be before noon
    or after noon. For example, "5:30" or "12"

  Returns:
    Tuple of (hour, minute). The hour is still not on a 24 hour clock.
  """
  ambiguous_time = re.match(AMBIGUOUS_TIME_REGEX, time)
  if not ambiguous_time:
    return None, None

  hour_text = ambiguous_time.group(1)
  minute_text = ambiguous_time.group(2)
  if hour_text:
    hour = int(hour_text)
  else:
    hour = 0
  if minute_text:
    minute = int(minute_text)
  else:
    minute = 0
  return hour, minute


def split_string(string, tokenizers=None):
  """Splits a string based on a list of potential substrings.

  Strings will only be split once, if at all. That is, at most two tokens can be
  returned, even if a tokenizer is found in multiple positions. The left-most
  tokenizer will be used to split.

  Args:
    string: String to split.
    tokenizers: List of strings that should act as a point to split around.
        Default None to use range tokenizers defined in this module.

  Returns:
    Tuple of (left_token, [True|False], right_token). The middle element is True
    if a tokenizer was found in the provided string, and is False otherwise.
  """
  if not string:
    return ('', False, '')
  if not tokenizers:
    tokenizers = _RANGE_TOKENIZERS
  for tokenizer in tokenizers:
    if string.find(tokenizer) != -1:
      left_token, _, right_token = string.partition(tokenizer)
      return (left_token.strip(), True, right_token.strip())
  return (string.strip(), False, '')


def split_time(date_string, tokenizers):
  day_token, _, hour_token = split_string(date_string, tokenizers)
  if not hour_token:
    # If there was not a specific token for the hour, assume that the
    # day_token c
    hour_token = day_token
    day_token = ''
  return day_token, hour_token


def _is_specific_date(day_token):
  if day_token == 'today' or day_token.lower().find('%y') != -1:
    return True
  else:
    return False


class Date(object):
  def __init__(self, local_datetime=None, utc_datetime=None, all_day=False):
    """Does not check utc info, pass with appropriate keyword argument."""
    if not (local_datetime or utc_datetime):
      raise Error('Need to provide a local or UTC datetime')
    if local_datetime:
      self.local = local_datetime
      if not utc_datetime:
        self.utc = self.local + get_utc_timedelta()
    if utc_datetime:
      self.utc = utc_datetime
      if not local_datetime:
        self.local = self.utc - get_utc_timedelta()
    self.all_day = all_day

  def __add__(self, other):
    """Returns a Date with other added to its time."""
    return Date(utc_datetime=(self.utc + other), all_day=self.all_day)

  def __sub__(self, other):
    """Returns a Date with other subtracted from its time."""
    return Date(utc_datetime=(self.utc - other))

  def __str__(self):
    basic_string_format = '%m/%d/%Y'
    if self.all_day:
      return self.local.strftime(basic_string_format)
    else:
      return self.local.strftime(basic_string_format + ' %H:%M')

  def to_query(self):
    """Converts UTC data to a query-friendly, date-inclusive string."""
    return self.to_format(QUERY_DATE_FORMAT)

  def to_inclusive_query(self):
    """Converts UTC data to query-friendly, date-inclusive string."""
    if self.all_day:
      delta = datetime.timedelta(hours=24)
      new_datetime = self.utc + delta
    else:
      new_datetime = self.utc
    return new_datetime.strftime(QUERY_DATE_FORMAT)

  def to_day(self):
    """Returns date formatted according to whether or not Date is an all-day
    date or not."""
    if self.all_day:
      return self.to_format(googlecl.base.DATE_FORMAT)
    else:
      return self.to_query()

  def to_format(self, format_string):
    """Converts UTC data to specific format string."""
    return self.utc.strftime(format_string)


class DateParser(object):
  """Produces Date objects given data."""

  def __init__(self, today=None, now=None):
    """Initializes the DateParser object.

    Args:
      today: Function capable of giving the current local date.
      now: Function capable of giving the current local time.
    """
    if today is None:
      today = datetime_today
    if now is None:
      now = datetime.datetime.now
    self.today = today
    self.now = now

  def parse(self, text, base=None, shift_dates=True):
    """Parses text into a Date object.

    Args:
      text: String representation of one date, or an offset from a date. Will be
          interpreted as local time, unless "UTC" appears somewhere in the text.
      base: Starting point for this Date. Used if the text represents an hour,
          or an offset.
      shift_dates: If the date is earlier than self.today(), and the year is not
          specified, shift it to the future. True by default.
          Set to False if you want to set a day in the past without referencing
          the year. For example, today is 10/25/2010. Parsing "10/24" with
          shift_dates=True will return a date of 10/24/2011. If
          shift_dates=False, will return a date of 10/24/2010.

    Returns:
      Date object.
    """
    delta = datetime.timedelta(hours=0)
    day = None
    try:
      # Unlikely anyone uses this, but if so, it's done in one shot
      return Date(local_datetime=datetime.datetime.strptime(text,
                                                      ACCEPTED_DAY_TIME_FORMAT))
    except ValueError:
      pass

    day_token, _, time_token = split_string(text, _DAY_TIME_TOKENIZERS)
    if not (day_token or time_token):
      raise ValueError('Invalid time text: "%s" ' % time_text)

    past_time_to_tomorrow = False
    if day_token:
      try:
        day = self._determine_day(day_token, shift_dates)
      except ValueError:
        past_time_to_tomorrow = True
        time_token = day_token
        if base:
          day = base
      else:
        all_day = True

    if time_token:
      all_day = False
      if time_token.startswith('+'):
        delta = determine_duration(time_token.lstrip('+'))
        if not day:
          day = self.now()
      else:
        time = self._determine_time(time_token)
        if past_time_to_tomorrow and self._time_has_passed(time):
          delta = datetime.timedelta(hours=time.hour + 24, minutes=time.minute)
        else:
          delta = datetime.timedelta(hours=time.hour, minutes=time.minute)
        if not day:
          day = self.today()

    return Date(local_datetime=day + delta, all_day=all_day)

  def _day_has_passed(self, date):
    """"Checks to see if date has passed."""
    today = self.today()
    return (date.month < today.month or
            (date.month == today.month and date.day < today.day))

  def _determine_day(self, day_token, shift_dates):
    if day_token == 'tomorrow':
      return self.today() + datetime.timedelta(hours=24)
    elif day_token == 'today':
      return self.today()
    else:
      date, valid_format = self._extract_time(day_token, ACCEPTED_DAY_FORMATS)
      # If the year was not explicitly mentioned...
      # (strptime will set a default year of 1900)
      if valid_format.lower().find('%y') == -1:
        if self._day_has_passed(date) and shift_dates:
          date = date.replace(year=self.today().year + 1)
        else:
          date = date.replace(year=self.today().year)
      return date

  def _determine_time(self, time_token):
    hour, minute = parse_ambiguous_time(time_token)
    if (hour or minute):
      # The ambiguous hours arranged in order, according to Google Calendar:
      # 7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6
      if 1 <= hour and hour <= 6:
        hour += 12
    else:
      tmp, _ = self._extract_time(time_token, ACCEPTED_TIME_FORMATS)
      hour = tmp.hour
      minute = tmp.minute
    return datetime.time(hour=hour, minute=minute)

  def _extract_time(self, time, possible_formats):
    """Returns date data contained in a string.

    Args:
      time: String representing a date and/or time.
      possible_formats: List of possible formats "time" may be in.

    Returns:
      datetime object populated by data found in "time", or None if no formats
      matched.
    """
    for time_format in possible_formats:
      try:
        date = datetime.datetime.strptime(time, time_format)
      except ValueError, err:
        continue
      else:
        return date, time_format
    raise ValueError('Token "%s" does not match any provided formats' % time)

  def _time_has_passed(self, time):
    now = self.now()
    return (time.hour < now.hour or
            (time.hour == now.hour and time.minute < now.minute))


class DateRange(object):
  def __init__(self, start, end, is_range):
    self.start = start
    self.end = end
    self.specified_as_range = is_range

class DateRangeParser(object):
  """Parser that treats strings as ranges."""

  def __init__(self, today=None, now=None, range_tokenizers=None):
    """Initializes the object.

    Args:
      today: Callback that returns the date.
      now: Callback that returns the date and time.
      range_tokenizers: List of strings that will be used to split date strings
          into tokens. Default None to use module default.
    """
    self.date_parser = DateParser(today, now)
    if range_tokenizers is None:
      range_tokenizers = _RANGE_TOKENIZERS
    self.range_tokenizers = range_tokenizers

  def parse(self, date_string, shift_dates=False):
    """"Parses a string into a start and end date.

    Note: This is Google Calendar specific. If date_string does not contain a
    range tokenizer, it will be treated as the starting date of a one day range.

    Args:
      date_string: String to parse.
      shift_dates: Whether or not to shift a date to next year if it has
          occurred earlier than today. See documentation for DateParser. Default
          False.

    Returns:
      Tuple of (start_date, end_date), representing start and end dates of the
      range. Either may be None, in which case it is an open range (i.e. from
      start until the distant future, or from the distant past until the end
      date.) If date_string is empty or None, this will be (None, None).
    """
    start_date = None
    end_date = None
    if not date_string:
      return (None, None)
    start_text, is_range, end_text = split_string(date_string,
                                                  self.range_tokenizers)
    if start_text:
      start_date = self.date_parser.parse(start_text, shift_dates=shift_dates)
    if end_text:
      if start_date:
        base = start_date.local
      else:
        base = None
      end_date = self.date_parser.parse(end_text, base=base,
                                        shift_dates=shift_dates)
    elif not is_range:
      # If no range tokenizer was given, the end date is effectively the day
      # after the given date.
      end_date = start_date
    return DateRange(start_date, end_date, is_range)
