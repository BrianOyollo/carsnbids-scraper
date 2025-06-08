import os
from datetime import datetime


def get_most_recent_url_file(daily_urls_dir):
    most_recent_date = None
    most_recent_file = None

    file_list = [file for file in os.listdir(daily_urls_dir)]
    for file in file_list:
        date_str = file.split('.')[0]
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')

        if most_recent_date is None or date_obj > most_recent_date:
            most_recent_date = date_obj
            most_recent_file = file

    return most_recent_file




# daily_urls_dir = "../daily_urls"
# print(get_most_recent_url_file(daily_urls_dir))
# 