import time
import pyjade
import datetime

from bson.objectid import ObjectId

from pyramid.config import Configurator
from pyramid.events import BeforeRender
from pyramid.events import NewRequest
from pyramid.renderers import JSON

from videodb.helpers import *

@pyjade.register_filter('css')
def css(text, ast):
    return '<style>\n' + text + '\n</style>'

json_renderer = JSON()

def datetime_adapter(obj, request):
    return obj.isoformat()
json_renderer.add_adapter(datetime.datetime, datetime_adapter)

def objectid_adapter(obj, request):
    return str(obj)
json_renderer.add_adapter(ObjectId, objectid_adapter)

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('pyjade.ext.pyramid')

    config.add_renderer('json', json_renderer)

    config.add_subscriber(add_tmpl_funcs, BeforeRender)
    config.add_subscriber(new_request, NewRequest)

    config.add_route('home',             '/')
    config.add_route('admin',            '/admin')
    config.add_route('admin-tags',       '/admin/{tag}')
    config.add_route('categories',       '/categories')
    config.add_route('delete',           '/delete/{video}')
    config.add_route('edit',             '/edit/{video}')
    config.add_route('pending',          '/pending')
    config.add_route('player',           '/player/{video}')
    config.add_route('random',           '/random')
    config.add_route('tags-overview',    '/tags')
    config.add_route('tags',             '/tags/*tags')
    config.add_route('tags-json',        '/tags.json')
    config.add_route('video-add-tag',    '/video/{video}/add-tag/{tag}')
    config.add_route('video-remove-tag', '/video/{video}/remove-tag/{tag}')
    config.add_route('video-add-view',   '/video/{video}/add-view')
    config.add_route('videos',           '/videos')
    config.add_route('videos-json',      '/videos.json')

    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_static_view('thumbs', settings['thumbs_dir'], cache_max_age=3600)
    config.add_static_view('videos', settings['videos_dir'], cache_max_age=3600)

    config.scan()
    return config.make_wsgi_app()

def add_tmpl_funcs(event):
    event['fduration'] = fduration
    event['fsize'] = fsize
    event['ftags'] = ftags
    event['time'] = time.time()

def new_request(event):
    event.request.thumbs_dir = event.request.registry.settings['thumbs_dir']
    event.request.videos_dir = event.request.registry.settings['videos_dir']
