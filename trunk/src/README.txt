
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

1. INTRODUCTION
Please visit the project homepage at http://code.google.com/p/googlecl/ for the most up-to-date information.

For installation instructions, see INSTALL.txt

For help with the configuration file, see README.config

2. COMMANDS
Some terminology:
  * service - The Google service being used (Picasa, Blogger, etc.)
	* task - The task that the service will be doing (tag, post, delete, etc.)

You can also access help by typing {{{$ ./google.py help}}} or help on a specific service with {{{$ ./google.py help <service>}}}. For help with available options and what they mean, use {{{$ ./google.py --help}}}

=Services=
Each sub-section corresponds to a service, and each list item is a task that service can do. Each list item follows the format "task: description. {{{example}}}". Note that the example omits the initial {{{$ ./google.py <service>}}}

==Blogger==
  * delete: Delete posts. {{{delete --title "Silly post number [0-9]*"}}}
  * list: List posts. {{{list title,url-site}}}
	* post: Upload posts. {{{post --tags "GoogleCL, awesome" "Here's a really short post. The next posts will be much longer!" ~/blog/2010/may/*}}}
	* tag: Label posts {{{tag --title "Dev post" --tags "Python, software"}}}

==Calendar==
  * add: Add event to calendar. {{{add "Dinner party with George tomorrow at 6pm"}}}
	* delete: Delete an event. {{{delete --cal "GoogleCL dev cal" --title "Release.*"}}}
	* list: List events. {{{list --date 2010-06-01,2010-06-30}}}
	* today: List events for today only. {{{today}}}

==Contacts==
  * add: Add contacts. {{{add "Jim Raynor, jimmy@noreaster.com" contacts.csv}}}
	* delete: Delete contacts. {{{delete --title Jerkface}}}
	* list: List contacts. {{{list name,email --title ".*bob.*" > the_bobs.csv}}}

==Docs==
  * delete: Delete docs. {{{delete --title "Evidence"}}}
	* edit: Edit or view a document. {{{edit --title "Shopping list" --editor vim}}}
	* get: Download docs. {{{get --title "Homework [0-9]*"}}}
	* list: List documents. {{{list title,url-direct --delimiter ": "}}}
	* upload: Upload documents. {{{upload the_bobs.csv ~/work/docs_to_share/*}}}

==Picasa==
  * create: Create an album. {{{create --title "Summer Vacation 2009" --tags Vermont ~/photos/vacation2009/*}}}
	* delete: Delete photos or albums. {{{delete --title "Stupid album"}}}
  * get: Download photos. {{{get --title "My Album" /path/to/download/folder}}}
	* list: List photos or albums. {{{list title,url-direct --query "A tag"}}}
	* post: Add photos to an album. {{{post --title Summer Vacation 2008" ~/old_photos/*.jpg}}}
	* tag: Tag photos. {{{tag --title "Album I forgot to tag" --tags oops}}}

==Youtube==
  * delete: Delete videos. {{{delete --title ".*"}}}
  * list: List your videos. {{{list}}}
	* post: Post a video. {{{post --category Education --devtags GoogleCL killer_robots.avi}}}
  * tag: Tag videos. {{{tag -n ".*robot.*" --tags robot}}}

===The List task===
The list task can be given additional arguments to specify what exactly is being listed. For example,

{{{$ ./google.py <service> list style1,style2,style3 --delimiter ": "}}}

will output those styles, in that order, with ": " as a delimiter. Valid values for `<`style1`>` etc. are:
  * 'title' - title of the entry.
  * 'url' - treated as 'url-direct' or 'url-site' depending on setting in preferences file.
  * 'url-site' - url of the site associated with the entry.
  * 'url-direct' - url directly to the resource.
  * 'author' - author(s) of the entry.
  * 'when' - "when" data for the entry (typically calendar-only, for start and end date of the event).
        'where' - "where" data for the entry (typically calendar-only, for where the event takes place).

The difference between 'url-site' and 'url-direct' is best exemplified by a picasa PhotoEntry: 'url-site' gives a link to the photo in the user's album, 'url-direct' gives a link to the image url. If 'url-direct' is specified but is not applicable, 'url-site' is placed in its stead, and vice-versa.
