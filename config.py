from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
CARPETA_CARGA = BASE_DIR.joinpath("files/upload")
CARPETA_DESCARGA = BASE_DIR.joinpath("files/download")

DATABASE_URI = os.environ.get('DATABASE_URI')
BUCKET_NAME = os.environ.get('BUCKET_NAME')
SQS_URL = os.environ.get('SQS_URL')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

