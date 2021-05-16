#!/usr/bin/env python3
import crypto_lookup


if __name__ == "__main__":
  #test with full crypto name
  coin = crypto_lookup.LunarCrush('dogecoin')
  print(coin.data)

  #test with crypto symbol
  coin = crypto_lookup.LunarCrush('doge')
  print(coin.data)