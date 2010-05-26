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
__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import gdata.contacts.service
import util
from googlecl.contacts import SECTION_HEADER


class ContactsServiceCL(gdata.contacts.service.ContactsService,
                        util.BaseServiceCL):

  def __init__(self, regex=False, tags_prompt=False, delete_prompt=True):
    """Constructor.
    
    Keyword arguments:
      regex: Indicates if regular expressions should be used for matching
             strings, such as contact names. (Default False)
      tags_prompt: Indicates if while inserting photos, instance should prompt
                   for tags for each photo. (Default False)
      delete_prompt: Indicates if instance should prompt user before
                     deleting a contact. (Default True)
              
    """
    gdata.contacts.service.ContactsService.__init__(self)
    util.BaseServiceCL.set_params(self, regex, tags_prompt, delete_prompt)

  def add_contact(self, string_or_csv_file):
    """Add contact(s).
    
    Keyword arguments:
      string_or_csv_file: String representing a name/email address to add, or
                          a path to a csv file of such strings. Entries should
                          be of the form "name,email@server.com" (whitespace
                          before/after the comma is ignored).

    """
    import atom
    import os.path
    if os.path.exists(string_or_csv_file):
      with open(string_or_csv_file, 'r') as file:
        for line in file:
          if line.strip():    # filter out empty lines
            self.add_contact(line)
    else:
      name, junk, email = string_or_csv_file.partition(',')
      new_contact = gdata.contacts.ContactEntry(title=atom.Title(
                                                             text=name.strip()))
      new_contact.email.append(gdata.contacts.Email(address=email.strip()))
      try:
        self.CreateContact(new_contact)
      except gdata.service.RequestError as e:
        if e.args[0]['reason'] == 'Conflict':
          print 'Already have a contact for e-mail address ' + email.strip()
        else:
          raise 

  def get_contacts(self, name):
    # The API only states that to return all the contacts, pass a large number
    # to max_results. Multiple queries never seem to run out of contacts...
    # so here we are.
    uri = self.GetFeedUri() + '?max-results=10000'
    return self.GetEntries(uri, name,
                           converter=gdata.contacts.ContactsFeedFromString)

  GetContacts = get_contacts

  def is_token_valid(self):
    """Check that the token being used is valid."""
    return util.BaseServiceCL.IsTokenValid(self, self.GetFeedUri())

  IsTokenValid = is_token_valid


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
    style_list = util.get_config_option(SECTION_HEADER, 'list_style').split(',')
  for e in entries:
    print util.entry_to_string(e, style_list, delimiter=options.delimiter)


def _run_add(client, options, args):
  for contact in args:
    client.add_contact(contact)


tasks = {'list': util.Task('List contacts', callback=_run_list,
                           required='delimiter', optional='title'),
         'add': util.Task('Add contacts', callback=_run_add,
                          args_desc='CONTACT DATA or CSV FILE')}