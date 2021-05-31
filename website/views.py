from flask import Blueprint, request, flash, session, render_template, redirect, url_for, escape
from flask_login import current_user
from threading import Thread
from datetime import datetime
from . import db
from .models import Currency, CoinGeckoDb
from . import crypto_lookup


views = Blueprint('views', __name__)


def reorder_list(correct_order=list, thread_output=list):
  corrected_list = []
  for i in range(len(correct_order)):
    coin_check = correct_order[i].lower()
    for coin in thread_output:
      if str(coin['name']).lower() == coin_check or str(coin['symbol']).lower() == coin_check or str(coin['id']).lower() == coin_check:
        corrected_list.append(coin)
  return corrected_list


def load_favorites_data(current_favorites):
  if len(current_user.currencies) > 0:
    verbose_favorites = []
    threads = []
    for i in range(len(current_favorites)):
      coin_query = coinGeckoDB_query(current_favorites[i])
      process = Thread(target=crypto_lookup.Query, args=[(coin_query.coinSymbol, coin_query.coinID), verbose_favorites])
      process.start()
      threads.append(process)
    for process in threads:
      process.join()
    return reorder_list(current_favorites, verbose_favorites)


def currency_search(to_search):
  search = to_search.lower()
  coin_query = coinGeckoDB_query(search)
  if not coin_query:
    coin_list = crypto_lookup.CoinGecko(refresh=True)
    if coin_list is not None:
      if search in coin_list.all_coins or CoinGeckoDb.query.count() == 0:
        db.session.query(CoinGeckoDb).delete()
        db.session.commit()
        for coin in coin_list.all_coins:
          new_coin = CoinGeckoDb(coinID=coin['id'].lower(), coinSymbol=coin['symbol'].lower(), coinName=coin['name'].lower())
          db.session.add(new_coin)
        db.session.commit()
        coin_query = coinGeckoDB_query(search)
  if coin_query is None:
    result = None
    bad_query = search
    session.pop('_flashes', None)
    flash(f"{search} is not valid or not yet tracked. Please try a new search.", category='error')
  else:
    coin = crypto_lookup.Query((coin_query.coinSymbol, coin_query.coinID))
    result = coin.data
    bad_query = None
  return result, bad_query


def favorites_check(to_check):
  if to_check:
    if len(current_user.currencies) > 0:
      if str(to_check['name']).lower() in session['favorites'] or str(to_check['symbol']).lower() in session['favorites']:
        return True
  return False


def coinGeckoDB_query(search):
  coinName_check = CoinGeckoDb.query.filter_by(coinName=search).first()
  coinID_check = CoinGeckoDb.query.filter_by(coinID=search).first()
  coinSymbol_check = CoinGeckoDb.query.filter_by(coinSymbol=search).first()
  check_list = [coinName_check, coinID_check, coinSymbol_check]
  for i in range(len(check_list)):
    if check_list[i] is not None:
      return check_list[i]
  return None


def add_to_favorites(to_add):
  currency = to_add.lower()
  try:
    new_currency = Currency(name=currency, user_id=current_user.id)
    db.session.add(new_currency)
    db.session.commit()
    if 'favorites' in session:
      temp_list = session['favorites']
    else:
      temp_list = []
    temp_list.append(currency)
    session['favorites'] = sorted(temp_list)
    return True
  except Exception as e:
    print(vars(e))
    return False


def remove_from_favorites(to_remove):
  to_remove = to_remove.lower()
  try:
    for currency in current_user.currencies:
      if currency.name == to_remove:
        to_remove_id = currency.id

    coin = Currency.query.get(to_remove_id)
    if coin:
      if coin.user_id == current_user.id:
        db.session.delete(coin)
        db.session.commit()
        session.pop('favorites', None)
        return True
  except Exception as e:
    print(vars(e))
    return False
  


@views.route('/', methods=['GET', 'POST'])
def home():
  result = None
  bad_query = None
  in_favorites = False
  sorted_favorites = None
  
  if current_user.is_authenticated:
    if len(current_user.currencies) > 0:
      if 'favorites' not in session:
        favorites_list = []
        for currency in current_user.currencies:
          favorites_list.append(currency.name)
        session['favorites'] = sorted(favorites_list, key=str.lower)

      sorted_favorites = load_favorites_data(session['favorites'])
    else:
      flash("Your Dashboard is empty! Use the search bar to find and add cryptocurrencies.", category='error')
  else:
    flash("You must log in to use some features, though you may still search for currencies!", category='success')

  if request.method == 'POST':
    if 'search' in request.form:
      result, bad_query = currency_search(str(escape(request.form['search'])))
      
      if current_user.is_authenticated:
        in_favorites = favorites_check(result)

    elif 'add_favorites' in request.form:
      added_to_favorites = add_to_favorites(request.form['add_favorites'])
      session.pop('_flashes', None)
      if added_to_favorites:
        flash(f"{request.form['add_favorites']} has been added to favorites!", category='success')
      else:
        flash("Oops! Something went wrong!", category='error')
      return redirect(url_for('views.home'))

    elif 'remove_favorite' in request.form:
      removed_from_fav = remove_from_favorites(request.form['remove_favorite'])
      session.pop('_flashes', None)
      if removed_from_fav:
        flash(f"{request.form['remove_favorite']} has been removed from favorites!", category='success')
      else:
        flash("Oops! Something went wrong!", category='error')
      return redirect(url_for('views.home'))

  time = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

  return render_template('home.html', user=current_user, result=result, bad_query=bad_query, in_favorites=in_favorites, favorites=sorted_favorites, time=time)