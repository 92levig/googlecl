**8 June 2015: GoogleCL is currently broken due to the OAuth1 turndown, and likely to remain so. Thanks for your support over the years, and apologies for the lack of prior notice.**

#summary How to use GoogleCL.


Some terminology:
  * service - The Google service being used (Picasa, Blogger, etc.)
  * task - The task that the service will be doing (tag, post, delete, etc.)

You can also access help by typing `$ google help` or help on a specific service with `$ google help <service>`. For help with available options and what they mean, use `$ google --help`

If you are looking for instructions for the Discovery APIs, use the DiscoveryManual.

# Services #
Each sub-section corresponds to a service, which lists the available tasks and some options commonly used with that service. Each task follows the format "task: description. `example`". Note that the `example` omits the initial `$ google <service>`

You can access a list of available tasks and their options with the "help" command as described above.

## Blogger ##
Common options:
  * blog: If you have multiple blogs, you can indicate which one to use. The value you give here the is saved in your config file for future use, if your config file does not already contain an entry for "blog". See ConfigurationOptions.

Tasks:
  * delete: Delete posts. `delete --title "Silly post number [0-9]*"`
  * list: List posts. `list --fields=title,url-site`
  * post: Upload posts. `post --tags "GoogleCL, awesome" "Here's a really short post. The next posts will be much longer!" ~/blog/2010/may/*`
  * tag: Label posts `tag --title "Dev post" --tags "Python, software"`

Note: You can use `--owner` to specify another user's blog when listing posts, but you have to provide a Blogger ID (the number in http://www.blogger.com/profile/NUMBER), not the Google account name.

## Calendar ##
Common options:
  * cal: Specify the name of the calendar. This can be a regular expression. If this option is not given, the primary calendar is used.
  * date: Specify a date, or date range, to retrieve events from for listing or deletion. This will not (yet) do anything for the add task. Dates are inclusive, so `--date 2010-06-23,2010-06-25` will include the 23rd, 24th, and 25th of June.
  * reminder: (for add task only) Add a reminder to the events being added, one per default reminder type in your calendar settings. Default is in minutes, though you can say something like `--reminder 2h` for reminder(s) two hours beforehand, `--reminder 1d` for one day, etc.

Tasks:
  * add: Add event to calendar. `add "Dinner party with George tomorrow at 6pm" --reminder 1h`
  * delete: Delete an event. `delete --cal "GoogleCL dev cal" --title "Release.*"`
  * list: List events. `list --date 2010-06-01,2010-06-30`
  * today: List events for today only. `today`

Note: The add task uses the 'Quick Add' feature, which you can read about [here](http://www.google.com/support/calendar/bin/answer.py?answer=36604#text)
**Warning**: Because the add task uses 'Quick Add', it will not work for non-English calendars. See [Issue 211](https://code.google.com/p/googlecl/issues/detail?id=211).

**Note:** The default parameter is parsed for special values so you can set the time and the event length:

  * ` add "Meeting on 29 December at 10pm" `

will add the entry from 10pm till 11pm on Dec 29 with the description "Meeting"

  * ` add "Meeting on 29 December at 8am till 2pm" `

will add the entry from 8am till 2pm on Dec 29 with the description "Meeting"

  * ` add "Meeting with Megi on 29 December from 8am till 2pm" `

will add the entry from 8am till 2pm on Dec 29 with the description "Meeting with Megi"


## Contacts ##
Tasks:
  * add: Add contacts. `add "Jim Raynor, jimmy@noreaster.com" contacts.csv`
  * delete: Delete contacts. `delete --title Jerkface`
  * list: List contacts. `list --fields name,email --title ".*bob.*" > the_bobs.csv`
  * add-groups: Add contact groups. `add-groups "Work" "Friends"`
  * delete-groups: Delete contact groups. `delete-groups "Friends"`
  * list-groups: List contact groups. `list-groups "my group"`

## Docs ##
Common options:
  * format: Force docs to use the extension you provide.
  * folder: Specify a folder on Docs to search in or upload to.

Tasks:
  * delete: Delete docs. `delete --title "Evidence"`
  * edit: Edit or view a document. `edit --title "Shopping list" --editor vim`
  * get: Download docs. `get --title "Homework [0-9]*"`
  * list: List documents. `list --fields title,url-direct --delimiter ": "`
  * upload: Upload documents. `upload the_bobs.csv ~/work/docs_to_share`

Note: Uploading arbitrary files is only possible for Apps Premier customers, using the --no-convert option. See the FAQ.

## Picasa ##
Common options:
  * owner: Owner of the albums you want to deal with. This will work with all tasks but create and delete. For example, to download bob's album, add `--owner bob` to the "get" task. To post to your friend's album that she shared with you, add `--owner your_friend` to the "post" task.

Tasks:
  * create: Create an album. `create --title "Summer Vacation 2009" --tags Vermont ~/photos/vacation2009/*`
  * delete: Delete photos or albums. `delete --title "Stupid album"`
  * get: Download photos. `get --title "My Album" /path/to/download/folder`
  * list: List photos or albums. `list --fields=title,url-direct --query "A tag"`
  * post: Add photos to an album. `post --title "Summer Vacation 2008" ~/old_photos/*.jpg`
  * tag: Tag photos. `tag --title "Album I forgot to tag" --tags oops`

## YouTube ##
Common options:
  * category: YouTube category to assign to the video. This is required, and a little tricky. Here's the mapping for YouTube categories to `--category` values (and capitalization counts!)
| **YouTube category** | **Value for** `--category` |
|:---------------------|:---------------------------|
| Autos & Vehicles     | Autos                      |
| Comedy               | Comedy                     |
| Education            | Education                  |
| Entertainment        | Entertainment              |
| Film & Animation     | Film                       |
| Gaming               | Games                      |
| Howto & Style        | Howto                      |
| Music                | Music                      |
| News & Politics      | News                       |
| Nonprofits & Activism | Nonprofit                  |
| People & Blogs       | People                     |
| Pets & Animals       | Animals                    |
| Science & Technology | Tech                       |
| Sports               | Sports                     |
| Travel & Events      | Travel                     |

If there's a category you frequently classify your videos as, I'd recommend sticking a default value in your [config file](ConfigurationOptions.md)

Tasks:
  * delete: Delete videos. `delete --title ".*"`
  * list: List your videos. `list`
  * post: Post a video. `post --category Education --devtags GoogleCL killer_robots.avi`
  * tag: Tag videos. `tag -n ".*robot.*" --tags robot`

# The List task #
The list task can be given additional arguments to specify what exactly is being listed. For example,

`$ google <service> list --fields=field1,field2,field3 --delimiter ": "`

will output those fields, in that order, with ": " as a delimiter. Valid values for `<`field1`>` etc. are dependent on the service being used.

## Common (all services): ##
  * 'summary' - summary text. Includes Picasa captions.
  * 'title', 'name' - displayed title or name.
  * 'url' - treated as 'url-direct' or 'url-site' depending on setting in preferences file. See the note at the end of this section.
  * 'url-site' - url of the site associated with the resource.
  * 'url-direct' - url directly to the resource.
  * 'xml' - dump the XML representation of the result.

## Blogger: ##
  * 'author' - author of the post

## Calendar: ##
  * 'when' - when an event takes place.
  * 'where' - where the event takes place.

## Contacts: ##
  * 'address', 'where' - postal addresses.
  * 'birthday', 'bday' - birthday.
  * 'email' - email address(es).
  * 'event', 'dates', 'when' - events such as birthdays, anniversaries, etc.
  * 'im' - instant messanger handles.
  * 'name' - full name.
  * 'nickname' - nickname.
  * 'notes' - notes on a contact.
  * 'organization', 'company' - company or organization.
  * 'phone\_number', 'phone' - phone numbers.
  * 'relation' - names of relations, such as manager, spouse, etc.
  * 'title', 'org\_title' - job title.
  * 'user\_defined', 'other' - custom labels.
  * 'website', 'links' - websites and links.

## Picasa: ##
  * 'distance' - distance between the camera and object.
  * 'ev' - [exposure value](http://en.wikipedia.org/wiki/Exposure_value).
  * 'exposure', 'shutter', 'speed' - Exposure time used.
  * 'flash' - whether flash was used or not.
  * 'focallength' - focal length used.
  * 'fstop' - fstop value.
  * 'imageUniqueId', 'id' - EXIF unique image ID.
  * 'iso' - ISO equivalent value of the film speed.
  * 'make' - make of the camera.
  * 'model' - camera model.
  * 'time', 'when' - timestamp of when the photo was taken (in milliseconds since 1/1/1970).

The difference between 'url-site' and 'url-direct' is best exemplified by a picasa photo: 'url-site' gives a link to the photo in the user's album, 'url-direct' gives a link to the image url. If 'url-direct' is specified but is not applicable, 'url-site' is placed in its stead, and vice-versa.

# Options #
GoogleCL will fill in options in what it hopes is a natural way. If you do not specify any options explicitly with `-<letter>` or `--<option>`, the program will suck in values from the command line to replace the missing required options. For example,
```
$ google help contacts
...
list: List contacts
   Requires: fields AND title AND delimiter
```

says that `--fields --title --delimiter` are all required. If you haven't changed your basic configuration, there should be a line under the config header `[CONTACTS]` that says `fields = name,email`, so that required option is fulfilled. (Note that there is a `fields` entry under `[GENERAL]` so you never need to supply a value for `fields`, and shouldn't, unless you specify it with `--fields=<my new fields>`)

Next up is `title`, so if you issue the contacts list command with any free-floating arguments, the first one will be set to `title`.

Finally, `delimiter` is always set to "," by default, so that's satisfied as well.

This means that

```
$ google contacts list Huey Dewey Louie
$ google contacts list Huey Dewey Louie --fields name,email
$ google contacts list --fields name,email --title Huey Dewey Louie
```

all give the same output.

Some tasks have a conditional requirement, such as (title OR query). In this case, `title` is filled first, and GoogleCL assumes you do not want to specify a query. Of course, if you filled `query` explicitly and not `title`, `title` is not filled in with any command line arguments.

There is another example of how options are filled in over at ExampleScripts, plus a bunch of example commands.

Here are some more details on the trickier options you can specify.

## Tags ##
The tags option will let you both add and remove tags / labels. Here are some examples:
  * 'tag1, tag2, tag3': Add tag1, tag2, and tag3 to the item's tags
  * '-tag1, tag4': Remove tag1, add tag4
  * '-- tag5': Remove all tags, then add tag5

## Date ##
The behavior given here is applicable to the calendar service.
  * '2010-06-01': Specify June 1st, 2010
  * '2010-06-01,': On and after June 1st, 2010
  * '2010-06-01,2010-06-25': Between June 1st and June 25th, inclusive
  * ',2010-06-15': On or before June 15th

Note that the delete task will still interpret 'date,' and ',date' identically.

# Configuration #
GoogleCL also incorporates a configuration file that you can use to customize its behavior, including automatic determination of command line options. Take a look at ConfigurationOptions for documentation on the configuration file.

# Search, Plus, Gmail, etc. #

We'd love to support more Google services with GoogleCL, but we're currently limited by the [availability of gdata APIs](http://code.google.com/apis/gdata/docs/directory.html).

Before hacking in our own services, it's probably best if we encourage the gdata teams to add new services (and python interfaces to those new APIs) first.