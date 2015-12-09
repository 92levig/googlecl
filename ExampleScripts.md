**8 June 2015: GoogleCL is currently broken due to the OAuth1 turndown, and likely to remain so. Thanks for your support over the years, and apologies for the lack of prior notice.**

#summary Example commands and tasks GoogleCL can do.


Also see the [Manual](Manual.md) and the [SystemRequirements](SystemRequirements.md).  Note that (only) the first time you use each service, you'll need to grant authorization from a web browser.

GoogleCL will do its best to figure out what you wanted without specific options being mentioned. In the descriptions that follow, any required options will be filled in by leftover command line arguments. For example, here is the description for the Blogger "tag" task:

Requires: title AND tags Optional: blog

So if you do not specify `--title` or `--tags`, either on the command line or with your configuration file, GoogleCL will read the first argument as the title, and the second as a comma-separated list of tags. That is,

`$ google blogger tag "My Post" "tag1, tag2, tag3"`

is equivalent to

`$ google blogger tag --title "My Post --tags "tag1, tag2, tag3"`

If you think something strange is going on, add the `--verbose` flag to the command, and you should see an output of what required fields were not specified with an option flag, and what the options were ultimately filled in with. Here's an example output from `blogger list`:

`missing_reqs: ['fields']`<br>
<code>Option convert: True</code><br>
<code>Option delimiter: ,</code><br>
<code>Option fields: title,url-site        # Filled in from the config file</code><br>
<code>Option hostid: MY_HOST_ID</code><br>
<code>Option src: []</code><br>
<code>Option user: tom.h.miller</code><br>
<code>Option verbose: True</code><br>

There are also instances, (usually when listing or deleting events) where you want to specify more than one value for an argument. These should be picked up from the command line arguments semi-intelligently. For example:<br>
<br>
<code>$ google calendar today Breakfast Lunch Dinner</code>

will decide that you're looking for events with titles that start with "Breakfast", or "Lunch", or "Dinner".<br>
<br>
These examples use regular expressions (albeit very simple ones). GoogleCL will only accept expressions that work with the <a href='http://docs.python.org/library/re.html'>Python re package</a>. Regular expressions are enabled by default, but you can disable them with the <code>regex</code> configuration option. See ConfigurationOptions.<br>
<br>
The following examples omit the leading <code>$ google &lt;service&gt;</code>
<h1>Blogger</h1>
<b>Note:</b> <code>--blog</code> is required the first time you run a blogger task, unless you only have one blog. If you have more than one blog and do not specify <code>--blog</code>, the blog that you entered the first time you ran GoogleCL will be used.<br>
<br>
<h2>delete</h2>
Delete posts.<br>
<br>
Requires: title Optional: blog<br>
<br>
<ul><li><code>delete bad_post really_bad\w*</code>
</li><li><code>delete --blog ".*" --title ".*fanfic.*"</code></li></ul>

<h2>list</h2>
List posts.<br>
<br>
Requires: fields AND delimiter Optional: blog, title, owner<br>
<br>
<ul><li><code>list name,author,url --blog ".*"</code>
</li><li><code>list --owner &lt;Blogger Profile ID Number&gt;</code>
</li><li><code>list --delimiter="|" --title wiki</code></li></ul>

<h2>post</h2>
Post content to a blog.<br>
<br>
Requires: src Optional: blog, title, tags, draft<br>
<br>
<ul><li><code>post --tags "GoogleCL, awesome" --title "Test Post" --src "I'm posting from the command line"</code>
</li><li><code>post blogpost.txt</code>
</li><li><code>post ~/old_posts/*.txt ~/new_posts/*.html</code>
</li><li><code>post --blog "Ye Olde Tech Blog" "Hark! Android 2.2 released." --tags "google, android" --draft</code></li></ul>

<h2>tag</h2>
Label/tag posts in a blog.<br>
<br>
Requires: title AND tags Optional: blog<br>
<br>
See the <a href='http://code.google.com/p/googlecl/wiki/Manual#Options'>Manual</a> for tag syntax<br>
<br>
<ul><li><code>tag "Chaffeur" "-confidential awesome"</code>
</li><li><code>tag --blog "Tagless" ".*" "--"</code></li></ul>

<h1>Calendar</h1>
<b>Note:</b> if <code>--cal</code> is omitted, your primary/default calendar will be used.<br>
<br>
<b>Note:</b> For <code>list</code> and <code>delete</code>, your ENTIRE CALENDAR will be retrieved. This can take a while. Use <code>--date</code> to restrict date ranges, and <code>--query</code> to match text in the event title or description. See the Manual for how to use <code>--date</code>.<br>
<br>
<h2>add</h2>
Add events.<br>
<br>
Requires: src Optional: cal<br>
<br>
<ul><li><code>add "Dinner party tomorrow at 6pm"</code>
</li><li><code>add --cal launch "Release .deb tomorrow" "Release .zip at 5"</code></li></ul>

<b>Note:</b> The src parameter is parsed for special values so you can set the time and the event length:<br>
<br>
<ul><li><code> add "Meeting on 29 December at 10pm" </code></li></ul>

will add the entry from 10pm till 11pm on Dec 29 with the description "Meeting"<br>
<br>
<ul><li><code> add "Meeting on 29 December at 8am till 2pm" </code></li></ul>

will add the entry from 8am till 2pm on Dec 29 with the description "Meeting"<br>
<br>
<ul><li><code> add "Meeting with Megi on 29 December from 8am till 2pm" </code></li></ul>

will add the entry from 8am till 2pm on Dec 29 with the description "Meeting with Megi"<br>
<br>
<h2>delete</h2>
Delete events.<br>
<br>
Requires: (title OR query) Optional: date, cal<br>
<br>
<ul><li><code>delete "Lunch with that jerk"</code>
</li><li><code>delete --cal "tentative" --title ".*"</code></li></ul>

<h2>list</h2>
List events.<br>
<br>
Requires: fields AND delimiter Optional: title, query, date, cal<br>
<br>
<ul><li><code>list --fields title,when,where --cal "commitments"</code>
</li><li><code>list Breakfast Lunch Dinner --date 2010-10-14</code>
</li><li><code>list -q party --cal ".*"</code></li></ul>

<h2>today</h2>
List events going on today. Essentially shorthand for <code>--date &lt;today&gt;,&lt;tomorrow&gt;</code> with the <code>list</code> task.<br>
<br>
Requires: fields AND delimiter Optional: title, query, cal<br>
<br>
<ul><li><code>today --cal ".*"</code>
</li><li><code>today --fields name,where --delimiter " :: "</code></li></ul>

<h1>Contacts</h1>
<b>Note:</b> <code>--title</code> is required for most of these. If you are prompted to enter a title, just hitting enter is equivalent to and faster than specifying ".<b>".</b>

<h2>add</h2>
Add contacts.<br>
<br>
Requires: src<br>
<br>
<b>Note:</b> <code>src</code> can be a name,email pair, or a file that contains one name,email pair per line.<br>
<br>
<ul><li><code>add "J. Random Hacker, jrandom@example.com"</code>
</li><li><code>add "contacts.csv" "Jim Raynor, jimmy@noreaster.com"</code></li></ul>

<h2>add-groups</h2>
Add contact group(s)<br>
<br>
Requires: title<br>
<br>
<ul><li><code>add "LAN buddies"</code>
</li><li><code>add "Wedding guests" "Wedding services"</code></li></ul>

<h2>delete</h2>
Delete contacts.<br>
<br>
Requires: title<br>
<br>
<ul><li><code>delete Huey Dewey Louie</code>
</li><li><code>delete ".*Kerrigan"</code></li></ul>

<h2>delete-groups</h2>
Delete contact group.<br>
<br>
Requires: title<br>
<br>
<ul><li><code>delete-groups "In-laws"</code></li></ul>

<h2>list</h2>
List contacts.<br>
<br>
Requires: fields AND title AND delimiter<br>
<br>
<ul><li><code>list --fields=name,email,relations .*bert</code>
</li><li><code>list Jane Charlotte Emily</code></li></ul>

<h2>list-groups</h2>
List contact groups.<br>
<br>
Requires: title<br>
<br>
<b>Note:</b> Groups that begine with "System Group:" are the groups Gmail starts with.<br>
<br>
<ul><li><code>list-groups ".*"</code>
</li><li><code>list-groups "System Group:"</code></li></ul>

<h1>Docs</h1>
<b>Note:</b> <code>--folder</code> will take the name of any folder, even subfolders.  (Also note that --folder is currently broken; uploads all happen to the root folder).<br>
<br>
<h2>delete</h2>
Delete documents.<br>
<br>
Requires: title Optional: folder<br>
<br>
<ul><li><code>delete "Evidence"</code>
</li><li><code>delete ".*" --folder junk</code></li></ul>

<h2>edit</h2>
Edit a document.<br>
<br>
Requires: title Optional: format, editor, folder<br>
<br>
<b>Note:</b> editing with Open Office will not work. See <a href='https://code.google.com/p/googlecl/issues/detail?id=79'>Issue 79</a>.<br>
<br>
<b>Note:</b> You must have python-gdata >= 1.3.0 to edit documents.<br>
<br>
<ul><li><code>edit "Shopping list" --editor vim</code>
</li><li><code>edit "Budget" --format html</code></li></ul>

<h2>get</h2>
Download a document.<br>
<br>
Requires: (title OR folder) AND dest Optional: format<br>
<br>
<b>Note:</b> You must have python-gdata >= 1.3.0 to download documents.<br>
<br>
<ul><li><code>get --folder Homework .</code>
</li><li><code>get "Expense sheet" expenses.xls</code></li></ul>

<h2>list</h2>
List documents.<br>
<br>
Requires: fields AND delimiter Optional: title, folder<br>
<br>
<ul><li><code>list</code>
</li><li><code>list --folder essays --fields title,url --delimiter " : "</code></li></ul>

<h2>upload</h2>
Upload a document.<br>
<br>
Requires: src Optional: title, folder, format<br>
<br>
<b>Note:</b> <code>--folder</code> will accept only one folder to upload into. If you have two or more folders with the same name, even subfolders, you will have to pick between them (hard to do when they have the same name).  (Also note that --folder is currently broken; uploads all happen to the root folder).<br>
<br>
<b>Note:</b> Users with a Google Apps Premium account can use an additional option: <code>--no-convert</code>. This will let you upload arbitrary filetypes to Docs, like you can through the web interface. Unfortunately, this is not enabled for regular users.<br>
<br>
<ul><li><code>upload ~/docs/to/share/*</code>
</li><li><code>upload Necronomicon.doc --folder "Book club" --title "Pride and Prejudice"</code>
</li><li><code>upload my_contacts.csv                 # Upload a CSV file, automatically converted to a spreadsheet.</code>
</li><li><code>upload my_contacts.csv --format txt    # Upload a CSV file, keep as plain text.</code></li></ul>

<h1>Picasa</h1>
<h2>create</h2>
Create an album.<br>
<br>
Requires: title Optional: src, date, summary, tags<br>
<br>
<b>Note:</b> <code>--tags</code> will be applied to each photo being uploaded, not the album.<br>
<br>
<ul><li><code>create "Vacation 2010" ~/Photos/2010/06/*.jpg</code>
</li><li><code>create "Empty album"</code>
</li><li><code>create --summary "Planet earth turns 6013" --date 2009-10-23 "Happy birthday, earth" ~/pics/trolling/*</code>
</li><li><code>create "CATS" ~/photos/theater/broadway/cats/*.png --tags lol</code></li></ul>

<h2>delete</h2>
Delete photos or albums.<br>
<br>
Requires: (title OR query)<br>
<br>
<b>Note:</b> <code>--title</code> will match on album names, <code>--query</code> on photo tags and captions. If <code>--query</code> is specified, the objects being deleted will be photos that match the query value that are also in the album that matches <code>--title</code>.<br>
<br>
<ul><li><code>delete "Vacation 2010" -q "kind of boring"    # Delete photos in album "Vacation 2010" that have a tag or caption of "kind of boring"</code>
</li><li><code>delete "Cosplay" "LARPing"   # Delete the albums "Cosplay" and "LARPing"</code></li></ul>

<h2>get</h2>
Download albums.<br>
<br>
Requires: title AND dest Optional: owner, format<br>
<br>
<b>Note:</b> <code>--format</code> applies to videos ONLY, and should be either mp4 or swf<br>
<br>
<ul><li><code>get "My album" .</code>
</li><li><code>get "Close-ups of large-toothed creatures" --owner sirwin --dest ~/photos</code></li></ul>

<h2>list</h2>
List photos.<br>
<br>
Requires: fields AND delimiter Optional: title, query, owner<br>
<br>
<b>Note:</b> <code>--title</code> still matches on album titles. This will list photos inside albums that match the title.<br>
<br>
<ul><li><code>list</code>
</li><li><code>list --fields title,url,summary "cats" "more cats" "lolcats"</code>
</li><li><code>list --owner dr.horrible -q Penny</code>
</li><li><code>list --owner fancy.pants.cameraman --fields title,fstop,exposure,ev,model,flash</code></li></ul>

<h2>list-albums</h2>
List albums.<br>
<br>
Requires: fields AND delimiter Optional: title, owner<br>
<br>
<ul><li><code>list-albums --owner peter.parker, --fields </code>
</li><li><code>list-albums "Skiing .*"</code></li></ul>

<h2>post</h2>
Post photos or video to an album.<br>
<br>
Requires: title AND src Optional: tags, owner<br>
<br>
<ul><li><code>post "Empty album" ~/photos/new/*</code>
</li><li><code>post --src profile_picture.png --title "Me" --tags vanity</code>
</li><li><code>post "Collaboration Album 1" ~/photos/my_photos/*.jpg --owner a.adams</code></li></ul>

<h2>tag</h2>
Tag photos.<br>
<br>
Requires: (title OR query) AND tags Optional: owner<br>
<br>
<ul><li><code>tag "Stand-up night" "humor, comedy, night-out"</code>
</li><li><code>tag --owner anon "Photoshopped" "-plausible ridiculous"</code></li></ul>

<h1>Youtube</h1>
<b>Note:</b> You must log on with your Google account, but the <code>--owner</code> option will only accept YouTube usernames.<br>
<br>
<b>Note:</b> The devkey is provided for you. However, because of the nature of the key, it may become invalid in the future, and in that case you will have to supply your own. <code>--devkey</code> will also take the name of a file where the devkey is stored.<br>
<br>
<h2>delete</h2>
Delete videos.<br>
<br>
Requires: title AND devkey<br>
<br>
<ul><li><code>delete ".*cat.*"</code>
</li><li><code>delete "Vlog episode [0-9]+" --devkey mydevkey.txt</code></li></ul>

<h2>list</h2>
List videos by user.<br>
<br>
Requires: fields AND delimiter Optional: title, owner<br>
<br>
<ul><li><code>list --owner pomplamoosemusic</code>
</li><li><code>list --fields title,summary,url "My video" "My other video"</code></li></ul>

<h2>post</h2>
Post a video.<br>
<br>
Requires: src AND category AND devkey Optional: title, summary, tags<br>
<br>
<b>Note:</b> A list of legal values for category can be found in the Manual. If you don't really care what category your video gets uploaded to, set a default in your configuration file (see ConfigurationOptions).<br>
<br>
<ul><li><code>post --category Education killer_robots.avi</code>
</li><li><code>post ~/videos/cat-falls-down-stairs.avi Comedy --tags "currency of the internet" --summary "Poor whiskers takes a tumble. She's fine, though, don't worry."</code></li></ul>

<h2>tag</h2>
Add tags to a video and/or change its category.<br>
<br>
Requires: title AND (tags OR category) AND devkey<br>
<br>
<ul><li><code>tag "Cooking with Rob" --category Education</code>
</li><li><code>tag "Vlog .*" "my life, video blogging, AWESOME" --category People</code>