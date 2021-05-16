#!/usr/bin/env python3
import crypto_lookup


if __name__ == "__main__":
  coin = crypto_lookup.LunarCrush('dogecoin')
  try:
    print(coin.data)
  except Exception as e:
    print(e)