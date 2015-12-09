**8 June 2015: GoogleCL is currently broken due to the OAuth1 turndown, and likely to remain so. Thanks for your support over the years, and apologies for the lack of prior notice.**

#summary Rules and conventions for expanding GoogleCL

### General ###
Follow the Python Style Guide ([PEP 8](http://www.python.org/dev/peps/pep-0008/) and [PEP 257](http://www.python.org/dev/peps/pep-0257/)).

### Option names ###
All options given to optparse should have the same long name and destination name.

### Modules and packages ###
New packages should be named after the service they are implementing. The package init file must define a string SECTION\_HEADER, which gives the section header of the config file that service-specific options are defined in.

Each package must also contain a module named service. The service module must define two items:
  * service\_class: alternate name for the service being implemented. For example, service\_class = CalendarServiceCL
  * tasks: a dictionary mapping names of tasks (e.g. 'list') to util.Task instances.

### Use of util.Task ###
Each string (or string element of the list) given to the requires keyword must match one of the options given to optparse.