import os
import boto3
from datetime import datetime,timedelta
import json
from dotenv import load_dotenv

load_dotenv()

# access keys
aws_access_key_id = os.environ['AWS_ACCESS_KEY_ID12']
aws_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY12']

saving_date =  datetime.today().date() - timedelta(days=1)
project_path = "/home/ec2-user/carsnbids"

# s3
s3 = boto3.client(
    's3',
    region_name = 'us-east-1',
    aws_access_key_id = aws_access_key_id,
    aws_secret_access_key = aws_secret_access_key
)

# print(s3.list_buckets())

auctions_file = f"{project_path}/daily_auctions/{saving_date}.json"
urls_file = f"{project_path}/daily_urls/{saving_date}.txt"

auction_files_bucket = 'carsandbids-daily-auctions'
urls_files_bucket = 'carsandbids-daily-urls'


try:
    if os.path.isfile(auctions_file):
        # upload files  
        print("uploading urls and auction files to cloud....")
        s3.upload_file(Filename = f"{project_path}/daily_auctions/{saving_date}.json",Bucket = auction_files_bucket, Key = f"{saving_date}.json")
        s3.upload_file(Filename = f"{project_path}/daily_urls/{saving_date}.txt", Bucket = urls_files_bucket, Key = f"{saving_date}.txt")  

except Exception as e:
    print(e)
