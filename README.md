A personal use crypto tracker.

Current features:<br/>
<ol>
<li>Uses the <a href="https://lunarcrush.com/developers/docs#assets">LunarCrush API</a> to query cryptocurrencies, returning a command line output.</li>
<li>Ability to pass a either a single currency or a list of currencies as an argument for the command line output feature.</li>
<li>Connected Flask app to look up cryptocurrencies</li>
</ol><br/>

Planned features:<br/>
<ol>
<li>Store 'favorited' currencies for quick querying with command line output.</li>
<li>Connected Flask app to act as a tracking dasboard.</li>
<li>Database to track historical data of tracked currencies.</li>
<li>Connect additional APIs to source data for currencies not available through LunarCrush.</li>
</ol><br/>

```
Output from examples in main.py:

> # test with full crypto name
> coin = crypto_lookup.LunarCrush('dogecoin')
> print(coin.data)

.. Attempting to find the symbol for 'dogecoin'.
.. Success! 'dogecoin' is 'DOGE'
.. {'name': 'Dogecoin', 'id': 29, 'symbol': 'DOGE', 'price': 0.53744006, 'price_btc': 1.117434529914e-05, 'percent_change_24h': -4.53, 'percent_change_7d': -11.35, 'percent_change_30d': 67.4, 'interval': 'day', 'open': 0.51333036, 'close': 0.53757696, 'high': 0.53569002, 'low': 0.51094014}


> # test with crypto symbol
> coin = crypto_lookup.LunarCrush('doge')
> print(coin.data)

.. {'name': 'Dogecoin', 'id': 29, 'symbol': 'DOGE', 'price': 0.53744006, 'price_btc': 1.117434529914e-05, 'percent_change_24h': -4.53, 'percent_change_7d': -11.35, 'percent_change_30d': 67.4, 'interval': 'day', 'open': 0.51333036, 'close': 0.53757696, 'high': 0.53569002, 'low': 0.51094014}


> # test with list of cryptos, mixed format and non-existing currency: 'asdb'
> coin_list = ['dogecoin', 'doge', 'safemoon', 'btc', 'asdb', 'bitcoin']
> coin = crypto_lookup.LunarCrush(coin_list)
> print(*coin.data_list, sep='\n')

.. Attempting to find the symbol for 'dogecoin'.
.. Success! 'dogecoin' is 'DOGE'
.. Attempting to find the symbol for 'asdb'.
.. 'asdb' not found. Please retry with the correct symbol or full name.
.. Attempting to find the symbol for 'bitcoin'.
.. Success! 'bitcoin' is 'BTC'
.. {'name': 'Dogecoin', 'id': 29, 'symbol': 'DOGE', 'price': 0.53744006, 'price_btc': 1.117434529914e-05, 'percent_change_24h': -4.53, 'percent_change_7d': -11.35, 'percent_change_30d': 67.4, 'interval': 'day', 'open': 0.51333036, 'close': 0.53757696, 'high': 0.53569002, 'low': 0.51094014}
.. {'name': 'Dogecoin', 'id': 29, 'symbol': 'DOGE', 'price': 0.53744006, 'price_btc': 1.117434529914e-05, 'percent_change_24h': -4.53, 'percent_change_7d': -11.35, 'percent_change_30d': 67.4, 'interval': 'day', 'open': 0.51333036, 'close': 0.53757696, 'high': 0.53569002, 'low': 0.51094014}
.. {'name': 'SafeMoon', 'id': 12242, 'symbol': 'SAFEMOON', 'price': 9.22e-06, 'price_btc': 1.9170038e-10, 'percent_change_24h': 2.4, 'percent_change_7d': 6.65, 'percent_change_30d': 679.82, 'interval': 'day', 'open': 9.25e-06, 'close': 8.87e-06, 'high': 9.25e-06, 'low': 9.25e-06}
.. {'name': 'Bitcoin', 'id': 1, 'symbol': 'BTC', 'price': 48095.88800172, 'price_btc': 1, 'percent_change_24h': -5.01, 'percent_change_7d': -17.73, 'percent_change_30d': -21.09, 'interval': 'day', 'open': 48048.52111538, 'close': 48169.10815053, 'high': 48667.50607115, 'low': 46883.95534405}
.. None
.. {'name': 'Bitcoin', 'id': 1, 'symbol': 'BTC', 'price': 48095.88800172, 'price_btc': 1, 'percent_change_24h': -5.01, 'percent_change_7d': -17.73, 'percent_change_30d': -21.09, 'interval': 'day', 'open': 48048.52111538, 'close': 48169.10815053, 'high': 48667.50607115, 'low': 46883.95534405}
```