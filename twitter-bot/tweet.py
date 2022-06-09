import os
import json
import tweepy
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time
from update_data import update_json
from config import API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
import unidecode

# FOLDER_WIKI = '/home/tanguy/workspace/jupyter/wiki'
FOLDER_WIKI = '/home/tanguy/wiki-tracker/wiki-tracker'

def process_article(article):
    name = article[0]
    list_filter = ['Wikipédia:', 'Wikip?dia:', 'Special:', 'Spécial:', 'Sp?cial:', 'Fichier:', 'Utilisateur:', 'Portail:', 'Aide:', 'Discussion:', 'Discussion_utilisateur:', 'Sujet:']
    for e in list_filter:
        if e in name:
            return False
    return True
    
def __make_workcloud(freq, name):
    wc = WordCloud(background_color="white", max_words=100, width=2000, height=1000)
    wc.generate_from_frequencies(freq)
    plt.figure(figsize=(30,15))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    file_path = os.path.join(FOLDER_WIKI, 'static', 'output', f'{name}.png')
    plt.savefig(file_path)

def to_hashtag(s):
    clean_s = s.replace(' ', '').replace("'", '').replace('-', '')
    clean_s = clean_s.split('(')[0]
    clean_s = unidecode.unidecode(clean_s)
    return f'#{clean_s}'

def make_image(year, month, day):
    file_path = os.path.join(FOLDER_WIKI, 'json', f'{year}_{month:02d}.json')
    with open(file_path, 'r') as f:
        date = f'{year}_{month:02d}_{day:02d}'
        list_articles = json.load(f)[date]

    list_articles = list(filter(process_article, list_articles))
    list_articles = list_articles[:50]

    dict_articles = {e[0].replace('_', ' '):e[1] for e in list_articles}
    dict_long_name = {"Liste de sondages sur l'élection présidentielle française de 2022": "Sondages Election Présidentielle",
                      "Liste de sondages sur les élections législatives françaises de 2022": "Sondages Elections Législatives"
                     }
    for long_name, short_name in dict_long_name.items():
        if long_name in dict_articles:
            dict_articles[short_name] = dict_articles.pop(long_name)

    name_file = f'{year}-{month:02d}-{day:02d}'
    __make_workcloud(dict_articles, name_file)
    
    hashtag_str = ' '.join([to_hashtag(e[0]) for e in list(dict_articles.keys())[:5]])[:280]
    return hashtag_str


def tweet(date):
    # Generate image
    hashtag_str = make_image(date.year, date.month, date.day)
    name_file = f'{date.year}-{date.month:02d}-{date.day:02d}'

    auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)
    
    file_path = os.path.join(FOLDER_WIKI, 'static', 'output', f'{name_file}.png')
    date_format = yesterday.strftime("%d/%m/%Y")
    text = f'{date_format} {hashtag_str}'
    status = api.update_status_with_media(text, file_path)


if __name__ == '__main__':
    yesterday = datetime.now() - timedelta(1)
    update_json(yesterday)
    time.sleep(5)
    tweet(yesterday)