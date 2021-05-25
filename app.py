from flask import Flask, render_template, request, url_for, redirect, session
from threading import Thread
from pathlib import Path
#from werkzeug.utils import redirect
import crypto_lookup


app = Flask(__name__)
app.config.from_object("config.DevelopmentConfig")

FAVORITES = "favorites.txt"

def run_search(coin_query):
  coin = crypto_lookup.Query(coin_query)
  if coin.data is None:
    result = None
    bad_query = coin_query
  else:
    result = coin.data
    bad_query = None

  return result, bad_query
    

def reorder_list(correct_order=list, thread_output=list):
  corrected_list = []
  for i in range(len(correct_order)):
    coin_check = correct_order[i].lower()
    for coin in thread_output:
      if str(coin['name']).lower() == coin_check or str(coin['symbol']).lower() == coin_check or str(coin['id']).lower() == coin_check:
        corrected_list.append(coin)
        
  return corrected_list



@app.route("/")
def home():
  return redirect(url_for("search"))


@app.route("/search", methods=['POST', 'GET'])
def search():
  result = None
  bad_query = None
  in_favorites = False

  if 'favorites' not in session:
    with open(FAVORITES, 'r') as f:
      session['favorites'] = f.read().lower().splitlines()
      
  if request.method == 'POST':
    if 'coin_query' in request.form:
      if request.form['coin_query'] != "":
        session.pop('result', None)
        coin_query = request.form['coin_query']
        result, bad_query = run_search(coin_query)

        if str(result['name']).lower() in session['favorites'] or str(result['symbol']).lower() in session['favorites']:
          in_favorites = True

    elif "add_favorites" in request.form:
      to_add = request.form['add_favorites']
      with open(FAVORITES, 'a') as f:
        if to_add is not None:
          if Path(FAVORITES).stat().st_size > 0:
            f.write('\n' + to_add)
          else:
            f.write(to_add)

  elif request.method == 'GET':
    if 'result' in session:
      result = session['result']
      bad_query = session['bad_query']
      session.pop('result', None)
  return render_template('search.html', result=result, bad_query=bad_query, in_favorites=in_favorites)


@app.route("/favorites", methods=['POST', 'GET'])
def favorites():
  if 'favorites' in session:
    session.pop('favorites', None)

  if request.method == 'POST':
    if 'remove_favorite' in request.form:
      to_remove = request.form['remove_favorite'].lower().split(',')

      with open(FAVORITES, 'r') as f:
        temp_list = f.read().lower().splitlines()

      with open(FAVORITES, 'w') as f:
        index_check = 2
        for i in range(len(temp_list)):
          if temp_list[i] not in to_remove:
            if i == len(temp_list) - index_check:
              f.write(temp_list[i])
            else:
              f.write(temp_list[i] + '\n')
      return redirect(url_for("favorites"))

    elif 'coin_query' in request.form:
      coin_query = request.form['coin_query']
      session['result'], session['bad_query'] = run_search(coin_query)
      return redirect(url_for("search"))

  elif request.method == 'GET':
    if Path(FAVORITES).is_file() and Path(FAVORITES).stat().st_size > 0:
      with open(FAVORITES, 'r') as f:
        favorite_coins = f.read().splitlines()

        for i in range(len(favorite_coins)):
          if i == 0:
            threads = []
            thread_output = []
          process = Thread(target=crypto_lookup.Query, args=[favorite_coins[i], thread_output])
          process.start()
          threads.append(process)
        for process in threads:
          process.join()

        corrected_list = reorder_list(favorite_coins, thread_output)
      return render_template('favorites.html', favorites_list=corrected_list)

    else:
      return redirect(url_for("search"))