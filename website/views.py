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



def load_favorites_data(current_favorites):
  if len(current_user.currencies) > 0:
    verbose_favorites = []
    threads = []
    for i in range(len(current_favorites)):
      coin_query = coinGeckoDB_query(current_favorites[i][0])
      process = Thread(target=crypto_lookup.Query, args=[(coin_query.coinSymbol, coin_query.coinID), verbose_favorites])
      process.start()
      threads.append(process)
    for process in threads:
      process.join()
    return reorder_list(current_favorites, verbose_favorites)


def reorder_list(correct_order=list, thread_output=list):
  corrected_list = []
  usd_rate = convert_currency(str(session['displaycurrency']))
  
  for i in range(len(correct_order)):
    coin_check = correct_order[i][0].lower()
    coin_quant = float(correct_order[i][1])

    for coin in thread_output:
      if str(coin['name']).lower() == coin_check or str(coin['symbol']).lower() == coin_check or str(coin['id']).lower() == coin_check:
        num = float(coin['price'])/float(usd_rate)
        coin['price'] = crypto_lookup.DigitLimit(num, max_len=10).out
        quant_value = crypto_lookup.DigitLimit(coin_quant * num, max_len=10).out
        corrected_list.append((coin, coin_quant, quant_value))
  return corrected_list


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
  check_list = []
  for item in session['favorites']:
    check_list.append(item[0])
  if to_check:
    if len(current_user.currencies) > 0:
      if str(to_check['name']).lower() in check_list or str(to_check['symbol']).lower() in check_list:
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
    quantity = 0
    new_currency = Currency(name=currency, user_id=current_user.id, quantity=quantity, value=0)
    db.session.add(new_currency)
    db.session.commit()
    if 'favorites' in session:
      temp_list = session['favorites']
    else:
      temp_list = []
    temp_list.append((currency, quantity))
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
  utc_now = pytz.utc.localize(datetime.utcnow())

  if current_user.is_authenticated:
    if current_user.settings is not None:
      user_settings = json.loads(current_user.settings)
      if 'displaycurrency' not in session:
        session['displaycurrency'] = user_settings['displaycurrency']
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
    time = utc_now.astimezone(pytz.timezone(str(user_settings['timezone']))).strftime("%m/%d/%Y %H:%M:%S")

    if len(current_user.currencies) > 0:
      show_time = True
      if 'favorites' not in session:
        favorites_list = []
        for currency in current_user.currencies:
          favorites_list.append((currency.name, currency.quantity))
        session['favorites'] = sorted(favorites_list)
      sorted_favorites = load_favorites_data(session['favorites'])
    else:
      session.pop('_flashes', None)
      flash("Your Dashboard is empty! Use the search bar to find and add cryptocurrencies.", category='error')
  else:
    time = utc_now.strftime("%m/%d/%Y %H:%M:%S")
    user_settings = None

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
        usd_rate = convert_currency(str(user_settings['displaycurrency']))
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

    elif 'quantity' in request.form:
      to_save = request.form['to_save'].split(',')
      quantity = request.form['quantity']

      location = int(to_save[1])
      _coin = sorted_favorites[location][0]

      to_update = Currency.query.join(User, Currency.user_id==current_user.id).filter(Currency.name==to_save[0].lower()).first()
      to_update.quantity = quantity
      to_update.value = float(_coin['price']) * float(quantity)

      db.session.commit()

      sorted_favorites[location] = (_coin, float(quantity), to_update.value)

      session.pop('favorites', None)
      return render_template('home.html', user=current_user, result=result, bad_query=bad_query, in_favorites=in_favorites, favorites=sorted_favorites, time=time, show_time=show_time, settings = user_settings)
       # test = current_user.currencies.filter(Currency.name==to_save[0].lower()).first()
      # print(test.name)
      #backref=db.backref('items', lazy='dynamic')



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

  # utc_now = pytz.utc.localize(datetime.utcnow())
  # if current_user.is_authenticated:
  #   time = utc_now.astimezone(pytz.timezone(str(user_settings['timezone']))).strftime("%m/%d/%Y %H:%M:%S")
  # else:
  #   time = utc_now.strftime("%m/%d/%Y %H:%M:%S")
  #   user_settings = None

  return render_template('home.html', user=current_user, result=result, bad_query=bad_query, in_favorites=in_favorites, favorites=sorted_favorites, time=time, show_time=show_time, settings = user_settings)


@views.route('/usersettings', methods=['GET', 'POST'])
@login_required
def usersettings():
  show_time = False
  if current_user.is_authenticated:
    try:
      user_settings = json.loads(current_user.settings)
    except:
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

        _24hours = request.form.get('24hours')
        _7days = request.form.get('7days')
        _30days = request.form.get('30days')
        quantity = request.form.get('quantity')
        netvalue = request.form.get('netvalue')
        dash_settings = {'24hours':_24hours, '7days':_7days, '30days':_30days, 'quantity':quantity, 'netvalue':netvalue}

        for key, value in dash_settings.items():
          if value is not None:
            if user_settings['dashboard'][key] != True:
              user_settings['dashboard'][key] = True
              changes.append(key.capitalize() )
          else:
            if user_settings['dashboard'][key] != False:
              user_settings['dashboard'][key] = False
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