import os
import random
import datetime

from videodb.lib import get_video_info, generate_thumbnails
from videodb.model import Video

def update_info(video):
    info = get_video_info(video.path)
    video.length = int(info['ID_LENGTH'])
    video.save()

video = Video.objects().first()
#generate_thumbnails(video)
update_info(video)
