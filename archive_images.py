#!/usr/bin/env python
"""
Sorts image files by time - copies them into folders by year and month.

Written by Friedrich C. Kischkel.

From the usage info:

usage: archive_images.py [-h] [-m] [-f] [-d D] [--exec FILTER]
                         SOURCE [SOURCE ...] DESTINATION

Copy images into year/month sub-folders by time they were taken. Useful to get
some chronological orientations when copying a bulk of images from a camera's
memory card to a local pictures folder.

positional arguments:
  SOURCE           source path(s)
  DESTINATION      destination path

optional arguments:
  -h, --help       show this help message and exit
  -m, --move       move file instead of copying it (default: copy)
  -f, --force      force overwriting of existing files (default: do not
                   overwrite)
  -d D, --depth D  descend this deep into SOURCE directories
  --exec FILTER    for each SRC, execute FILTER SRC DST
"""

import os
import re
import shutil
import time
import argparse
import subprocess

IMAGE_FILE = re.compile(r"""\.(jpe?g)|(png)|(tiff?)$""", re.IGNORECASE)
EXIF_TIME_FORMAT = "%Y:%m:%d %H:%M:%S"

def time_taken(path):
    """Get time a picture was taken or at least file c/mtime."""
    times = [
        time.localtime(os.path.getctime(path)),
        time.localtime(os.path.getmtime(path)),
        time.localtime() # now
    ]
    import exifread
    with open(path, 'rb') as imagefile:
        tags = exifread.process_file(imagefile, details=False)
        for tag in ['Image DateTime', 'EXIF DateTimeOriginal', 'EXIF DateTimeDigitized']:
            try:
                times.append(time.strptime(str(tags[tag]), EXIF_TIME_FORMAT))
            except KeyError, err:
                print \
"WARNING: tag %(tag)s could not be retrieved from %(file)s" % \
{"tag": err, "file": path}
    times.sort()
    return times[0]

def archive_image(srcpath, filename, dstpath, overwrite=False, file_function=shutil.copy2):
    """Copy image "filename" in "path" into a subfolder "dstpath"."""
    if re.search(IMAGE_FILE, filename):
        srcpath = os.path.join(srcpath, filename)
        ctime = time_taken(srcpath)
        dst = os.path.join(
            dstpath,
            time.strftime("%Y", ctime),
            time.strftime("%m", ctime))
        try:
            os.makedirs(dst)
        except OSError:
            pass
        if not overwrite and os.path.exists(os.path.join(dst, filename)):
            raise IOError('"%(path)s" already exists' % \
                {'path': os.path.join(dst, filename)})
        file_function(srcpath, dst)

def archive_all(srcpath, dstpath, overwrite=False, max_depth=None, file_function=shutil.copy2):
    """Copy files by creation time into sub-folders"""
    iteration = 0
    for current, _, files in os.walk(srcpath):
        for filename in files:
            try:
                archive_image(current, filename, dstpath, overwrite, file_function)
            except IOError, err:
                print "ERROR: copying image: %(msg)s" % {'msg': str(err)}
        iteration += 1
        if max_depth != None and iteration > max_depth:
            return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""\
Copy images into year/month sub-folders by time they were taken.

Useful to get some chronological orientations when copying a bulk of
images from a camera's memory card to a local pictures folder.""")
    parser.add_argument('SOURCE', nargs='+', help='source path(s)')
    parser.add_argument('DESTINATION', nargs=1, help='destination path')
    parser.add_argument('-m', '--move', action='store_true', default=False, help='move file instead of copying it (default: copy)')
    parser.add_argument('-f', '--force', action='store_true', default=False, help='force overwriting of existing files (default: do not overwrite)')
    parser.add_argument('-d', '--depth', metavar='D', type=int, help='descend this deep into SOURCE directories')
    parser.add_argument('--exec', metavar='FILTER', dest='execext', help='for each SRC, execute FILTER SRC DST')
    ARGS = parser.parse_args()
    fct = shutil.copy2
    if ARGS.move:
        fct = shutil.move
    if ARGS.execext:
        def make_call(cmd):
            """Create lambda for call to 'cmd src dst'."""
            return lambda src, dst: subprocess.check_call(cmd.split() + [src, dst])
        fct = make_call(ARGS.execext)
    for source in ARGS.SOURCE:
        archive_all(\
            source,\
            ARGS.DESTINATION[0],\
            overwrite=ARGS.force,\
            max_depth=ARGS.depth,\
            file_function=fct)
