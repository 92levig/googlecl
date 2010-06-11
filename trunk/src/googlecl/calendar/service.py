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


"""Service details and instances for the Picasa service.

Some use cases:
Add event:
  calendar add "Lunch with Tony on Tuesday at 12:00" 

List events for today:
  calendar today

"""
__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import datetime
import gdata.calendar.service
import googlecl.util as util
from googlecl.calendar import SECTION_HEADER


USER_BATCH_URL_FORMAT = \
               gdata.calendar.service.DEFAULT_BATCH_URL.replace('default', '%s')


class CalendarServiceCL(gdata.calendar.service.CalendarService,
                        util.BaseServiceCL):

  def __init__(self, regex=False, tags_prompt=False, delete_prompt=True):
    """Constructor.
    
    Keyword arguments:
      regex: Indicates if regular expressions should be used for matching
             strings, such as event titles. (Default False)
      tags_prompt: Indicates if while inserting events, instance should prompt
                   for tags for each photo. (Default False)
      delete_prompt: Indicates if instance should prompt user before
                     deleting a calendar or event. (Default True)
              
    """
    gdata.calendar.service.CalendarService.__init__(self)
    util.BaseServiceCL.set_params(self, regex, tags_prompt, delete_prompt)

  def _batch_delete_recur(self, date, event, cal_user):
    """Delete a subset of instances of recurring events."""
    request_feed = gdata.calendar.CalendarEventFeed()
    single_events = self.get_events(cal_user, date=date, 
                                    title=event.title.text,
                                    expand_recurrence=True)
    delete_events = [e for e in single_events if e.original_event and
                     e.original_event.id == event.id.text.split('/')[-1]]
    map(request_feed.AddDelete, [None], delete_events, [None])
    response_feed = self.ExecuteBatch(request_feed,
                                      USER_BATCH_URL_FORMAT % cal_user)
    for entry in response_feed.entry:
      print 'batch id: %s' % (entry.batch_id.text,)
      print 'status: %s' % (entry.batch_status.code,)
      print 'reason: %s' % (entry.batch_status.reason,)
    # For some reason, batch requests always fail...
    # Do it the slow way.
    #for d in delete_events:
    #  gdata.service.GDataService.Delete(self, d.GetEditLink().href)

  def delete_events(self, events, date, calendar_user):
    """Delete events from a calendar.
    
    Keyword arguments:
      events: List of non-expanded calendar events to delete.
      date: Date string specifying the date range of the events, as the date
            option.
      calendar_user: "User" of the calendar to delete events from.
    
    """
    single_events = [e for e in events if not e.recurrence and
                     e.event_status.value != 'CANCELED']
    recurring_events = [e for e in events if e.recurrence]
    # Not sure which is faster/better: above approach, or using set subtraction
    # recurring_events = set(events) - set(single_events)
    delete_default = util.config.getboolean('GENERAL', 'delete_by_default')
    self.Delete(single_events, 'event', delete_default)
    
    start_date, end_date = get_start_and_end(date)
    if not end_date:
      end_date = 'the distant future'
    if not start_date:
      start_date = 'the dawn of time'
    prompt_str = ('1) Instances between %s and %s\n' +
                  '2) All events in this series\n' +
                  '3) All events following %s\n' +
                  '4) Do not delete') % (start_date, end_date, end_date)
    for event in recurring_events:
      if self.prompt_for_delete:
        delete_selection = 0
        while delete_selection < 1 or delete_selection > 4:
          delete_selection = int(raw_input('Delete "%s"?\n%s\n' % 
                                           (event.title.text, prompt_str)))
        if delete_selection == 1:
          self._batch_delete_recur(date, event, calendar_user)
        elif delete_selection == 2:
          gdata.service.GDataService.Delete(self, event.GetEditLink().href)
        elif delete_selection == 3:
          self._batch_delete_recur(start_date, event, calendar_user)
      else:
        gdata.service.GDataService.Delete(self, event.GetEditLink().href)

  DeleteEvents = delete_events

  def quick_add_event(self, quick_add_strings, calendar_user):
    """Add an event using the Calendar Quick Add feature.
    
    Keyword arguments:
      quick_add_strings: List of strings to be parsed by the Calendar service,
                         as if it was entered via the "Quick Add" function.
      calendar_user: "User" of the calendar to add to.
    
    Returns:
      The event that was added, or None if the event was not added. 
    
    """
    import atom
    request_feed = gdata.calendar.CalendarEventFeed()
    for i, event_str in enumerate(quick_add_strings):
      event = gdata.calendar.CalendarEventEntry()
      event.content = atom.Content(text=event_str)
      event.quick_add = gdata.calendar.QuickAdd(value='true')
      request_feed.AddInsert(event, 'insert-request' + str(i))
    response_feed = self.ExecuteBatch(request_feed,
                                      USER_BATCH_URL_FORMAT % calendar_user)
    return response_feed.entry

  QuickAddEvent = quick_add_event

  def get_calendar_user(self, cal_name=None):
    """Get "user" name for one calendar.
    
    The "user" for a calendar is an awful misnomer for the ID for the calendar.
    To get events for a calendar, you can form a query with
      user = self.get_calendar_user('my calendar name')
      if user:
        query = gdata.calendar.CalendarEventQuery(user=user)
    
    Keyword arguments:
      cal_name: Name of the calendar to match. Default None to return the 
                uri of the default / main calendar.
      
    Returns:
      Single CalendarEntry, or None of there were no matches for cal_name.
    
    """
    import urllib
    if not cal_name or cal_name == 'default':
      return 'default'
    else:
      cal = self.GetSingleEntry('/calendar/feeds/default/allcalendars/full',
                                 cal_name,
                            converter=gdata.calendar.CalendarListFeedFromString)
      if cal:
        # Non-primary calendar feeds look like this:
        # http:blah/blah/.../feeds/JUNK%40group.calendar.google.com/private/full
        # So grab the part after /feeds/ and unquote it.
        return urllib.unquote(cal.content.src.split('/')[-3])
      else:
        return None

  GetCalendarUser = get_calendar_user

  def get_events(self, calendar_user, date=None, title=None, query=None, 
                 max_results=100, expand_recurrence=True):
    """Get events.
    
    Keyword arguments:
      calendar_user: "user" of the calendar to get events for.
      date: Date of the event(s). Sets one or both of start-min or start-max in
            the uri. Must follow the format 'YYYY-MM-DD' in one of three ways:
              '<format>' - set a start date.
              '<format>,<format>' - set a start and end date.
              ',<format>' - set an end date.
            Default None for only getting future events.
      title: Title to look for in the event, supporting regular expressions.
             Default None for any title.
      query: Query string (not encoded) for doing full-text searches on event
             titles and content.
      max_results: Maximum number of events to get. Default 100.
      expand_recurrence: If true, expand recurring events per the 'singleevents'
                         query parameter. Otherwise, don't.
    
    Returns:
      List of events from primary calendar that match the given params.
                  
    """
    query = gdata.calendar.service.CalendarEventQuery(user=calendar_user,
                                                      text_query=query)
    start_min, start_max = get_start_and_end(date)
    if start_min:
      query.start_min = start_min
    if start_max:
      query.start_max = start_max
    if expand_recurrence:
      query.singleevents = 'true'
    query.orderby = 'starttime'
    query.sortorder = 'ascend'
    query.max_results = max_results
    return self.GetEntries(query.ToUri(), title,
                           converter=gdata.calendar.CalendarEventFeedFromString)

  GetEvents = get_events

  def is_token_valid(self):
    """Check that the token being used is valid."""
    return util.BaseServiceCL.IsTokenValid(self,
                                         '/calendar/feeds/default/private/full')

  IsTokenValid = is_token_valid


service_class = CalendarServiceCL


def get_start_and_end(date):
  """Split a string representation of a date or range of dates.
  
  Ranges should be designated via a comma. For example, '2010-06-01,2010-06-20'
  will set return ('2010-06-01', '2010-06-20')
  
  Returns:
    Tuple of (start, end) where start is either the starting date or None and
                                end is either the ending date or None
  
  """
  if date and date != ',':
    # Partition won't choke on date == '2010-06-05', split will.
    start, junk, end = date.partition(',')
  else:
    # If no date is given, set a start of today.
    start = datetime.datetime.today().strftime(util.DATE_FORMAT)
    end = None
  return (start, end)


#===============================================================================
# Each of the following _run_* functions execute a particular task.
#  
# Keyword arguments:
#  client: Client to the service being used.
#  options: Contains all attributes required to perform the task
#  args: Additional arguments passed in on the command line, may or may not be
#        required
#===============================================================================
def _run_list(client, options, args):
  cal_user = client.get_calendar_user(options.cal)
  if not cal_user:
    print 'No calendar matches "' + options.cal + '"'
    return
  entries = client.get_events(cal_user,
                              date=options.date,
                              title=options.title,
                              query=options.query)
  if args:
    style_list = args[0].split(',')
  else:
    style_list = util.get_config_option(SECTION_HEADER, 'list_style').split(',')
  for e in entries:
    print util.entry_to_string(e, style_list, delimiter=options.delimiter)


def _run_list_today(client, options, args):
  now = datetime.datetime.now()
  tomorrow = now + datetime.timedelta(days=1)
  options.date = now.strftime(util.DATE_FORMAT) + ',' + \
                 tomorrow.strftime(util.DATE_FORMAT)
  _run_list(client, options, args)


def _run_add(client, options, args):
  cal_user = client.get_calendar_user(options.cal)
  if not cal_user:
    print 'No calendar matches "' + options.cal + '"'
    return
  client.quick_add_event(args, cal_user)


def _run_delete(client, options, args):
  cal_user = client.get_calendar_user(options.cal)
  if not cal_user:
    print 'No calendar matches "' + options.cal + '"'
    return
  events = client.get_events(cal_user, date=options.date,
                             title=options.title, query=options.query,
                             expand_recurrence=False)
  client.delete_events(events, options.date, cal_user)


tasks = {'list': util.Task('List events on primary calendar',
                           callback=_run_list,
                           required=['delimiter'],
                           optional=['title', 'query', 'date', 'cal']),
         'today': util.Task('List events for today',
                            callback=_run_list_today,
                            required='delimiter',
                            optional=['title', 'query', 'cal']),
         'add': util.Task('Add event to primary calendar', callback=_run_add,
                          optional='cal',
                          args_desc='QUICK_ADD_TEXT'),
         'delete': util.Task('Delete event from calendar',
                             callback=_run_delete,
                             required=[['title', 'query']],
                             optional=['date', 'cal'])}