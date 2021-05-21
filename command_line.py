#!/usr/bin/env python3
import crypto_lookup


def coin_query(coin, is_list):
  if is_list:
    coin_list = []
    for crypto in coin:
      result = crypto_lookup.LunarCrush(crypto)
      if result.data is not None:
        coin_list.append(result.data)
      else:
        result = crypto_lookup.CoinGecko(crypto)
        if result.data is not None:
          coin_list.append(result.data)
    try:
      print(*coin_list, sep='\n')
    except Exception as e:
      print(e)
  
  else:
    result = crypto_lookup.LunarCrush(coin)
    if result.data is not None:
      try:
        print(result.data)
      except Exception as e:
        print(e)
    else:
      result = crypto_lookup.CoinGecko(coin)
      if result.data is not None:
        try:
          print(result.data)
        except Exception as e:
          print(e)


def input_to_list(cli_input):
  return cli_input.split(',')


if __name__ == "__main__":
  is_list = False
  coin = input("Enter one or more cryptos, comma-separated with no spaces:")
  if ',' in coin:
        coin = input_to_list(coin)
        is_list = True

  coin_query(coin, is_list)