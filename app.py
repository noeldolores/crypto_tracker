from flask import Flask, render_template, request, url_for, redirect, session
from threading import Thread

from werkzeug.utils import redirect
import crypto_lookup


app = Flask(__name__)
app.secret_key = "test"

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
  if request.method == 'POST':
    session.pop('result', None)
    coin_query = request.form['coin_query']
    result, bad_query = run_search(coin_query)

  elif request.method == 'GET':
    if 'result' in session:
      result = session['result']
      bad_query = session['bad_query']
      session.pop('result', None)
    else:
      result = None
      bad_query = None

  return render_template('search.html', result=result, bad_query=bad_query)


@app.route("/favorites", methods=['POST', 'GET'])
def favorites():
  if request.method == 'POST':
    coin_query = request.form['coin_query']
    session['result'], session['bad_query'] = run_search(coin_query)

    return redirect(url_for("search"))

  elif request.method == 'GET':
    with open("favorites.txt", 'r') as f:
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