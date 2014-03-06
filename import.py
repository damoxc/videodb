#!/usr/bin/python2

import os
import re
import sys
import time
import pipes
import shutil
import argparse
import datetime
import traceback
import subprocess

from pyramid.paster import bootstrap

from videodb import fduration
from videodb.lib import get_video_info, get_video_track
from videodb.lib import generate_thumbnails
from videodb.model import Video

FFMPEG_RE = re.compile(r"""
    frame=\s*([0-9.]+)\s*
    fps=\s*([0-9.]+)\s*
    q=\s*([0-9.]+)\s*(L|)
    size=\s*(\d+[a-zA-Z]+)\s*
    time=\s*(\d{2}:\d{2}:\d{2}.\d{2})\s*
    bitrate=\s*((\d+.\d+)kbits/s|N/A)
""", re.VERBOSE)

def by_id(id_):
    return Video.objects(id=id_).first()

# ffmpeg -i input.avi -c:v libx264 -s HxW -crf 19 -preset slow -c:a libfaac -b:a 192k -ac 2 out.mp4
def encode_video(path, callback=None, size=None):
    print
    output_dir = os.path.dirname(path)
    print 'Output Dir:', output_dir
    filename, ext = os.path.splitext(os.path.basename(path))
    print 'Filename:', filename
    output = os.path.join(output_dir, '.' + filename + '.mp4')
    print 'Output:', output
    print
    args = ['/usr/bin/ffmpeg', '-i', path, '-strict', '-2', '-c:v', 'libx264']
    if size:
        args += ['-s', '%dx%d' % size]
    args += ['-crf', '19', '-preset', 'slow', '-c:a', 'aac']
    args += ['-b:a', '192k', '-ac', '2', output]

    print args

    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        start = time.time()
        buf = ''
        decoding = False
        while p.poll() is None:
            buf += p.stderr.read(16)
            if '\n' in buf:
                buf = buf[buf.rindex('\n') + 1:]

            if decoding:
                if '\r' in buf:
                    line = buf[0:buf.index('\r')]
                    buf  = buf[buf.index('\r') + 1:]

                    m = FFMPEG_RE.match(line)
                    if not m:
                        continue

                    frame   = int(m.group(1))
                    fps     = float(m.group(2))
                    q       = float(m.group(3))
                    size    = m.group(4)
                    vtime   = m.group(5)
                    bitrate = m.group(6)
                    dur     = time.time() - start

                    if callback:
                        callback(frame, fps, q, size, vtime, bitrate, dur)
            else:
                if not decoding and buf.startswith('frame'):
                    decoding = True
                else:
                    continue

    finally:
        if p.returncode is None:
            p.terminate()
            for i in xrange(0, 10):
                if p.poll() is not None:
                    break
                if i == 9:
                    p.kill()
                time.sleep(1)
        elif p.returncode > 0:
            raise Exception('stdout=%s; stderr=%s' % (p.stdout.read(), p.stderr.read()))

    return output

def import_video(path, config, skip_encoding=False):
    print 'Importing %s' % path
    videos_dir = config['videos_dir']
    thumbs_dir = config['thumbs_dir']

    print 'Checking video info...'
    info = get_video_info(path)
    if not info['tracks']:
        print 'Unable to detect any tracks'
        return

    general = info['tracks'].pop(0)
    needs_encoding = general['format'] != 'MPEG-4'
    vt = get_video_track(info)

    width = vt['width']
    height = vt['height']
    if width > 852:
        needs_encoding = True
        resize = True

        ratio = float(width) / height

        width = 852
        height = width / ratio
        if height % 2:
            height += 1
    else:
        resize = False

    if needs_encoding and skip_encoding:
        return

    if needs_encoding:
        frames = float(vt['frame_count']) if 'frame_count' in vt else None
        length = 0
        avg_fpses = []

        def progress(frame, fps, q, size, time, bitrate, duration):
            if frames:
                percent = '%.2f%%' % (frame / frames * 100)
            else:
                percent = -1

            duration = fduration(duration)

            if fps > 0 and frames:
                avg_fpses.append(fps)
                if len(avg_fpses) > 10:
                    avg_fpses.pop(0)
                avg_fps = sum(avg_fpses) / len(avg_fpses)
                remaining = fduration((frames - frame) / avg_fps)
            else:
                remaining = '00:00'

            sys.stdout.write('\b' * 26)
            sys.stdout.write('%8s %8s %8s' % (percent, duration, remaining))
            sys.stdout.flush()

        sys.stdout.write('Encoding video to mp4...' + ' ' * 26)
        sys.stdout.flush()

        old_path = path
        if resize:
            path = encode_video(path, progress, (width, height))
        else:
            path = encode_video(path, progress)
        sys.stdout.write('\n')
        os.remove(old_path)

    video = Video(old_path=path)
    video.name   = general['file_name']
    video.width  = vt['width']
    video.height = vt['height']
    video.length = vt['duration'] / 1000
    video.size   = general['file_size']
    video.save()

    video.path = os.path.join(videos_dir, str(video.id) + '.mp4')
    print 'Moving video to library...'
    shutil.move(path, video.path)
    print 'Generating thumbnails...'
    generate_thumbnails(video, thumbs_dir)
    video.active = True
    video.save()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', nargs='+')
    parser.add_argument('-s', '--skip-encoding', action='store_true', default=False)
    args = parser.parse_args()

    env = bootstrap('development.ini')
    config = env['registry'].settings

    for path in args.path:
        if '.data' in path:
            continue

        try:
            import_video(path, config, args.skip_encoding)
        except:
            print 'Error importing %r' % path
            traceback.print_exc()
            continue

if __name__ == '__main__':
    main()
