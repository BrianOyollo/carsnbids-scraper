import boto3
from dotenv import load_dotenv
import os

load_dotenv()
aws_access_key_id = os.environ['AWS_ACCESS_KEY_ID12']
aws_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY12']

region = 'us-east-1'
instances = ['i-xx']
ec2 = boto3.client(
    'ec2',
    region_name = 'us-east-1',
    aws_access_key_id = aws_access_key_id,
    aws_secret_access_key = aws_secret_access_key
)

# ec2.start_instances(InstanceIds=instances)
ec2.stop_instances(InstanceIds=instances)
# print('started your instances: ' + str(instances))
print('stopped your instances: ' + str(instances))