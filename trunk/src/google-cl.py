#!/usr/bin/python
"""Main function for the Google command line tool.

This program provides some functionality for a number of Google services from
the command line. 

Example usage (omitting the initial "./google-cl.py"):
  # Create a photo album with tags "Vermont" and name "Summer Vacation 2009"
  picasa create -n "Summer Vacation 2009" -t Vermont ~/photos/vacation2009/*
  
  # Post photos to an existing album
  picasa post -n "Summer Vacation 2008" ~/old_photos/*.jpg
  
  # Download another user's albums whose titles match a regular expression
  picasa get --user my.friend.joe --name ".*computer.*" ~/photos/joes_computer
  
  # Delete some posts you accidentally put up
  blogger delete -n "Silly post, number [0-9]*"
  
  # Post your latest film endeavor to YouTube
  youtube post --category Film --tag "Jane Austen, zombies" ~/final_project.mp4
  
Some terminology in use:
  service: The Google service being accessed (e.g. Picasa, Blogger, YouTube).
  task: What the client wants done by the service (e.g. post, get, delete).
  
"""
import ConfigParser
import optparse
import os
import urllib
import util


def fill_out_options(task, options, logged_in):
  """Fill out required options via config file and command line prompts.
  
  If there are any required fields missing for a task, fill them in.
  This is attempted first by checking the OPTION_DEFAULTS section of the
  preferences file, then prompting the user if the prior method fails.
  
  Keyword arguments:
    task: Requirements of the task (see class util.Task).
    options: Contains attributes that have been specified already, typically
             through options on the command line (see setup_parser()).
    logged_in: If the client is logged in or not
    
  Returns:
    Nothing, though options may be modified to hold the required fields.
    
  """
  if not logged_in and task.requires('user') and not options.user:
    if util.config.getboolean('GENERAL', 'use_default_username'):
      email, password = util.read_creds()
      if email:
        options.user = email
    if not options.user:
      options.user = raw_input('Enter a username: ')
  
  if options.summary and os.path.exists(os.path.expanduser(options.summary)):
    with open(options.summary, 'r') as summary_file:
      options.summary = summary_file.read()

  # Grab all attributes from options that match two criteria:
  # 1) They contain no underscores at the beginning or end of the name
  # 2) They evaluate to False (NoneType or '')
  missing_attributes = [attr for attr in dir(options)
                        if attr.strip('_') == attr and
                        not getattr(options, attr)]
  for attr in missing_attributes:
    if task.requires(attr, options):
      try:
        setattr(options, attr, util.config.get('OPTION_DEFAULTS', attr))
      except ConfigParser.NoOptionError:
        setattr(options, attr, raw_input('Please specify ' + attr + ': '))
  if options.query:
    options.encoded_query = urllib.quote_plus(options.query)
  else:
    options.encoded_query = None


def import_service_module(service):
  """Imports the service module from a package.
  
  Keyword arguments:
    service: Name of the service, which should coincide with the name of the
             package.
  
  Returns:
    Module as if imported via "import <service>.service" statement.
    
  """
  return __import__(service+'.service', globals(), locals(), -1)


def print_help(service=None, tasks=None):
  """Print help messages to the screen.
  
  Keyword arguments:
    service: Service to get help on. (Default None, prints general help)
    tasks: Dictionary of tasks that can be done by the given service.
           (Default None)
    
  """
  if not service:
    available_services = ['picasa', 'blogger', 'youtube', 'docs']
    print 'Welcome to the Google CL tool!'
    print '  Commands are broken into several parts: service, task, ' + \
          'options, and arguments.'
    print '  For example, in the command'
    print '      "> picasa post --title "My Cat Photos" photos/cats/*"'
    print '  the service is "picasa", the task is "post", the single ' + \
          'option is a name of "My Cat Photos", and the argument is the ' + \
          'path to the photos.'
    print '  The available services are ' + str(available_services)[1:-1]
    print '  Enter "> help <service>" for more information on a service.'
    print '  Or, just "quit" to quit.'
  else:
    print 'Available tasks for service ' + service + \
          ': ' + str(tasks.keys())[1:-1]
    for task_name in tasks.keys():
      print '  ' + task_name + ': ' + tasks[task_name].description
      print '\t' + tasks[task_name].usage


def run_interactive(parser):
  """Run an interactive shell for the google commands.
  
  Keyword arguments:
    parser: Object capable of parsing a list of arguments via parse_args.
    
  """
  while True:
    command_string = raw_input('> ')
    if not command_string:
      continue
    elif command_string == '?':
      print_help()
    elif command_string == 'quit':
      break
    else:
      args_list = util.expand_as_command_line(command_string)
      (options, args) = parser.parse_args(args_list)
      run_once(options, args)


def run_once(options, args):
  """Run one command.
  
  Keyword arguments:
    options: Options instance as built and returned by optparse.
    args: Arguments to google-cl, also as returned by optparse.
  
  """
  try:
    service = args.pop(0)
    task_name = args.pop(0)
  except IndexError as e:
    if service == 'help':
      print_help()
    else:
      print 'Must specify at least a service and a task!'
    return

  if service == 'help':
    service_module = import_service_module(task_name)
    if service_module:
      print_help(task_name, service_module.tasks)
    return
  
  regex = util.config.getboolean('GENERAL', 'regex')
  tags_prompt = util.config.getboolean('GENERAL', 'tags_prompt')
  delete_prompt = util.config.getboolean('GENERAL', 'delete_prompt')
  
  service_module = import_service_module(service)
  if not service_module:
    return
  client = service_module.service_class(regex, tags_prompt, delete_prompt)
  
  try:
    task = service_module.tasks[task_name]
    task.name = task_name
  except KeyError:
    print 'Did not recognize task, please use one of ' + \
          str(service_module.tasks.keys())
    return
  
  if task.login_required:
    token = util.read_auth_token(service)
    if token:
      try:
        client.SetClientLoginToken(token)
      except AttributeError:
        client.auth_token = token
      if client.IsTokenValid():
        client.logged_in = True
      else:
        util.remove_auth_token(service)
    if not client.logged_in:
      util.try_login(client, options.user, options.password)
      if client.logged_in:
        try:
          token = client.GetClientLoginToken()
        except AttributeError:
          token = client.auth_token
        util.write_auth_token(service, token)
      else:
        print 'Failed to log on!'
        return
  
  fill_out_options(task, options, client.logged_in)
  
  task.run(client, options, args)


def setup_parser():
  """Set up the parser.
  
  Returns:
    optparse.OptionParser with options configured.
  
  """
  usage = "usage: %prog service task [options]"
  parser = optparse.OptionParser(usage=usage)
  parser.add_option('-c', '--category', dest='category',
                    help='YouTube only - specify video categories' + 
                    ' as a comma-separated list, e.g. "Film, Travel"')
  parser.add_option('--devtags', dest='devtags',
                    help='YouTube only - specify developer tags' +
                    ' as a comma-separated list.')
  parser.add_option('-d', '--date', dest='date',
                    help='Date of the album in MM/DD/YYYY format.' + 
                    ' If omitted, uses today.')
  parser.add_option('--delimiter', dest='delimiter',
                    help='Specify a delimiter for the output of the list task.')
  parser.add_option('--editor', dest='editor',
                    help='Docs only - editor to use on a file.')
  parser.add_option('-f', '--folder', dest='folder',
                    help='Docs only - specify folder(s) to upload to '+ 
                    '/ search in.')
  parser.add_option('--format', dest='format',
                    help='Docs only - format to download documents as.')
  parser.add_option('-n', '--title', dest='title',
                    help='Title of the item')
  parser.add_option('--no-convert', dest='convert',
                    action='store_false', default=True,
                    help='Google Apps Premier only - do not convert the file' +
                    ' on upload. (Else converts to native Google Docs format')
  parser.add_option('-p', '--password', dest='password',
                    help='Password for the username specifed via -u option.')
  parser.add_option('-q', '--query', dest='query',
                    help=('Full text query string for specifying items.'
                          + ' Searches on titles, captions, and tags.'))
  parser.add_option('-s', '--summary', dest='summary', 
                    help=('Description of the upload, ' +
                          'or file containing the description.'))
  parser.add_option('-t',  '--tags', dest='tags',
                    help='Tags for item, e.g. "Sunsets, Earth Day"')
  parser.add_option('-u', '--user', dest='user',
                    help=('Username to use for the task. Exact application ' +
                          'is task-dependent. If authentication is ' +
                          'necessary, this will force the user to specify a ' +
                          'password through a command line prompt or option.'))
  return parser


def main():
  util.load_preferences()
  parser = setup_parser()
    
  (options, args) = parser.parse_args()
  if not args:
    try:
      run_interactive(parser)
    except KeyboardInterrupt:
      print ''
      print 'Quit via keyboard interrupt'
    except EOFError:
      print ''
  else:
    try:
      run_once(options, args)
    except KeyboardInterrupt:
      print ''


if __name__ == '__main__':
  main()