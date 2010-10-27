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
"""Data for GoogleCL's calendar service."""
import datetime
import googlecl
import googlecl.base
import re
import time

service_name = __name__.split('.')[-1]
LOGGER_NAME = googlecl.LOGGER_NAME + '.' + service_name
SECTION_HEADER = service_name.upper()


def filter_recurring_events(events, recurrences_expanded):
  if recurrences_expanded:
    is_recurring = lambda event: event.original_event
  else:
    is_recurring = lambda event: event.recurrence
  return [e for e in events if not is_recurring(e)]


def filter_single_events(events, recurrences_expanded):
  if recurrences_expanded:
    is_single = lambda event: not event.original_event
  else:
    is_single = lambda event: not event.recurrence
  return [e for e in events if not is_single(e)]


def filter_all_day_events_outside_range(start_date, end_date, events):
  if start_date.all_day:
    start_datetime = start_date.local
  else:
    start_datetime = datetime.datetime(year=start_date.local.year,
                                       month=start_date.local.month,
                                       day=start_date.local.day)
  if end_date.all_day:
    end_datetime = end_date.local
  else:
    end_datetime = datetime.datetime(year=end_date.local.year,
                                     month=end_date.local.month,
                                     day=end_date.local.day)
  new_events = []
  for event in events:
    try:
      start = datetime.datetime.strptime(event.when[0].start_time, '%Y-%m-%d')
      end = datetime.datetime.strptime(event.when[0].end_time, '%Y-%m-%d')
    except ValueError, err:
      if str(err).find('unconverted data remains') == -1:
        raise err
      else:
        #Errors that complain of unconverted data are events with duration
        new_events.append(event)
    else:
      inclusive_end_datetime = end_datetime + datetime.timedelta(hours=24)
      if start >= start_datetime and end <= inclusive_end_datetime:
        new_events.append(event)
  return new_events


def filter_cancelled_events(events):
  return [e for e in events if e.event_status.value != 'CANCELED' or not e.when]


def get_datetimes(cal_entry):
  """Get datetime objects for the start and end of the event specified by a
  calendar entry.

  Keyword arguments:
    cal_entry: A CalendarEventEntry.

  Returns:
    (start_time, end_time, freq) where
      start_time - datetime object of the start of the event.
      end_time - datetime object of the end of the event.
      freq - string that tells how often the event repeats (NoneType if the
           event does not repeat (does not have a gd:recurrence element)).

  """
  if cal_entry.recurrence:
    return parse_recurrence(cal_entry.recurrence.text)
  else:
    freq = None
    when = cal_entry.when[0]
    try:
      # Trim the string data from "when" to only include down to seconds
      start_time_data = time.strptime(when.start_time[:19],
                                      '%Y-%m-%dT%H:%M:%S')
      end_time_data = time.strptime(when.end_time[:19],
                                    '%Y-%m-%dT%H:%M:%S')
    except ValueError:
      # Try to handle date format for all-day events
      start_time_data = time.strptime(when.start_time, '%Y-%m-%d')
      end_time_data = time.strptime(when.end_time, '%Y-%m-%d')
  return (start_time_data, end_time_data, freq)


def parse_recurrence(time_string):
  """Parse recurrence data found in event entry.

  Keyword arguments:
    time_string: Value of entry's recurrence.text field.

  Returns:
    Tuple of (start_time, end_time, frequency). All values are in the user's
    current timezone (I hope). start_time and end_time are datetime objects,
    and frequency is a dictionary mapping RFC 2445 RRULE parameters to their
    values. (http://www.ietf.org/rfc/rfc2445.txt, section 4.3.10)

  """
  # Google calendars uses a pretty limited section of RFC 2445, and I'm
  # abusing that here. This will probably break if Google ever changes how
  # they handle recurrence, or how the recurrence string is built.
  data = time_string.split('\n')
  start_time_string = data[0].split(':')[-1]
  start_time = time.strptime(start_time_string,'%Y%m%dT%H%M%S')

  end_time_string = data[1].split(':')[-1]
  end_time = time.strptime(end_time_string,'%Y%m%dT%H%M%S')

  freq_string = data[2][6:]
  freq_properties = freq_string.split(';')
  freq = {}
  for prop in freq_properties:
    key, value = prop.split('=')
    freq[key] = value
  return (start_time, end_time, freq)
