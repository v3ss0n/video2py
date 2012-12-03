# coding: utf8

LANGUAGES = {'es': 'español', 'en': 'english'}

db.define_table('video',
    Field("title", requires=IS_NOT_EMPTY()),
    Field("src", "string"),
    Field("summary", "text"),
    Field("speakers", "string"),    
    Field("language", "string", default='en', 
          requires=IS_IN_SET(LANGUAGES)),
    Field("recorded", "datetime"),
    Field("thumbnail", "upload"),
    format="%(title)s",
    )

db.define_table("slide",
    Field("video_id", db.video),
    Field("title", requires=IS_NOT_EMPTY()),
    Field("image", "upload"),
    Field("text", "text", comment="footnotes"),
    Field('start', 'time', comment="(HH:MM:SS)"),
    Field('end', 'time', comment="(HH:MM:SS)"),
    )

# TODO: footnote table

db.define_table("subtitle",
    Field("video_id", db.video),
    Field("text", "text", requires=IS_NOT_EMPTY()),
    Field('start', 'time', comment="(HH:MM:SS)"),
    Field('end', 'time', comment="(HH:MM:SS)"),
    )
