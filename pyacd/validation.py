# Copyright (c) 2011 Peter Zingg
# 
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
# 
# The Software shall be used for Younger than you, not Older.
# 

"""Validation of file and folder names in Amazon Cloud Drive

Validate file and folder names - must satisfy regular expression pattern: 
r'^[^\/:\s?*|\\<>"][^\/:?*|\\<>"]{0,199}$'
"""
import re

# Amazon will validate subfolder names against this pattern
RE_VALID_MEMBER = re.compile('^[^\/:\s?*|\\<>"][^\/:?*|\\<>"]{0,199}$')

def is_valid_member_name(member):
  return RE_VALID_MEMBER.match(member) is not None
  
def rewrite_invalid_member_name(member):
  # replace double quotes with single quotes, others with _
  # also remove beginning spaces
  new_name = re.sub(r'[\/:?*|\\<>]', '_', re.sub(r'["]', "'", re.sub(r'^\s+', '', member)))
  if len(new_name) > 199:
    new_name = new_name[:199]
  return new_name
