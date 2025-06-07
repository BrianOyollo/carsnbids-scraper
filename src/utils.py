import os
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

from logger import setup_json_logger

load_dotenv()
logger = setup_json_logger()

uls_file_path = os.getenv('URLS_FILE_PATH')
filter_duration = os.getenv('URLS_FILTER_DURATION')


def filter_urls(urls:list, urls_file_path:str='urls.csv', filter_duration:int=7)->list:
    # read the file at urls_file_path
    # extract urls that are atleast filter_duration old
    # return unique urls between urls and filtered urls
    
