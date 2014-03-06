import os
import random
import datetime
import subprocess

from PIL import Image
from pymediainfo import MediaInfo
from videodb.model import Video

MEDIAINFO = '/usr/bin/mediainfo'
MPLAYER = '/usr/bin/mplayer'

class ToolError(Exception):
    pass

class MplayerError(ToolError):
    pass

class MediaInfoError(ToolError):
    pass

def mplayer(path, vo=None, ao=None, frames=0, args=None):
    if vo is None:
        vo = 'null'
    if ao is None:
        ao = 'null'

    margs = [MPLAYER, '-vo', vo, '-ao', ao, '-frames', str(frames)]
    if args:
        margs.extend(args)
    margs.append(path)

    return subprocess.Popen(margs, stdout=subprocess.PIPE,
                            stderr=open(os.devnull, 'w'))

def generate_thumbnails(video, thumbs_dir=None):
    if thumbs_dir is None:
        thumbs_dir = 'data/thumbs'
    outdir = thumbs_dir + '/%s' % video.id
    vo = 'jpeg:outdir=%s' % outdir
    frame_count = video.length / 30

    p = mplayer(video.path, vo, None, frame_count, ['-ss', '30', '-sstep', '30'])
    if p.wait():
        raise MplayerError('Error generating the thumbnails')

    width  = 600
    height = int((600.0 / video.width) * video.height)

    for x in xrange(1, frame_count):
        path = os.path.join(outdir, '%08d.jpg' % x)
        im = Image.open(path)
        im.thumbnail((width, height),  Image.ANTIALIAS)
        im.save(path)

    video.thumbs = frame_count
    video.thumb = random.randint(1, frame_count)

def get_video_info(path):
    mi = MediaInfo.parse(path)
    return mi.to_data()

def get_video_track(info):
    for track in info['tracks']:
        if track['track_type'] == 'Video':
            return track
