#!/usr/bin/env python3
import crypto_lookup
import sys


def coin_query(coin):
  result = crypto_lookup.LunarCrush(coin)
  if result.data_list is None:
    try:
      print(result.data)
    except Exception as e:
      print(e)
  else:
    try:
      print(*result.data_list, sep='\n')
    except Exception as e:
      print(e)


def input_to_list(cli_input):
  return cli_input.split(',')


if __name__ == "__main__":
  coin = input("Enter one or more cryptos, comma-separated with no spaces:")
  if ',' in coin:
        coin = input_to_list(coin)

  coin_query(coin)