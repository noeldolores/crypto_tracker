from flask import Flask, render_template, request, url_for, redirect, session
from threading import Thread
from pathlib import Path
from werkzeug.utils import redirect
import crypto_lookup


app = Flask(__name__)
app.config.from_object("config.DevelopmentConfig")

FAVORITES = Path("favorites.txt")

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
      if coin['name'].lower() == coin_check or coin['symbol'].lower() == coin_check or str(coin['id']).lower() == coin_check:
        corrected_list.append(coin)

  return corrected_list


@app.route("/")
def home():
  return redirect(url_for("search"))


@app.route("/search", methods=['POST', 'GET'])
def search():
  result = None
  bad_query = None

  if request.method == 'POST':
    if request.form['coin_query'] != "":
      session.pop('result', None)
      coin_query = request.form['coin_query']
      result, bad_query = run_search(coin_query)
    elif "add_favorites" in request.form:
      to_add = request.form['add_favorites']
      with open('favorites.txt', 'a') as f:
        if to_add is not None:
          if FAVORITES.stat().st_size > 0:
            f.write('\n' + to_add)
          else:
            f.write(to_add)

  elif request.method == 'GET':
    if 'result' in session:
      result = session['result']
      bad_query = session['bad_query']
      session.pop('result', None)

  return render_template('search.html', result=result, bad_query=bad_query)


@app.route("/favorites", methods=['POST', 'GET'])
def favorites():
  if request.method == 'POST':
    if 'remove_favorite' in request.form:
      with open('favorites.txt', 'r') as f:
        temp_list = f.read().splitlines()
      with open('favorites.txt', 'w') as f:
        for coin in temp_list:
          if coin.lower() not in request.form['remove_favorite'].split(','):
            if temp_list[-1] == coin:
              f.write(coin)
            else:
              f.write(coin + '\n')

      return redirect(url_for("favorites"))

    elif 'coin_query' in request.form:
      coin_query = request.form['coin_query']
      session['result'], session['bad_query'] = run_search(coin_query)

      return redirect(url_for("search"))


  elif request.method == 'GET':
    favorites_file = Path("favorites.txt")
    if favorites_file.is_file() and favorites_file.stat().st_size > 0:
      with open(favorites_file, 'r') as f:
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