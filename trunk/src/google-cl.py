"""Main function for the Google command line utility.

Some terminology in use:
client -- the end user.
service -- the Google service being accessed (Picasa, translate, YouTube, etc.)
task -- what the client wants done by the service.

"""
import gdata.photos.service
import getpass
import glob
import myparser
import os
import pickle
import stat

def get_albums(client, user='default', title=None):
    """Get albums from a user.
    
    Keyword arguments:
    client -- the gdata.photos.service.PhotosService() object.
    user -- the user whose albums are being retrieved. (Default 'default')
    title -- title that the album should have. (Default None, for all albums)
    
    Returns: list of albums that match parameters, or [] if none do.
    
    """
    wanted_albums = []
    feed = client.GetUserFeed(user=user)
    for album in feed.entry:
        if not title or album.title.text == title:
            wanted_albums.append(album)
    return wanted_albums


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


def requires_login(task):
    """Check if a task requires a client login.
    
    Keyword arguments:
    task -- the task to be performed.
    
    """
    login_tasks = ['create', 'delete']
    if task in login_tasks:
        return True
    else:
        return False
           
           
def run_interactive(parser):
    """Run an interactive shell for the google commands."""
    command_string = ''
    while not command_string == 'quit': 
        command_string = raw_input('> ')
        if not command_string:
            continue
        command_list = command_string.split()
        (options, args) = parser.parse_args(command_list)
        if is_supported_service(args[0]):
            run_once(options, args)
        elif command_string == '?' or command_string == 'help':
            print_help()
        elif command_string != 'quit':
            print '> Enter "?" or "help" to print the help menu'
 
            
def run_once(options, args):
    """Run one command.
    
    Keyword arguments:
    options -- the options class as built and returned by optparse.
    args -- the arguments to google-cl, also as returned by optparse.
    
	"""
    service = args[0]
    if not is_supported_service(service):
        print 'Service %s is not supported' % service
        return
    
    task = args[1]
    client = gdata.photos.service.PhotosService()
     
    if requires_login(task):
        loggedOn = try_login(client)
        if not loggedOn:
            print 'Failed to log on, exiting'
            exit()
            
    if task == 'create':
        album = client.InsertAlbum(title=options.title, summary=options.summary)
        if len(args) == 3:
            file_glob = args[2]
            album_url = ('/data/feed/api/user/%s/albumid/%s' % 
                         ('default', album.gphoto_id.text))
            for file in glob.glob(file_glob):
                print 'Loading file', file
                photo = client.InsertPhotoSimple(album_url, file, '', file)
    elif task == 'delete':
        albums = get_albums(client, title=options.title)
        if not albums:
            print 'No albums with title', options.title
        for album in albums:
            delete = raw_input('Are you sure you want to delete album ' + 
                               album.title.text + 
                               '? (Y/n): ')
            if not delete or delete.lower() == 'y':
                client.Delete(album)
    else:
        print ('Sorry, task "%s" is currently unsupported for %s.' % 
               (task, service))
        
        
def try_login(client):
    """Try to use programmatic login to log into Picasa.
    
    Keyword arguments:
	client -- client for the Picasa service.
	
	Returns: True if login was successful, False otherwise.
	
	"""
    cred_directory = os.path.expanduser('~/.googlecl')
    if not os.path.exists(cred_directory):
        os.makedirs(cred_directory)
        
    cred_filename = os.path.join(cred_directory, 'creds')
    used_auth_from_file = False
    if os.path.exists(cred_filename):
        with open(cred_filename, 'r') as cred_file:
            try:
                (email, password) = pickle.load(cred_file)
            except EOFError:
                cred_file.close()
                os.remove(cred_filename)
            else:
                used_auth_from_file = True
    
    if not used_auth_from_file:
        email = raw_input('Enter your username: ')
        password = getpass.getpass('Enter your password: ')
        with open(cred_filename, 'w') as cred_file:
            os.chmod(cred_filename, stat.S_IRUSR | stat.S_IWUSR)
            pickle.dump((email, password), cred_file)
        
    client.email = email
    client.password = password
    client.source = 'google-cl'
    try:
        client.ProgrammaticLogin()
    except gdata.service.BadAuthentication as e:
        print e
        if used_auth_from_file:
            os.remove(cred_filename)
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
    parser = myparser.MyParser(usage=usage)
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
