import os
import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
import sys


class DigitLimit:
  def __init__(self, value, max_len=11):
    self.max_len = max_len
    self.out = self.truncate(value)

  def truncate(self, num):
    if num is not None:
      int_len = len(str(int(float(num))))
      return (f"%.{max(self.max_len, int_len) - min(self.max_len, int_len)}f" % num).rstrip('0').rstrip('.')
    return float(0)



class Query:
  def __init__(self, search, list_to_append=None):
    coin = CoinGecko(query=search)
    if coin:
      self.data = coin.data
    else:
      self.data = None
    # if type(search) == tuple:
    #   for query in search:
    #     #print(f'{type(query)}: {query}', file=sys.stderr)
    #     coin = LunarCrush(query)
    #     #print(f'Lunar: {coin.data}', file=sys.stderr)
    #     if coin.data is not None:
    #       self.data = coin.data
    #       if list_to_append:
    #         list_to_append.append(self.data)
    #       break
    #     else:
    #       coin = CoinGecko(query=query.lower())
    #       #print(f'Gecko: {coin.data}', file=sys.stderr)
    #       if coin.data is not None:
    #         self.data = coin.data
    #         if list_to_append:
    #           list_to_append.append(self.data)
    #         break
    #   if self.data is None:
    #     print(f'Query not found: {search}', file=sys.stderr)

    # else:
    #   #print(f'Input: {search}', file=sys.stderr)
    #   coin = LunarCrush(search[0])
    #   if coin.data is not None:
    #     self.data = coin.data
    #     if list_to_append:
    #       list_to_append.append(self.data)
    #   else:
    #     coin = CoinGecko(search[0])
    #     if coin.data is not None:
    #       self.data = coin.data
    #       if list_to_append:
    #         list_to_append.append(self.data)
    #     else:
    #       print(f'Query not found: {search}', file=sys.stderr)





    #else:
    #  lunar_search = search
    #  gecko_search = search

    #coin = LunarCrush(lunar_search)
    #if coin.data is None:
    #  coin = CoinGecko(gecko_search)
     # if coin.data is not None:
     #   self.data = coin.data
     #   if list_to_append is not None:
    #      list_to_append.append(coin.data)
    #  else:
     #   print(f'Query not found: {search}')
    #else:
     # self.data = coin.data
    #  if list_to_append is not None:
      #  list_to_append.append(coin.data)



class LunarCrush:
  def __init__(self, symbol):
    self.api_key = self.load_api_key()
    self.interval = 'day'
    self.data = None

    self.data = self.get_data(symbol.lower(), self.interval)


  def get_data(self, symbol, interval='day'):
    ## interval = ('day', 'hour')
    url = self.set_url(self.api_key, symbol, interval)

    try:
      response = requests.get(url)
      if response.status_code == 400:
        result = self.symbol_lookup(symbol)
        if result is not None:
          symbol = result
          url = self.set_url(self.api_key, symbol, interval)
          response = requests.get(url)
        else:
          return None
      temp_dict = json.loads(response.content)['data'][0]
      self.data = self.parse_relevant_data(temp_dict)
    except:# Exception as e:
      #print("Lunar Crush.get_data", e)
      return None
    #return self.data


  def set_url(self, api_key, symbol, interval):
    #return f"https://api.lunarcrush.com/v2?data=assets&key={api_key}&symbol={symbol}"
    return f"https://api.lunarcrush.com/v2?data=assets&key={api_key}&symbol={symbol}&data_points=1&interval={interval}&time_series_indicators=open,close,high,low"


  def load_api_key(self):
    load_dotenv()
    return os.getenv('LUNARCRUSH_API_KEY')


  def parse_relevant_data(self, data):
    try:
      data = {
        "name": data['name'],
        "id": data['id'],
        "symbol": data['symbol'],
        "price": data['price'],
        # "price_btc": data['price_btc'],
        "percent_change_24h": data['percent_change_24h'],
        "percent_change_7d": data['percent_change_7d'],
        "percent_change_30d": data['percent_change_30d'],
        # "interval": self.interval,
        # "open": data['timeSeries'][0]['open'],
        # "close": data['timeSeries'][0]['close'],
        # "high": data['timeSeries'][0]['high'],
        # "low": data['timeSeries'][0]['low']
      }
      return data
    except:
      return None


  def symbol_lookup(self, full_name):
    response = requests.request(method='GET', url=f"https://coinmarketcap.com/currencies/{full_name}/")
    soup = BeautifulSoup(response.content, "html.parser")
    result = soup.find('script', {'type': 'application/ld+json'})
    if result is not None:
      raw_json = json.loads(result.string)
      return raw_json['currency']
    return None



class CoinGecko:
  def __init__(self, query=None, refresh=False):
    self.refresh = refresh
    self.data = None

    if not self.refresh:
      coin_id = query
      if coin_id is not None:
        coin_data = self.get_data(coin_id)
        if coin_data:
          self.data = coin_data
          #self.data = self.parse_relevant_data(coin_data)
          #print(self.data, file=sys.stderr)
    else:
      self.all_coins = self.generate_coin_list()


  def symbol_lookup(self, query):
    coin_list = self.generate_coin_list()
    if coin_list is not None:
      for coin in coin_list:
        if query == coin['id'].lower() or query == coin['symbol'].lower() or query == coin['name'].lower():
          return coin['id']
    return None


  def get_data(self, coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={coin_id}&sparkline=true&price_change_percentage=1h,24h,7d,14d,30d,200d,1y"
    response = requests.request(method='GET', url=url)
    if response.status_code == 200:
      soup = BeautifulSoup(response.content, "html.parser")
      try:
        return json.loads(soup.string)
      except Exception as e:
        print(f"query_market_data: {e}", file=sys.stderr)
        return None
    else:
      print(f"query_market_data: {response} : {response.status_code}", file=sys.stderr)
      return None

    # response = requests.request(method='GET', url=f"https://api.coingecko.com/api/v3/coins/{coin_id}?market_data=true")
    # #print(f'gecko response {response.status_code}', file=sys.stderr)
    # if response.status_code == 200:
    #   soup = BeautifulSoup(response.content, "html.parser")
    #   coin_data = json.loads(soup.string)
    #   return coin_data
    # return None


  def parse_relevant_data(self, coin_data):
    if 'market_data' in coin_data:
      if 'current_price' in coin_data['market_data']:
        if 'usd' in coin_data['market_data']['current_price']:
            data = {
              "name": coin_data['name'],
              "id": coin_data['id'],
              "symbol": coin_data['symbol'],
              "price": coin_data['market_data']['current_price']['usd'],
              "percent_change_24h": coin_data['market_data']['price_change_percentage_24h'],
              "percent_change_7d": coin_data['market_data']['price_change_percentage_7d'],
              "percent_change_30d": coin_data['market_data']['price_change_percentage_30d'],
            }
            return data
    return None


  def generate_coin_list(self):
    if self.refresh:
      coin_list = []
      response = requests.request(method='GET', url="https://api.coingecko.com/api/v3/coins/list?include_platform=false")
      if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        coin_list = json.loads(soup.string)
        return coin_list
    return None