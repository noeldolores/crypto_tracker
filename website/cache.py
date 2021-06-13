from datetime import datetime
import json
import sys
import requests
from bs4 import BeautifulSoup
from . import db
from .models import CurrencyCache


def retrieve_supported_cryptos():
  url = "https://api.coingecko.com/api/v3/coins/list?include_platform=true"
  response = requests.request(method='GET', url=url)
  if response.status_code == 200:
    soup = BeautifulSoup(response.content, "html.parser")
    try:
      json_soup = json.loads(soup.string)
      return json_soup
    except Exception as e:
      print(f"retrieve_crypto_list: {e}", flush=True)
      return None
  return None


def create_id_query_list(crypto_ids=list):
  list_of_query_lists = []
  max_count = 100
  if crypto_ids:
    id_list = []
    for i in range(len(crypto_ids)):
      _id = crypto_ids[i]['id']
      if i == len(crypto_ids) - 1:
        id_list.append(_id)
        list_of_query_lists.append(id_list)
      elif len(id_list) < max_count:
        id_list.append(_id)
      else:
        list_of_query_lists.append(id_list)
        id_list = []
        id_list.append(_id)
    return list_of_query_lists
  return None


def create_id_query_string(query_ids=list):
  list_of_query_strings = []
  if query_ids:
    for _ids in query_ids:
      list_of_query_strings.append(",".join(_ids))
    return list_of_query_strings
  return None


def query_market_data(query_string=list):
  market_data = []
  for query in query_string:
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={query}&sparkline=true&price_change_percentage=1h,24h,7d,14d,30d,200d,1y"
    response = requests.request(method='GET', url=url)
    if response.status_code == 200:
      soup = BeautifulSoup(response.content, "html.parser")
      try:
        query_result = json.loads(soup.string)
        market_data.append(query_result)
      except Exception as e:
        print(f"query_market_data: {e}", flush=True)
    else:
      print(f"query_market_data: {response} : {response.status_code}", flush=True)
  if market_data:
    return [data for data_list in market_data for data in data_list]
  return None


def add_to_currency_cache(market_data=list, from_scratch=False):
  update_rate = 0
  add_rate = 0
  if market_data:
    for crypto in market_data:
      try:
        if not from_scratch:
          try:
            query = currency_cache_id_query(crypto['id'])
          except Exception as e:
            print(f"add_to_currency_cache 1: {e} : {crypto}", flush=True)
            query = None
          if query:
            CurrencyCache_Update(query, crypto)
            update_rate += 1
          else:
            CurrencyCache_Add(crypto)
            add_rate += 1
        else:
          CurrencyCache_Add(crypto)
          add_rate += 1
      except Exception as e:
        print(f"add_to_currency_cache 2: {e}", flush=True)
        return None
    return f"Updated: {update_rate}; Added: {add_rate}; Total: {add_rate + update_rate} / {len(market_data)} : {(add_rate + update_rate) / len(market_data) * 100}%"


def request_cpu_usage():
  username = 'noeldolores'
  token = '9c6af631448c052f3322723a5986bad0b6704af0'

  response = requests.get(f'https://www.pythonanywhere.com/api/v0/user/{username}/cpu/',
                          headers={'Authorization': f'Token {token}'})
  if response.status_code == 200:
    cpu_usage = json.loads(response.content)
    limit = cpu_usage["daily_cpu_limit_seconds"]
    used = cpu_usage["daily_cpu_total_usage_seconds"]
    total_used = round(used/limit, 2) * 100
    return f'CPU quotao: {total_used}'
  else:
    print(f'Got unexpected status code {response.status_code}: {response.content}', flush=True)
    return None



def CurrencyCache_Query(query):
  if query is not None:
    cached_coin = currency_cache_id_query(query)

    if cached_coin:
      too_old = CurrencyCache_OldAge(cached_coin, 60 * 1) #1 minute
      if too_old:
        return cached_coin,"old"
      return cached_coin, "fresh"
    else:
      return None, None
  return None, None


def CurrencyCache_Update(sql_coin, coin):
  try:
    sql_coin.last_update=datetime.utcnow()
    sql_coin.coin_id = coin['id'].lower()
    sql_coin.name = coin['name'].lower()
    sql_coin.symbol = coin['symbol']
    sql_coin.img_url = coin['image']
    sql_coin.price = coin['current_price']
    sql_coin.change1h = coin['price_change_percentage_1h_in_currency']
    sql_coin.change24h = coin['price_change_percentage_24h_in_currency']
    sql_coin.change7d = coin['price_change_percentage_7d_in_currency']
    sql_coin.change14d = coin['price_change_percentage_14d_in_currency']
    sql_coin.change30h = coin['price_change_percentage_30d_in_currency']
    sql_coin.change200d = coin['price_change_percentage_200d_in_currency']
    sql_coin.change1y = coin['price_change_percentage_1y_in_currency']
    sql_coin.sparkline = coin['sparkline_in_7d']['price']
    db.session.commit()
    return True
  except Exception as e:
    print("CurrencyCache_Update ", e)
    return False


def CurrencyCache_Add(coin):
  if coin:
    try:
      new_coin = CurrencyCache(coin_id=coin['id'].lower(),
                            name=coin['name'].lower(),
                            symbol=coin['symbol'].lower(),
                            img_url=coin['image'],
                            price=coin['current_price'],
                            change1h=coin['price_change_percentage_1h_in_currency'],
                            change24h=coin['price_change_percentage_24h_in_currency'],
                            change7d=coin['price_change_percentage_7d_in_currency'],
                            change14d=coin['price_change_percentage_14d_in_currency'],
                            change30d=coin['price_change_percentage_30d_in_currency'],
                            change200d=coin['price_change_percentage_200d_in_currency'],
                            change1y=coin['price_change_percentage_1y_in_currency'],
                            sparkline=coin['sparkline_in_7d']['price'],
                            platforms=None)
      db.session.add(new_coin)
      db.session.commit()
      return True
    except:
      return False
  else:
    return False


def CurrencyCache_OldAge(sql_coin, max_age):
  utc_now = datetime.utcnow()
  last_update = sql_coin.last_update
  time_diff = (utc_now - last_update).seconds
  if time_diff > max_age:
    return True
  return False


def currency_cache_id_query(crypto_id=str):
  id_check = str(crypto_id).lower()
  try:
    crypto = CurrencyCache.query.filter_by(coin_id=id_check).first()
    if crypto:
      return crypto
    return None
  except Exception as e:
    print(f"currency_cache_id_query: {e}", file=sys.stderr)
    return None