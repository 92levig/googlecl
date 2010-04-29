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
  
  def __init__(self, regex=False, tags_prompt=False, delete_prompt=True):
    """Constructor.
    
    Keyword arguments:
      regex: Indicates if regular expressions should be used for matching
             strings, such as album titles. (Default False)
      tags_prompt: Indicates if while inserting photos, instance should prompt
                   for tags for each photo. (Default False)
      delete_prompt: Indicates if instance should prompt user before
                     deleting an album or photo. (Default True)
              
    """ 
    self.client = gdata.photos.service.PhotosService()
    self.logged_in = False
    self.use_regex = regex
    self.prompt_for_tags = tags_prompt
    self.prompt_for_delete = delete_prompt
  
  def CreateAlbum(self, title, summary, date='', photo_list=[], tags='', 
                  access='public'): 
    """Create an album.
    
    Keyword arguments:
      title: Title of the album.
      summary: Summary of the album.
      date: Date of the album, in MM/DD/YYYY format as a string. (Default '')
      photo_list: List of filenames of photos on local host. (Default [])
      tags: Text of the tags to be added to each photo, e.g. 'Islands, Vacation'
      access: Access level of the album. Should be one of:
              'public' for "Public" sharing setting.
              'private' for "Unlisted" sharing setting.
              'protected' for "Sign-in required" sharing setting.
              (Default 'public')
    
    """
    timestamp_text = None
    if date:
      try:
        timestamp = time.mktime(time.strptime(date, '%m/%d/%Y'))
      except ValueError as e:
        print e
      else:
        # Timestamp needs to be in milliseconds after the epoch
        timestamp_text = '%i' % (timestamp * 1000)
    
    album = self.client.InsertAlbum(title=title, summary=summary, 
                                    access=access,
                                    timestamp=timestamp_text)
    if photo_list:
        self.InsertPhotos(album, photo_list=photo_list, tags=tags)
        
  def Delete(self, title='', query='', delete_default=False):
    """Delete album(s) or photo(s).
    
    Keyword arguments:
      title: Albums matching this title should be deleted.
      query: Photos matching this url-encoded query should be deleted.
      delete_default: If the user is being prompted to confirm deletion, hitting
            enter at the prompt will delete or keep the album if this is True or
            False, respectively. (Default False)
    
    """
    if delete_default and self.prompt_for_delete:
      prompt_str = '(Y/n)'
    elif self.prompt_for_delete:
      prompt_str = '(y/N)'
    
    if query:
      if title:
        print 'Cannot specify an album and a query. Ignoring the album.'
      uri = '/data/feed/api/user/default?kind=photo&q=%s' % query
      entries = self.client.GetFeed(uri).entry
      entry_type = 'photo'
      search_string = query
    elif title:
      entries = self.GetAlbum(title=title)
      entry_type = 'album'
      search_string = title
    if not entries:
      print 'No %ss matching %s' % (entry_type, search_string)
    for item in entries:
      if self.prompt_for_delete:
        delete_str = raw_input('Are you SURE you want to delete %s %s? %s:' % 
                               (entry_type, item.title.text, prompt_str))
        if not delete_str:
          delete = delete_default
        else:
          delete = delete_str.lower() == 'y'
      else:
        delete = True
      
      if delete:
        self.client.Delete(item)
        
  def DownloadAlbum(self, base_path, user='default', title=None):
    """Download an album to the client.
    
    Keyword arguments:
      base_path: Path on the filesystem to copy albums to. Each album will
                 be stored in base_path/<album title>. If base_path does not
                 exist, it and each non-existent parent directory will be
                 created. 
      user: User whose albums are being retrieved. (Default 'default')
      title: Title that the album should have. (Default None, for all albums)
       
    """
    entries = self.GetAlbum(user=user, title=title)
    
    for album in entries:
      album_path = os.path.join(base_path, album.title.text)
      album_concat = 1
      if os.path.exists(album_path):
        base_album_path = album_path
        while os.path.exists(album_path):
          album_path = base_album_path + '-%i' % album_concat
          album_concat += 1
      os.makedirs(album_path)
      
      f = self.client.GetFeed('/data/feed/api/user/%s/albumid/%s?kind=photo' %
                              (user, album.gphoto_id.text))
      
      for photo in f.entry:
        #TODO: Test on Windows (upload from one OS, download from another)
        photo_name = os.path.split(photo.title.text)[1]
        photo_path = os.path.join(album_path, photo_name)
        # Check for a file extension, add it if it does not exist.
        if not '.' in photo_path:
          type = photo.content.type
          photo_path += '.' + type[type.find('/')+1:]
        if os.path.exists(photo_path):
          base_photo_path = photo_path
          photo_concat = 1
          while os.path.exists(photo_path):
            photo_path = base_photo_path + '-%i' % photo_concat
            photo_concat += 1
        print 'Downloading %s to %s' % (photo.title.text, photo_path)
        url = photo.content.src
        high_res_url = url[:url.rfind('/')+1]+'d'+url[url.rfind('/'):]
        urllib.urlretrieve(high_res_url, photo_path)
        
  def GetAlbum(self, user='default', title=None):
    """Get albums from a user feed.
    
    Keyword arguments:
      user: The user whose albums are being retrieved. (Default 'default')
      title: Title that the album should have. (Default None, for all albums)
         
    Returns:
      List of albums that match parameters, or [] if none do.
    
    """
    wanted_albums = []
    feed = self.client.GetUserFeed(user=user, kind='album')
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
    
  def InsertPhotos(self, album, photo_list, tags=''):
    """Insert photos into an album.
    
    Keyword arguments:
    album: The album entry of the album getting the photos.
    photo_list: a list of paths, each path a picture on the local host.
    tags: Text of the tags to be added to each photo, e.g. 'Islands, Vacation'
    
    """
    album_url = ('/data/feed/api/user/%s/albumid/%s' %
                 ('default', album.gphoto_id.text))
    keywords = tags
    for file in photo_list:
      if not tags and self.prompt_for_tags:
        keywords = raw_input('Enter tags for photo %s: ' % file)
      print 'Loading file %s to album %s' % (file, album.title.text)
      try:
        self.client.InsertPhotoSimple(album_url, 
                                      title=os.path.split(file)[1], 
                                      summary='',
                                      filename_or_handle=file, 
                                      keywords=keywords)
      except gdata.photos.service.GooglePhotosException as e:
        print 'Failed to upload %s. (%s: %s)' % (file, e.reason, e.body)    
  
  def LoadCreds(self, credentials_path):
    """Return the email/password found in the credentials file."""
    with open(credentials_path, 'r') as cred_file:
      (email, password) = pickle.load(cred_file)
          
    return (email, password)
  
  def Login(self, email=None, password=None, credentials_path=None):
    """Try to use programmatic login to log into Picasa.
    
    Either email and password must both be defined, or credentials_path must
    be defined. If all three arguments are defined, the data in credentials_path
    is used.
    
    Keyword arguments:
    email: the email to log in with.
    password: the password to log in with.
    credentials_path: absolute path to file that contains email/password
      for Picasa Web.
    
    Returns: Nothing, but sets self.logged_in to True if login was a success.
    
    """
    if credentials_path:
      (email, password) = self.LoadCreds(credentials_path)
    elif not (email and password):
      print ('You must give an email/password combo to log in with, '
             'or a file where they can be found!')
      self.logged_in = False
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
    else:
      self.logged_in = True