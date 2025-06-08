#!/bin/bash

cd /home/ec2-user/carsnbids
source env/bin/activate
python /home/ec2-user/carsnbids/auctions.py
python /home/ec2-user/carsnbids/upload.py
