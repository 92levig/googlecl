**8 June 2015: GoogleCL is currently broken due to the OAuth1 turndown, and likely to remain so. Thanks for your support over the years, and apologies for the lack of prior notice.**

#summary Description of the configuration file and its options

Your configuration/preferences file is searched for in the following order:
  * Current directory
  * $XDG\_CONFIG\_HOME/googlecl or $HOME/.config/googlecl if $XDG\_CONFIG\_HOME is undefined
  * $XDG\_CONFIG\_DIRS or /etc/xdg if $XDG\_CONFIG\_DIRS is undefined (with /googlecl appended to each directory)
  * ~/.googlecl (The configuration file home from v0.9.8 and earlier)
The file is assumed to be called "config." If no file is found, one is created. On POSIX systems, in the directory specified by the second item in the above list. On other systems, in ~/.googlecl as before. You can also specify a file with the --config option.

Windows users: Your configuration and data folder should be in the same folder as Documents, Photos, My Videos, etc. I believe it's typically C:\Users\USERNAME\.googlecl for Windows 7, and C:\Documents and Settings\USERNAME for XP.

## Options ##
Each option description follows the format `<name>: [<values>]` description

### All sections ###
Each of these values can be found in any section. The service being run will try to find the option in its own section, and failing that, in the GENERAL section.

  * `<option>: [<string>]` You can specify any option in the config file to use as a "general" case. When a command-line option is required (for example the username, or the title of an album created with Picasa), and nothing is passed in via the command line, this value will be used.
  * `cap_results: [True, False]` Cap the number of results to max\_results. (That is, queries will only return one feed).
  * `delete_prompt: [True, False]` Prompt to confirm deletion of items.
  * `force_gdata_v1: [True, False]` Force GoogleCL to use the code written for version 1 of the gdata API. True will disable some functionality (e.g. being able to see/manipulate arbitrary uploads to Docs), but may be required if you are unable to copy and paste the verification code in the browser. (For advanced users: This forces the import\_service() function in the google script to load the "service" module even when the "client" module is available.)
  * `list_fields: [<field>,<field>,...]` Comma-separated (no spaces) list of attributes to print out when using the 'list' task and no fields are specified on the command line. For a list of valid fields, see the README / manual.
  * `max_results: [<integer>]` Maximum number of results / entries to return. Sets the max-results query parameter of the uri. You can use this with cap\_results to limit the amount of data being sent over the network.
  * `regex: [True, False]` Use regular expressions in matching titles.
  * `tags_prompt: [True, False]` Prompt for tags for each item being uploaded. (Not fully implemented).

### Picasa ###
  * `access: [public, private, protected]` The default access level of the albums you create. Public means visible to all, private means unlisted, protected means sign-in required to view the album.

### Docs ###
  * `xxx_format: [<extension>]` The extension to use for a type of document. The types of document are document, spreadsheet, and presentation. PDF files automatically use 'pdf' as the extension
  * `xxx_editor: [<editor>]` The editor to use for a type of document. The types of document are the same as the xxx\_format option, plus pdf\_editor in case you have a pdf editor.
  * `decode_utf_8: [True,False]` When you retrieve docs from the server, you can have GoogleCL try to remove the UTF-8 byte-order marker (BOM) from the document. Most users will not need to worry about this and want to leave this as undefined or false, but it's handy if you have an application sensitive to the BOM such as `less` or `tex`.
  * `editor: [<editor>]` The editor to use by default if the document type is not defined by an xxx\_editor option. If this is not defined, will use the EDITOR environment variable instead.
  * `format: [<extension>]` The extension to use by default if the document type is not defined by an xxx\_format option.

### General ###
  * `* auth_browser: [<browser>]` Browser to launch when authenticating the OAuth request token. You should only need to authenticate to each service once.
  * `* date_print_format: [<format string>]` Format to use when printing date information. See the Python "time" documentation for formats (http://docs.python.org/library/time.html#time.strftime). For example: "`%m %d at %H`" for "`<month> <day> at <hour>`"
  * `* delete_by_default: [True, False]` When prompted to confirm deletion of an object, hitting enter directly will confirm the delete.
  * `* missing_field_value: [<string>]` Placeholder string to use when listing an invalid attribute, for example, the url of a contact.
  * `* url_style: [site, direct]` Which sub-style to use for listing urls. "Site" will typically put you at the website, while "direct" is usually a link directly to the resource.