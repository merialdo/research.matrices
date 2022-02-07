from database import db
import datetime


class Model(db.Document):
    name = db.StringField(required=True, unique=True)
    language = db.StringField(required=True)
    description = db.StringField(required=True)
    weights = db.FileField()
    h_avg = db.IntField()
    created_at = db.DateTimeField(default=datetime.datetime.now())
    training_data = db.ReferenceField('Dataset')

    @staticmethod
    def from_fields(name, language, description, weights, h_avg, training_data):
        model = Model()
        model.name = name
        model.language = language
        model.description = description
        model.weights = weights
        model.h_avg = h_avg
        model.training_data = training_data


class Sample(db.EmbeddedDocument):
    x = db.FloatField()
    y = db.FloatField()
    width = db.FloatField()
    height = db.FloatField()
    text = db.StringField()

    @staticmethod
    def from_fields(x, y, width, height, text):
        sample = Sample()
        sample.x = x
        sample.y = y
        sample.width = width
        sample.height = height
        sample.text = text
        return sample


class Page(db.EmbeddedDocument):
    filename = db.StringField()
    image = db.FileField()
    samples = db.EmbeddedDocumentListField(Sample)
    is_confirmed = db.BooleanField()
    list_active_texts = db.ListField(db.StringField())
    index = db.IntField()

    @staticmethod
    def from_fields(filename, content, is_confirmed, list_active_texts, index):
        page = Page()
        page.filename = filename
        page.image.put(content.stream.read(), content_type='image/png')     # todo: what if the input image is not PNG?
        page.is_confirmed = is_confirmed
        page.list_active_texts = list_active_texts
        page.index = index
        return page


class Dataset(db.Document):
    name = db.StringField(required=True, unique=True)
    language = db.StringField(required=True)
    description = db.StringField()
    pages = db.EmbeddedDocumentListField(Page)

    @staticmethod
    def from_fields(name, language, description, pages=None):
        dataset = Dataset()

        dataset.name = name
        dataset.language = language
        dataset.description = description
        dataset.pages = pages if pages is not None else []
        dataset.created_at = db.DateTimeField(default=datetime.datetime.now())

        return dataset