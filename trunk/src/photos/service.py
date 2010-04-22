"""
Created on Apr 20, 2010

A more user-friendly wrapper around the gdata.photos.service.PhotosService 
class.

@author: Tom Miller

"""
import gdata.photos.service
import pickle
import re

class PhotosService(object):
  """Wrapper class for gdata.photos.service.PhotosService()."""
  client = None
  
  def __init__(self):
    """Constructor.""" 
    self.client = gdata.photos.service.PhotosService()
    self.logged_in = False
  
  def CreateAlbum(self, title, summary, photo_list=None): 
    """Create an album.
    
    Keyword arguments:
    title -- Title of the album.
    summary -- Summary of the album.
    photo_list -- List of filenames of photos on local host.
    
    """
    album = self.client.InsertAlbum(title=title, summary=summary)
    if photo_list:
        self.InsertPhotos(album, photo_list)
        
  def DeleteAlbum(self, title, regex=False):
    """Delete album(s).
    
    Keyword arguments:
    title -- albums matching this title should be deleted.
    regex -- indicates if regular expressions should be used in the title. 
          (Default False)
    
    """
    albums = self.GetAlbum(title=title, regex=regex)
    if not albums:
      print 'No albums with title', title
    for album in albums:
      delete = raw_input('Are you SURE you want to delete album %s? (y/N):' % 
                         album.title.text)
      if delete and delete.lower() == 'y':
        self.client.Delete(album)
        
  def GetAlbum(self, user='default', title=None, regex=False):
    """Get albums from a user feed.
    
    Keyword arguments:
    user -- the user whose albums are being retrieved.
            (Default 'default')
    title -- title that the album should have. 
             (Default None, for all albums)
    regex -- indicates if regular expressions should be used in the title. 
             (Default False)
          
    Returns: list of albums that match parameters, or [] if none do.
    
    """
    wanted_albums = []
    feed = self.client.GetUserFeed(user=user)
    if not title:
      return feed.entry
    for album in feed.entry:
      if ((regex and re.match(title, album.title.text)) or
          (not regex and album.title.text == title)):
        wanted_albums.append(album)
    return wanted_albums
  
  def InsertPhotos(self, album, photo_list):
    """Insert photos into an album.
    
    Keyword arguments:
    album -- The album entry of the album getting the photos.
    photo_list -- a list of paths, each path a picture on the local host.
    
    """
    album_url = ('/data/feed/api/user/%s/albumid/%s' %
                 ('default', album.gphoto_id.text))
    for file in photo_list:
      print 'Loading file', file
      try:
        self.client.InsertPhotoSimple(album_url, file, '', file)
      except gdata.photos.service.GooglePhotosException as e:
        print 'Failed to upload %s. (%s -- %s)' % (file, e.reason, e.body)    
  
  def Login(self, email=None, password=None, credentials_path=None):
    """Try to use programmatic login to log into Picasa.
    
    Either email and password must both be defined, or credentials_path must
    be defined. If all three arguments are defined, the data in credentials_path
    is used.
    
    Keyword arguments:
    email -- the email to log in with.
    password -- the password to log in with.
    credentials_path -- absolute path to file that contains email/password
      for Picasa Web.
    
    Returns: True if login was successful, False otherwise.
    
    """
    if credentials_path:
      with open(credentials_path, 'r') as cred_file:
        try:
          (email, password) = pickle.load(cred_file)
        except Exception as e:
          self.logged_in = False
    elif not (email and password):
      print ('You must give an email/password combo to log in with, '
             'or a file where they can be found!')
      self.logged_in = False
      return self.logged_in
    
    if email == self.client.email and password == self.client.password:
      return self.logged_in
    
    self.client.email = email
    self.client.password = password
    self.client.source = 'google-cl'
    
    try:
      self.client.ProgrammaticLogin()
    except gdata.service.BadAuthentication as e:
      print e
      self.logged_in = False
    except gdata.service.CaptchaRequired:
      print 'Too many false logins; Captcha required.'
      self.logged_in = False
    except Exception as e:
      raise
    else:
      self.logged_in = True
      
    return self.logged_in