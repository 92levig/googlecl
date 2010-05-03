#!/usr/bin/python
"""Main function for the Google command line utility.

Some terminology in use:
client -- the end user.
service -- the Google service being accessed (Picasa, translate, YouTube, etc.)
task -- what the client wants done by the service.

"""
import gdata.youtube.service
import optparse
import os
import photos.service
import urllib
import util


def fill_out_options(task, options, logged_in):
  if not logged_in and task.requires('user') and not options.user:
    if util.config.getboolean('DEFAULT', 'use_default_username'):
      email, password = util.read_creds()
      if email:
        options.user = email
    if not options.user:
      options.user = raw_input('Enter a username: ')
  
  if options.summary and os.path.exists(os.path.expanduser(options.summary)):
    with open(options.summary, 'r') as summary_file:
      options.summary = summary_file.read()

  if task.requires('title', options):
    options.title = raw_input('Please specify an album title: ')
  if task.requires('query', options):  
    options.query = raw_input('Please specify a photos query: ')
  if task.requires('tags', options):
    options.tags = raw_input('Please specify photo tags: ')


def is_supported_service(service):
  """Check to see if a service is supported."""
  if service.lower() == 'picasa':
    return True
  else:
    return False


def print_help():
  """Print a help message."""
  print 'Welcome to the google-cl super alpha'
  print ('The only thing working so far is picasa, ', 
       'so give that a shot by entering ''picasa'' at the prompt')
  print ('Quitting also works, despite what your parents told you.',
       ' Enter ''quit'' to exit.') 

       
def run_interactive(parser):
  """Run an interactive shell for the google commands.
  
  Keyword arguments:
    parser: Object capable of parsing a list of arguments via parse_args.
    
  """
  command_string = ''
  while not command_string == 'quit': 
    command_string = raw_input('> ')
    if not command_string:
      continue
    args_list = util.expand_as_command_line(command_string)
    (options, args) = parser.parse_args(args_list)
    if is_supported_service(args[0]):
      run_once(options, args)
    elif command_string == '?' or command_string == 'help':
      print_help()
    elif command_string != 'quit':
      print '> Enter "?" or "help" to print the help menu'
 
      
def run_once(options, args):
  """Run one command.
  
  Keyword arguments:
    options: The options class as built and returned by optparse.
    args: The arguments to google-cl, also as returned by optparse.
  
  """
  try:
    service = args.pop(0)
    task_name = args.pop(0)
  except IndexError as e:
    print e
    print 'Must specify at least a service and a task!'
    return
  
  if service == 'youtube':
    tasks = youtube.service.tasks
    client = gdata.youtube.service.YouTubeService()
    run_task = youtube.service.run_task
  elif service == 'picasa':
    tasks = photos.service.tasks
    regex = util.config.getboolean('DEFAULT', 'regex')
    tags_prompt = util.config.getboolean('DEFAULT', 'tags_prompt')
    delete_prompt = util.config.getboolean('DEFAULT', 'delete_prompt')
    client = photos.service.PhotosServiceCL(regex, tags_prompt, delete_prompt)
    run_task = photos.service.run_task
  else:
    print 'Service %s is not supported' % service
    return
  try:
    task = tasks[task_name]
  except KeyError:
    print ('Did not recognize task %s, please use one of %s' %
           (task, tasks.keys()))
    return
  
  if task.login_required:
    util.try_login(client, options.user, options.password)
    if not client.logged_in:
      print 'Failed to log on!'
      return
  
  fill_out_options(task, options, client.logged_in)
  
  run_task(client, task_name, options, args)


def setup_parser():
  """Set up the parser.
  
  Returns:
    optparse.OptionParser with options configured.
  
  """
  usage = "usage: %prog service task [options]"
  parser = optparse.OptionParser(usage=usage)
  parser.add_option('-a', '--album', dest='title',
                    help='Title of the album')
  parser.add_option('-d', '--date', dest='date',
                    help='Date of the album in MM/DD/YYYY format.' + 
                    ' If omitted, uses today.')
  parser.add_option('-p', '--password', dest='password',
                    help='Password for the username specifed via -u option.')
  parser.add_option('-q', '--query', dest='query',
                    help=('Full text query string for specifying photos.'
                          + ' Searches on titles, captions, and tags.'))
  parser.add_option('-s', '--summary', dest='summary', 
                    help=('Description of the album, ' +
                          'or file containing the description.'))
  parser.add_option('-t',  '--tag', dest='tags',
                    help='Tags for photos, e.g. "Sunsets, Earth Day"')
  parser.add_option('-u', '--user', dest='user',
                    help=('Username to use for the task. Exact application ' +
                          'is task-dependent. If authentication is ' +
                          'necessary, this will force the user to specify a ' +
                          'password through a command line prompt or option.'))
 
  return parser


def main():
  
  if not util.load_preferences():
    print 'Invalid preferences, quitting...'
    return -1
  parser = setup_parser()
    
  (options, args) = parser.parse_args()
  if not args:
    try:
      run_interactive(parser)
    except KeyboardInterrupt:
      print ''
      print 'Quit via keyboard interrupt'
  else:
    if is_supported_service(args[0]):
      try:
        run_once(options, args)
      except KeyboardInterrupt:
        print ''
    else:
      print 'Unsupported service:', args[0]
     
     
if __name__ == '__main__':
  main()
