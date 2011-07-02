#!/usr/bin/env python
#
# Copyright (c) 2011 Peter Zingg
# Code and api by anatanokeitai.com(sakurai_youhei)
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
"""
administrator@Tualatin ~/svn/pyacd $ ./acdputr.py --help
Usage: acdputr.py [Options] srcdir

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -e EMAIL, --email=EMAIL
                        email address for Amazon.com
  -p PASSWORD, --password=PASSWORD
                        password for Amazon.com
  -s FILE, --session=FILE
                        save or load login session to/from FILE
  -d PATH, --destination=PATH
                        upload path [default: /]
  -v, --verbose         show debug infomation
  -q, --quiet           quiet mode

This command uploads directories recursively to your Amazon Cloud Drive. 
If there is same named file, uploading file is renamed automatically. 
(e.g. 'test.mp3' -> 'test(2).mp3')

administrator@Tualatin ~/svn/pyacd $ ./acdputr.py -e someone@example.com -p xxxx ~/Pictures 
Logging in to Amazon.com ... Done
Uploading test.jpg to / ... Done
"""

import sys
import os
from optparse import OptionParser
import pickle

pyacd_lib_dir=os.path.dirname(os.__file__)+os.sep+"pyacd"
if os.path.exists(pyacd_lib_dir) and os.path.isdir(pyacd_lib_dir):
  sys.path.insert(0, pyacd_lib_dir)

import pyacd

parser=OptionParser(epilog="This command uploads directories recursively to your Amazon Cloud Drive. "+
                            "If there is same named file, uploading file is renamed "+
                            "automatically. (e.g. 'test.mp3' -> 'test (2).mp3')",
                    usage="%prog [Options] srcdir",version="%prog 0.2.1")

parser.add_option("-e","--email",dest="email",action="store",default=None,
                  help="email address for Amazon.com")
parser.add_option("-p","--password",dest="password",action="store",default=None,
                  help="password for Amazon.com")
parser.add_option("-s","--session",dest="session",action="store",default=None,
                  metavar="FILE",help="save or load login session to/from FILE")
parser.add_option("-d","--destination",dest="path",action="store",default="/",
                  help="upload path [default: %default]")
parser.add_option("-v","--verbose",dest="verbose",action="store_true",default=False,
                  help="show debug infomation")
parser.add_option("-q","--quiet",dest="quiet",action="store_true",default=False,
                  help="quiet mode")
parser.add_option("-r","--dry-run",dest="dryrun",action="store_true",default=False,
                  help="just walk directories, don't upload")

def main():
  opts,args=parser.parse_args(sys.argv[1:])

  # Check options of authentication
  if opts.session and os.path.exists(opts.session) and not os.path.isdir(opts.session):
    pass
  elif not opts.email or not opts.password:
    sys.stderr.write("!! email and password are required !!\n")
    parser.print_help()
    sys.exit(2)
    
  args=list(set(args))
  if "-" in args:
    args.remove("-")
    args += [x.strip() for x in sys.stdin.readlines()]

  if 1!=len(args):
    sys.stderr.write("!! no source directory selected !!\n")
    parser.print_help()
    sys.exit(2)
  else:
    srcdir=args[0]
    if not os.path.exists(srcdir):
      sys.stderr.write('Not found "%s"\n'%srcdir)
      sys.exit(2)
    elif not os.path.isdir(srcdir):
      sys.stderr.write('"%s" is not a directory\n'%srcdir)
      sys.exit(2)

  # Login to Amazon.com
  session=None
  try:
    if not opts.quiet:
      sys.stderr.write("Logging in to Amazon.com ... ")
    if opts.email and opts.password:
      session=pyacd.login(opts.email,opts.password)
    else:
      fp=open(opts.session,"rb")
      session=pickle.load(fp)
      fp.close()
      session=pyacd.login(session=session)
  except:
    pass

  # Check login status
  if not session:
    sys.stderr.write("Unexpected error occured.\n")
    sys.exit(2)
  elif not session.is_valid():
    sys.stderr.write("Session is invalid.\n%s\n"%session)
    sys.exit(2)
  elif not session.is_logined():
    sys.stderr.write("Login failed.\n%s\n"%session)
    sys.exit(2)

  if not opts.quiet:
    sys.stderr.write("Done\n")

  if opts.session:
    if not opts.quiet:
      sys.stderr.write("Updating %s ... "%opts.session)
    fp=open(opts.session,"wb")
    fp.truncate()
    pickle.dump(session,fp)
    fp.close()
    if not opts.quiet:
      sys.stderr.write("Done\n")

  # Check destination
  path=opts.path
  if path[0]!='/':path='/'+path
  if path[-1]!='/':path=path+'/'

  basedir = os.path.abspath(args[0])
  baselen = len(basedir)
  directories = [ basedir ]
  while len(directories)>0:
    # entering new folder
    srcdir = directories.pop()
    destdir = path[:-1] + srcdir[baselen:]
    if not opts.quiet:
      sys.stderr.write("Uploading to folder '%s' ...\n"%destdir)
      
    try:
      fileobj = pyacd.api.get_info_by_path(destdir)
      if fileobj.Type == pyacd.types.FOLDER:
        # do nothing, folder exists
        pass
      elif fileobj.Type == pyacd.types.FILE:
        # problem, we won't use this folder
        if not opts.quiet:
          sys.stderr.write("Skipping destination '%s' - it's a file\n"%destdir)
        continue
      else:
        if not opts.quiet:
          sys.stderr.write("Skipping destination '%s' - type is %d\n"%(destdir,fileobj.Type))
        continue
    except pyacd.PyAmazonCloudDriveApiException,e:
      # error getting folder. no folder there, need to create  
      parent, folder = os.path.split(destdir)
      parent += '/'

      if opts.verbose:
        sys.stderr.write("create folder '%s' in '%s'"%(folder,parent))
      if opts.dryrun:
        if opts.verbose:
          sys.stderr.write("(Done)\n")
      else:
        try:
          pyacd.api.create_by_path(parent,folder,Type=pyacd.types.FOLDER)
          if opts.verbose:
            sys.stderr.write("-> ")
          if not opts.quiet:
            sys.stderr.write("Done\n")
        except pyacd.PyAmazonCloudDriveApiException,e:
          sys.stderr.write("Aborted. ('%s')\n"%str(e))
          continue

    for name in os.listdir(srcdir):
      if name[0]=='.':
        continue
      fullpath = os.path.join(srcdir,name)
      if os.path.isdir(fullpath):
        directories.append(fullpath)
      elif os.path.isfile(fullpath):
        # That's a file. Do something with it.
        filename = os.path.basename(fullpath)

        if not opts.quiet:
          sys.stderr.write("Uploading %s to %s ...\n"%(filename,destdir))

        if opts.dryrun:
          if not opts.quiet:
            sys.stderr.write("(Done)\n")
        else:
          f=open(fullpath,"rb")
          filedata = f.read()
          f.close()
        
          # create file
          if opts.verbose:
            sys.stderr.write("create ")
          fileobj = pyacd.api.create_by_path(destdir,filename)
          if opts.verbose:
            sys.stderr.write("-> ")

          # get upload_url
          if opts.verbose:
            sys.stderr.write("url ")
          upload_url = pyacd.api.get_upload_url_by_id(fileobj.object_id,len(filedata))
          if opts.verbose:
            sys.stderr.write("-> ")

          end_point=upload_url.http_request.end_point
          parameters=upload_url.http_request.parameters

          storage_key=upload_url.storage_key
          object_id=upload_url.object_id

          # upload file
          if opts.verbose:
            sys.stderr.write("send ")
          pyacd.api.upload(end_point,parameters,filename,filedata)
          if opts.verbose:
            sys.stderr.write("-> ")

          # completeing file
          if opts.verbose:
            sys.stderr.write("finish ")
          pyacd.api.complete_file_upload_by_id(object_id,storage_key)
          if opts.verbose:
            sys.stderr.write("-> ")

          if not opts.quiet:
            sys.stderr.write("Done\n")


if __name__=="__main__":
  main()
