# Copyright (C) 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Service details and instances for the Picasa service."""


from __future__ import with_statement

__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import os
import urllib
import googlecl.util as util
from googlecl.picasa import SECTION_HEADER
from gdata.photos.service import PhotosService, GooglePhotosException


class PhotosServiceCL(PhotosService, util.BaseServiceCL):
  
  """Extends gdata.photos.service.PhotosService for the command line.
  
  This class adds some features focused on using Picasa via an installed app
  with a command line interface.
  
  """
  
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
        
  def build_entry_list(self, user='default', title=None, query=None,
                       force_photos=False):
    """Build a list of entries of either photos or albums.
    
    If no title is specified, entries will be of photos matching the query.
    If no query is specified, entries will be of albums matching the title.
    If both title and query are specified, entries will be of photos matching
      the query that are also in albums matching the title.
      
    Keyword arguments:
      user: Username of the owner of the albums / photos (Default 'default').
      title: Title of the album (Default None).
      query: Query for photos, url-encoded (Default None).
      force_photos: If true, returns photo entries, even if album entries would
                    typically be returned. The entries will be for all photos
                    in each album.
      
    Returns:
      A list of entries, as specified above.
      
    """
    album_entry = []
    if title or not(title or query):
      album_entry = self.GetAlbum(user=user, title=title)
    if query or force_photos:
      uri = '/data/feed/api/user/' + user
      if query and not album_entry:
        entries = self.GetFeed(uri + '?kind=photo&q=' + query).entry
      else:
        entries = []
        uri += '/albumid/%s?kind=photo'
        if query:
          uri += '&q=' + query
        for album in album_entry:
          f = self.GetFeed(uri % album.gphoto_id.text)
          entries.extend(f.entry)
    else:
      entries = album_entry
      
    return entries
  
  def delete(self, title='', query='', delete_default=False):
    """Delete album(s) or photo(s).
    
    Keyword arguments:
      title: Albums matching this title should be deleted.
      query: Photos matching this url-encoded query should be deleted.
      delete_default: If the user is being prompted to confirm deletion, hitting
            enter at the prompt will delete or keep the album if this is True or
            False, respectively. (Default False)
    
    """
    entries = self.build_entry_list(title=title, query=query)
    if query:
      entry_type = 'photo'
      search_string = query
    else:
      entry_type = 'album'
      search_string = title
    if not entries:
      print 'No %ss matching %s' % (entry_type, search_string)
    util.BaseServiceCL.Delete(self, entries, entry_type, delete_default)

  Delete = delete

  def download_album(self, base_path, user, title=None):
    """Download an album to the local host.
    
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

  DownloadAlbum = download_album

  def get_album(self, user='default', title=None):
    """Get albums from a user feed.
    
    Keyword arguments:
      user: The user whose albums are being retrieved. (Default 'default')
      title: Title that the album should have. (Default None, for all albums)
         
    Returns:
      List of albums that match parameters, or [] if none do.
    
    """
    uri = '/data/feed/api/user/' + user + '?kind=album'
    return self.GetEntries(uri, title)

  GetAlbum = get_album

  def insert_photo_list(self, album, photo_list, tags=''):
    """Insert photos into an album.
    
    Keyword arguments:
      album: The album entry of the album getting the photos.
      photo_list: A list of paths, each path a picture on the local host.
      tags: Text of the tags to be added to each photo, e.g. 'Islands, Vacation'
            (Default '').
    
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
      except GooglePhotosException, e:
        print 'Failed to upload %s. (%s: %s)' % (file, e.reason, e.body) 
        failures.append(file)   
    return failures

  InsertPhotoList = insert_photo_list

  def is_token_valid(self):
    """Check that the token being used is valid."""
    return util.BaseServiceCL.IsTokenValid(self, '/data/feed/api/user/default')

  IsTokenValid = is_token_valid

  def tag_photos(self, photo_entries, tags):
    """Add or remove tags on a list of photos.
    
    Keyword arguments:
      photo_entries: List of photo entry objects. 
      tags: String representation of tags in a comma separated list.
            For how tags are generated from the string, 
            see util.generate_tag_sets().
    
    """
    from gdata.media import Group, Keywords
    remove_set, add_set, replace_tags = util.generate_tag_sets(tags)
    for photo in photo_entries:
      if not photo.media:
        photo.media = Group()
      if not photo.media.keywords:
        photo.media.keywords = Keywords()
  
      # No point removing tags if the photo has no keywords,
      # or we're replacing the keywords.
      if photo.media.keywords.text and remove_set and not replace_tags:
        current_tags = photo.media.keywords.text.replace(', ', ',')
        current_set = set(current_tags.split(','))
        photo.media.keywords.text = ','.join(current_set - remove_set)
      
      if replace_tags or not photo.media.keywords.text:
        photo.media.keywords.text = ','.join(add_set)
      elif add_set: 
        photo.media.keywords.text += ',' + ','.join(add_set)
 
      self.UpdatePhotoMetadata(photo)

  TagPhotos = tag_photos


service_class = PhotosServiceCL


#===============================================================================
# Each of the following _run_* functions execute a particular task.
#  
# Keyword arguments:
#  client: Client to the service being used.
#  options: Contains all attributes required to perform the task
#  args: Additional arguments passed in on the command line, may or may not be
#        required
#===============================================================================
def _run_create(client, options, args):
  if options.date:
    import time
    try:
      timestamp = time.mktime(time.strptime(options.date, util.DATE_FORMAT))
    except ValueError, e:
      print e
      print 'Ignoring date option, using today'
      options.date = ''
    else:
      # Timestamp needs to be in milliseconds after the epoch
      options.date = '%i' % (timestamp * 1000)
  
  album = client.InsertAlbum(title=options.title, summary=options.summary, 
                             access=util.config.get(SECTION_HEADER, 'access'),
                             timestamp=options.date)
  if args:
    client.InsertPhotoList(album, photo_list=args, tags=options.tags)


def _run_delete(client, options, args):
  client.Delete(title=options.title,
                query=options.encoded_query,
                delete_default=util.config.getboolean('GENERAL',
                                                      'delete_by_default'))


def _run_list(client, options, args):
  entries = client.build_entry_list(user=options.user,
                                    title=options.title,
                                    query=options.encoded_query,
                                    force_photos=True)
  if args:
    style_list = args[0].split(',')
  else:
    style_list = util.get_config_option(SECTION_HEADER, 'list_style').split(',')
  for item in entries:
    print util.entry_to_string(item, style_list, delimiter=options.delimiter)


def _run_list_albums(client, options, args):
  entries = client.build_entry_list(user=options.user,
                                    title=options.title,
                                    force_photos=False)
  if args:
    style_list = args[0].split(',')
  else:
    style_list = util.get_config_option(SECTION_HEADER, 'list_style').split(',')
  for item in entries:
    print util.entry_to_string(item, style_list, delimiter=options.delimiter)


def _run_post(client, options, args):
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


def _run_get(client, options, args):
  if not args:
    print 'Must provide destination of album(s)!'
    return
  base_path = args[0]
  client.DownloadAlbum(base_path, user=options.user, title=options.title)


def _run_tag(client, options, args):
  entries = client.build_entry_list(query=options.query,
                                    title=options.title,
                                    force_photos=True)
  if entries:
    client.TagPhotos(entries, options.tags)
  else:
    print 'No matches for the title and/or query you gave.'


tasks = {'create': util.Task('Create an album', callback=_run_create,
                             required='title',
                             optional=['date', 'summary', 'tags'],
                             args_desc='PATH_TO_PHOTOS'), 
         'post': util.Task('Post photos to an album', callback=_run_post,
                           required='title', optional='tags',
                           args_desc='PATH_TO_PHOTOS'), 
         'delete': util.Task('Delete photos or albums', callback=_run_delete,
                             required=[['title', 'query']]),
         'list': util.Task('List photos', callback=_run_list,
                           required=['user', 'delimiter'],
                           optional=['title', 'query'], 
                           login_required=False),
         'list-albums': util.Task('List albums', callback=_run_list_albums,
                                  required=['user', 'delimiter'],
                                  optional=['title'],
                                  login_required=False),
         'get': util.Task('Download photos', callback=_run_get,
                          required='user', optional=['title', 'query'], 
                          login_required=False,
                          args_desc='LOCATION'),
         'tag': util.Task('Tag photos', callback=_run_tag,
                          required=['tags', ['title', 'query']])}
