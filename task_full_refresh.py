from website import cache, app
import json
import requests



def request_cpu_usage():
  username = 'noeldolores'
  token = '9c6af631448c052f3322723a5986bad0b6704af0'

  response = requests.get(f'https://www.pythonanywhere.com/api/v0/user/{username}/cpu/',
                          headers={'Authorization': f'Token {token}'})
  if response.status_code == 200:
    cpu_usage = json.loads(response.content)
    limit = cpu_usage["daily_cpu_limit_seconds"]
    used = cpu_usage["daily_cpu_total_usage_seconds"]
    total_used = round(used/limit, 2) * 100
    return f'CPU quota: {total_used}%'
  else:
    print(f'Got unexpected status code {response.status_code}: {response.content}', flush=True)
    return None



with app.app_context():
  from_scratch = False
  try:
    all_cryptos = cache.retrieve_supported_cryptos()
  except Exception as e:
    print(f"retrieve_supported_cryptos: {e}", flush=True)

  try:
    if all_cryptos:
      id_batches = cache.create_id_query_list(all_cryptos)
    else:
      id_batches = None
  except Exception as e:
    print(f"create_id_query_list: {e}", flush=True)

  try:
    if id_batches:
      query_batches = cache.create_id_query_string(id_batches)
    else:
      query_batches = None
  except Exception as e:
    print(f"create_id_query_string: {e}", flush=True)

  try:
    if query_batches:
      full_market_data = cache.query_market_data(query_batches)
    else:
      full_market_data = None
  except Exception as e:
    print(f"query_market_data: {e}", flush=True)

  try:
    if full_market_data:
      results = cache.add_to_currency_cache(full_market_data, from_scratch=from_scratch)
      usage = request_cpu_usage()
      print(results, flush=True)
      print(usage, flush=True)
  except Exception as e:
    print(f"add_to_currency_cache: {e}", flush=True)