from flask import Blueprint, request, flash, session, render_template, redirect, url_for
from flask_login import current_user
from threading import Thread
from . import db
from .models import Currency
import crypto_lookup


views = Blueprint('views', __name__)


def reorder_list(correct_order=list, thread_output=list):
  corrected_list = []
  for i in range(len(correct_order)):
    coin_check = correct_order[i].lower()
    for coin in thread_output:
      if str(coin['name']).lower() == coin_check or str(coin['symbol']).lower() == coin_check or str(coin['id']).lower() == coin_check:
        corrected_list.append(coin)
        
  return corrected_list


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
    else:
      flash("Your Dashboard is empty! Use the search bar to find and track cryptocurrencies.", category='error')

  if request.method == 'POST':
    if 'search' in request.form:
      search = request.form['search']
      coin = crypto_lookup.Query(search)
      if coin.data is None:
        bad_query = search
        flash(f"{search} is not valid. Please try a new search.", category='error')
      else:
        result = coin.data
      
      if current_user.is_authenticated:
        if result is not None:
          if len(current_user.currencies) > 0:
            if str(result['name']).lower() in session['favorites'] or str(result['symbol']).lower() in session['favorites']:
              in_favorites = True

    elif 'add_favorites' in request.form:
      currency = request.form['add_favorites'].lower()
      new_currency = Currency(name=currency, user_id=current_user.id)
      db.session.add(new_currency)
      db.session.commit()
      if 'favorites' in session:
        temp_list = session['favorites']
      else:
        temp_list = []
      temp_list.append(currency)
      session['favorites'] = sorted(temp_list)
      flash(f"{request.form['add_favorites']} has been added to favorites!", category='success')
      return redirect(url_for('views.home'))

    elif 'remove_favorite' in request.form:
      to_remove = request.form['remove_favorite'].lower()
      for currency in current_user.currencies:
        if currency.name == to_remove:
          to_remove_id = currency.id
      coin = Currency.query.get(to_remove_id)

      if coin:
        if coin.user_id == current_user.id:
            db.session.delete(coin)
            db.session.commit()
            session.pop('favorites', None)
            return redirect(url_for('views.home'))

  if current_user.is_authenticated:
    if len(current_user.currencies) > 0:
      verbose_favorites = []
      threads = []
      for i in range(len(session['favorites'])):
        process = Thread(target=crypto_lookup.Query, args=[session['favorites'][i], verbose_favorites])
        process.start()
        threads.append(process)
      for process in threads:
        process.join()

      #sorted_favorites = reorder_list(session['favorites'], verbose_favorites)
      sorted_favorites = []
      for i in range(len(session['favorites'])):
        coin_check = session['favorites'][i].lower()
        for coin in verbose_favorites:
          if str(coin['name']).lower() == coin_check or str(coin['symbol']).lower() == coin_check or str(coin['id']).lower() == coin_check:
            sorted_favorites.append(coin)
  else:
    flash("You must log in to use some features, though you may still search for currencies!", category='success')

  return render_template('home.html', user=current_user, result=result, bad_query=bad_query, in_favorites=in_favorites, favorites=sorted_favorites)