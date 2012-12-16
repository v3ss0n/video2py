# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

default_options = {"language": LANGUAGE, "timeout": 3}

def authorize(table, record_id):
    myrecord = db[table][record_id]
    if not ((myrecord.user_id != auth.user_id) or (auth.has_membership(role="manager"))):
        raise HTTP(403, T("The requeste action could not be performed. You must own the record or be in the managers list"), lazy=False)

if auth.is_logged_in():
    if not session.options:
        user_options = db(db.option.user_id==auth.user_id).select().first()
        if not user_options:
            db.option.insert(user_id=auth.user_id,
                             language=default_options["language"],
                             timeout=default_options["timeout"])
            session.options = default_options
        else:
            session.options = user_options.as_dict()
elif (not session.options):
    session.options = default_options
    
if request.function in ["show", "subtitles", "slides"]:
    response.files.append(URL(c='static', f="js/popcorn_complete.js"))
    response.files.append(URL(c='static', f="js/jquery.scrollTo.min.js"))
    response.files.append(URL(c='static', f="css/video.css"))


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
    mylanguage = session.options["language"]
    if not mylanguage: response.flash = T("No language selected! Please visit the Setup page")
    video = db.video[request.args(1)]
    sources = db(db.source.video_id==request.args(1)).select()

    sq = db.presentation.user_id == auth.user_id
    sq &= db.presentation.video_id == request.args(1)
    sq &= db.presentation.language == mylanguage
    presentation = db(sq).select().first()

    if presentation is None:
        presentation_id = db.presentation.insert(user_id=auth.user_id,
                                                 video_id=request.args(1),
                                                 language=mylanguage,
                                                 title=video.title)

        # Fill presentation with previous slides
        other_slides = db((db.presentation.video_id==request.args(1)) & \
                        (db.presentation.language==mylanguage) & \
                        (db.presentation.id!=presentation_id)).select()
        slides_qties = dict()

        for oslide in other_slides:
            subcount = db(db.slide.presentation_id==oslide.id).count()
            slides_qties[subcount] = oslide.id

        if len(slides_qties) > 0:
            other_slides_id = slides_qties[max(slides_qties)]
            other_slides = db(db.slide.presentation_id==other_slides_id).select()
            for other_slide in other_slides:
                oslide = other_slide.as_dict()
                del(oslide["id"])
                del(oslide["presentation_id"])
                del(oslide["vurl"])
                oslide["presentation_id"] = presentation_id
                db.slide.insert(**oslide)
        else:
            # This is the first presentation for this language
            # set as default
            db.presentation[presentation_id].update_record(auto=True)
    else:
        presentation_id = presentation.id

    slides_set = db((db.slide.presentation_id==presentation_id)&(db.slide.template==False))
    slides = slides_set.select()
    templates = db((db.slide.presentation_id==presentation_id)&(db.slide.template==True)).select()

    # Custom form for editing slides client-side
    db.slide.clones.requires = CLONES_SLIDE(presentation_id)    
    ioform = crud.create(db.slide)
    if ioform.process(formname="ioform"):
        pass

    return dict(video=video, sources=sources, slides=slides,
                presentation=presentation_id, ioform=ioform,
                templates=templates)


@auth.requires_login()
def subtitles():
    mylanguage = session.options["language"]
    if not mylanguage: response.flash = T("No language selected! Please visit the Setup page")    

    video = db.video[request.args(1)]
    sources = db(db.source.video_id==request.args(1)).select()

    # Custom form for editing subtitles client-side
    ioform = crud.create(db.subtitle)
    if ioform.process(formname="ioform"):
        pass

    sq = db.subtitulation.user_id == auth.user_id
    sq &= db.subtitulation.video_id == request.args(1)
    sq &= db.subtitulation.language == mylanguage
    subtitulation = db(sq).select().first()

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
    mypresentation = request.args(3)
    subtitles = slides = None
    language = session.options["language"]
    video = db.video[request.args(1)]
    sources = db(db.source.video_id==request.args(1)).select()
    subtitulation = db((db.subtitulation.video_id==request.args(1))&(db.subtitulation.language==session.options["language"])).select().first()
    if subtitulation:
        subtitles = db(db.subtitle.subtitulation_id==subtitulation.id).select()
    presentations = db(db.presentation.video_id==video.id).select()
    mypresentations = dict()
    for presentation in presentations:
        p_user = db.auth_user[presentation.user_id]
        mypresentations[presentation.id] = T("(%(language)s): %(slides)s slides, by %(user)s") % dict(language=presentation.language, slides=db((db.slide.presentation_id==presentation.id)&(db.slide.template==False)).count(), user=str(p_user.first_name) + " " + str(p_user.last_name))
    if mypresentation:
        default_p = mypresentation
    else:
        try:
            default_p = presentations.first().id
        except AttributeError:
            default_p = None
    form = SQLFORM.factory(Field("presentation", requires=IS_IN_SET(mypresentations), default=default_p))
    form.custom.submit["_value"] = T("Change")
    if form.process().accepted:
        redirect(URL(f="show", args=["video", video.id, "presentation", form.vars.presentation]))
    if mypresentation:
        presentation = db.presentation[mypresentation]
    else:
        presentation = presentations.first()
    if presentation:
        slides = db((db.slide.presentation_id==presentation.id)&(db.slide.template==False)).select()
    return dict(video=video, sources=sources, subtitles=subtitles, slides=slides, form=form,
                presentation=presentation)

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
    from gluon.contrib import simplejson
    T.lazy = False
    if request.args(1) in ["delete", "update"]:
        subtitulation = db.subtitulation[request.vars.subtitulation_id]
        authorize("subtitulation", subtitulation.id)
        
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
            authorize("subtitle", sub["id"])
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
        authorize("subtitle", request.vars.id)
        result = db.subtitle[request.vars.id].delete_record()
        return simplejson.dumps("ok")
    else:
        raise HTTP(501, "Not implemented")

@auth.requires_login()
def slide():
    if request.extension == "json":
        from gluon.contrib import simplejson
        T.lazy = False

        if request.args(1) == "create":
            starts = seconds_to_time(request.vars.starts)
            ends = seconds_to_time(request.vars.ends)
            if request.vars.clones:
                clones = request.vars.clones
            else:
                clones = None
            slide_id = db.slide.insert(presentation_id=request.vars.presentation_id,
                                       starts=starts,
                                       ends=ends,
                                       clones=clones)
            slide = db.slide[slide_id]
            option = SLIDE(slide)
            slide=slide.as_dict()
            slide["starts"] = str(slide["starts"])
            slide["ends"] = str(slide["ends"])
            if not clones:
                slide["clones"] = ""
            result = simplejson.dumps(dict(option=option.xml(), slide=slide))
            return result
    
        elif request.args(1) == "update":
            def update_record(myslide):
                del(myslide["startEvent"])
                del(myslide["endEvent"])
                authorize("slide", myslide["id"])                
                db.slide[myslide["id"]].update_record(**myslide)
    
            payload = simplejson.loads(request.vars.data)
            if isinstance(payload, dict):
                update_record(payload)
            elif isinstance(payload, list):
                for item in payload:
                    update_record(item)
            else:
                raise HTTP(500, "Unexpected data format")
            return simplejson.dumps(T("Done!"))
        elif request.args(1) == "delete":
            authorize("slide", request.vars.id)
            result = db.slide[request.vars.id].delete_record()
            return simplejson.dumps(T("Done!"))
        else:
            raise HTTP(501, T("Not implemented"))

    else:
        slides = None
        video = db.video[int(request.args(1))]
        authorize("video", video.id)
        sources = db(db.source.video_id==request.args(1)).select()
        presentation = db((db.presentation.video_id==request.args(1))).select().first()
        if presentation:
            presentation_id = presentation.id
        else:
            presentation_id = db.presentation.insert(video_id=request.args(1), title=video.title)

        db.slide.presentation_id.writable = False
        db.slide.template.default = True
        db.slide.presentation_id.default = presentation_id
        db.slide.starts.writable = db.slide.starts.readable = False
        db.slide.ends.writable = db.slide.ends.readable = False
        db.slide.clones.writable = db.slide.clones.readable = False
        form = crud.create(db.slide)
        slides = db((db.slide.presentation_id==presentation_id)&(db.slide.template==True)).select()
        return dict(video=video, sources=sources, slides=slides, form=form)

@auth.requires_login()
def video():
    action = request.args(0)
    video_id = request.args(1)
    db.video.user_id.writable = False
    if action == "update":
        video = db.video[video_id]
        authorize("video", video.id)
        form = crud.update(db.video, video_id)
    else:
        form = crud.create(db.video)
    return dict(form=form, video_id=video_id)

@auth.requires_login()
def sources():
    video = db.video[request.args(1)]
    authorize("video", video.id)
    action = request.args(3)
    source_id = request.args(5)
    if (action == "update") and source_id:
        form = crud.update(db.source, source_id)
    else:
        db.source.video_id.default = video.id
        form = crud.create(db.source)
    db.source.id.represent = lambda field, row: A(T("Edit"),
                                                _href=URL(f="sources", \
args=["video", video.id,"action", "update", "source", field]))
    sources = db(db.source.video_id==video.id).select()
    return dict(form=form, sources=sources, video=video, action=action)
