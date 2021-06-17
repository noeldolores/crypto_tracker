import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
import base64
from io import BytesIO
from IPython.display import HTML
from datetime import date, timedelta, timezone, datetime, time
import os
import requests
from bs4 import BeautifulSoup
import json
import matplotlib.dates as mdates
from . import crypto_lookup

import numpy as np

def get_market_data(coin_id=str, interval=str, time_range=int):
    # Interval: hour (60*60), day (60*60*24), month (60*60*24*30), year (60*60*24*30*12)
    unix_now = int(datetime.now(timezone.utc).timestamp())

    if interval == "hour":
        sec = 60*60
    elif interval == "day":
        sec = 60*60*24
    elif interval == "month":
        sec = 60*60*24*30
    elif interval == "year":
        sec = 60*60*24*7*52

    query_delta = time_range * sec
    query_start = unix_now - query_delta

    response = requests.request(method='GET', url=f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range?vs_currency=usd&from={query_start}&to={unix_now}")
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        return json.loads(soup.string)
    return None


def get_dates_from(day_delta):
    today = date.today()
    dates = []
    for i in range(1,day_delta +1):
        dates.append((today - timedelta(days = i)).strftime("%b %d"))
    dates.reverse()
    return dates


def sparkline(data=list, figsize=(10, 3), class_add=None, show_ticks=False, hours=168, **kwags):
    """ This function creates an HTML <img> of a graph.
        data: List of 168 hourly price points
        figsize: Default size (10,3) for Dashboard. (20,6) for Home carousel
        class_add: Default (None) for dashboard. ("d-block w-100") for Home carousel to keep image centered.
        show_ticks: Default (None) for dashboard. (True) for Home carousel as there is more space to view.
    """

    _, ax = plt.subplots(1, 1, figsize=figsize, **kwags)
    ax.plot(data, 'w')

    for _, v in ax.spines.items():
        v.set_visible(False)

    if not show_ticks: 
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        ax.set_xticks([0,24,48,72,96,120,144,168])
        a=ax.get_xticks().tolist()
        a = get_dates_from(8)
        ax.set_xticklabels(a)
        ax.set_yticks([max(data), min(data)])
        ax.tick_params(axis="y",direction="in", pad=-40)
        ax.tick_params(axis=u'both', which=u'both',length=0)


    ymax = max(data)
    xmax = data.index(ymax)
    plt.plot(xmax, ymax, 'g.', markersize=20, alpha=0.5)

    ymin = min(data)
    xmin = data.index(ymin)
    plt.plot(xmin, ymin, 'r.', markersize=20, alpha=0.5)
  
    vert_lines = [x for x in range(0, len(data) + 1, 24)]
    for v in vert_lines:
        plt.axvline(x=v, color="white", alpha=0.1, ls="--")

    img = BytesIO()
    plt.savefig(img, transparent=True, bbox_inches='tight')
    img.seek(0)
    plt.close()

    return HTML('<img src="data:image/png;base64,{}" class="img-fluid {}"/>'.format(base64.b64encode(img.read()).decode("UTF-8"), class_add))



def market_graph(coin_id=str, interval=str, time_range=int, figsize=(20, 6), class_add="", **kwags):
    """ This function creates an HTML <img> of a graph.
        data: List of 168 hourly price points
        figsize: Default size (10,3) for Dashboard. (20,6) for Home carousel
        class_add: Default (None) for dashboard. ("d-block w-100") for Home carousel to keep image centered.
        show_ticks: Default (None) for dashboard. (True) for Home carousel as there is more space to view.
    """
    full_data = get_market_data(coin_id, interval, time_range)
    price_data = full_data['prices']
    cap_data = full_data['market_caps']
    volume_data = full_data['total_volumes']


    price_data_x = []
    for i in price_data:
        u = datetime.utcfromtimestamp(i[0]/1000)
        price_data_x.append(u)



    price_data_y = [x[1] for x in price_data]

    _, ax = plt.subplots(1, 1, figsize=figsize, **kwags)

    color = 'k'
    if price_data[0][1] < price_data[len(price_data) - 1][1]:
        color = "g"
    else:
        color = 'r'

    ax.plot(np.array(price_data_x), np.array(price_data_y), color)

    # Hide graph border
    for _, v in ax.spines.items():
        v.set_visible(False)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))

    
    ax.tick_params(axis='both', which='both', length=0, colors='white', labelsize=20)

    if interval == "hour":
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%R'))
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))

    # Set Y-axis tick labels to the high and low price points
    ax.set_yticks([max(price_data_y), min(price_data_y)])

    ax.tick_params(axis="y",direction="in", pad=-40)

    for i in ax.get_yticks():
        plt.axhline(i, color="white", alpha=0.15, ls="--", xmin=0.05, xmax=.95)

    for i in ax.get_xticks():
        plt.axvline(i, color="white", alpha=0.15, ls="-")


    # Place a color dot indicator at the graph high and low points
    ymax = max(price_data_y)
    xmax = price_data_y.index(ymax)
    plt.plot(price_data_x[xmax], ymax, 'g.', markersize=20, alpha=0.5)

    ymin = min(price_data_y)
    xmin = price_data_y.index(ymin)
    plt.plot(price_data_x[xmin], ymin, 'r.', markersize=20, alpha=0.5)


    img = BytesIO()
    plt.savefig(img, transparent=True, format='png')
    img.seek(0)
    plt.close()

    return HTML('<img src="data:image/png;base64,{}" class="img-fluid {}"/>'.format(base64.b64encode(img.read()).decode("UTF-8"), class_add))