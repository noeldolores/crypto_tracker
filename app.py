from flask import Flask, render_template, request
import crypto_lookup

app = Flask(__name__)

@app.route("/", methods=['POST', 'GET'])
def search(result=None, bad_query=None):
    if request.method == 'POST':
        coin_query = request.form['coin_query']
        coin = crypto_lookup.LunarCrush(coin_query)
        if coin.data is not None:
            result = coin
            bad_query = None

            return render_template('search.html', result=result, bad_query=bad_query)
        else:
            bad_query = coin_query

    return render_template('search.html', result=result, bad_query=bad_query)