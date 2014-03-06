import os
import re
import random
import shutil
import urlparse

from pyramid.httpexceptions import HTTPFound
from pyramid.response import FileResponse, Response
from pyramid.view import view_config

from bson.son import SON
from bson.objectid import ObjectId
from videodb.model import Video

def get_page(request):
    if 'page' in request.GET:
        try:
            return int(request.GET.get('page', 1))
        except:
            return 1
    else:
        return 1

@view_config(route_name='admin', renderer='/admin.jade')
@view_config(route_name='admin-tags', renderer='/admin.jade')
def admin_view(request):
    return {
        'videos': Video.objects(active=True, pending=False).order_by('-size')
    }

@view_config(route_name='home', renderer='/home.jade')
def home_view(request):
    return {
        'recent': Video.objects(active=True, pending=False).order_by('-date').limit(8)
    }

@view_config(route_name='random')
def random_view(request):
    r = random.random()
    try:
        views = int(request.GET.get('views', '1'))
    except:
        views = 1

    if views:
        video = Video.objects(_random__gte=r, views=0).first()
    else:
        video = Video.objects(_random__gte=r).first()
    return HTTPFound(location='/player/%s' % video.id)

@view_config(route_name='delete')
def delete_view(request):
    video = Video.objects(id=ObjectId(request.matchdict.get('video'))).first()

    vpath = os.path.join(request.videos_dir, str(video.id) + '.mp4')
    if os.path.isfile(vpath):
        os.remove(vpath)

    tpath = os.path.join(request.thumbs_dir, str(video.id))
    if os.path.isdir(tpath):
        shutil.rmtree(tpath)

    video.delete()

    return HTTPFound(location=request.GET.get('return_url', '/'))

@view_config(route_name='edit', renderer='/video/edit.jade')
def edit_view(request):
    video = Video.objects(id=ObjectId(request.matchdict.get('video'))).first()
    col = Video._get_collection()
    results = col.aggregate([
        {'$unwind': '$tags'},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": SON([("count", -1), ("_id", -1)])}
    ])
    tags = [r['_id'] for r in results['result']]
    q = Video.objects(active=True, pending=True).order_by('+date')

    try:
        next_video = q.next()
    except StopIteration:
        next_video = None
    else:
        if next_video == video:
            try:
                next_video = q.next()
            except StopIteration:
                next_video = None

    if request.POST:
        video.name = request.POST.get('name')
        video.pending = False
        video.save()

        if request.POST.get('mode') == 'pending':
            if not next_video:
                return HTTPFound(location='/videos')
            else:
                return HTTPFound(location='/edit/%s?mode=pending' % next_video.id)
        else:
            return HTTPFound(location='/player/%s' % video.id)

    mode  = request.GET.get('mode')
    if mode is None:
        if urlparse.urlparse('http://earth:6543/pending').path == '/pending':
            mode = 'pending'
        else:
            mode = 'editing'

    for tag in video.tags:
        tags.remove(tag)

    if next_video:
        next_url = '/edit/%s?mode=pending' % next_video.id
    else:
        next_url = None

    return {'video': video, 'tags': tags, 'mode': mode, 'next': next_url}

@view_config(route_name='pending', renderer='/pending.jade')
def pending_view(request):
    videos = Video.objects(active=True, pending=True).order_by('+date')
    return {'videos': videos}

@view_config(route_name='player', renderer='/video/player.jade')
def player_view(request):
    video = Video.objects(id=ObjectId(request.matchdict.get('video'))).first()

    if not video.size:
        video.size = os.stat(video.path).st_size
        video.save()

    return {
        'video': video,
        'width': 640,
        'height': 380
    }

@view_config(route_name='tags-overview', renderer='/tags-overview.jade')
def tags_overview_view(request):
    col = Video._get_collection()
    results = col.aggregate([
        {'$unwind': '$tags'},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": SON([("count", -1), ("_id", -1)])}
    ])
    return {
        'tags': results['result']
    }

@view_config(route_name='tags-json', renderer='json')
def tags_search_view(request):
    query = request.GET.get('q')
    col = Video._get_collection()
    pipeline = [
        {'$unwind': '$tags'},
        {'$group': {'_id': '$tags', 'count': {'$sum': 1}}},
    ]

    if query:
        pipeline.append({'$match': {'_id': {'$regex': '.*' + re.escape(query) + '.*'}}})

    pipeline.append({'$sort': SON([('count', -1), ('_id', -1)])})
    results = col.aggregate(pipeline)

    return {
        'tags': [t['_id'] for t in results['result']]
    }

@view_config(route_name='tags', renderer='json', xhr=True)
@view_config(route_name='tags', renderer='/tags.jade')
def tags_view(request):
    _tags = request.matchdict.get('tags')
    tags  = [t for t in _tags if t[0] != '!']
    ntags = [t[1:] for t in _tags if t[0] == '!']

    print tags
    print ntags

    page  = get_page(request)
    pages = (Video.objects(active=True, pending=False, tags__all=tags, tags__not_all=ntags).count() / 20) + 1
    order = request.GET.get('order', '-date')

    start = (page - 1) * 20
    videos = Video.objects(active=True, pending=False, tags__all=tags, tags__not__all=ntags).order_by(order)[start:start + 20]
    return {
        'tags': tags,
        'page': page,
        'pages': pages,
        'videos': list(videos)
    }

@view_config(route_name='videos', renderer='/videos.jade')
@view_config(route_name='videos-json', renderer='json')
@view_config(route_name='videos', renderer='json', xhr=True)
def videos_view(request):
    page  = get_page(request)
    pages = (Video.objects(active=True, pending=False).count() / 20) + 1

    start = (page - 1) * 20
    videos = Video.objects(active=True, pending=False).order_by('-date')[start:start + 20]

    return {
        'page': page,
        'pages': pages,
        'videos': list(videos)
    }

@view_config(route_name='video-add-view')
def video_add_view(request):
    video = Video.objects(id=ObjectId(request.matchdict.get('video'))).first()
    video.views += 1
    video.save()

    if request.is_xhr:
        return Response()

    return HTTPFound(location=request.referer)

# Tag Management
@view_config(route_name='video-add-tag')
def video_add_tag_view(request):
    video = Video.objects(id=ObjectId(request.matchdict.get('video'))).first()
    tag = request.matchdict.get('tag')
    if tag not in video.tags:
        video.tags.append(tag)
    video.save()

    if request.is_xhr:
        return Response()

    return HTTPFound(location=request.referer)

@view_config(route_name='video-remove-tag')
def video_remove_tag_view(request):
    video = Video.objects(id=ObjectId(request.matchdict.get('video'))).first()
    video.tags.remove(request.matchdict.get('tag'))
    video.save()

    if request.is_xhr:
        return Response()

    return HTTPFound(location=request.referer)
