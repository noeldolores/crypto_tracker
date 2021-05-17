A personal use crypto tracker.

Current features:<br/>
<ol>
<li>Uses the <a href="https://lunarcrush.com/developers/docs#assets">LunarCrush API</a> to query cryptocurrencies, outputting to command line or Flask app.</li>
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
![Image of Flask Output](https://github.com/noeldolores/crypto_tracker/blob/master/images/flask_example.png)