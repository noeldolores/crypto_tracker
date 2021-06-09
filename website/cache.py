from datetime import datetime
from . import db
from .models import CurrencyCache, Currency



def CurrencyCache_Query(query):
  nameQuery = query.coinName.lower() #coin['name'].lower()
  symbolQuery = query.coinSymbol.lower() #coin['symbol'].lower()

  lookup = CurrencyCache_IdLookup(name=nameQuery, symbol=symbolQuery)
  if lookup:
    too_old = CurrencyCache_OldAge(lookup)
    if too_old:
      return "old"
    return lookup
  else:
    return None

  
def CurrencyCache_IdLookup(name=None, symbol=None):
  coinSymbol_check = CurrencyCache.query.filter_by(coinSymbol=str(symbol).lower()).first()
  coinName_check = CurrencyCache.query.filter_by(coinName=str(name).lower()).first()
  
  if coinSymbol_check:
    return coinSymbol_check
  elif coinName_check:
    return coinName_check
  return None


def CurrencyCache_Update(sql_coin, coin):
  try:
    sql_coin.last_update=datetime.utcnow()
    sql_coin.coinSymbol=coin['symbol'].lower()
    sql_coin.coinName=coin['name'].lower()
    sql_coin.price=float(coin['price'])
    sql_coin.change24h=coin['percent_change_24h']
    sql_coin.change7d=coin['percent_change_7d']
    sql_coin.change30d=coin['percent_change_30d']
    db.session.commit()
    return True
  except Exception as e:
    print("CurrencyCache_Update ", e)
    return False


def CurrencyCache_Add(coin):
  if coin:
    new_coin = CurrencyCache(coinSymbol=coin['symbol'].lower(),coinName=coin['name'].lower(),price=float(coin['price']),
              change24h=coin['percent_change_24h'],change7d=coin['percent_change_7d'],change30d=coin['percent_change_30d'])
    db.session.add(new_coin)
    db.session.commit()
    return True
  else:
    return False


def CurrencyCache_OldAge(sql_coin):
  too_old = 60 * 60 # 1 hour in seconds
  utc_now = datetime.utcnow()
  last_update = sql_coin.last_update
  time_diff = (utc_now - last_update).seconds
  if time_diff > too_old:
    return True
  return False