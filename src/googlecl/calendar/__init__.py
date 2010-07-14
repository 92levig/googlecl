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
import googlecl.service
import googlecl

service_name = __name__.split('.')[-1]
LOGGER_NAME = googlecl.LOGGER_NAME + '.' + service_name
SECTION_HEADER = service_name.upper()
QUERY_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'


class Date(object):

  """Contains information on a date."""

  def __init__(self, date):
    """Constructor.

    Keyword arguments:
      date: String representation of a date in RFC 3339 
            ('YYYY-MM-DD' or 'YYYY-MM-DD' + 'T' + 'HH:MM:SS')
    """
    if date and date != ',':
      self.start, is_range, self.end = date.partition(',')
    else:
      self.start = None
      self.end = None
    self.utc_start_data = None
    self.utc_end_data = None
    utc_timedelta = get_utc_timedelta()
    # Even though the "when" elements of events will be properly shifted into
    # the user's timezone, all queries are interpreted as UTC (GMT) time.
    if self.start:
      try:
        start_time = datetime.datetime.strptime(self.start,
                                                googlecl.service.DATE_FORMAT)
      except ValueError:
        start_time = datetime.datetime.strptime(self.start, QUERY_DATE_FORMAT)
      self.utc_start_data = start_time + (utc_timedelta)
      # If start is defined, and not as part of a range,
      # the end should be undefined.
      if not is_range:
        # If the user specified a start, but not as a range, assume
        # they want just that day
        self.utc_end_data = self.utc_start_data + datetime.timedelta(hours=24)
    if self.end:
      try:
        end_time = datetime.datetime.strptime(self.end,
                                              googlecl.service.DATE_FORMAT)
      except ValueError:
        end_time = datetime.datetime.strptime(self.end, QUERY_DATE_FORMAT)
      self.utc_end_data = end_time + (utc_timedelta)
      # Queries exclude the end date, so advance by one day to include the day
      # the user specified.
      self.utc_end_data += datetime.timedelta(hours=24)

    if self.utc_end_data:
      self.utc_end = self.utc_end_data.strftime(QUERY_DATE_FORMAT)
    else:
      self.utc_end = None
    if self.utc_start_data:
      self.utc_start = self.utc_start_data.strftime(QUERY_DATE_FORMAT)
    else:
      self.utc_start = None


def get_utc_timedelta():
  """Return the UTC offset of local zone at present time as a timedelta."""
  import time
  if time.localtime().tm_isdst and time.daylight:
    return datetime.timedelta(hours=time.altzone/3600)
  else:
    return datetime.timedelta(hours=time.timezone/3600)
