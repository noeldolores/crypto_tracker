import os
import requests
from bs4 import BeautifulSoup
import html
import json
from dotenv import load_dotenv
import sys


class LunarCrush:
  def __init__(self, symbol):
    self.symbol = symbol
    self.api_key = self.load_api_key()
    self.interval = 'day'
    
    self.get_data(self.interval)


  def get_data(self, interval):
    ## interval can equal "day" or "hour"
    self.interval = interval
    url = self.set_url()

    try:
      response = requests.get(url)

      if response.status_code == 400:
        print(f"Attempting to lookup the symbol for '{self.symbol}'...")
        result = self.symbol_lookup(self.symbol)

        if result is not None:
          print(f"Success! '{self.symbol}' is '{result}'")
          self.symbol = result
          url = self.set_url()
          response = requests.get(url)
        else:
          print(f"'{self.symbol}' not found. Please retry with the correct symbol or full name.")
          sys.exit(1)

      temp_dict = json.loads(response.content)['data'][0]
      self.data = self.parse_relevant_data(temp_dict)

    except Exception as e:
      print(e)
      sys.exit(1)

    return self.data


  def set_url(self):
    return f"https://api.lunarcrush.com/v2?data=assets&key={self.api_key}&symbol={self.symbol}&data_points=1&interval={self.interval}&time_series_indicators=open,close,high,low"


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
      raw_json = json.loads(html.unescape(result.string))
      return raw_json['currency']

    return None