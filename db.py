from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config import DATABASE_URI

Base = declarative_base()
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()
