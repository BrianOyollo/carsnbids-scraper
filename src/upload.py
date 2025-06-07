import boto3
import time
import json
import os

bucket_name = os.getenv('AUCTIONS_BUCKET')

def upload_to_s3(auction_data):
    # Upload to S3

    timestamp = int(time.time())
    output_file = f"rescraped_results_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(auction_data, f, indent=3)

    s3 = boto3.client("s3")
    s3.upload_file(output_file, bucket_name, f"{output_file}")
