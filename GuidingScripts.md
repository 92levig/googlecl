**8 June 2015: GoogleCL is currently broken due to the OAuth1 turndown, and likely to remain so. Thanks for your support over the years, and apologies for the lack of prior notice.**

#summary Commands and scripts that GoogleCL CANNOT do, but would be nice to do.

# Soon #
Things we want GoogleCL to be able to do in the short term.

### Upload a photo to picasa then email the link to all your contacts ###
Code:
```
> picasa post --album album_to_post_to /path/to/photo.jpg
> picasa list url-site --album album_to_post > link_to_photo_in_album.txt
> mail --to contact1,contact2 --subject "New Photo!" link_to_photo_in_album.txt
```
Blocking: No Gmail python client library, no write access to gmail (read-only feeds), difficult to list photos unless you know precise tags / name of photo.

# Brainstorming #
Things that would be really super cool if GoogleCL could do them. They may be totally feasible given a decent amount of time, or insanely difficult.

### Arbitrary gdata calls ###

Not all gdata APIs have python convenience libraries.  It'd be great if I could use googlecl to make calls to the underlying AtomPub / JSON services.  The command line options might not look as pretty, but googlecl might then be able to be come forward-compatible with new gdata APIs.

For example, say I want to use Google Maps geocoding features even though they're not "natively" supported by googlecl.  I find the documentation page for the javascript library: http://code.google.com/apis/maps/documentation/javascript/services.html#GeocodingRequests and somehow pass enough information to googlecl for it to construct the proper (potentially very ugly) request object and display the (potentially very ugly) response object.


### Search Google for top results, summaries, links, etc. ###
Code:
```
> search --csv 'omgponies'
"OMG! Ponies!","Apr 9, 2010","OMG! Ponies! is powered by WordPress 2.9.1 and Re...","www.omg-ponies.com/"

[...]
```
Blocking: Google search results aren't involved with the GData protocol - a separate HTTP client would have to be written.

### Get latitude and longitude for arbitrary addresses ###
Code:
```
> maps search --latlong "1600 Amphitheatre 94043"
122.1234091,38.12313587,12
```
Blocking: No client libraries.

### Translate text via Google translate ###
Code:
```
> translate --to "French" "this cheese is delicious"
```
Blocking: No python client library, low priority