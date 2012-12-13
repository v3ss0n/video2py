# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

if auth.is_logged_in() and (not session.options):
    USER_OPTIONS = db(db.option.user_id==auth.user_id).select().first()
    if USER_OPTIONS is not None:
        session.options = USER_OPTIONS.as_dict()
    else:
        session.options = {"subtitle_language": None, "subtitle_time": 3}

if request.function in ["show", "subtitles", "slides"]:
    response.files.append(URL(c='static', f="js/popcorn_complete.js"))
    response.files.append(URL(c='static', f="js/jquery.scrollTo.min.js"))


def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

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
    return dict(videos=videos, slides=slides, subtitles=subtitles)
    """
    videos = db(db.video).select()
    return dict(videos=videos)

@auth.requires_login()
def slides():
    slides = None
    video = db.video[request.args(1)]
    sources = db(db.source.video_id==request.args(1)).select()
    presentation = db((db.presentation.video_id==request.args(1))).select().first()
    if presentation:
        presentation_id = presentation.id
        slides = db(db.slide.presentation_id==presentation_id).select()
    else:
        presentation_id = db.presentation.insert(video_id=request.args(1), title=video.title)

    db.slide.presentation_id.writable = False
    db.slide.presentation_id.default = presentation_id
    form = crud.create(db.slide)
    return dict(video=video, sources=sources, slides=slides, form=form)

@auth.requires_login()
def subtitles():
    video = db.video[request.args(1)]
    sources = db(db.source.video_id==request.args(1)).select()

    # Custom form for editing subtitles client-side
    ioform = crud.create(db.subtitle)
    if ioform.process(formname="ioform"):
        pass

    sq = db.subtitulation.user_id == auth.user_id
    sq &= db.subtitulation.video_id == request.args(1)
    sq &= db.subtitulation.language == session.options["subtitle_language"]
    subtitulation = db(sq).select().first()
    mylanguage = session.options["subtitle_language"]

    if subtitulation is None:
        subtitulation_id = db.subtitulation.insert(user_id=auth.user_id,
                                                   video_id=request.args(1),
                                                   language=mylanguage)

        # Fill subtitulation with previous subtitles
        other_subs = db((db.subtitulation.video_id==request.args(1)) & \
                        (db.subtitulation.language==mylanguage) & \
                        (db.subtitulation.id!=subtitulation_id)).select()
        sub_qties = dict()

        for osub in other_subs:
            subcount = db(db.subtitle.subtitulation_id==osub.id).count()
            sub_qties[subcount] = osub.id

        if len(sub_qties) > 0:
            other_subs_id = sub_qties[max(sub_qties)]
            other_subtitles = db(db.subtitle.subtitulation_id==other_subs_id).select()
            for other_subtitle in other_subtitles:
                osad = other_subtitle.as_dict()
                del(osad["id"])
                del(osad["subtitulation_id"])
                osad["subtitulation_id"] = subtitulation_id
                db.subtitle.insert(**osad)
        else:
            # This is the first subtitulation for this language
            # set as default
            db.subtitulation[subtitulation_id].update_record(auto=True)
    else:
        subtitulation_id = subtitulation.id

    subs_set = db(db.subtitle.subtitulation_id==subtitulation_id)
    subtitles = subs_set.select()

    return dict(video=video, sources=sources, subtitles=subtitles,
                subtitulation=subtitulation_id, ioform=ioform)

def show():
    subtitles = None
    video = db.video[request.args(1)]
    sources = db(db.source.video_id==request.args(1)).select()
    subtitulation = db((db.subtitulation.video_id==request.args(1))&(db.subtitulation.language==session.options["subtitle_language"])).select().first()
    if subtitulation:
        subtitles = db(db.subtitle.subtitulation_id==subtitulation.id).select()
    return dict(video=video, sources=sources, subtitles=subtitles)

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


@auth.requires_login()
def setup():
    messages = UL()
    managers = db(db.auth_group.role=="manager").select().first()
    if managers is None:
        managers_id = db.auth_group.insert(role="manager")
        manager_id = db.auth_membership.insert(user_id=auth.user_id, group_id=managers_id)
        messages.append(LI("You've been added to the managers group"))
    if auth.has_membership(role="manager"):
        videos_form = SQLFORM.factory()
        videos_form.element("[type=submit]").attributes["_value"] = T("Update videos")
        if videos_form.process(formname="videos_form").accepted:
            messages.append(LI(T("Added %s videos") % setup_videos()))
    else:
        videos_form = None
    options = db(db.option.user_id==auth.user_id).select().first()
    if options is None:
        options_id = db.option.insert(user_id=auth.user_id)
    else:
        options_id = options.id
    user_form = SQLFORM(db.option, options_id)
    if user_form.process(formname="user_form").accepted:
        for k, v in user_form.vars.iteritems():
            session.options[k] = v        
        messages.append(LI(T("Done!")))
    return dict(messages=messages, videos_form=videos_form,
                user_form=user_form)

@auth.requires_login()
def subtitle():
    import simplejson
    if request.args(1) == "create":
        starts = seconds_to_time(request.vars.starts)
        ends = seconds_to_time(request.vars.ends)
        subtitle_id = db.subtitle.insert(subtitulation_id=request.vars.subtitulation_id,
                                         starts=starts,
                                         ends=ends)
        subtitle = db.subtitle[subtitle_id]
        option = SUBTITLE(subtitle)
        subtitle=subtitle.as_dict()
        subtitle["starts"] = str(subtitle["starts"])
        subtitle["ends"] = str(subtitle["ends"])
        subtitle["body"] = ""
        result = simplejson.dumps(dict(option=option.xml(), subtitle=subtitle))
        return result

    elif request.args(1) == "update":
        def update_record(sub):
            del(sub["startEvent"])
            del(sub["endEvent"])
            db.subtitle[sub["id"]].update_record(**sub)

        payload = simplejson.loads(request.vars.data)
        if isinstance(payload, dict):
            update_record(payload)
        elif isinstance(payload, list):
            for item in payload:
                update_record(item)
        else:
            raise HTTP(500, "Unexpected data format")
        return simplejson.dumps("Done!")
    elif request.args(1) == "delete":
        result = db.subtitle[request.vars.id].delete_record()
        return simplejson.dumps("ok")
    else:
        raise HTTP(501, "Not implemented")


