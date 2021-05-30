import os
import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
import pickle



class Query:
  def __init__(self, search, list_to_append=None):
    self.data = None
    
    coin = LunarCrush(search)
    if coin.data is None:
      coin = CoinGecko(search)
      if coin.data is not None:
        self.data = coin.data
        if list_to_append is not None:
          list_to_append.append(coin.data)
    else:
      self.data = coin.data
      if list_to_append is not None:
        list_to_append.append(coin.data)
    


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
        #print(f"Attempting to find the symbol for '{symbol}'.")
        result = self.symbol_lookup(symbol)

        if result is not None:
          #print(f"Success! '{symbol}' is '{result}'")
          symbol = result
          url = self.set_url(self.api_key, symbol, interval)
          response = requests.get(url)

        else:
          #print(f"'{symbol}' not found on LunarCrush. Searching CoinGecko database.")
          return None

      temp_dict = json.loads(response.content)['data'][0]
      self.data = self.parse_relevant_data(temp_dict)

    except Exception as e:
      print(e)
      return None

    return self.data


  def set_url(self, api_key, symbol, interval):
    return f"https://api.lunarcrush.com/v2?data=assets&key={api_key}&symbol={symbol}&data_points=1&interval={interval}&time_series_indicators=open,close,high,low"


  def load_api_key(self):
    load_dotenv()
    return os.getenv('LUNARCRUSH_API_KEY')


  def parse_relevant_data(self, data):
    data = {
      "name": data['name'],
      "id": data['id'],
      "symbol": data['symbol'],
      "price": self.convert_sci_to_dec(data['price']),
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


  def symbol_lookup(self, full_name):
    response = requests.request(method='GET', url=f"https://coinmarketcap.com/currencies/{full_name}/")
    soup = BeautifulSoup(response.content, "html.parser")
    result = soup.find('script', {'type': 'application/ld+json'})
    if result is not None:
      raw_json = json.loads(result.string)
      return raw_json['currency']

    return None


  def convert_sci_to_dec(self, num):
    max_dig = 10
    int_len = len(str(int(num)))
    return (f"%.{max(max_dig, int_len) - min(max_dig, int_len)}f" % num).rstrip('0').rstrip('.')



class CoinGecko:
  def __init__(self, query):
    self.data = None
    coin_id = self.symbol_lookup(query.lower())
    if coin_id is not None:
      coin_data = self.get_data(coin_id)
      self.data = self.parse_relevant_data(coin_data)
    else:
      print(f"'{query}' not found. Please check your search and try again.")


  def symbol_lookup(self, query):
    coin_list = self.generate_coin_list()
    if coin_list is not None:
      for coin in coin_list:
        if query == coin['id'].lower() or query == coin['symbol'].lower() or query == coin['name'].lower():
          return coin['id']

    return None


  def get_data(self, coin_id):
    response = requests.request(method='GET', url=f"https://api.coingecko.com/api/v3/coins/{coin_id}?market_data=true")

    if response.status_code == 200:
      soup = BeautifulSoup(response.content, "html.parser")
      coin_data = json.loads(soup.string)
      return coin_data

    return None


  def parse_relevant_data(self, coin_data):
    data = {
      "name": coin_data['name'],
      "id": coin_data['id'],
      "symbol": coin_data['symbol'],
      "price": self.convert_sci_to_dec(coin_data['market_data']['current_price']['usd']),
      "percent_change_24h": coin_data['market_data']['price_change_percentage_24h'],
      "percent_change_7d": coin_data['market_data']['price_change_percentage_7d'],
      "percent_change_30d": coin_data['market_data']['price_change_percentage_30d'],
    }
    return data


  def convert_sci_to_dec(self, num):
    return ("%.10f" % num).rstrip('0').rstrip('.')

    
  def generate_coin_list(self):
    filename = 'coingecko.txt'
    coin_list = []
    if not os.path.exists(filename):
      response = requests.request(method='GET', url="https://api.coingecko.com/api/v3/coins/list?include_platform=false")
      if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        coin_list = json.loads(soup.string)
        with open(filename, 'wb+') as f:
          pickle.dump(coin_list, f)

        return coin_list
    
    else:
      with open(filename, 'rb') as f:
        coin_list = pickle.load(f)

        return coin_list
        
    return None