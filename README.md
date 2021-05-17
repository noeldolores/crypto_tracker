A personal use crypto tracker.

Requires the <a href="https://lunarcrush.com/developers/docs">LunarCrush API</a> to use.

Current features:<br/>
<ol>
<li>Uses <a href="https://lunarcrush.com/dashboard">LunarCrush</a> to query cryptocurrencies, outputting to command line or Flask app.</li>
<li>Ability to pass a either a single currency or a list of currencies as an argument for the command line output feature.</li>
<li>Connected Flask app to look up cryptocurrencies</li>
<li>Scrapes <a href="https://coinmarketcap.com/">CoinMarketCap</a> when necessary to allow searching by crypto's name or symbol/shorthand.</li>
</ol><br/>

Planned features:<br/>
<ol>
<li>Store 'favorited' currencies for quick querying with command line output.</li>
<li>Connected Flask app to act as a tracking dasboard.</li>
<li>Database to track historical data of tracked currencies.</li>
<li>Connect additional APIs to source data for currencies not available through LunarCrush.</li>
</ol><br/>

Example Outputs:<br/>
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
Flask App Interface<br/>

![Image of Flask Output](https://github.com/noeldolores/crypto_tracker/blob/master/images/flask_example.png)