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


"""Service details and instances for the Contacts service.

Some use cases:
Add contacts:
  contacts add "Bob Smith, bob@smith.com" "Jim Raynor, jimmy@noreaster.com" 

List contacts:
  contacts list title,email

"""
from __future__ import with_statement

__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import gdata.contacts.service
import googlecl
import googlecl.service
from googlecl.contacts import SECTION_HEADER


class ContactsServiceCL(gdata.contacts.service.ContactsService,
                        googlecl.service.BaseServiceCL):
  
  """Extends gdata.contacts.service.ContactsService for the command line.

  This class adds some features focused on using Contacts via an installed
  app with a command line interface.

  """

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
    googlecl.service.BaseServiceCL._set_params(self, regex,
                                               tags_prompt, delete_prompt)

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
      with open(string_or_csv_file, 'r') as contacts_csv_file:
        for line in contacts_csv_file:
          if line.strip():    # filter out empty lines
            self.add_contact(line)
    else:
      try:
        name, email = string_or_csv_file.split(',')
      except ValueError:
        print string_or_csv_file + ' is neither a name,email pair nor a file.'
        return
      new_contact = gdata.contacts.ContactEntry(title=atom.Title(
                                                             text=name.strip()))
      new_contact.email.append(gdata.contacts.Email(address=email.strip()))
      try:
        self.CreateContact(new_contact)
      except gdata.service.RequestError, err:
        if err.args[0]['reason'] == 'Conflict':
          print 'Already have a contact for e-mail address ' + email.strip()
        else:
          raise 

  AddContact = add_contact

  def get_contacts(self, name):
    """Get all contacts that match a name."""
    # The API only states that to return all the contacts, pass a large number
    # to max_results. Multiple queries never seem to run out of contacts...
    # so here we are.
    uri = self.GetFeedUri() + '?max-results=10000'
    return self.GetEntries(uri, name,
                           converter=gdata.contacts.ContactsFeedFromString)

  GetContacts = get_contacts

  def is_token_valid(self, test_uri=None):
    """Check that the token being used is valid."""
    if not test_uri:
      test_uri = self.GetFeedUri()
    return googlecl.service.BaseServiceCL.IsTokenValid(self, test_uri)

  IsTokenValid = is_token_valid


SERVICE_CLASS = ContactsServiceCL


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
    style_list = googlecl.get_config_option(SECTION_HEADER,
                                            'list_style').split(',')
  for entry in entries:
    print googlecl.service.entry_to_string(entry, style_list,
                                           delimiter=options.delimiter)


def _run_add(client, options, args):
  for contact in args:
    client.add_contact(contact)


def _run_delete(client, options, args):
  entries = client.GetContacts(options.title)
  client.Delete(entries, 'contact',
                googlecl.CONFIG.getboolean('GENERAL', 'delete_by_default'))


TASKS = {'list': googlecl.service.Task('List contacts', callback=_run_list,
                                       required='delimiter', optional='title'),
         'add': googlecl.service.Task('Add contacts', callback=_run_add,
                                      args_desc='CONTACT DATA or CSV FILE'),
         'delete': googlecl.service.Task('Delete contacts',
                                         callback=_run_delete,
                                         optional='title')}
