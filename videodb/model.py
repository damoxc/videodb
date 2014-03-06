import random
import datetime

from mongoengine import *

class Video(Document):

    path    = StringField()
    name    = StringField()
    width   = IntField()
    height  = IntField()
    length  = IntField()
    size    = IntField()
    views   = IntField(default=0)
    tags    = ListField(StringField())
    date    = DateTimeField(default=datetime.datetime.now)
    thumb   = IntField(default=0)
    thumbs  = IntField()

    active  = BooleanField(default=False)
    pending = BooleanField(default=True)
    _random = FloatField(default=random.random)

    old_path = StringField()

    def __json__(self, request):
        return {
            'id':      str(self.id),
            'path':    self.path,
            'name':    self.name,
            'width':   self.width,
            'height':  self.height,
            'length':  self.length,
            'size':    self.size,
            'views':   self.views,
            'tags':    self.tags,
            'date':    self.date,
            'thumb':   self.thumb,
            'thumbs':  self.thumbs,
            'active':  self.active,
            'pending': self.pending
        }

connect('videodb')
