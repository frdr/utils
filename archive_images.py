#!/usr/bin/env python
"""
Sorts image files by time - copies them into folders by year and month.

Written by Friedrich C. Kischkel.
"""

import os
import re
import shutil
import time
import argparse

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

def archive_image(srcpath, filename, dstpath, overwrite=False):
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
        shutil.copy2(srcpath, dst)

def archive_all(srcpath, dstpath):
    """Copy files by creation time into sub-folders"""
    for current, _, files in os.walk(srcpath):
        for filename in files:
            try:
                archive_image(current, filename, dstpath)
            except IOError, err:
                print "ERROR: copying image: %(msg)s" % {'msg': str(err)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Copy images into year/month sub-folders by time they were taken.')
    parser.add_argument('SOURCE', nargs='+', help='source path(s)')
    parser.add_argument('DESTINATION', nargs=1, help='destination path')
    #parser.add_argument('-f', '--force', action='store_true', default=False, help='force overwriting of existing files (default: do not overwrite)')
    #parser.add_argument('--exec', help='execute command with args SRC DST')
    ARGS = parser.parse_args()
    for source in ARGS.SOURCE:
        archive_all(source, ARGS.DESTINATION[0])
