"""
Created on Apr 19, 2010

@author: Tom Miller

Contains a simple extension to optparse.OptionParser capable of handling 
quotation marks.

"""
import optparse
import sys

class MyParser(optparse.OptionParser):
  """A simple extension to optparse.OptionParser that handles quotation marks"""

  def parse_args(self, given_args=sys.argv[1:]):
    """Parse arguments with quotes.
    
    Same as optparse.OptionParser.parse_args(), but combines args in quotes.
    For example, picasa delete -a "Boring Album Title" will combine 
    "Boring Album Title" into the argument for -a 
    
    Keyword arguments:
    given_args -- the list of arguments. (default sys.argv[1:])
    
    Returns: optparse.OptionParser.parse_args(self, merged_arguments_list)
    
    """
    if not given_args:
      return optparse.OptionParser.parse_args(self, given_args)
    merged_args = ' '.join(given_args)
    quote_index = merged_args.find('"')
    if quote_index == -1:
      final_args = given_args
    else:
      final_args = []
      while quote_index != -1:
        start = quote_index
        end = merged_args[start+1:].find('"') + start + 1
        quoted_arg = merged_args[start+1:end] 
        non_quoted_args = merged_args[:start].split()
        final_args.extend(non_quoted_args)
        final_args.extend([quoted_arg])
        merged_args = merged_args[end+1:]
        if merged_args:
          quote_index = merged_args.find('"')
        else:
          quote_index = -1
          
      final_args.extend([merged_args.strip()])
    
    return optparse.OptionParser.parse_args(self, final_args)