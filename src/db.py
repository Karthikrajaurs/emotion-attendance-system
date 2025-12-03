# src/db.py
from peewee import *
import os
from config import DATABASE_PATH

os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
db = SqliteDatabase(DATABASE_PATH)

class BaseModel(Model):
    class Meta:
        database = db

class Person(BaseModel):
    usn_id = CharField(unique=True)
    name = CharField()
    class_section = CharField(null=True)
    domain = CharField(null=True)
    authorizer_email = CharField()
    photo_path = CharField()

class Attendance(BaseModel):
    person = ForeignKeyField(Person)
    date = DateField()
    timestamp = DateTimeField()

class EmotionRecord(BaseModel):
    person = ForeignKeyField(Person)
    date = DateField()
    dominant_emotion = CharField()
    confidence = FloatField()
    timestamp = DateTimeField()

class AlertLog(BaseModel):
    person = ForeignKeyField(Person)
    trigger_date = DateField()
    reason = TextField()
    sent_at = DateTimeField()

db.connect()
db.create_tables([Person, Attendance, EmotionRecord, AlertLog], safe=True)