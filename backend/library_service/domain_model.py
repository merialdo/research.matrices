from .db import db
import datetime


class Model(db.Document):
    name = db.StringField(required=True, unique=True)
    language = db.StringField(required=True)
    description = db.StringField(required=True)
    weights = db.FileField()
    h_avg = db.IntField()
    created_at = db.DateTimeField(default=datetime.datetime.now())
    training_data = db.ReferenceField('Dataset')


class Sample(db.EmbeddedDocument):
    x = db.FloatField()
    y = db.FloatField()
    width = db.FloatField()
    height = db.FloatField()
    text = db.StringField()


class DatasetImage(db.EmbeddedDocument):
    filename = db.StringField()
    image = db.FileField()
    samples = db.EmbeddedDocumentListField(Sample)
    is_confirmed = db.BooleanField()
    list_active_texts = db.ListField(db.StringField())
    index = db.IntField()


class Dataset(db.Document):
    name = db.StringField(required=True, unique=True)
    language = db.StringField(required=True)
    description = db.StringField()
    data = db.EmbeddedDocumentListField(DatasetImage)
    created_at = db.DateTimeField(default=datetime.datetime.now())
