import os
from flask import Flask, render_template, send_from_directory, request, url_for, redirect
from datetime import datetime, timedelta
import json
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os.path
import pandas as pd
import plotly
import plotly.express as px
import calendar

app = Flask(__name__)

@app.route('/')
def index():
    yesterday = datetime.now() - timedelta(days=1, hours=7)
    last_date = yesterday.strftime("%Y-%m-%d")
    return render_template('index.html', last_date=last_date)

def process_article(article):
    name = article[0]
    list_filter = ['Wikipédia:', 'Wikip?dia:', 'Special:', 'Spécial:', 'Sp?cial:', 'Fichier:', 'Utilisateur:', 'Portail:', 'Aide:', 'Discussion:', 'Discussion_utilisateur:']
    for e in list_filter:
        if e in name:
            return False
    return True

def makeImage(freq, name):
    wc = WordCloud(background_color="white", max_words=100, width=2000, height=1000)
    wc.generate_from_frequencies(freq)
    plt.figure(figsize=(30,15))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    file_path = f'static/output/{name}.png'
    plt.savefig(file_path)

def get_wordcloud(year, month, day):
    file_path = f'json/{year}_{month}.json'
    with open(file_path, 'r') as f:
        date = f'{year}_{month}_{day}'
        list_articles = json.load(f)[date]

    list_articles = list(filter(process_article, list_articles))
    list_articles = list_articles[:50]

    dict_articles = {e[0].replace('_', ' '):e[1] for e in list_articles}
    long_name = "Liste de sondages sur l'élection présidentielle française de 2022"
    if long_name in dict_articles:
        dict_articles["Sondages élection présidentielle"] = dict_articles.pop(long_name)

    name_file = f'{year}-{month}-{day}'
    makeImage(dict_articles, name_file)


@app.route('/button', methods=["GET"])
def button():
    date = request.args.get('date', type = str)
    year, month, day = date.split('-')
    if not os.path.isfile(f'static/output/{year}-{month}-{day}.png'):
        get_wordcloud(year, month, day)

    return 'test'


def agreg_date(list_date):
    if len(list_date) == 1:
        return [[list_date[0], list_date[0] + timedelta(days=1)]]

    start = list_date[0]
    old_date = start
    list_period = []
    for date in list_date[1:-1]:
        if date == old_date + timedelta(days=1):
            pass
        else:
            list_period.append([start, old_date + timedelta(days=1)])
            start = date

        old_date = date

    # Last row
    if list_date[-1] == old_date + timedelta(days=1):
        list_period.append([start, list_date[-1] + timedelta(days=1)])
    else:
        list_period.append([start, old_date + timedelta(days=1)])
        list_period.append([list_date[-1], list_date[-1] + timedelta(days=1)])
    return list_period



@app.route('/periods', methods=["GET"])
def periods():
    start_date = request.args.get('start', type = str)
    end_date = request.args.get('end', type = str)

    yesterday = datetime.now() - timedelta(days=1, hours=7)
    last_week = yesterday - timedelta(days=7)
    LIMIT_DATE = yesterday.strftime("%Y-%m-%d")
    DEFAULT_START = last_week.strftime("%Y-%m-%d")
    DEFAULT_END = yesterday.strftime("%Y-%m-%d")
    if start_date is None or end_date is None or start_date > LIMIT_DATE or end_date > LIMIT_DATE or end_date < start_date:
        return redirect(url_for('.periods', start=DEFAULT_START, end=DEFAULT_END))

    # TODO : period max
    list_dates = list(pd.date_range(start_date, end_date).strftime("%Y-%m-%d"))
    list_year_month = {date[:7] for date in list_dates}

    if len(list_dates) > 31:
        return redirect(url_for('.periods', start=DEFAULT_START, end=DEFAULT_END))

    list_articles_month = dict()
    for year_month in list_year_month:
        year_month = year_month.replace('-', '_')
        file_path = f'json/{year_month}.json'
        with open(file_path, 'r') as f:
            list_articles_month[year_month] = json.load(f)

    dict_article = {}

    list_df = []

    for date in list_dates:
        dt = datetime.strptime(date, '%Y-%m-%d')
        dt_next = dt + timedelta(days=1)
        date_und = date.replace('-', '_')
        list_articles = list_articles_month[date_und[:7]][date_und]
        list_articles = list(filter(process_article, list_articles))
        # TODO : why 15 ?
        for article in list_articles[:15]:
            name = article[0]
            if name in dict_article:
                dict_article[name].append(dt)
            else:
                dict_article[name] = [dt]
    nb_day_article = {k:len(v) for k,v in dict_article.items()}
    dict_article = {k:agreg_date(v) for k,v in dict_article.items()}

    for name, periods in dict_article.items():
        if nb_day_article[name] > 1:
            for period in periods:
                list_df.append(dict(Page=name.replace('_', ' '), Start=period[0], Finish=period[1], Cluster="0"))

    df = pd.DataFrame(list_df)

    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Page", color="Cluster")
    fig.update_yaxes(autorange="reversed", title=None)
    fig.update_layout(showlegend=False, title=f'Tendances Wikipédia FR du {start_date} au {end_date}')

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('periods.html', graphJSON=graphJSON, last_date=LIMIT_DATE)




if __name__ == '__main__':
      app.run(host='0.0.0.0', port=os.getenv('PORT'))