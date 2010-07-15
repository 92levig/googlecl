
 Copyright (C) 2010 Google Inc.

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.

Contents:
---------
1. Introduction
  1.1 README style
2. Commands
  2.1 Services
    2.1.1 Blogger
    2.1.2 Calendar
    2.1.3 Contacts
    2.1.4 Docs
    2.1.5 Picasa
    2.1.6 YouTube
  2.2 The 'list' task
3. Options
  3.1 Tags
  3.2 Date

1. Introduction
Welcome to the README. If you're reading this after unzipping it from a tarball, you may want to check the project homepage at http://code.google.com/p/googlecl/ for the most up-to-date information. If you're reading this after checking out the svn repository, this should have the most up-to-date information on the capabilities and usage of the code in svn HEAD.

For installation instructions, see INSTALL.txt

For help with the configuration file, see README.config

1.1 README style
Wiki markup is used occasionally in this document:
  * The '`' character is marks example commands.
  * '*' denotes an entry in a list (such as this one).

2. Commands
Some terminology:
  * service - The Google service being used (Picasa, Blogger, etc.)
  * task - The task that the service will be doing (tag, post, delete, etc.)

You can also access help by typing `$ google help` or help on a specific service with `$ google help <service>`. For help with available options and what they mean, use `$ google --help`

2.1 Services
Each sub-section corresponds to a service, which lists the available tasks and some options commonly used with that service. Each task follows the format "task: description. `example`". Note that the `example` omits the initial `$ google <service>`

You can access a list of available tasks and their options with the "help" command as described above.

2.1.1 Blogger
Common options:
  * blog: If you have multiple blogs, you can indicate which one to use. The value you give here the is saved in your config file for future use, if your config file does not already contain an entry for "blog". See ConfigurationOptions.

Tasks:
  * delete: Delete posts. `delete --title "Silly post number [0-9]*"`
  * list: List posts. `list title,url-site`
  * post: Upload posts. `post --tags "GoogleCL, awesome" "Here's a really short post. The next posts will be much longer!" ~/blog/2010/may/*`
  * tag: Label posts `tag --title "Dev post" --tags "Python, software"`

2.1.2 Calendar
Common options:
  * cal: Specify the name of the calendar. This can be a regular expression. If this option is not given, the primary calendar is used.
  * date: Specify a date, or date range. Dates are inclusive, so `--date 2010-06-23,2010-06-25` will include the 23rd, 24th, and 25th of June.
  * reminder: (for add task only) Add a reminder to the events being added, one per default reminder type in your calendar settings. Default is in minutes, though you can say something like "2h" for one hour, "1d" for one day, etc.

Tasks:
  * add: Add event to calendar. `add "Dinner party with George tomorrow at 6pm"`
  * delete: Delete an event. `delete --cal "GoogleCL dev cal" --title "Release.*"`
  * list: List events. `list --date 2010-06-01,2010-06-30`
  * today: List events for today only. `today`

Note: The add task uses the 'Quick Add' feature, which you can read about here: http://www.google.com/support/calendar/bin/answer.py?answer=36604#text

2.1.3 Contacts
Tasks:
  * add: Add contacts. `add "Jim Raynor, jimmy@noreaster.com" contacts.csv`
  * delete: Delete contacts. `delete --title Jerkface`
  * list: List contacts. `list name,email --title ".*bob.*" > the_bobs.csv`
  * add-groups: Add contact groups. `add-groups "Work" "Friends"`
  * delete-groups: Delete contact groups. `delete-groups "Friends"`
  * list-groups: List contact groups. `list-groups "my group"`

2.1.4 Docs
Common options:
  * format: Force docs to use the extension you provide.
  * folder: Specify a folder on Docs to search in or upload to.

Tasks:
  * delete: Delete docs. `delete --title "Evidence"`
  * edit: Edit or view a document. `edit --title "Shopping list" --editor vim`
  * get: Download docs. `get --title "Homework [0-9]*"`
  * list: List documents. `list title,url-direct --delimiter ": "`
  * upload: Upload documents. `upload the_bobs.csv ~/work/docs_to_share`

2.1.5 Picasa
Common options:
  * owner: Owner of the albums you want to deal with. For example, to download bob's album, add --owner bob to the "get" task. To post to your friend's album that she shared with you, add --owner your_friend to the "post" task.

Tasks:
  * create: Create an album. `create --title "Summer Vacation 2009" --tags Vermont ~/photos/vacation2009/*`
  * delete: Delete photos or albums. `delete --title "Stupid album"`
  * get: Download photos. `get --title "My Album" /path/to/download/folder`
  * list: List photos or albums. `list title,url-direct --query "A tag"`
  * post: Add photos to an album. `post --title Summer Vacation 2008" ~/old_photos/*.jpg`
  * tag: Tag photos. `tag --title "Album I forgot to tag" --tags oops`

2.1.6 YouTube
Tasks:
  * delete: Delete videos. `delete --title ".*"`
  * list: List your videos. `list`
  * post: Post a video. `post --category Education --devtags GoogleCL killer_robots.avi`
  * tag: Tag videos. `tag -n ".*robot.*" --tags robot`

2.2. The List task
The list task can be given additional arguments to specify what exactly is being listed. For example,

`$ google <service> list style1,style2,style3 --delimiter ": "`

will output those styles, in that order, with ": " as a delimiter. Valid values for `<`style1`>` etc. are (with common services in parentheses):
  * 'address' - postal addresses. (Contacts)
  * 'author' - author(s). (Blogger)
	* 'company' - company name. (Contacts)
  * 'email' - email address(es). (Contacts)
	* 'im' - instant messanger handles. (Contacts)
	* 'notes' - notes on a contact. (Contacts)
	* 'phone' - phone numbers. (Contacts)
  * 'summary' - summary text.
  * 'title' or 'name' - displayed title or name.
  * 'url' - treated as 'url-direct' or 'url-site' depending on setting in preferences file.
  * 'url-site' - url of the site.
  * 'url-direct' - url directly to the resource.
  * 'when' - "when" data. (Calendar)
  * 'where' - "where" data. (Calendar)
  * 'xml' - full XML dump.

The difference between 'url-site' and 'url-direct' is best exemplified by a picasa PhotoEntry: 'url-site' gives a link to the photo in the user's album, 'url-direct' gives a link to the image url. If 'url-direct' is specified but is not applicable, 'url-site' is placed in its stead, and vice-versa.

3. Options
Some more details on the trickier options you can specify.

3.1 Tags
The tags option will let you both add and remove tags / labels. Here are some examples:
  * 'tag1, tag2, tag3': Add tag1, tag2, and tag3 to the item's tags
  * '-tag1, tag4': Remove tag1, add tag4
  * '-- tag5': Remove all tags, then add tag5

3.2 Date
The behavior given here is applicable to the calendar service.
  * '2010-06-01': Specify June 1st, 2010
  * '2010-06-01,': On and after June 1st, 2010
  * '2010-06-01,2010-06-25': Between June 1st and June 25th, inclusive
  * ',2010-06-15': On or before June 15th

Note that the delete task will still interpret 'date,' and ',date' indentically.
