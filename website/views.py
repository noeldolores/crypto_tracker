from flask import Blueprint, request, flash, session, render_template, redirect, url_for, escape
from flask_login import current_user, login_required, login_user
from datetime import datetime
import json
import sys
from currency_converter import CurrencyConverter
import pytz
from sqlalchemy.orm import query
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, crypto_lookup, cache, sparkline
from .models import User, Currency, CurrencyCache
import time
from sqlalchemy import desc, select


views = Blueprint('views', __name__)



def print_stderr(output=str):
  try:
    print(output, file=sys.stderr)
    return True
  except Exception as e:
    print(f"print_stderr: {e}", file=sys.stderr)
    return False


def timer(time_history=None, function=None):
  if not time_history:
    base = time.time()
    time_history = [('start', base, 0)]
    print_stderr(time_history[0])
    return time_history

  if function:
    stamp = time.time()
    lap_num = len(time_history) - 1
    total_time = round(stamp - time_history[0][1], 4)
    lap_time = round(total_time - time_history[lap_num][2], 4)
    lap_data = ((str(function), lap_time, total_time))
    time_history.append(lap_data)
    print_stderr(lap_data)
    return time_history
    

def search(query):
  search_results = []
  cached_coins = currency_cache_query(query)
  if cached_coins: 
    try:
      usd_rate = convert_currency(session['displaycurrency'])
    except:
      usd_rate = 1

    for coin_id in cached_coins:
      result = crypto_lookup.Query(coin_id)
      search_results.append(result.data[0])

    for coin in search_results:
      _price = float(coin['current_price']) * float(usd_rate)
      _1h = coin['price_change_percentage_1h_in_currency']
      _24h = coin['price_change_percentage_24h_in_currency']
      _7d = coin['price_change_percentage_7d_in_currency']
      _14d = coin['price_change_percentage_14d_in_currency']
      _30d = coin['price_change_percentage_30d_in_currency']
      _200d = coin['price_change_percentage_200d_in_currency']
      _1y = coin['price_change_percentage_1y_in_currency']
      spark = coin['sparkline_in_7d']['price']


      coin['current_price'] = crypto_lookup.DigitLimit(_price, max_len=10).out
      coin['price_change_percentage_1h_in_currency'] = crypto_lookup.DigitLimit(_1h, max_len=6).out
      coin['price_change_percentage_24h_in_currency'] = crypto_lookup.DigitLimit(_24h, max_len=6).out
      coin['price_change_percentage_7d_in_currency'] = crypto_lookup.DigitLimit(_7d, max_len=6).out
      coin['price_change_percentage_14d_in_currency'] = crypto_lookup.DigitLimit(_14d, max_len=6).out
      coin['price_change_percentage_30d_in_currency'] = crypto_lookup.DigitLimit(_30d, max_len=6).out
      coin['price_change_percentage_200d_in_currency'] = crypto_lookup.DigitLimit(_200d, max_len=6).out
      coin['price_change_percentage_1y_in_currency'] = crypto_lookup.DigitLimit(_1y, max_len=6).out
      coin['sparkline_in_7d'] = (sparkline.sparkline(data=spark), crypto_lookup.DigitLimit(max(spark), max_len=10).out, crypto_lookup.DigitLimit(min(spark), max_len=10).out)

    return search_results
  
  flash(f"'{query}' not found. Please try a different search. You may also report below if your crypto exists!", category='error')
  return search_results


def load_favorites_data(refresh=False):
  if len(current_user.currencies) > 0:
    if 'favorites' not in session:
      session['favorites'] = []
    usd_rate = convert_currency(session['displaycurrency'])
    user_currencies = current_user.currencies
    user_currency_data = []
    query_ids = []

    for i in range(len(user_currencies)):
      coin_id = user_currencies[i].coin_id
      session['favorites'].append(coin_id)

      coin_quantity = user_currencies[i].quantity
      if not coin_quantity:
        coin_quantity = 0
      elif coin_quantity > 0:
        coin_quantity = str(coin_quantity).strip('0')

      coin_id = user_currencies[i].coin_id
      load_cache, _ = cache.CurrencyCache_Query(coin_id)
      if load_cache is not None:
        if not refresh:
          spark = load_cache.sparkline
          if type(spark) == dict:
            spark = load_cache.sparkline['price']
          cached_coin = {
            'name': load_cache.name,
            'symbol': load_cache.symbol,
            'id': load_cache.coin_id,
            'current_price': apply_conversion_rate(num=load_cache.price, rate=usd_rate, max_digits=10),
            'current_price_usd': crypto_lookup.DigitLimit(load_cache.price, max_len=10).out,
            'price_change_percentage_1h_in_currency': crypto_lookup.DigitLimit(load_cache.change1h, max_len=6).out,
            'price_change_percentage_24h_in_currency': crypto_lookup.DigitLimit(load_cache.change24h, max_len=6).out,
            'price_change_percentage_7d_in_currency': crypto_lookup.DigitLimit(load_cache.change7d, max_len=6).out,
            'price_change_percentage_14d_in_currency': crypto_lookup.DigitLimit(load_cache.change14d, max_len=6).out,
            'price_change_percentage_30d_in_currency': crypto_lookup.DigitLimit(load_cache.change30d, max_len=6).out,
            'price_change_percentage_200d_in_currency': crypto_lookup.DigitLimit(load_cache.change200d, max_len=6).out,
            'price_change_percentage_1y_in_currency': crypto_lookup.DigitLimit(load_cache.change1y, max_len=6).out,
            'sparkline_in_7d': (sparkline.sparkline(data=spark), crypto_lookup.DigitLimit(max(spark), 
                                max_len=10).out, crypto_lookup.DigitLimit(min(spark), max_len=10).out)
          }

          num = float(coin_quantity) * float(cached_coin['current_price'])
          coin_value = crypto_lookup.DigitLimit(num, max_len=10).out
          user_currency_data.append((cached_coin, float(coin_quantity), coin_value))
        else:
          query_ids.append((coin_id, coin_quantity))

    if len(query_ids) > 0:
      try:
        query_list = [_id[0] for _id in query_ids]
        query_string = cache.create_id_query_string([query_list])
        query_data = cache.query_market_data(query_string)
        cache.add_to_currency_cache(query_data)
        for data in query_data:
          for k in range(len(query_ids)):
            if data['id'] == query_ids[k][0]:
              coin_quantity = query_ids[k][1]
          
          data['current_price_usd'] = crypto_lookup.DigitLimit(data['current_price'], max_len=10).out
          data['current_price'] = apply_conversion_rate(num=data['current_price'], rate=usd_rate, max_digits=10)
          data['price_change_percentage_1h_in_currency'] = crypto_lookup.DigitLimit(data['price_change_percentage_1h_in_currency'], max_len=6).out
          data['price_change_percentage_24h_in_currency'] = crypto_lookup.DigitLimit(data['price_change_percentage_24h_in_currency'], max_len=6).out
          data['price_change_percentage_7d_in_currency'] = crypto_lookup.DigitLimit(data['price_change_percentage_7d_in_currency'], max_len=6).out
          data['price_change_percentage_14d_in_currency'] = crypto_lookup.DigitLimit(data['price_change_percentage_14d_in_currency'], max_len=6).out
          data['price_change_percentage_30d_in_currency'] = crypto_lookup.DigitLimit(data['price_change_percentage_30d_in_currency'], max_len=6).out
          data['price_change_percentage_200d_in_currency'] = crypto_lookup.DigitLimit(data['price_change_percentage_200d_in_currency'], max_len=6).out
          data['price_change_percentage_1y_in_currency'] = crypto_lookup.DigitLimit(data['price_change_percentage_1y_in_currency'], max_len=6).out
          spark = data['sparkline_in_7d']
          if type(spark) == dict:
            spark = data['sparkline_in_7d']['price']
          data['sparkline_in_7d'] = (sparkline.sparkline(data=spark), crypto_lookup.DigitLimit(max(spark), max_len=10).out, crypto_lookup.DigitLimit(min(spark), max_len=10).out)

          num = float(coin_quantity) * float(data['current_price'])
          coin_value = crypto_lookup.DigitLimit(num, max_len=10).out
          user_currency_data.append((data, float(coin_quantity), coin_value))
      except Exception as e:
        print_stderr(f"load_favorites_data: {e}")
    return sorted(user_currency_data, key = lambda i: i[0]['name'])
  return None  


def favorites_check(to_check):
  check_list = []
  check_result = []
  if 'favorites' in session:
    for item in session['favorites']:
      check_list.append(item)
  for coin in to_check:
    if str(coin['id']).lower() in check_list:
      check_result.append(True)
    else:
      check_result.append(False)
  return check_result


def add_to_favorites(to_add):
  default_num = 0
  try:
    cache_id = CurrencyCache.query.filter_by(coin_id=to_add).first()
  except Exception as e:
    print_stderr(f"add_to_favorites {to_add}: {e}")
    cache_id = None
  if cache_id:
    new_currency = Currency(coin_id=cache_id.coin_id,
                        name=cache_id.name,
                        symbol=cache_id.symbol,
                        quantity=default_num,
                        value=default_num,
                        cache_id=cache_id.id,
                        user_id=current_user.id)
    db.session.add(new_currency)
    db.session.commit()

    session.pop('favorites', None)
    return True
  return False
  

def remove_from_favorites(to_remove):
  to_remove = to_remove.lower()
  to_remove_id = None
  try:
    for currency in current_user.currencies:
      if currency.coin_id == to_remove:
        to_remove_id = currency.id
    if to_remove_id:
      coin = Currency.query.get(to_remove_id)
      if coin.user_id == current_user.id:
        db.session.delete(coin)
        db.session.commit()
        session.pop('favorites', None)
        return True
    return False
  except Exception as e:
    print_stderr(f"remove_from_favorites: {e}")
    return False


def load_dashboard_summary(currency_locale):
  if current_user.is_authenticated:
    usd_rate = convert_currency(currency_locale)
    dashboard_summary = {
      'value': 0,
      'change24h': 0,
      'change7d': 0,
      'change30d': 0
    }
  
    if current_user.role != "guest":
      if current_user.value:
        dashboard_summary['value'] = apply_conversion_rate(num=current_user.value, rate=usd_rate, max_digits=10)
      if current_user.change24h:
        dashboard_summary['change24h'] = current_user.change24h
      if current_user.change7d:
        dashboard_summary['change7d'] = current_user.change7d
      if current_user.change30d:
        dashboard_summary['change30d'] = current_user.change30d
    return dashboard_summary
  return None
  

def update_dashboard_summary(update_list):
  try:
    new_value = 0
    _24hour = []
    _7day = []
    _30day = []
    for item in update_list:
      usd_val = float(item[1]) * float(item[0]['current_price_usd'])
      val = {
      'item_val': usd_val,
      'item_quant': item[1],
      'item_24h': item[0]['price_change_percentage_24h_in_currency'],
      'item_7d': item[0]['price_change_percentage_7d_in_currency'],
      'item_30d': item[0]['price_change_percentage_30d_in_currency'] }

      for key, value in val.items():
        if value is None:
          val[key] = 0.0

      new_value += json.loads(str(val['item_val']))
      _24hour.append((float(val['item_val']), float(val['item_24h'])))
      _7day.append((float(val['item_val']), float(val['item_7d'])))
      _30day.append((float(val['item_val']), float(val['item_30d'])))

    current_user.value = new_value
    current_user.change24h = weighted_percent(_24hour)
    current_user.change7d = weighted_percent(_7day)
    current_user.change30d = weighted_percent(_30day)
    db.session.commit()
    return True
  except Exception as e:
    print_stderr(f"update_dashboard_summary: {e}")
    return False


def weighted_percent(val_list): #list of tuples
  current = 0
  previous = 0
  for item in val_list:
    current += item[0]
    previous += item[0] / ((100 + item[1])/100)

  if previous != 0:
    new_percent = (current - previous) / previous * 100
    return new_percent
  return 0


def convert_currency(convert_to):
  c = CurrencyConverter(decimal=True)
  base = 1
  try:
    return c.convert(base, 'USD', convert_to)
  except:
    return base


def apply_conversion_rate(num, rate, max_digits):
  if num > 0:
    new_num = float(str(float(num) * float(rate)).strip('0'))
    return crypto_lookup.DigitLimit(new_num, max_len=max_digits).out
  return 0


def currency_cache_query(search):
  id_check = CurrencyCache.query.filter_by(coin_id=search).all()
  name_check = CurrencyCache.query.filter_by(name=search).all()
  symbol_check = CurrencyCache.query.filter_by(symbol=search).all()
  ids_to_check = id_check + name_check + symbol_check
  ids_to_query = []
  for _id in ids_to_check:
    id_check = _id.coin_id
    if id_check not in ids_to_query:
      ids_to_query.append(id_check)
  if len(ids_to_query) > 0:
    return ids_to_query
  return None



def init_user_settings():
  if not current_user.is_authenticated:
    user_settings = {
      'timezone':'UTC',
      'displaycurrency':'USD',
      'dashboard': {
        'grid':True,
        'table':False,
        'sparkline':False,
        '1hour':False,
        '24hours':True,
        '7days':True,
        '14days':False,
        '30days':True,
        '200days':False,
        '1year':False,
        'quantity':True,
        'netvalue':True
      },
      'search': {
        'sparkline':True,
        '1hour':True,
        '24hours':True,
        '7days':True,
        '14days':False,
        '30days':True,
        '200days':False,
        '1year':True,
      }
    }
  elif current_user.settings is not None:
    user_settings = json.loads(current_user.settings)
    if 'search' not in user_settings:
      user_settings['dashboard']['sparkline'] = False
      user_settings['dashboard']['1hour'] = False
      user_settings['dashboard']['14days'] = False
      user_settings['dashboard']['200days'] = False
      user_settings['dashboard']['1year'] = False

      user_settings['search'] = {
        'sparkline':True,
        '1hour':True,
        '24hours':True,
        '7days':True,
        '14days':False,
        '30days':True,
        '200days':False,
        '1year':True,
      }
      current_user.settings = json.dumps(user_settings)
      db.session.commit()
  return user_settings


def get_time(timezone):
  utc_now = pytz.utc.localize(datetime.utcnow())
  if current_user.is_authenticated:
    return utc_now.astimezone(pytz.timezone(timezone)).strftime("%m/%d/%Y %H:%M:%S")
  else:
    return utc_now.strftime("%m/%d/%Y %H:%M:%S")



@views.route('/', methods=['GET', 'POST'])
def redirect_to_home():
  return redirect(url_for('views.home'))


@views.route('/home', methods=['GET', 'POST'])
def home():
  search_results = None
  in_favorites = None
  user_settings = init_user_settings()
  session['displaycurrency'] = user_settings['displaycurrency']
  time = get_time(user_settings['timezone'])
  usd_rate = convert_currency(session['displaycurrency'])
  active_table = "price"

  top_1h = CurrencyCache.query.order_by(desc(CurrencyCache.change1h)).limit(1).first()
  top_24h = CurrencyCache.query.order_by(desc(CurrencyCache.change24h)).limit(1).first()
  top_7d = CurrencyCache.query.order_by(desc(CurrencyCache.change7d)).limit(1).first()
  top_30d = CurrencyCache.query.order_by(desc(CurrencyCache.change30d)).limit(1).first()
  top_200d = CurrencyCache.query.order_by(desc(CurrencyCache.change200d)).limit(1).first()
  top_1y = CurrencyCache.query.order_by(desc(CurrencyCache.change1y)).limit(1).first()

  top_1h_growth = {
    'id': top_1h.coin_id.capitalize(),
    'graph': sparkline.market_graph(coin_id=top_1h.coin_id, interval='hour', time_range=12, figsize=(20,6), class_add="d-block w-100"),
    'current_price': apply_conversion_rate(num=top_1h.price, rate=usd_rate, max_digits=10),
    'change': crypto_lookup.DigitLimit(top_1h.change1h, max_len=6).out
  }
  top_24h_growth = {
    'id': top_24h.coin_id.capitalize(),
    'graph': sparkline.market_graph(coin_id=top_24h.coin_id, interval='hour', time_range=24, figsize=(20,6), class_add="d-block w-100"),
    'current_price': apply_conversion_rate(num=top_24h.price, rate=usd_rate, max_digits=10),
    'change': crypto_lookup.DigitLimit(top_24h.change24h, max_len=6).out
  }
  top_7d_growth = {
    'id': top_7d.coin_id.capitalize(),
    'graph': sparkline.market_graph(coin_id=top_7d.coin_id, interval='day', time_range=7, figsize=(20,6), class_add="d-block w-100"),
    'current_price': apply_conversion_rate(num=top_7d.price, rate=usd_rate, max_digits=10),
    'change': crypto_lookup.DigitLimit(top_7d.change24h, max_len=6).out
  }
  top_30d_growth = {
    'id': top_30d.coin_id.capitalize(),
    'graph': sparkline.market_graph(coin_id=top_30d.coin_id, interval='day', time_range=30, figsize=(20,6), class_add="d-block w-100"),
    'current_price': apply_conversion_rate(num=top_30d.price, rate=usd_rate, max_digits=10),
    'change': crypto_lookup.DigitLimit(top_30d.change24h, max_len=6).out
  }
  top_200d_growth = {
    'id': top_200d.coin_id.capitalize(),
    'graph': sparkline.market_graph(coin_id=top_200d.coin_id, interval='day', time_range=200, figsize=(20,6), class_add="d-block w-100"),
    'current_price': apply_conversion_rate(num=top_200d.price, rate=usd_rate, max_digits=10),
    'change': crypto_lookup.DigitLimit(top_200d.change24h, max_len=6).out
  }
  top_1y_growth = {
    'id': top_1y.coin_id.capitalize(),
    'graph': sparkline.market_graph(coin_id=top_1y.coin_id, interval='year', time_range=1, figsize=(20,6), class_add="d-block w-100"),
    'current_price': apply_conversion_rate(num=top_1y.price, rate=usd_rate, max_digits=10),
    'change': crypto_lookup.DigitLimit(top_1y.change24h, max_len=6).out
  }
  carousel = {
    'top_1h_growth': top_1h_growth,
    'top_24h_growth': top_24h_growth,
    'top_7d_growth': top_7d_growth,
    'top_30d_growth': top_30d_growth,
    'top_200d_growth': top_200d_growth,
    'top_1y_growth': top_1y_growth,
  }

  if request.method == 'POST':
    if 'search' in request.form:
      query = str(request.form['search']).lower()
      search_results = search(query)
      if current_user.is_authenticated:
        in_favorites = favorites_check(search_results)
                              
    elif 'add_favorites' in request.form:
      to_add = request.form['add_favorites']

      if current_user.role == "guest":
        if len(current_user.currencies) < 6:
          session.pop('_flashes', None)
          added_to_favorites = add_to_favorites(to_add)
        else:
           added_to_favorites = False
           flash("Guest account can only have 6 favorites.", category='error')
      else:
        added_to_favorites = add_to_favorites(to_add)
        session.pop('_flashes', None)

      if added_to_favorites:
        flash(f"{to_add} has been added to favorites!", category='success')
      elif current_user.role != "guest":
        flash("Oops! Something went wrong!", category='error')

    elif 'table_switch' in request.form:
      active_table = request.form['table_switch']

  if active_table == "price":
    table_data = CurrencyCache.query.order_by(desc(CurrencyCache.price)).limit(25).all()
  if active_table == "change1h":
    table_data = CurrencyCache.query.order_by(desc(CurrencyCache.change1h)).limit(25).all()
  if active_table == "change24h":
    table_data = CurrencyCache.query.order_by(desc(CurrencyCache.change24h)).limit(25).all()
  if active_table == "change7d":
    table_data = CurrencyCache.query.order_by(desc(CurrencyCache.change7d)).limit(25).all()
  if active_table == "change30d":
    table_data = CurrencyCache.query.order_by(desc(CurrencyCache.change30d)).limit(25).all()
  if active_table == "change200d":
    table_data = CurrencyCache.query.order_by(desc(CurrencyCache.change200d)).limit(25).all()
  if active_table == "change1y":
    table_data = CurrencyCache.query.order_by(desc(CurrencyCache.change1y)).limit(25).all()

  table = []
  for coin in table_data:
    table.append(
      {
        'coin_id': coin.coin_id,
        'symbol': coin.symbol,
        'price': crypto_lookup.DigitLimit(coin.price, max_len=12).out,
        'change1h': crypto_lookup.DigitLimit(coin.change1h, max_len=12).out,
        'change24h': crypto_lookup.DigitLimit(coin.change24h, max_len=12).out,
        'change7d': crypto_lookup.DigitLimit(coin.change7d, max_len=12).out,
        'change30d': crypto_lookup.DigitLimit(coin.change30d, max_len=12).out,
        'change200d': crypto_lookup.DigitLimit(coin.change200d, max_len=12).out,
        'change1y': crypto_lookup.DigitLimit(coin.change1y, max_len=12).out
      }
    )

  return render_template("home.html", search_results=search_results, user=current_user, in_favorites=in_favorites, 
                          settings=user_settings, table=table, time=time, carousel=carousel)



@views.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
  stopwatch = timer()
  search_results = None
  sorted_favorites = None
  in_favorites = False

  user_settings = init_user_settings()
  time = get_time(user_settings['timezone'])
  session['displaycurrency'] = user_settings['displaycurrency']
  dashboard_summary = load_dashboard_summary(user_settings['displaycurrency'])

  if current_user.is_authenticated:
    if len(current_user.currencies) > 0:
      sorted_favorites = load_favorites_data()
      try:
        if current_user.role != "guest":
          update_dashboard_summary(sorted_favorites)
        dashboard_summary = load_dashboard_summary(session['displaycurrency'])
      except Exception as e:
        print_stderr(f"update_dashboard_summary(sorted_favorites): {e}")

    else:
      session.pop('_flashes', None)
      flash("Your Dashboard is empty! Use the search bar to find and add cryptocurrencies.", category='error')

    stopwatch = timer(stopwatch, f'Initial load-in with {len(current_user.currencies)} currencies.')
  else:
    user_settings = None
    session['displaycurrency'] = "USD"

    if 'first_visit' not in session:
      session['first_visit'] = True
      session.pop('_flashes', None)
      flash("Welcome to SearchCrypto: A Multi-Market Cryptocurrency Tracking Dashboard powered by CoinGecko and LunarCrush!", category='success')
    else:
      session.pop('_flashes', None)
      flash("Use the Search bar above to get started, or sign-up/login to save cryptos to your Dashboard. You may also try out our Guest Account below! ", category='success')

    stopwatch = timer(stopwatch, f'Initial load-in non-user.')
  
  if request.method == 'POST':
    if 'search' in request.form:
      query = str(request.form['search']).lower()
      stopwatch = timer(stopwatch, f'Search function "{query}": start')
      search_results = search(query)

      if current_user.is_authenticated:
        in_favorites = favorites_check(search_results)

      stopwatch = timer(stopwatch, f'Search function "{query}": finish')

    elif 'add_favorites' in request.form:
      stopwatch = timer(stopwatch, f'Add to Favorites function: start')
      to_add = request.form['add_favorites']

      if current_user.role == "guest":
        if len(current_user.currencies) < 6:
          session.pop('_flashes', None)
          added_to_favorites = add_to_favorites(to_add)
        else:
           added_to_favorites = False
           flash("Guest account can only have 6 favorites.", category='error')
      else:
        added_to_favorites = add_to_favorites(to_add)
        session.pop('_flashes', None)

      if added_to_favorites:
        flash(f"{to_add} has been added to favorites!", category='success')
      elif current_user.role != "guest":
         flash("Oops! Something went wrong!", category='error')

      stopwatch = timer(stopwatch, f'Add to Favorites function: finish')
      return redirect(url_for('views.dashboard'))

    elif 'remove_favorite' in request.form:
      stopwatch = timer(stopwatch, f'Remove from Favorites function: start')

      to_remove = request.form['remove_favorite'].lower()
      removed_from_fav = remove_from_favorites(to_remove)
      session.pop('_flashes', None)
      if removed_from_fav:
        flash(f"{to_remove} has been removed from favorites!", category='success')
      else:
        flash("Oops! Something went wrong!", category='error')

      stopwatch = timer(stopwatch, f'Remove from Favorites function: finish')
      return redirect(url_for('views.dashboard'))

    elif 'quantity' in request.form:
      stopwatch = timer(stopwatch, f'Adjust quantity function: start')

      to_save = request.form['to_save'].split(',')
      if request.form['quantity'] == "":
        quantity = 0
      else:
        quantity = float(request.form['quantity'])

      location = int(to_save[1])
      _coin = sorted_favorites[location][0]

      to_update = Currency.query.join(User, Currency.user_id==current_user.id).filter(Currency.coin_id==to_save[0].lower()).first()
      to_update.quantity = quantity
      value = float(_coin['current_price_usd']) * float(quantity)
      to_update.value = value
      db.session.commit()

      usd_rate = convert_currency(session['displaycurrency'])
      converted_val = apply_conversion_rate(num=(float(quantity) * float(_coin['current_price_usd'])), rate=usd_rate, max_digits=10)

      sorted_favorites[location] = (_coin, quantity, converted_val)

      try:
        update_dashboard_summary(sorted_favorites)
        dashboard_summary = load_dashboard_summary(session['displaycurrency'])
      except Exception as e:
        print_stderr(f"quantity in request.form: {e}")

      session.pop('favorites', None)

      stopwatch = timer(stopwatch, f'Adjust quantity function: finish')
      return render_template('dashboard.html', user=current_user, in_favorites=in_favorites, dashboard_summary=dashboard_summary,
                              favorites=sorted_favorites, time=time, settings=user_settings)

    if 'guest' in request.form:
      if not current_user.is_authenticated:
        email = 'guest@searchcrypto.app'
        password = 'guest@searchcrypto.app'

        user = User.query.filter_by(email=email).first()
        if user:
          if check_password_hash(user.password, password):
            session.pop('_flashes', None)
            flash('Logged in successfuly!', category='success')
            login_user(user, remember=True)
            return redirect(url_for('views.dashboard/'))

  stopwatch = timer(stopwatch, f'Everything ready to render.')
  return render_template('dashboard.html', user=current_user, search_results=search_results, in_favorites=in_favorites, 
                          favorites=sorted_favorites, time=time, settings=user_settings, dashboard_summary=dashboard_summary)



@views.route('/usersettings', methods=['GET', 'POST'])
@login_required
def usersettings():
  if current_user.is_authenticated:
    user_settings = init_user_settings()

    if request.method == 'POST':
      if 'search' in request.form:
        in_favorites = True
        query = str(request.form['search']).lower()
        search_results = search(query)

        utc_now = pytz.utc.localize(datetime.utcnow())
        time = utc_now.astimezone(pytz.timezone(str(user_settings['timezone']))).strftime("%m/%d/%Y %H:%M:%S")

        return render_template('usersettings.html', search_results=search_results, time=time,
                                user=current_user, firstName=current_user.firstName, email=current_user.email, settings=user_settings, in_favorites=in_favorites)

      changes = []
      timezone = str((request.form.get('timezone')))
      displaycurrency = str((request.form.get('displaycurrency')))

      if current_user.role != "guest" and 'search' not in request.form:
        email = str((request.form.get('email')))
        firstName = str((request.form.get('firstName')))
        password1 = str((request.form.get('password1')))
        password2 = str((request.form.get('password2')))

        if len(email) == 0:
          pass
        elif len(email) < 4:
          flash('Email must be greater than 4 characters', category='error')
        else:
          email_exists = User.query.filter_by(email=email).first()
          if email_exists:
            flash('Email already exists.', category='error')
          else:
            current_user.email = email
            changes.append("Email")

        if len(firstName) == 0:
          pass
        elif len(firstName) < 2:
          flash('Name must be at least 2 characters', category='error')
        elif current_user.firstName == firstName:
          flash(f'Name is already {firstName}', category='error')
        else:
          current_user.firstName = firstName
          changes.append("Display Name")

        if len(password1) == 0:
          pass
        elif password1 != password2:
          flash('Passwords do not match', category='error')
        elif len(password1) < 7:
          flash('Password must be at least 7 characters', category='error')
        elif check_password_hash(current_user.password, password1):
          flash('New password must be different than current password.', category='error')
        else:
          current_user.password=generate_password_hash(password1, method='sha256')
          changes.append("Password")

        layout = request.form.getlist('layout')
        for selection in layout:
          if 'grid' in selection:
            if user_settings['dashboard']['grid'] != True:
              user_settings['dashboard']['grid'] = True
              user_settings['dashboard']['table'] = False
              changes.append('Grid View')
          else:
            if user_settings['dashboard']['table'] != True:
              user_settings['dashboard']['grid'] = False
              user_settings['dashboard']['table'] = True
              changes.append('Table View')

        d_1hour = request.form.get('dash_1hour')
        d_24hours = request.form.get('dash_24hours')
        d_7days = request.form.get('dash_7days')
        d_14days = request.form.get('dash_14days')
        d_30days = request.form.get('dash_30days')
        d_200days = request.form.get('dash_200days')
        d_1year = request.form.get('dash_1year')
        quantity = request.form.get('quantity')
        netvalue = request.form.get('netvalue')
        d_sparkline = request.form.get('dash_sparkline')
        dash_settings = {'1hour':d_1hour, '24hours':d_24hours, '7days':d_7days, '14days':d_14days, '30days':d_30days, 
                        '200days':d_200days, '1year':d_1year, 'quantity':quantity, 'netvalue':netvalue, 'sparkline':d_sparkline}

        for key, value in dash_settings.items():
          if value is not None:
            if user_settings['dashboard'][key] != True:
              user_settings['dashboard'][key] = True
              if key.capitalize() not in changes:
                changes.append(key.capitalize() )
          else:
            if user_settings['dashboard'][key] != False:
              user_settings['dashboard'][key] = False
              if key.capitalize() not in changes:
                changes.append(key.capitalize() )


        s_1hour = request.form.get('search_1hour')
        s_24hours = request.form.get('search_24hours')
        s_7days = request.form.get('search_7days')
        s_14days = request.form.get('search_14days')
        s_30days = request.form.get('search_30days')
        s_200days = request.form.get('search_200days')
        s_1year = request.form.get('search_1year')
        s_sparkline = request.form.get('search_sparkline')
        search_settings = {'1hour':s_1hour, '24hours':s_24hours, '7days':s_7days, '14days':s_14days, 
                          '30days':s_30days, '200days':s_200days, '1year':s_1year, 'sparkline':s_sparkline}

        for key, value in search_settings.items():
          if value is not None:
            if user_settings['search'][key] != True:
              user_settings['search'][key] = True
              if key.capitalize() not in changes:
                changes.append(key.capitalize() )
          else:
            if user_settings['search'][key] != False:
              user_settings['search'][key] = False
              if key.capitalize() not in changes:
                changes.append(key.capitalize() )

      if timezone != "None":
        if timezone != user_settings['timezone']:
          user_settings['timezone'] = timezone
          changes.append('Timezone')
      elif user_settings['timezone'] == "None":
        user_settings['timezone'] = "UTC"
        changes.append('Timezone')

      if displaycurrency != "None":
        if timezone != user_settings['displaycurrency']:
          user_settings['displaycurrency'] = displaycurrency
          changes.append('Currency')
      elif user_settings['displaycurrency'] == "None":
        user_settings['displaycurrency'] = "USD"
        changes.append('Currency')

      if current_user.role != "guest":
        if 'delete' in request.form:
          return redirect(url_for('views.deleteaccount'))

      if len(changes) > 0:
        current_user.settings = json.dumps(user_settings)
        db.session.commit()
        user_settings = json.loads(current_user.settings)
        flash(f'Settings Saved: {", ".join(changes)}', category='success')

    return render_template('usersettings.html', user=current_user, firstName=current_user.firstName, email=current_user.email, settings=user_settings)


@views.route('/deleteaccount', methods=['GET', 'POST'])
@login_required
def deleteaccount():
  if request.method == 'POST':
    if current_user.is_authenticated:

      email = str(escape(request.form.get('email')))
      password1 = str(escape(request.form.get('password1')))

      if current_user.email == email:
        if check_password_hash(current_user.password, password1):
          db.session.delete(current_user)
          db.session.commit()
          return redirect(url_for('/'))
        else:
          flash('Incorrect Password, please try again.', category='error')
      else:
        flash('Incorrect Email, please try again.', category='error')

  return render_template('deleteaccount.html', user=current_user)