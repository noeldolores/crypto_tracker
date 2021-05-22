#!/usr/bin/env python3
from threading import Thread
import crypto_lookup


def search(query, coin_list):
  coin = crypto_lookup.Query(query)
  if coin.data is not None:
    coin_list.append(coin.data)
    return True
  return False


def threaded_query(coin, is_list):
  if is_list:
    coin_list = []
    threads = []

    for i in range(len(coin)):
      process = Thread(target=search, args=[coin[i], coin_list])
      process.start()
      threads.append(process)
    for process in threads:
      process.join()

    try:
      print(*coin_list, sep='\n')
    except Exception as e:
      print(e)

  else:
    result = crypto_lookup.Query(coin)

    if result.data is not None:
      try:
        print(result.data)
      except Exception as e:
        print(e)


def input_to_list(cli_input):
  return cli_input.split(',')



if __name__ == "__main__":
  is_list = False
  coin_input = input("Enter one or more cryptos, comma-separated with no spaces:")

  if ',' in coin_input:
    coin = input_to_list(coin_input)
    is_list = True

  else:
    coin = coin_input

  threaded_query(coin, is_list)