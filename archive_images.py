#!/usr/bin/env python
"""
Sorts image files by time - copies them into folders by year and month.

Written and put in the public domain by Friedrich C. Kischkel.
"""

import os
import re
import shutil
import sys
import time
import argparse

IMAGE_FILE = re.compile(r"""\.(jpe?g)|(png)|(tiff?)$""", re.IGNORECASE)
EXIF_TIME_FORMAT = "%Y:%m:%d %H:%M:%S"

def print_usage_info():
    """Prints the usage info."""
    print \
"""Usage: archive_images SOURCE_PATHS... DESTINATION_PATH
"""

def time_taken(path):
    """Get time a picture was taken or at least file c/mtime."""
    times = [
        time.localtime(os.path.getctime(path)),
        time.localtime(os.path.getmtime(path)),
        time.localtime()
    ]
    import exifread
    with open(path, 'rb') as imagefile:
        tags = exifread.process_file(imagefile, details=False)
        for tag in ['Image DateTime', 'EXIF DateTimeOriginal', 'EXIF DateTimeDigitized']:
            try:
                times.append(time.strptime(str(tags[tag]), EXIF_TIME_FORMAT))
            except KeyError, err:
                print "WARNING: tag %(tag)s could not be retrieved from %(file)s"\
                % {"tag": err, "file": path}
    times.sort()
    return times[0]

def archive_image(srcpath, filename, dstpath):
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
        shutil.copy(srcpath, dst)

def archive_all(dstpath, dirname, names):
    """Copy files by creation time into subfolders"""
    for filename in names:
        archive_image(dirname, filename, dstpath)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Copy images into year/month sub-folders by time they were taken.')
    parser.add_argument('SOURCE', nargs='+', help='source path(s)')
    parser.add_argument('DESTINATION', nargs=1, help='destination path')
    #parser.add_argument('-o', '--overwrite', action='store_true', default=False, help='overwrite destination (default: off)')
    #parser.add_argument('--exec', help='execute command with args SRC DST')
    ARGS = parser.parse_args()
    for source in ARGS.SOURCE:
        os.path.walk(source, archive_all, ARGS.DESTINATION[0])
