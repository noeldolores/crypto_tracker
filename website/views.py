from flask import Blueprint, request, flash, session, render_template, redirect, url_for, escape
from flask_login import current_user, login_required, login_user
from threading import Thread
from datetime import datetime
import json
from currency_converter import CurrencyConverter
import pytz
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import Currency, CoinGeckoDb, User
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
    new_currency = Currency(name=currency, user_id=current_user.id, quantity=0, value=0)
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


def convert_currency(convert_to):
  c = CurrencyConverter(decimal=True)
  try:
    return c.convert(1, 'USD', convert_to)
  except:
    return 1



@views.route('/', methods=['GET', 'POST'])
def redirect_to_home():
  return redirect(url_for('views.home'))


@views.route('/home', methods=['GET', 'POST'])
def home():
  result = None
  bad_query = None
  in_favorites = False
  sorted_favorites = None
  show_time = False
  usd_rate = 1

  if current_user.is_authenticated:
    if current_user.settings is not None:
      user_settings = json.loads(current_user.settings)
    else:
      user_settings = {
        'timezone':'UTC',
        'displaycurrency':'USD',
        'dashboard': {
          'grid':True,
          'table':False,
          '24hours':True,
          '7days':True,
          '30days':True,
          'quantity':False,
          'netvalue':False
        }
      }

    usd_rate = convert_currency(str(user_settings['displaycurrency']))

    if len(current_user.currencies) > 0:
      show_time = True
      if 'favorites' not in session:
        favorites_list = []
        for currency in current_user.currencies:
          favorites_list.append(currency.name)
        session['favorites'] = sorted(favorites_list, key=str.lower)
      sorted_favorites = load_favorites_data(session['favorites'])
      for item in sorted_favorites:
        num = float(item['price'])/float(usd_rate)
        item['price'] = crypto_lookup.DigitLimit(num, max_len=10).out
    else:
      session.pop('_flashes', None)
      flash("Your Dashboard is empty! Use the search bar to find and add cryptocurrencies.", category='error')
  else:
    if 'first_visit' not in session:
      session['first_visit'] = True
      session.pop('_flashes', None)
      flash("Welcome to SearchCrypto: A Multi-Market Cryptocurrency Tracking Dashboard powered by CoinGecko and LunarCrush!", category='success')
    else:
      session.pop('_flashes', None)
      flash("Use the Search bar above to get started, or sign-up/login to save cryptos to your Dashboard. You may also try out our Guest Account below! ", category='success')

  if request.method == 'POST':
    if 'search' in request.form:
      result, bad_query = currency_search(request.form['search'])
      if result is not None:
        num = float(result['price'])/float(usd_rate)
        result['price'] = crypto_lookup.DigitLimit(num, max_len=10).out

      if current_user.is_authenticated:
        show_time = True
        in_favorites = favorites_check(result)

    elif 'add_favorites' in request.form:
      if current_user.role == "guest":
        if len(current_user.currencies) < 6:
          session.pop('_flashes', None)
          added_to_favorites = add_to_favorites(request.form['add_favorites'])
        else:
          added_to_favorites = False
          flash("Guest account can only have 6 favorites.", category='error')
      else:
        added_to_favorites = add_to_favorites(request.form['add_favorites'])
        session.pop('_flashes', None)
      if added_to_favorites:
        flash(f"{request.form['add_favorites']} has been added to favorites!", category='success')
      elif current_user.role != "guest":
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
            return redirect(url_for('views.home'))

  utc_now = pytz.utc.localize(datetime.utcnow())
  if current_user.is_authenticated:
    time = utc_now.astimezone(pytz.timezone(str(user_settings['timezone']))).strftime("%m/%d/%Y %H:%M:%S")
  else:
    time = utc_now.strftime("%m/%d/%Y %H:%M:%S")
    user_settings = None

  return render_template('home.html', user=current_user, result=result, bad_query=bad_query, in_favorites=in_favorites, favorites=sorted_favorites, time=time, show_time=show_time, settings = user_settings)


@views.route('/usersettings', methods=['GET', 'POST'])
@login_required
def usersettings():
  show_time = False
  if current_user.is_authenticated:
    if current_user.settings is not None:
      user_settings = json.loads(current_user.settings)
    else:
      user_settings = {
        'timezone':'UTC',
        'displaycurrency':'USD',
        'dashboard': {
          'grid':True,
          'table':False,
          '24hours':True,
          '7days':True,
          '30days':True,
          'quantity':False,
          'netvalue':False
        }
      }
    # if str(user_settings['timezone']) == None:
    #   user_settings['timezone'] = "UTC"
    #   current_user.settings = json.dumps(user_settings)
    #   db.session.commit()
    #   user_settings = json.loads(current_user.settings)
    #   flash('Timezone reset!', category='success')
    # if str(user_settings['displaycurrency']) == None:
    #   user_settings['displaycurrency'] = "USD"
    #   current_user.settings = json.dumps(user_settings)
    #   db.session.commit()
    #   user_settings = json.loads(current_user.settings)
    #   flash('Display Currency reset!', category='success')

    if request.method == 'POST':
      if 'search' in request.form:
        result, bad_query = currency_search(request.form['search'])
        if result is not None:
          utc_now = pytz.utc.localize(datetime.utcnow())
          time = utc_now.astimezone(pytz.timezone(str(user_settings['timezone']))).strftime("%m/%d/%Y %H:%M:%S")
          show_time = True

          usd_rate = convert_currency(str(user_settings['displaycurrency']))
          num = float(result['price'])/float(usd_rate)
          result['price'] = crypto_lookup.DigitLimit(num, max_len=10).out
          return render_template('usersettings.html', result=result, bad_query=bad_query, time=time, show_time=show_time,
                                  user=current_user, firstName=current_user.firstName, email=current_user.email, settings=user_settings)


      timezone = str((request.form.get('timezone')))
      displaycurrency = str((request.form.get('displaycurrency')))
      
      if current_user.role != "guest" and 'search' not in request.form:
        email = str((request.form.get('email')))
        firstName = str((request.form.get('firstName')))
        password1 = str((request.form.get('password1')))
        password2 = str((request.form.get('password2')))

        layout = request.form.getlist('layout')
        if len(layout) > 0:
          for selection in layout:
            if 'grid' in selection:
              user_settings['dashboard']['grid'] = True
              user_settings['dashboard']['table'] = False
            else:
              user_settings['dashboard']['grid'] = False
              user_settings['dashboard']['table'] = True
          current_user.settings = json.dumps(user_settings)
          db.session.commit()
          user_settings = json.loads(current_user.settings)

        _24hours = request.form.get('24hours')
        _7days = request.form.get('7days')
        _30days = request.form.get('30days')
        quantity = request.form.get('quantity')
        netvalue = request.form.get('netvalue')
        dash_settings = {'24hours':_24hours, '7days':_7days, '30days':_30days, 'quantity':quantity, 'netvalue':netvalue}

        commit = True
        for key, value in dash_settings.items():
          if value is not None:
            user_settings['dashboard'][key] = True
          else:
            user_settings['dashboard'][key] = False

        if commit:
          current_user.settings = json.dumps(user_settings)
          db.session.commit()
          user_settings = json.loads(current_user.settings)


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
            db.session.commit()
            user_settings = json.loads(current_user.settings)

        if len(firstName) == 0:
          pass
        elif len(firstName) < 2:
          flash('Name must be at least 2 characters', category='error')
        elif current_user.firstName == firstName:
          flash(f'Name is already {firstName}', category='error')
        else:
          current_user.firstName = firstName
          db.session.commit()
          user_settings = json.loads(current_user.settings)

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
          db.session.commit()
          user_settings = json.loads(current_user.settings)

      if timezone != "None" and str(user_settings['timezone']) != "None":
        if str(user_settings['timezone']) == timezone or timezone == "":
          pass
        else:
          user_settings['timezone'] = timezone
          current_user.settings = json.dumps(user_settings)
          db.session.commit()
          user_settings = json.loads(current_user.settings)
          flash('Timezone updated!', category='success')
      elif timezone == "None" and str(user_settings['timezone']) != "None":
        pass
      else:
        user_settings['timezone'] = "UTC"
        current_user.settings = json.dumps(user_settings)
        db.session.commit()
        user_settings = json.loads(current_user.settings)
        flash('Timezone reset!', category='success')

      if displaycurrency != "None" and str(user_settings['displaycurrency']) != "None":
        if str(user_settings['displaycurrency']) == displaycurrency:
          pass
        elif displaycurrency == "":
          pass
        else:
          user_settings['displaycurrency'] = displaycurrency
          current_user.settings = json.dumps(user_settings)
          db.session.commit()
          user_settings = json.loads(current_user.settings)
          flash('Display Currency updated!', category='success')
      elif displaycurrency == "None" and str(user_settings['displaycurrency']) != "None":
        pass
      else:
        user_settings['displaycurrency'] ="USD"
        current_user.settings = json.dumps(user_settings)
        db.session.commit()
        user_settings = json.loads(current_user.settings)
        flash('Display Currency reset!', category='success')

      if current_user.role != "guest":
        if 'delete' in request.form:
          return redirect(url_for('views.deleteaccount'))

    return render_template('usersettings.html', user=current_user, firstName=current_user.firstName, email=current_user.email, settings=user_settings)


@views.route('/deleteaccount', methods=['GET', 'POST'])
@login_required
def deleteaccount():
  show_time = False
  if request.method == 'POST':
    if current_user.is_authenticated:

      email = str(escape(request.form.get('email')))
      password1 = str(escape(request.form.get('password1')))

      if current_user.email == email:
        if check_password_hash(current_user.password, password1):
          db.session.delete(current_user)
          db.session.commit()
          return redirect(url_for('views.home'))
        else:
          flash('Incorrect Password, please try again.', category='error')
      else:
        flash('Incorrect Email, please try again.', category='error')

  return render_template('deleteaccount.html', user=current_user, show_time=show_time)