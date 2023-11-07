import requests

websocket_js_url = "https://kdaexplorer.com/_nuxt/index.bc0005f9.js"
rates_url = "https://backend2.euclabs.net/ticker/v2/rates/all/USD"
recent_txs_url = (
    "https://backend2.euclabs.net/kadena-indexer-v2/v2/recent-txs?pageId=0&pageSize=5"
)
recent_txs_2_url = "https://estats.chainweb.com/txs/recent"

recent_blocks_url = "https://backend2.euclabs.net/kadena-indexer-v2/v2/recent-blocks?pageId=0&pageSize=5"
analytics_data_url = (
    "https://backend2.euclabs.net/kadena-indexer-v2/v1/statistics/analytics-data"
)
transaction_volume_url = "https://backend2.euclabs.net/kadena-indexer-v2/v1/statistics/transaction-volume-sparkline"
websocket_connection_url = "wss://backend2.euclabs.net/kadena-indexer-v2-websockets"
node_chain_info_url = "https://estats.chainweb.com/info"
current_blocks_url = "https://estats.chainweb.com/chainweb/0.0/mainnet01/cut"
stats_url = "https://estats.chainweb.com/stats"
payload_url = "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/0/payload/s3hNTYDg3eLsJfElYUgXS-bjrVFCr5iAftLJnaRTwDg/outputs"
header_url = "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/0/header/H0CgJkVLQ__B8rIIOdYQv8NeLietugrRIHMLANrfrx8?t=json"

block_data_min_max_urls = [
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/0/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/1/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/2/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/3/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/4/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/5/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/6/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/7/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/8/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/9/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/10/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/11/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/12/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/13/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/14/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/15/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/16/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/17/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/18/header?minheight=4231225&limit=4231229",
    "https://estats.chainweb.com/chainweb/0.0/mainnet01/chain/19/header?minheight=4231225&limit=4231229",
]

def get_websocket_javascript():
    response = requests.get(websocket_js_url)
    return response.content


javascript_data = get_websocket_javascript()

with open("index.bc005f9.js", "wb") as fp:
    fp.write(javascript_data)
