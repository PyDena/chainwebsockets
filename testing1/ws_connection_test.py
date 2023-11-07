import websocket
import threading
import time
import json
import requests
from typing import Literal, Any
import networkx as nx
import matplotlib as plt
from matplotlib import pyplot as plt
from pyvis.network import Network
chainweb_node_structure_url = "https://estats.chainweb.com/info"
block_keys = ["height", "hash", "chainId", "totalTransactions", "creationTime"]
tx_keys = ["requestKey", "chainId", "status", "timestamp", "fromAccount", "toAccount"]


from pydantic import BaseModel




class Block(BaseModel):
    height: int
    hash: str
    chainId: int
    totalTransactions: int
    creationTime: int

class Transaction(BaseModel):
    requestKey: str
    chainId: int
    status: str
    timestamp: int
    fromAccount: str
    toAccount: str


class ChainWebInfo(BaseModel):
    nodeApiVersion: float
    nodeChains: list[int]
    nodeGraphHistory: list[list[int|list[list[int|list[int]]]]]
    nodeLatestBehaviorHeight: int
    nodeNumberOfChains: int
    nodeVersion: str

blocks:list[Block] = []
block_nodes:set[str] = set()
block_relationships = []
transactions = []
transaction_nodes:set[str] = set()
address_nodes:set[str] = set()
transaction_relationships = []
transaction_block_relationships = []
all_relationships = []

def create_networkx_graph():
    print("creating graph")
    [all_relationships.append(i) for i in block_relationships]
    [all_relationships.append(i) for i in transaction_relationships]
    [all_relationships.append(i) for i in transaction_block_relationships]
    net = Network()
    for node in block_nodes:
        net.add_node(node, title="Block",size=10, color="#f0a30a")
    for node in transaction_nodes:
        net.add_node(node, title="Transaction", label="", size=5, color="#f2a30a")
    for relationship in block_relationships:
        net.add_edge(relationship[0], relationship[1], title="Block Relationship", label="")
    for relationship in transaction_block_relationships:
        net.add_edge(relationship[0], relationship[1], title="tx block relationship", label="")
    #net.set_options(net_options)
    net.show("kadena.html", notebook=False)

def get_chainweb_info():
    r = requests.get(chainweb_node_structure_url).json()
    return ChainWebInfo(**r)

def get_and_handle_recent_blocks():
    url = "https://backend2.euclabs.net/kadena-indexer-v2/v2/recent-blocks?pageId=0&pageSize=20"
    r:list[dict] = requests.get(url).json()
    for block_data in r:
        block_data.update({"creationTime":block_data.get("timestamp")})
    [handle_block(Block(**block_data)) for block_data in r]

def handle_block(block_data: Block):
    block_nodes.add(block_data.hash)
    blocks.append(block_data)
    desired_chainId = block_data.chainId
    creationTime = block_data.creationTime
    wanted_height = block_data.height-1
    filtered_blocks = filter(lambda b: b.chainId == desired_chainId and b.height == wanted_height, blocks)
    # If you want to use the blocks as a list again
    filtered_blocks_list = list(filtered_blocks)
    if len(filtered_blocks_list) > 0:
        previous_block = sorted(filtered_blocks_list, key=lambda block: block.creationTime)[-1]
        block_relationships.append((block_data.hash,previous_block.hash))
    
    chain_ids = node_structure.nodeGraphHistory[-1][-1][desired_chainId]
    wanted_height = block_data.height
    for wanted_chain_id in chain_ids[-1]:
        filtered_blocks = filter(lambda b: b.chainId == wanted_chain_id and b.height == wanted_height, blocks)
        filtered_blocks_list = list(filtered_blocks)
        if len(filtered_blocks_list) > 0:
            previous_block = filtered_blocks_list[-1]
            print(previous_block.hash, block_data.hash)
            block_relationships.append((block_data.hash,previous_block.hash))
    
    

def handle_tx(ws:websocket.WebSocketApp, tx_data: Transaction):
    transaction_nodes.add(tx_data.requestKey)
    desired_chainId = tx_data.chainId
    creationTime = tx_data.timestamp
    address_nodes.add(tx_data.toAccount)
    address_nodes.add(tx_data.fromAccount)
    filtered_blocks = filter(lambda b: b.chainId == desired_chainId and b.creationTime == creationTime, blocks)
    # If you want to use the blocks as a list again
    filtered_blocks_list = list(filtered_blocks)
    related_block = filtered_blocks_list[0] if len(filtered_blocks_list) == 1 else None
    if related_block:
        print(tx_data)
        print(related_block)
        transaction_block_relationships.append((tx_data.requestKey,related_block.hash))
def on_message(ws: websocket.WebSocketApp, message):
    ...


def on_content_message(ws: websocket.WebSocketApp, message):
    ...



def on_data(ws: websocket.WebSocketApp, data1: str, data2, data3):
    json_data_str = data1.split("\n\n")[-1].replace("\x00", "")
    if json_data_str.startswith("{") and json_data_str.endswith("}"):
        json_data: dict[str, Any] = json.loads(json_data_str)
        if sorted(json_data.keys()) == sorted(tx_keys):
            #handle_tx(ws,Transaction(**json_data))
            pass
        elif sorted(json_data.keys()) == sorted(block_keys):
            #handle_block(Block(**json_data))
            handle_block(Block(**json_data))
        else:
            print(json_data)
            with open("new_data_schema_found.json", "w") as fp:
                json.dump(json_data, fp)
            ws.close(100, "new data found")


def on_error(ws: websocket.WebSocketApp, error):
    ...


def on_close(ws: websocket.WebSocketApp, close_status_code, close_msg):
    ...


def on_open(ws: websocket.WebSocketApp):
    def run(*args):
        # Send CONNECT frame
        connect_frame = (
            "CONNECT\naccept-version:1.2,1.1,1.0\nheart-beat:1000,1000\n\n\x00"
        )
        ws.send(connect_frame)

        time.sleep(1)
        subscribe_frame1 = "SUBSCRIBE\nid:sub-0\ndestination:/topic/blocks-v2\n\n\x00"
        ws.send(subscribe_frame1)

        subscribe_frame2 = (
            "SUBSCRIBE\nid:sub-1\ndestination:/topic/transactions-v2\n\n\x00"
        )
        ws.send(subscribe_frame2)

    thread = threading.Thread(target=run)
    thread.start()


if __name__ == "__main__":
    node_structure = get_chainweb_info()
    node_structure.nodeGraphHistory = sorted([[chain_id, sorted(graph)] for chain_id, graph in node_structure.nodeGraphHistory])
    get_and_handle_recent_blocks()
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(
        "wss://backend2.euclabs.net/kadena-indexer-v2-websockets",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_cont_message=on_content_message,
        on_data=on_data,
    )

    ws.run_forever()
    create_networkx_graph()
