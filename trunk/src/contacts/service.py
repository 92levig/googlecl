"""
Service details and instances for the Picasa service.

Some use cases:
Add contacts:
  contacts add "Bob Smith, bob@smith.com" "Jim Raynor, jimmy@noreaster.com" 

List contacts:
  contacts list title,email
  
Created on May 20, 2010

@author: Tom Miller
"""
import gdata.contacts.service
import util
import contacts


class ContactsServiceCL(gdata.contacts.service.ContactsService,
                        util.BaseServiceCL):

  def __init__(self, regex=False, tags_prompt=False, delete_prompt=True):
    """Constructor.
    
    Keyword arguments:
      regex: Indicates if regular expressions should be used for matching
             strings, such as album titles. (Default False)
      tags_prompt: Indicates if while inserting photos, instance should prompt
                   for tags for each photo. (Default False)
      delete_prompt: Indicates if instance should prompt user before
                     deleting an album or photo. (Default True)
              
    """
    gdata.contacts.service.ContactsService.__init__(self)
    util.BaseServiceCL.set_params(self, regex, tags_prompt, delete_prompt)

  def get_contacts(self, name):
    uri = self.GetFeedUri()
    return self.GetEntries(uri, name,
                           converter=gdata.contacts.ContactsFeedFromString)

  GetContacts = get_contacts

  def IsTokenValid(self):
    """Check that the token being used is valid."""
    return util.BaseServiceCL.IsTokenValid(self, self.GetFeedUri())


service_class = ContactsServiceCL


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
  entries = client.GetContacts(options.title)
  if args:
    style_list = args[0].split(',')
  else:
    style_list = util.get_list_style(contacts.SECTION_HEADER)
  for e in entries:
    print util.entry_to_string(e, style_list, delimiter=options.delimiter)


tasks = {'list': util.Task('List contacts', callback=_run_list,
                           optional='title')}