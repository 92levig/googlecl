"""
Created on Apr 20, 2010

A more user-friendly wrapper around the gdata.photos.service.PhotosService 
class.

@author: Tom Miller

"""
import gdata.photos.service
import getpass
import glob
import os
import pickle
import re

class PhotosService(object):
    """Wrapper class for gdata.photos.service.PhotosService()."""
    client = None
    
    def __init__(self):
        """Constructor.""" 
        self.client = gdata.photos.service.PhotosService()
    
    def CreateAlbum(self, title, summary, photo_list=None): 
        """Create an album.
        
        Keyword arguments:
        title -- Title of the album.
        summary -- Summary of the album.
        photo_list -- List of filenames of photos on local host.
        
        """
        album = self.client.InsertAlbum(title=title, summary=summary)
        if photo_list:
            if len(photo_list) == 1:
                self.InsertPhotos(album, glob.glob(photo_list))
            else:
                self.InsertPhotos(album, photo_list)
                
    def DeleteAlbum(self, title):
        """Delete album(s).
        
        Keyword arguments:
        title -- albums matching this title should be deleted.
        
        """
        albums = self.GetAlbum(title=title)
        if not albums:
            print 'No albums with title', title
        for album in albums:
            delete = raw_input('Are you sure you want to delete album ' + 
                               album.title.text + 
                               '? (Y/n): ')
            if not delete or delete.lower() == 'y':
                self.client.Delete(album)
                
    def GetAlbum(self, user='default', title=None, regex=False):
        """Get albums from a user feed.
        
        Keyword arguments:
        user -- the user whose albums are being retrieved. 
                    (Default 'default')
        title -- title that the album should have. 
                    (Default None, for all albums)
        regex -- indicates if the title includes regular expressions. 
                    (Default False)
                    
        Returns: list of albums that match parameters, or [] if none do.
        
        """
        wanted_albums = []
        feed = self.client.GetUserFeed(user=user)
        if not title:
            return feed.entry
        for album in feed.entry:
            if (not regex and album.title.text == title or 
                regex and re.match(title, album.title.text)):
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
            self.client.InsertPhotoSimple(album_url, file, '', file)
            
    def Login(self, credentials_path=None):
        """Try to use programmatic login to log into Picasa.
        
        Keyword arguments:
        credentials_path -- absolute path to file that contains email/password
            for Picasa Web
        
        Returns: True if login was successful, False otherwise.
        
        """
        used_auth_from_file = False
        if os.path.exists(credentials_path):
            with open(credentials_path, 'r') as cred_file:
                try:
                    (email, password) = pickle.load(cred_file)
                except:
                    raise
                else:
                    used_auth_from_file = True
        
        if not used_auth_from_file:
            email = raw_input('Enter your username: ')
            password = getpass.getpass('Enter your password: ')
            
        self.client.email = email
        self.client.password = password
        self.client.source = 'google-cl'
        try:
            self.client.ProgrammaticLogin()
        except gdata.service.BadAuthentication as e:
            print e
            if used_auth_from_file:
                print 'Credentials in %s were rejected.' % credentials_path
                email = None
                password = None
        except gdata.service.CaptchaRequired:
            print 'Too many false logins; Captcha required.'
        except Exception as e:
            raise
        else:
            return (email, password, used_auth_from_file)   