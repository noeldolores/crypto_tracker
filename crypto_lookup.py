import os
import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv


class LunarCrush:
  def __init__(self, symbol):
    self.api_key = self.load_api_key()
    self.interval = 'day'

    if type(symbol) == str:
      self.data = self.get_data(symbol, self.interval)

    elif type(symbol) == list:
      self.data_list = [self.get_data(x, self.interval) for x in symbol]


  def get_data(self, symbol, interval='day'):
    ## interval = ('day', 'hour')
    url = self.set_url(self.api_key, symbol, interval)

    try:
      response = requests.get(url)

      if response.status_code == 400:
        print(f"Attempting to find the symbol for '{symbol}'.")
        result = self.symbol_lookup(symbol)

        if result is not None:
          print(f"Success! '{symbol}' is '{result}'")
          symbol = result
          url = self.set_url(self.api_key, symbol, interval)
          response = requests.get(url)

        else:
          print(f"'{symbol}' not found. Please retry with the correct symbol or full name.")
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
      "price": data['price'],
      "price_btc": data['price_btc'],
      "percent_change_24h": data['percent_change_24h'],
      "percent_change_7d": data['percent_change_7d'],
      "percent_change_30d": data['percent_change_30d'],
      "interval": self.interval,
      "open": data['timeSeries'][0]['open'],
      "close": data['timeSeries'][0]['close'],
      "high": data['timeSeries'][0]['high'],
      "low": data['timeSeries'][0]['low']
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