from flask import Flask, render_template, request, redirect
import crypto_lookup

app = Flask(__name__)

def run_search(coin_query):
    coin = crypto_lookup.LunarCrush(coin_query)
    if coin.data is not None:
        result = coin
        bad_query = None
    else:
        result = None
        bad_query = coin_query

    return result, bad_query
    

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
        #
        redirect('/')
        return search(result, bad_query)

    favorites_list = []
    with open("favorites.txt", 'r') as f:
        favorite_coins = f.readlines()
        for coin in favorite_coins:
            x = crypto_lookup.LunarCrush(coin)
            if x.data is not None:
                favorites_list.append(x.data)
    return render_template('favorites.html', favorites_list=favorites_list)