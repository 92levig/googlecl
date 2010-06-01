"""
Service details and instances for the Picasa service.

Some use cases:
Add event:
  calendar add "Lunch with Tony on Tuesday at 12:00" 

List events for today:
  calendar today
  
Created on May 24, 2010

@author: Tom Miller

"""
__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import datetime
import gdata.calendar.service
import util
from googlecl.calendar import SECTION_HEADER


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

  def quick_add_event(self, quick_add_strings, calendar=None):
    """Add an event using the Calendar Quick Add feature.
    
    Keyword arguments:
      quick_add_strings: List of strings to be parsed by the Calendar service,
                        cal_name as if it was entered via the "Quick Add" function.
      calendar: Name of the calendar to add to. 
                Default None for primary calendar.

    Returns:
      The event that was added, or None if the event was not added. 
    
    """
    import atom
    request_feed = gdata.calendar.CalendarEventFeed()
    if calendar:
      cal = self.get_calendar(calendar)
      if not cal:
        return None
      else:
        cal_uri = cal.content.src
    else:
      cal_uri = '/calendar/feeds/default/private/full'
    for i, event_str in enumerate(quick_add_strings):
      event = gdata.calendar.CalendarEventEntry()
      event.content = atom.Content(text=event_str)
      event.quick_add = gdata.calendar.QuickAdd(value='true')
      request_feed.AddInsert(event, 'insert-request' + str(i))
    response_feed = self.ExecuteBatch(request_feed, cal_uri + '/batch')
    return response_feed.entry

  QuickAddEvent = quick_add_event

  def get_calendar(self, cal_name):
    """Get one calendar entry.
    
    Keyword arguments:
      cal_name: Name of the calendar to match.
      
    Returns:
      Single CalendarEntry, or None of there were no matches for cal_name.
    
    """
    return self.GetSingleEntry('/calendar/feeds/default/allcalendars/full',
                               cal_name,
                            converter=gdata.calendar.CalendarListFeedFromString)

  GetCalendar = get_calendar

  def get_events(self, date=None, title=None, query=None, calendar=None):
    """Get events.
    
    Keyword arguments:
      date: Date of the event(s). Sets one or both of start-min or start-max in
            the uri. Must follow the format 'YYYY-MM-DD' in one of three ways:
              '<format>' - set a start date.
              '<format>,<format>' - set a start and end date.
              ',<format>' - set an end date.
            Default None for setting a start date of today.
      title: Title to look for in the event, supporting regular expressions.
             Default None for any title.
      query: Query string (not encoded) for doing full-text searches on event
             titles and content.
      calendar: Name of the calendar to get events for. Default None for the
                primary calendar.
                 
    Returns:
      List of events from primary calendar that match the given params.
                  
    """
    import urllib
    user = 'default'
    if calendar:
      cal = self.get_calendar(calendar)
      if cal:
        # Non-primary calendar feeds look like this:
        # http:blah/blah/.../feeds/JUNK%40group.calendar.google.com/private/full
        # So grab the part after /feeds/ and unquote it.
        user = urllib.unquote(cal.content.src.split('/')[-3])
    query = gdata.calendar.service.CalendarEventQuery(user=user,
                                                      text_query=query)
    if date:
      start, end = date.split(',')
      if start:
        query.start_min = start
      if end:
        query.start_max = end
    else:
      query.futureevents = 'true'
    query.orderby = 'starttime'
    query.sortorder = 'ascend'
    query.max_results = 100
    return self.GetEntries(query.ToUri(), title,
                           converter=gdata.calendar.CalendarEventFeedFromString)

  GetEvents = get_events

  def is_token_valid(self):
    """Check that the token being used is valid."""
    return util.BaseServiceCL.IsTokenValid(self,
                                         '/calendar/feeds/default/private/full')

  IsTokenValid = is_token_valid


service_class = CalendarServiceCL


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
  entries = client.get_events(date=options.date,
                              title=options.title,
                              query=options.query,
                              calendar=options.cal)
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
  client.quick_add_event(args, options.cal)


def _run_delete(client, options, args):
  events = client.get_events(options.date, options.title,
                             options.query, options.cal)
  client.Delete(events, 'event',
                util.config.getboolean('GENERAL', 'delete_by_default'))


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