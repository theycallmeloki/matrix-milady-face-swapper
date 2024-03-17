import logging
import sqlite3
from sqlite3 import Error
from peewee import *

db = SqliteDatabase('mmr.db')
logger = logging.getLogger(__name__)

class BaseModel(Model):
    class Meta:
        database = db

class Prediction(BaseModel):
    id = AutoField()
    image_id = TextField()
    prediction = TextField()
    human_face_landmarks = TextField()
    anime_face_landmarks = TextField()
    feedback = TextField(null=True)

class DatabaseManager:
    def initialize_db(self):
        logger.info("Initializing database...")
        db.connect()
        db.create_tables([Prediction])

    def insert_prediction(self, prediction):
        logger.info(f"Inserting prediction for image_id: {prediction[0]}")
        return Prediction.create(image_id=prediction[0], prediction=prediction[1])

    def insert_feedback(self, feedback):
        logger.info(f"Inserting feedback for image_id: {feedback[1]}")
        query = Prediction.update(feedback=feedback[0]).where(Prediction.image_id == feedback[1])
        query.execute()

    def fetch_feedback(self):
        logger.info("Fetching feedback...")
        return Prediction.select().where(Prediction.feedback.is_null(False))
