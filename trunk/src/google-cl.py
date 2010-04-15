import gdata.photos.service
import getpass

def tryLogin():
	try:
		client.email = raw_input('Enter your username: ')
		client.password = getpass.getpass('Enter your password: ')
		client.source = 'google-cl'
		client.ProgrammaticLogin()
	except gdata.service.BadAuthentication as e:
		print e
		tryLogin()
	except gdata.service.CaptchaRequired:
		print 'Too many false logins; Captcha required.'
		return False
	except Exception as e:
		print 'Unexpected exception', e
		return False
	else:
		return True


if __name__ == '__main__':
	client = gdata.photos.service.PhotosService()
	
	loggedOn = tryLogin()
	
	if not loggedOn:
		print 'Failed to log on, exiting'
		exit()
		
	albums = client.GetUserFeed()
	
	print 'Here are your albums:'
	for album in albums.entry:
		print album.title.text 
