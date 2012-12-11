# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    db = DAL('sqlite://storage.sqlite')
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore')
    ## store sessions and tickets there
    session.connect(request, response, db = db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db, hmac_key=Auth.get_or_create_key())
crud, service, plugins = Crud(db), Service(), PluginManager()

## create all tables needed by auth if not custom tables
auth.define_tables()

## configure email
mail=auth.settings.mailer
mail.settings.server = 'logging' or 'smtp.gmail.com:587'
mail.settings.sender = 'you@gmail.com'
mail.settings.login = 'username:password'

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.rpx_account import use_janrain
use_janrain(auth,filename='private/janrain.key')

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

LANGUAGES = ["es" ,"en", "it"]
LANGUAGE = "es"

CONTENTS = {"image": T("image"), "video": T("video"),
            "flash": T("flash"), "html": T("html"),
            "markmin": T("markmin")}

db.define_table("option",
                Field("user_id", "reference auth_user", default=auth.user_id,
                      writable=False),
                Field("subtitle_language", requires=IS_IN_SET(LANGUAGES),
                      default=LANGUAGE),
                Field("subtitle_time", "integer", default=3))

db.define_table("video",
                Field("title"),
                Field("abstract", "text"),
                Field("language", default="en", requires=IS_IN_SET(LANGUAGES)),
                Field("thumbnail", "upload"),
                Field("user_id", "reference auth_user", default=auth.user_id))

db.define_table("source",
                Field("video_id", "reference video"),
                Field("path"),
                Field("url"),
                Field("format"),
                Field("itself", "upload"))
                
db.define_table("presentation",
                Field("video_id", "reference video"),
                Field("title"),
                Field("abstract", "text"),
                Field("language", requires=IS_IN_SET(LANGUAGES)),
                Field("user_id", "reference auth_user", default=auth.user_id),
                Field("auto", "boolean", default=False),
                format="%(title)s")
                
db.define_table("slide",
                Field("presentation_id", "reference presentation"),
                Field("content", requires=IS_IN_SET(CONTENTS), default="image"),
                Field("url"),
                Field("itself", "upload"),
                Field("code"),
                Field("presentation_id", "reference presentation"),
                Field("starts", "time"),
                Field("ends", "time"))

db.define_table("subtitulation",
                Field("video_id", "reference video"),
                Field("language", default=LANGUAGE, requires=IS_IN_SET(LANGUAGES)),
                Field("auto", "boolean", default=False),
                Field("user_id", "reference auth_user", default=auth.user_id))

db.define_table("subtitle",
                Field("body", "text"),
                Field("subtitulation_id", "reference subtitulation"),
                Field("starts", "time"),
                Field("ends", "time"))

def setup_videos():
    # read the list of videos from /app/static/videos
    # filenames = [os.path.split(video.path)[1] for video in db(db.video).select()]
    import os
    videopath = os.path.join(request.folder, "static", "videos")
    videos = os.listdir(videopath)
    videocount = 0
    # for each video insert the video in the video table
    created = dict()
    for video in db(db.video).select():
        created[video.title] = video.id
    for filename in videos:
        # we assume the file has a format extension of type ".ext"
        splitted = filename.split(".")
        if len(splitted) > 1:
            ext = splitted.pop(-1)
        else:
            ext = None
        name = ".".join(splitted)
        if not name in created.keys():
            created[name] = db.video.insert(title=name)
        if db((db.source.video_id==created[name]) & \
              (db.source.format==ext)).select().first() is None:
            db.source.insert(video_id=created[name],
                             url=str(URL(c="static", f="videos/%s" % filename)),
                             format=ext,
                             path=os.path.join(videopath, filename))
            videocount += 1
    return videocount


class SOURCE(DIV):
    def __init__(self, *args, **kwargs):
        self.tag = "source"
        return DIV.__init__(self, *args, **kwargs)


class VIDEO(DIV):
    def __init__(self, *args, **kwargs):
        self.tag = "video"
        # Set controls by default unless specified
        if not ("_controls" in kwargs):
            kwargs["_controls"] = "controls"
        return DIV.__init__(self, *args, **kwargs)


def SUBTITLE(sub):
    li = LI(LABEL(sub.starts, " - ", sub.ends,
                  _class="label", _id=sub.id),
            DIV(TEXTAREA(value=sub.body, _class="body"),
                FORM(DIV(LABEL(T("Starts")),
                         INPUT(value=sub.starts, _class="starts")),
                     DIV(LABEL(T("Ends")),
                         INPUT(value=sub.ends, _class="ends")),
                     INPUT(value=T("Apply"), _type="button",
                           _class="apply", _id=sub.id)),
                _class="subtitle", _style="display:none;",
                _id="subtitle-%s" % sub.id),
                _id=sub.id)
    return li


def seconds_to_time(seconds):
    import datetime
    fseconds = float(seconds)
    rounded = int(round(fseconds))
    hours = rounded / 3600
    rounded -= hours*3600
    minutes = rounded /60
    rounded -= minutes*60
    seconds = rounded
    try:
        microseconds = str(fseconds).split(".")[1][:3]
        microseconds = microseconds.ljust(3).replace(" ", "0")
        microseconds = int(microseconds)*1000
    except ValueError:
        msc = 0
    return datetime.time(hours, minutes, seconds, microseconds)

