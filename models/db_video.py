# coding: utf8

LANGUAGES = {"es": T("Spanish")  ,"en": T("English"), "it": T("Italian")}
LANGUAGE = "es"

CONTENTS = {"image": T("image"), "video": T("video"),
            "flash": T("flash"), "html": T("html"),
            "markmin": T("markmin")}

SERVICES = {"static":T("HTML5/local"), "youtube":T("Youtu.be"), "vimeo": T("Vimeo")}

db.define_table("option",
                Field("user_id", "reference auth_user",
                      default=auth.user_id,
                      label=T("User"),
                      writable=False),
                Field("language", label=T("Language"),
                      comment=T("Language used for subtitles and slides"),
                      requires=IS_IN_SET(LANGUAGES), default=LANGUAGE),
                Field("timeout", "integer", default=3,
                      label=T("Duration/time"),
                      comment=T("Default time between start/end for subtitles or slides")))

db.define_table("video",
                Field("title"),
                Field("service", requires=IS_IN_SET(SERVICES),
                      default="static",
                      comment=T("Choose how the content should be retrieved")),
                Field("code",
                      comment=T("Used with services like Youtube for identifying streams")),
                Field("abstract", "text"),
                Field("language", default="en",
                      requires=IS_IN_SET(LANGUAGES)),
                Field("thumbnail", "upload"),
                Field("user_id", "reference auth_user",
                      label=T("User"), default=auth.user_id),
                format="%(title)s")

db.define_table("source",
                Field("video_id", "reference video",
                      label=T("Video")),
                Field("path", comment=T("OS path for a server stream source")),
                Field("url", requires=IS_EMPTY_OR(IS_URL()),
                      comment=T("For retrieving the stream remotely from a third party service")),
                Field("format", comment=T("Format extension name (i.e.: mpeg)")),
                Field("itself", "upload", label=T("File"), comment=T("Stores a video locally")))
                
db.define_table("presentation",
                Field("video_id", "reference video",
                      label=T("Video")),
                Field("title"),
                Field("abstract", "text"),
                Field("language", requires=IS_IN_SET(LANGUAGES)),
                Field("user_id", "reference auth_user", label=T("User"),
                      default=auth.user_id),
                Field("auto", "boolean",
                      comment=T("Use this presentation by default"),
                      default=False),
                format="%(title)s")
                
db.define_table("slide",
                Field("presentation_id", "reference presentation",
                      label=T("Presentation")),
                Field("clones", "reference slide"),
                Field("content", requires=IS_IN_SET(CONTENTS),
                      default="image"),
                Field("url", requires=IS_EMPTY_OR(IS_URL()),
                      comment=T("For retrieving the content remotely from a third party service")),
                Field("itself", "upload", label=T("File"),
                      comment=T("Stores a slide locally")),
                Field("code", comment=T("Slide index or other type of label for identifying the slide")),
                Field("template", "boolean", default=False,
                      readable=False, writable=False,
                      comment=T("Used as content reference for common slides")),
                Field("starts", "time"),
                Field("ends", "time"),
                format="%(presentation_id)s - %(code)s")

db.define_table("subtitulation",
                Field("video_id", "reference video",
                      label=T("Video")),
                Field("language", default=LANGUAGE,
                      requires=IS_IN_SET(LANGUAGES)),
                Field("auto", "boolean", default=False,
                      comment=T("Wether this subtitles set should be used by default")),
                Field("user_id", "reference auth_user",
                      default=auth.user_id, label=T("User")))

db.define_table("subtitle",
                Field("body", "text"),
                Field("subtitulation_id", "reference subtitulation",
                      label=T("Subtitulation")),
                Field("starts", "time"),
                Field("ends", "time"),
                format="%(starts) - %(ends)s")


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

def virtualSlideURL(row):
    if "slide" in row:
        slide = row.slide
    else:
        slide = row
    if "template" in slide:
        if slide.template:
            if slide.itself:
                vurl = URL(f="download", args=["filename", slide.itself])
                return vurl
            else:
                return slide.url
        elif slide.clones:
            return slide.clones.vurl
    else:
        return None

# lambda row: row.unit_price*row.quantity
db.slide.vurl = Field.Virtual(virtualSlideURL)

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

def CLONES_SLIDE(presentation_id):
    "Pseudo validator for a presentation slide"
    query = db.slide.presentation_id == int(presentation_id)
    query &= db.slide.template == True
    myslides = db(query).select()
    choices = dict()
    for myslide in myslides:
        if not myslide.code:
            choices[myslide.id] = T("No code (%(id)s)") % dict(id=myslide.id)
        else:
            choices[myslide.id] = myslide.code
    return IS_IN_SET(choices)

def SUBTITLE(sub):
    option = OPTION(sub.starts, " - ", sub.ends, _value=sub.id)
    return option

def SLIDE(myslide):
    option = OPTION(myslide.starts, " - ", myslide.ends, _value=myslide.id)
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
