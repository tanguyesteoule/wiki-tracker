from datetime import datetime, timedelta
from os.path import exists
import os
import calendar
import requests
import json

# FOLDER_WIKI = '/home/tanguy/workspace/jupyter/wiki'
FOLDER_WIKI = '/home/tanguy/wiki-tracker/wiki-tracker'


def update_json(end_date):
    for year in range(2016, end_date.year+1):
        for month in range(1, 13):
            DICT_DATA = {}
            nb_days = calendar.monthrange(year, month)[1]
            
            file_path = os.path.join(FOLDER_WIKI, 'json', f'{year}_{month:02d}.json')
            if exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if len(data.keys()) == nb_days:
                        # Json file already exists
                        print(f'{year}_{month:02d} PASSED')
                        continue
                    else:
                        DICT_DATA = data
            else:
                DICT_DATA = {}
            
            for day in range(1, nb_days+1):
                date = f'{year}_{month:02d}_{day:02d}'
                
                if date not in DICT_DATA:
                    print(date)
                    url = f'https://wikimedia.org/api/rest_v1/metrics/pageviews/top/fr.wikipedia/all-access/{year}/{month:02d}/{day:02d}'
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"}
                    r = requests.get(url, headers=headers)
                    d = json.loads(r.text)
                    list_articles = [(e['article'],e['views']) for e in d['items'][0]['articles']]

                    DICT_DATA[date] = list_articles
                    
                if year == end_date.year and month == end_date.month and day == end_date.day:
                    with open(file_path, 'w') as f:
                        json.dump(DICT_DATA, f)
                    return
                        
            with open(file_path, 'w') as f:
                json.dump(DICT_DATA, f)


if __name__ == '__main__':
    yesterday = datetime.now() - timedelta(1)
    update_json(yesterday)