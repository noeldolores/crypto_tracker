from flask import Flask, render_template, request
from threading import Thread
import crypto_lookup


app = Flask(__name__)


def run_search(coin_query):
  coin = crypto_lookup.Query(coin_query)
  if coin.data is None:
    result = None
    bad_query = coin_query
  else:
    result = coin
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



@app.route("/", methods=['POST', 'GET'])
def search(result=None, bad_query=None):
  if request.method == 'POST':
    coin_query = request.form['coin_query']
    result, bad_query = run_search(coin_query)

  return render_template('search.html', result=result, bad_query=bad_query)


@app.route("/favorites", methods=['POST', 'GET'])
def favorites():
  if request.method == 'POST':
    coin_query = request.form['coin_query']
    result, bad_query = run_search(coin_query)
      
    return render_template('search.html', result=result, bad_query=bad_query)

  if request.method == 'GET':
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