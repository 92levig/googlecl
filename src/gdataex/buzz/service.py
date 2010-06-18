import gdata
import gdata.service
import urllib

BASE_URI = 'https://www.googleapis.com/buzz/v1/'

class Error(Exception):
  pass


class BuzzService(gdata.service.GDataService):

  def __init__(self, email=None, password=None, source=None,
               server='www.google.com', additional_headers=None, **kwargs):
    """Creates a client for the Google Buzz service.

    Args:
      email: string (optional) The user's email address, used for
          authentication.
      password: string (optional) The user's password.
      source: string (optional) The name of the user's application.
      server: string (optional) The name of the server to which a connection
          will be opened. Default value: 'www.google.com'.
      **kwargs: The other parameters to pass to gdata.service.GDataService
          constructor.
    """
    gdata.service.GDataService.__init__(
        self, email=email, password=password, source=source,
        server=server, additional_headers=additional_headers, **kwargs)

  def GetActivityFeed(self, user):
    uri = BASE_URI + 'people/' +user + '/@self'
    print uri
    return self.Get(uri)
