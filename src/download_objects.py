import pandas as pd
from dotenv import load_dotenv
import os
import boto3
import json
import time

script_dir = os.path.dirname(os.path.abspath(__file__))

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID12')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY12')
RAW_AUCTIONS_BUCKET = os.getenv('RAW_AUCTIONS_BUCKET')
DAILY_URLS_BUCKET = os.getenv("DAILY_URLS_BUCKET")





def get_existing_files(auction_files_path):
    return os.listdir(auction_files_path)

def download_s3_objects(existing_files, bucket, objects_local_dir):
    s3_client = boto3.client(
        's3',
        aws_access_key_id = AWS_ACCESS_KEY_ID,
        aws_secret_access_key = AWS_SECRET_ACCESS_KEY
    )
    objects = s3_client.list_objects(Bucket=bucket)
    available_files = [file['Key'] for file in objects['Contents']]

    files_to_download = set(available_files)-set(existing_files)
    # print(files_to_download)
    for file in files_to_download:
        # key = file['Key']
        print(f"Downloading {file}")
        s3_client.download_file(bucket, file, f"{objects_local_dir}/{file}")



objects_local_dir = os.path.join(script_dir, "../urls/")
os.makedirs(objects_local_dir, exist_ok=True)


existing_files = get_existing_files(objects_local_dir)
download_s3_objects(existing_files, DAILY_URLS_BUCKET, objects_local_dir)

