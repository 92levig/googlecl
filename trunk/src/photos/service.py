"""
Created on Apr 20, 2010

A more user-friendly wrapper around the gdata.photos.service.PhotosService 
class.

@author: Tom Miller

"""
from gdata.photos.service import PhotosService, GooglePhotosException
import os
import re
import urllib
import util


tasks = {'create': util.Task('title', 'summary'), 
         'post': util.Task('title', 'tags'), 
         'delete': util.Task([['title', 'query']]),
         'list': util.Task('user', ['title', 'query'], login_required=False),
         'get': util.Task('user', ['title', 'query'], login_required=False),
         'tag': util.Task(['tags', ['title', 'query']])}


class PhotosServiceCL(PhotosService, util.BaseServiceCL):
  """Extends gdata.photos.service.PhotosService for the command line.
  
  This class adds some features focused on using Picasa in an installed app
  running on a local host."""
  
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
    PhotosService.__init__(self)
    util.BaseServiceCL.set_params(self, regex, tags_prompt, delete_prompt)
        
  def Delete(self, title='', query='', delete_default=False):
    """Delete album(s) or photo(s).
    
    Keyword arguments:
      title: Albums matching this title should be deleted.
      query: Photos matching this url-encoded query should be deleted.
      delete_default: If the user is being prompted to confirm deletion, hitting
            enter at the prompt will delete or keep the album if this is True or
            False, respectively. (Default False)
    
    """
    if query:
      if title:
        print 'Cannot specify an album and a query. Ignoring the album.'
      uri = '/data/feed/api/user/default?kind=photo&q=%s' % query
      entries = self.GetFeed(uri).entry
      entry_type = 'photo'
      search_string = query
    elif title:
      entries = self.GetAlbum(title=title)
      entry_type = 'album'
      search_string = title
    if not entries:
      print 'No %ss matching %s' % (entry_type, search_string)
    util.BaseServiceCL.Delete(self, entries, entry_type, delete_default)
    
        
  def DownloadAlbum(self, base_path, user, title=None):
    """Download an album to the client.
    
    Keyword arguments:
      base_path: Path on the filesystem to copy albums to. Each album will
                 be stored in base_path/<album title>. If base_path does not
                 exist, it and each non-existent parent directory will be
                 created. 
      user: User whose albums are being retrieved. (Default 'default')
      title: Title that the album should have. (Default None, for all albums)
       
    """
    if not user:
      user = 'default'
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
      
      f = self.GetFeed('/data/feed/api/user/%s/albumid/%s?kind=photo' %
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
    feed = self.GetUserFeed(user=user, kind='album')
    if not title:
      return feed.entry
    elif self.use_regex:
      return [album for album in feed.entry if re.match(title, album.title.text)]
    else:
      return [album for album in feed.entry if title == album.title.text]
  
  def InsertPhotoList(self, album, photo_list, tags=''):
    """Insert photos into an album.
    
    Keyword arguments:
      album: The album entry of the album getting the photos.
      photo_list: A list of paths, each path a picture on the local host.
      tags: Text of the tags to be added to each photo, e.g. 'Islands, Vacation'
    
    """
    album_url = ('/data/feed/api/user/%s/albumid/%s' %
                 ('default', album.gphoto_id.text))
    keywords = tags
    failures = []
    for file in photo_list:
      if not tags and self.prompt_for_tags:
        keywords = raw_input('Enter tags for photo %s: ' % file)
      print 'Loading file %s to album %s' % (file, album.title.text)
      try:
        self.InsertPhotoSimple(album_url, 
                               title=os.path.split(file)[1], 
                               summary='',
                               filename_or_handle=file, 
                               keywords=keywords)
      except GooglePhotosException as e:
        print 'Failed to upload %s. (%s: %s)' % (file, e.reason, e.body) 
        failures.append(file)   
    return failures
      

def run_task(client, task_name, options, args):
  if task_name == 'create':
    if options.date:
      import time
      try:
        timestamp = time.mktime(time.strptime(options.date, '%m/%d/%Y'))
      except ValueError as e:
        print e
        print 'Ignoring date option, using today'
        options.date = ''
      else:
        # Timestamp needs to be in milliseconds after the epoch
        options.date = '%i' % (timestamp * 1000)
    
    album = client.InsertAlbum(title=options.title, summary=options.summary, 
                               access=util.config.get('DEFAULT', 'access'),
                               timestamp=options.date)
    if args:
      client.InsertPhotoList(album, photo_list=args, tags=options.tags)
      
  elif task_name == 'delete':
    if options.query:
      client.Delete(query=urllib.quote_plus(options.query),
                    delete_default=util.config.getboolean('DEFAULT', 
                                                      'delete_by_default'))
    else:
      client.Delete(title=options.title,
                    delete_default=util.config.getboolean('DEFAULT', 
                                                      'delete_by_default'))
    
  elif task_name == 'list':
    if options.query:
      if options.title:
        print 'Cannot use both a query and an album title. Ignoring the album.'
      uri = ('/data/feed/api/user/%s?kind=photo&q=%s' % 
             (options.user, urllib.quote_plus(options.query)))
      entries = client.GetFeed(uri).entry
    else:
      entries = client.GetAlbum(user=options.user, title=options.title)
      
    for item in entries:
      print item.title.text
      
  elif task_name == 'post':
    if not args:
      print 'Must provide photos to post!'
      return
     
    albums = client.GetAlbum(title=options.title)
    if len(albums) == 1:
      client.InsertPhotoList(albums[0], args, tags=options.tags)
    elif len(albums) > 1:
      print 'More than one album matches "%s"' % options.title
      upload_all = raw_input('Would you like to upload photos ' + 
                             'to each album? (Y/n) ')
      if not upload_all or upload_all.lower() == 'y':
        for album in albums:
          client.InsertPhotoList(album, args, tags=options.tags)
      
    else:
      print 'No albums found that match %s' % options.title
    
  elif task_name == 'get':
    if not args:
      print 'Must provide destination of album(s)!'
      return
    base_path = args[0]
      
    client.DownloadAlbum(base_path, user=options.user, title=options.title)
    
  elif task_name == 'tag':
    from gdata.media import Group, Keywords
    if options.title:
      album_entries = client.GetAlbum(title=options.title)
      photo_entries = []
      for album in album_entries:
        uri = ('/data/feed/api/user/default/albumid/%s?kind=photo' % 
               album.gphoto_id.text)
        if options.query:
          uri += '&q=%s' %urllib.quote_plus(options.query)
        photo_feed = client.GetFeed(uri)
        photo_entries.extend(photo_feed.entry)
    else:
      uri = ('/data/feed/api/user/default?kind=photo&q=%s' % 
             (urllib.quote_plus(options.query)))
      photo_entries = client.GetFeed(uri).entry
      
    for photo in photo_entries:
      if not photo.media:
        photo.media = Group()
      if not photo.media.keywords:
        photo.media.keywords = Keywords()
      photo.media.keywords.text = options.tags
      client.UpdatePhotoMetadata(photo)
      
  else:
    print 'Sorry, task "%s" is currently unsupported for picasa.' % task_name