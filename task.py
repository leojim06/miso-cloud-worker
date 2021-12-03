import enum
import datetime
import db
from sqlalchemy import Column, String, Integer, DateTime, Enum

class Status(enum.Enum):
    UPLOADED = 1
    PROCESSED = 2

class AudioFormat(enum.Enum):
    MP3 = 1
    WAV = 2
    OGG = 3
    WMA = 4
    AAC = 5

class Task(db.Base):
    __tablename__ = 'task'
    id = Column(Integer(), primary_key=True)
    fileName = Column(String(512))
    newFormat = Column(Enum(AudioFormat))
    timeStamp = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(Enum(Status), default=Status.UPLOADED)

    def as_dict(self):
       return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}
    