from .db import db
import datetime
from flask_bcrypt import generate_password_hash, check_password_hash


class Model(db.Document):
    name = db.StringField(required=True, unique=True)
    language = db.StringField(required=True)
    description = db.StringField(required=True)
    weights = db.FileField()
    h_avg = db.IntField()
    created_at =  db.DateTimeField(default=datetime.datetime.now())
    training_data = db.ReferenceField('Dataset')
    added_by = db.ReferenceField('User')


class DatasetAnnotation(db.EmbeddedDocument):
    x = db.FloatField()
    y = db.FloatField()
    width = db.FloatField()
    height = db.FloatField()
    text = db.StringField()


class DatasetImage(db.EmbeddedDocument):
    filename = db.StringField()
    image = db.FileField()
    annotations = db.EmbeddedDocumentListField(DatasetAnnotation)
    is_confirmed = db.BooleanField()
    list_active_texts = db.ListField(db.StringField())
    index = db.IntField()


class Dataset(db.Document):
    name = db.StringField(required=True, unique=True)
    language = db.StringField(required=True)
    description = db.StringField()
    data = db.EmbeddedDocumentListField(DatasetImage)
    #annotations = db.EmbeddedDocumentListField(DatasetAnnotation)
    created_at =  db.DateTimeField(default=datetime.datetime.now())
    added_by = db.ReferenceField('User')


class User(db.Document):
    username = db.StringField(required=True, unique=True)
    email = db.EmailField(required=True, unique=True)
    password = db.StringField(required=True, min_length=6)
    created_at = db.DateTimeField(default=datetime.datetime.now())
    models = db.ListField(db.ReferenceField('Model', reverse_delete_rule=db.PULL))
    datasets = db.ListField(db.ReferenceField('Dataset', reverse_delete_rule=db.PULL))

    def hash_password(self):
        self.password = generate_password_hash(self.password).decode('utf8')

    def check_password(self,password):
        return check_password_hash(self.password, password)


User.register_delete_rule(Model, 'added_by', db.CASCADE)
User.register_delete_rule(Dataset, 'added_by', db.CASCADE)

