"""Main function for the Google command line utility."""
import gdata.photos.service
import getpass
import optparse


def print_help():
    """Print a help message."""
    print 'Welcome to the google-cl super alpha'
    print ('The only thing working so far is picasa, ', 
           'so give that a shot by entering ''picasa'' at the prompt')
    print ('Quitting also works, despite what your parents told you.',
           ' Enter ''quit'' to exit.') 

       
def run_interactive():
    """Run an interactive shell for the google commands."""
    command = ''
    while not command == 'quit': 
        command = raw_input('> ')
        if command == 'picasa':
            run_once({}, [])
        elif command == '?' or command == 'help':
            print_help()
 
            
def run_once(options, args):
    """Run one command.
    
    Keyword arguments:
    options -- the options class as built and returned by optparse.
    args -- the arguments to google-cl, also as returned by optparse.
    
	"""
    client = gdata.photos.service.PhotosService() 
    loggedOn = try_login(client)
    
    if not loggedOn:
        print 'Failed to log on, exiting'
        exit()
        
    albums = client.GetUserFeed()
    
    print 'Here are your albums:'
    for album in albums.entry:
        print album.title.text
        
        
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


if __name__ == '__main__':
    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()
    
    if not args:
        try:
            run_interactive()
        except KeyboardInterrupt:
            print ''
            print 'Quit via keyboard interrupt'
    else:
       run_once(options, args)
