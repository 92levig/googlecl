"""Main function for the Google command line utility.

Some terminology in use:
client -- the end user.
service -- the Google service being accessed (Picasa, translate, YouTube, etc.)
task -- what the client wants done by the service.

"""
import gdata.photos.service
import getpass
import glob
import optparse


def is_supported_service(service):
    """Check to see if a service is supported."""
    print service.lower()
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

       
def requires_login(task):
    """Check if a task requires a client login.
    
    Keyword arguments:
    task -- the task to be performed.
    
    """
    login_tasks = ['create', 'add', 'insert']
    if task in login_tasks:
        return True
    else:
        return False
           
           
def run_interactive(parser):
    """Run an interactive shell for the google commands."""
    command = ''
    while not command == 'quit': 
        command_string = raw_input('> ')
        command_list = command_string.split()
        (options, args) = parser.parse_args(command_list)
        if is_supported_service(command_list[0]):
            run_once(options, args)
        elif command_string == '?' or command_string == 'help':
            print_help()
        else:
            print '> Enter "?" or "help" to print the help menu'
 
            
def run_once(options, args):
    """Run one command.
    
    Keyword arguments:
    options -- the options class as built and returned by optparse.
    args -- the arguments to google-cl, also as returned by optparse.
    
	"""
    service = args[0]
    task = args[1]
    client = gdata.photos.service.PhotosService()
     
    if requires_login(task):
        loggedOn = try_login(client)
        if not loggedOn:
            print 'Failed to log on, exiting'
            exit()
        
    if task == 'create':
        print options.title
        print options.summary
        print client.email
        album = client.InsertAlbum(title=options.title, summary=options.summary)
        
        
def try_login(client):
    """Try to use programmatic login to log into Picasa.
    
    Keyword arguments:
	client -- client for the Picasa service.
	
	Returns: True if login was successful, False otherwise.
	
	"""
    try:
        client.email = raw_input('Enter your username: ')
        client.password = getpass.getpass('Enter your password: ')
        client.source = 'google-cl'
        client.ProgrammaticLogin()
    except gdata.service.BadAuthentication as e:
        print e
        try_login()
    except gdata.service.CaptchaRequired:
        print 'Too many false logins; Captcha required.'
        return False
    except Exception as e:
        print 'Unexpected exception: ', e
        return False
    else:
        return True


def main():
    usage = "usage: %prog service [options]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-a', '--album', dest='title', 
                      default='Boring Album Title',
                      help='Title of the album')
    parser.add_option('-d', '--date', dest='date',
                      help='Date of the album (if omitted, uses today).')
    parser.add_option('-s', '--summary', dest='summary', 
                      default='I am too lazy to summarize this album.',
                      help=('Description of the album, ' + 
                            'or file containing the description.'))
    parser.add_option('-t', '--title', dest='title',
                      help='Title of the album')
    
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
