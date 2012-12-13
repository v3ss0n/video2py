# coding: utf8

LANGUAGES = {"es": T("Spanish")  ,"en": T("English"), "it": T("Italian")}
LANGUAGE = "es"

CONTENTS = {"image": T("image"), "video": T("video"),
            "flash": T("flash"), "html": T("html"),
            "markmin": T("markmin")}

SERVICES = {"static":T("HTML5/local"), "youtube":T("Youtu.be"), "vimeo": T("Vimeo")}

db.define_table("option",
                Field("user_id", "reference auth_user", default=auth.user_id,
                      writable=False),
                Field("subtitle_language", requires=IS_IN_SET(LANGUAGES),
                      default=LANGUAGE),
                Field("subtitle_time", "integer", default=3))

db.define_table("video",
                Field("title"),
                Field("service", requires=IS_IN_SET(SERVICES), default="static"),
                Field("code", comment=T("Used with services like Youtube")),
                Field("abstract", "text"),
                Field("language", default="en", requires=IS_IN_SET(LANGUAGES)),
                Field("thumbnail", "upload"),
                Field("user_id", "reference auth_user", default=auth.user_id))

db.define_table("source",
                Field("video_id", "reference video", requires=IS_IN_DB(db, db.video, "%(title)s")),
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
                             service="static",
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
    option = OPTION(sub.starts, " - ", sub.ends, _value=sub.id)
    return option


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

