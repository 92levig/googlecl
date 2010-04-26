"""
Created on Apr 20, 2010

A more user-friendly wrapper around the gdata.photos.service.PhotosService 
class.

@author: Tom Miller

"""
import gdata.photos.service
import os
import pickle
import re
import time
import urllib

class PhotosService(object):
  """Wrapper class for gdata.photos.service.PhotosService()."""
  client = None
  use_regex = False
  
  def __init__(self, regex=False):
    """Constructor.
    
    Keyword arguments:
    regex -- indicates if regular expressions should be used for matching
            strings, such as album titles. (Default False)
            
    """ 
    self.client = gdata.photos.service.PhotosService()
    self.logged_in = False
    self.use_regex = regex
  
  def CreateAlbum(self, title, summary, date='', photo_list=[]): 
    """Create an album.
    
    Keyword arguments:
    title -- Title of the album.
    summary -- Summary of the album.
    date -- the date of the album, in MM/DD/YYYY format as a string.
          (Default '')
    photo_list -- List of filenames of photos on local host.
          (Default [])
    
    """
    timestamp_text = None
    if date:
      try:
        timestamp = time.mktime(time.strptime(date, '%m/%d/%Y'))
      except ValueError as e:
        print e
      else:
        # I have no idea why the timestamp gets made like this, but this is how
        # it's done...
        timestamp_text = '%i' % (timestamp * 1000)
    
    album = self.client.InsertAlbum(title=title, summary=summary, 
                                    timestamp=timestamp_text)
    if photo_list:
        self.InsertPhotos(album, photo_list)
        
  def DeleteAlbum(self, title, delete_default=False, prompt=True):
    """Delete album(s).
    
    Keyword arguments:
    title -- albums matching this title should be deleted.
    delete_default -- If the user is being prompted to confirm deletion, hitting
          enter at the prompt will delete or keep the album if this is True or
          False, respectively. (Default False)
    prompt -- whether or not there should be a prompt confirming deletion.
          (Default True)
    
    """
    if delete_default and prompt:
      prompt_str = '(Y/n)'
    elif prompt:
      prompt_str = '(y/N)'
    albums = self.GetAlbum(title=title)
    if not albums:
      print 'No albums with title', title
    for album in albums:
      if prompt:
        delete_str = raw_input('Are you SURE you want to delete album %s? %s:' % 
                               (album.title.text, prompt_str))
        if not delete_str:
          delete = delete_default
        else:
          delete = delete_str.lower() == 'y'
      else:
        delete = True
      
      if delete:
        self.client.Delete(album)
        
  def DownloadAlbum(self, base_path, user='default', title=None):
    """Download an album to the client.
    
    Keyword arguments:
    base_path -- the path on the filesystem to copy albums to. Each album will
                 be stored in base_path/<album title>. If base_path does not
                 exist, it and each non-existent parent directory will be
                 created. 
    user -- the user whose albums are being retrieved. (Default 'default')
    title -- title that the album should have. (Default None, for all albums)
       
    """
    entries = self.GetAlbum(user=user, title=title)
    
    for album in entries:
      album_path = os.path.join(base_path, album.title.text)
      album_concat = 1
      if os.path.exists(album_path):
        base_album_path = album_path
        while os.path.exists(album_path):
          album_path + base_album_path + '-%i' % album_concat
          album_concat += 1
      os.makedirs(album_path)
      
      f = self.client.GetFeed('/data/feed/api/user/%s/albumid/%s?kind=photo' %
                              (user, album.gphoto_id.text))
      
      photo_concat = 1
      for photo in f.entry:
        photo_path = os.path.join(album_path, photo.title.text)
        if os.path.exists(photo_path):
          base_photo_path = photo_path
          while os.path.exists(photo_path):
            photo_path = base_photo_path + '-%i' % photo_concat
            photo_concat += 1
        print 'Downloading %s to %s' % (photo.title.text, photo_path)
        urllib.urlretrieve(photo.content.src, photo_path)
        
  def GetAlbum(self, user='default', title=None):
    """Get albums from a user feed.
    
    Keyword arguments:
    user -- the user whose albums are being retrieved. (Default 'default')
    title -- title that the album should have. (Default None, for all albums)
       
    Returns: list of albums that match parameters, or [] if none do.
    
    """
    wanted_albums = []
    feed = self.client.GetUserFeed(user=user)
    if not title:
      return feed.entry
    for album in feed.entry:
      if ((self.use_regex and re.match(title, album.title.text)) or
          (not self.use_regex and album.title.text == title)):
        wanted_albums.append(album)
    return wanted_albums
  
  def GetFeed(self, uri):
    """Direct line to the original PhotosService.GetFeed()."""
    return self.client.GetFeed(uri)
    
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