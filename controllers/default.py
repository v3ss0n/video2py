# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html
    """
    response.flash = "Welcome to web2py!"
    response.files.append(URL(c='static',f="js/popcorn_complete.js"))
    video = "2012_11_16_10_49_42_00194_480p_60s"
    videos = [#"http://www.sistemasagiles.com.ar/soft/00194_480_html5.webm",
              URL(c='static',f="videos/%s%s" % (video, ext))
              for ext in ('_fast.mp4', '.webm', '.ogv')
              ]
    slides = [
        {'href': '',
         'src': URL(c='static',f='slides/flask-pycon_2012-%d.png' % i),
         'text': 'slide %d' % i,
         'start': i*3,
         'end': i*3+3,
         }  for i in range(15)]
    subtitles = [
        {'text': 'subtitle %d bla bla bla' % i,
         'start': i*3,
         'end': i*3+3,
         }  for i in range(15)]
    return dict(videos=videos, slides=slides, subtitles=subtitles )

def list():
    videos = db(db.video).select()
    return dict(videos=videos)

def edit():
    if request.args:
        video = db(db.video.id==request.args[0]).select().first()
    else:
        video = None
    form = SQLFORM(db.video, video)
    if form.accepts(request.vars, session):
        response.flash = "ok"
    elif form.errors:
        response.flash = "err!"
    return dict(form=form)

def show():
    response.files.append(URL(c='static',f="js/popcorn_complete.js"))

    debug = request.vars['debug'] and True or False

    video = db(db.video.id==request.args[0]).select().first()
    response.title = video.title

    sources = [URL(c='static',f="videos/%s%s" % (video.src, ext))
               for ext in ('_fast.mp4', '.webm', '.ogv')]

    footnotes = [{
         'text': video.summary.replace("\n"," ").replace("\r"," "),
         'start': 0,
         'end': 1,
         }]

    slides = []
    for slide in db(db.slide.video_id==video.id).select(orderby=db.slide.start):
        #TODO: calculate slide time looking at the next one
        start = (slide.start.second + slide.start.minute*60) if slide.start else -1
        end = (slide.end.second + slide.end.minute*60) if slide.end else -1
        slides.append({'href': '',
           'src': URL('download',args=slide.image),
           'text': 'slide %d' % slide.id if debug else '',
           'start': start,
           'end': end,
         })
        if slide.text:
            footnotes.append({
             'text': slide.text.replace("\n"," ").replace("\r"," "),
             'start': start,
             'end': end,
             })
    subtitles = []
    for subtitle in db(db.subtitle.video_id==video.id).select(orderby=db.subtitle.start):
        start = (subtitle.start.second + subtitle.start.minute*60) if subtitle.start else -1
        end = (subtitle.end.second + subtitle.end.minute*60) if subtitle.end else -1
        subtitles.append({'text': subtitle.text,
         'start': start,
         'end': end,
         })
    return dict(sources=sources, slides=slides, subtitles=subtitles, footnotes=footnotes)

def slides():
    "Simple CRUD for slides"
    # TODO 1: upload a PDF, convert it to jpg and move the images to static
    # ie: "convert -density 96 flask-pycon_2012.pdf flask-pycon_2012.png"
    # TODO 2: better sync of slides using pop.currentTime()
    video = db(db.video.id==request.args[0]).select().first()
    response.title = video.title
    db.slide.video_id.default = video.id
    if len(request.args)>1:
        slide = db(db.slide.id==request.args[1]).select().first()
    else:
        slide = None
    form = SQLFORM(db.slide, slide)
    if form.accepts(request.vars, session):
        response.flash = "ok"
    elif form.errors:
        response.flash = "err!"
    slides = db(db.slide.video_id==video.id).select()
    return dict(slides=slides, video=video, form=form)

def subtitles():
    "Simple CRUD for subtitles"
    # TODO 1: support uploading a SRT or similar
    # TODO 2: better sync of subtitles using pop.currentTime()
    video = db(db.video.id==request.args[0]).select().first()
    response.title = video.title
    db.subtitle.video_id.default = video.id
    if len(request.args)>1:
        subtitle = db(db.subtitle.id==request.args[1]).select().first()
    else:
        subtitle = None
    form = SQLFORM(db.subtitle, subtitle)
    if form.accepts(request.vars, session):
        response.flash = "ok"
    elif form.errors:
        response.flash = "err!"
    subtitles = db(db.subtitle.video_id==video.id).select()
    return dict(subtitles=subtitles, video=video, form=form)

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request,db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())
