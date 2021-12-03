import boto3
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

def aws_session():
    return boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

def s3_client():
    return aws_session().client('s3')

def sqs_client():
    return aws_session().client('sqs', region_name="us-east-1")