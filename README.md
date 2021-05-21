# A personal use crypto tracker.

<br/>
How to use:<br/>
<ol>
<li><a href="https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository">Clone</a> this repository.</li>
<li>Create a free account over at <a href="https://lunarcrush.com/">LunarCrush</a>, and generate your API Key <a href="https://lunarcrush.com/developers/docs">here.</a>.</li>
<li>In your project directory create a file named '.env', and on the first line write: LUNARCRUSH_API_KEY=YOURKEYHERE</li>
<li>Create and activate a virtual environment and run: pip install -r requirements.txt</li>
<li>In your project directory create a file named 'favorites.txt'. On each line, add Cryptos that you would like to auto-load upon visiting the */favorites page of your Flask app.</li>
<li>To use the command-line interface, run: ./command_line.py</li>
<li>To start the Flask interface, with a virtual environment run: source /start_app.sh</li>
</ol>


<br/>
Current features:<br/>
<ol>
<li>Uses <a href="https://lunarcrush.com/dashboard">LunarCrush</a> to query cryptocurrency information, outputting results to the command line or Flask app.</li>
<li>Ability to pass a either a single currency or a list of currencies as an argument for the command line output feature.</li>
<li>Scrapes <a href="https://coinmarketcap.com/">CoinMarketCap</a> when necessary to allow searching by crypto's name or symbol/shorthand.</li>
<li>The */favorites page reads a list of currencies from your local favorites.txt file to create a dashboard for viewing your choices with ease.</li>
<li>Uses CoinGecko as a backup database for coins not on LunarCrush.</li>
</ol><br/>

Planned features:<br/>
<ol>
<li>Add a 'go to favorites' button.</li>
<li>Add the ability to add and delete currencies from your 'favorites' within the Flask app interface.</li>
<li>Database to track historical data of tracked currencies from within an expanded dashboard.</li>
<li>Connect additional APIs to source data for currencies not available through LunarCrush.</li>
<li>Remove need for an API key using a suite of key-less sources.</li>
<li>Integrate Flask 2.0 async functions.</li>
</ol><br/>

## Example Outputs:<br/>
<br/>
Command Line Interface
<br/>

```
> ./command_line.py
> Enter one or more cryptos, comma-separated with no spaces:btc,doge,safemoon
{'name': 'Bitcoin', 'id': 1, 'symbol': 'BTC', 'price': 43531.62695627, 'price_btc': 1, 'percent_change_24h': -9.84, 'percent_change_7d': -23.66, 'percent_change_30d': -27.39, 'interval': 'day', 'open': 46622.50130081, 'close': 43857.82310945, 'high': 46788.92129675, 'low': 43190.60623945}
{'name': 'Dogecoin', 'id': 29, 'symbol': 'DOGE', 'price': 0.48784339, 'price_btc': 1.1206642712667e-05, 'percent_change_24h': -8.82, 'percent_change_7d': 1.73, 'percent_change_30d': 58.61, 'interval': 'day', 'open': 0.51932927, 'close': 0.4862366, 'high': 0.52152868, 'low': 0.46472414}
{'name': 'SafeMoon', 'id': 12242, 'symbol': 'SAFEMOON', 'price': 8.18e-06, 'price_btc': 1.87909356e-10, 'percent_change_24h': -8.04, 'percent_change_7d': -6.18, 'percent_change_30d': 319.99, 'interval': 'day', 'open': 8.26e-06, 'close': 8.34e-06, 'high': 8.87e-06, 'low': 7.86e-06}
```

<br/>
Flask App Interface:<br/>
<br/>
Search Result

![Image of Flask Output](https://github.com/noeldolores/crypto_tracker/blob/master/images/flask_example_search.png)
<br/>
Favorites Page

![Image of Flask Output](https://github.com/noeldolores/crypto_tracker/blob/master/images/flask_example_favorites.png)