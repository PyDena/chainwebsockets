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
from pydantic import BaseModel
import community as community_louvain
import os
from random import choice

chainweb_node_structure_url = "https://estats.chainweb.com/info"
block_keys = ["height", "hash", "chainId", "totalTransactions", "creationTime"]
tx_keys = ["requestKey", "chainId", "status", "timestamp", "fromAccount", "toAccount"]
max_nodes = 20


class Transaction(BaseModel):
    tx_id: str | None = None
    requestKey: str
    chainId: int
    status: str
    timestamp: int
    fromAccount: str
    toAccount: str


class Block(BaseModel):
    block_id: str | None = None
    height: int
    hash: str
    chainId: int
    totalTransactions: int
    creationTime: int
    transactions: list[Transaction] = []
    has_live_neighbors: bool = False


class ChainWebInfo(BaseModel):
    nodeApiVersion: float
    nodeChains: list[int]
    nodeGraphHistory: list[list[int | list[list[int | list[int]]]]]
    nodeLatestBehaviorHeight: int
    nodeNumberOfChains: int
    nodeVersion: str


blocks: list[Block] = []
block_nodes: set[str] = set()
block_relationships: list[tuple[Block, Block]] = []
transactions: list[Transaction] = []
transaction_nodes: set[str] = set()
address_nodes: set[str] = set()
transaction_block_relationships = []
all_relationships = []
file_path = os.path.abspath(__file__)
file_name = os.path.basename(file_path)
testing_dir = file_path.replace(file_name, "")
node_img_dir = os.path.join(testing_dir, "images")

node_image_paths = ["file:///"+os.path.abspath(os.path.join(node_img_dir, image_name)) for image_name in os.listdir(node_img_dir) if 'block' in image_name.lower()]
tx_node_image_paths = ["file:///"+os.path.abspath(os.path.join(node_img_dir, image_name)) for image_name in os.listdir(node_img_dir) if 'coin' in image_name.lower()]

print(node_image_paths)
def make_block_id(block: Block):
    block_chain_id = block.chainId
    block_height = block.height
    return f"C:{block_chain_id}-H:{block_height}"


def make_block_label(block: Block):
    label_string = f"""
        Chain: {block.chainId}
        Height: {block.height}
        Hash: {block.hash}
        Creation Time: {block.creationTime}
        Tx Qty: {block.totalTransactions}
        Displayed Tx Qty: {len(block.transactions)}
        """
    return label_string


def make_tx_label(tx: Transaction):
    label_string = f"""
        Chain: {tx.chainId}
        Request Key: {tx.requestKey}
        Creation Time: {tx.timestamp}
        From: {tx.fromAccount}
        To: {tx.toAccount}
        Status: {tx.status}
        """
    return label_string


def make_tx_id(tx: Transaction):
    tx_chain_id = tx.chainId
    tx_status = tx.status
    return f"{tx_chain_id}-{tx_status}"


def add_tx_to_block(tx: Transaction):
    # TODO break up this function
    wanted_chain_id = tx.chainId
    wanted_time = tx.timestamp
    filtered_blocks = filter(
        lambda b: b.chainId == wanted_chain_id, blocks
    )
    filtered_blocks_list = list(filtered_blocks)
    if len(filtered_blocks_list) == 1:
        tx_block = filtered_blocks_list[0]
    elif len(filtered_blocks_list) > 1:
        tx_block = sorted(filtered_blocks_list, key=lambda block: block.creationTime)[
            -1
        ]
    else:
        tx_block = None
    if tx_block:  # and len(tx_block.transactions) < 8:
        tx.tx_id = f"{tx_block.block_id}-Tx:{len(tx_block.transactions)}"
        tx_block.transactions.append(tx)
        transactions.append(tx)

def create_block_to_block_relationship(block_1: Block, block_2: Block):
    ...


def create_block_to_tx_relationship(block: Block, tx: Transaction):
    ...


def get_block_by_chain_and_height(chain_id: int, block_height: int):
    filtered_blocks = filter(
        lambda b: b.chainId == chain_id and b.height == block_height, blocks
    )
    filtered_blocks_list = list(filtered_blocks)
    block = filtered_blocks_list[0] if len(filtered_blocks_list) == 1 else None
    return block


def generate_neighbor_chain_ids(chain_id: int):
    for neighbor_id in node_structure.nodeGraphHistory[-1][-1][chain_id][-1]:
        yield neighbor_id


def generate_neighbor_blocks(block: Block):
    for neighbor_id in generate_neighbor_chain_ids(block.chainId):
        neighbor_block = get_block_by_chain_and_height(neighbor_id, block.height)
        if neighbor_block:
            yield neighbor_block


def handle_block(block: Block):
    block.block_id = make_block_id(block)
    blocks.append(block)


def handle_tx(ws: websocket.WebSocketApp, tx: Transaction):
    add_tx_to_block(tx)


def generate_nodes():
    for block in blocks:
        for neighbor_block in generate_neighbor_blocks(block):
            block.has_live_neighbors = True
        if not block.has_live_neighbors:
            previous_block = get_block_by_chain_and_height(
                block.chainId, block.height - 1
            )
            if previous_block:
                block.has_live_neighbors = True
        block_title = make_block_label(block)
        for tx in block.transactions:
            img_path = choice(tx_node_image_paths)
            tx_title = make_tx_label(tx)
            tx_label = tx.tx_id.split(":")[-1]
            if block.has_live_neighbors:
                yield {"id": tx.tx_id, "title": tx_title, "size":15, "label": tx_label, "image":img_path, "shape":"image"}
        #if block.has_live_neighbors:
        block_size = 10 if block.totalTransactions < 10 else block.totalTransactions
        img_path = choice(node_image_paths)
        yield {
            "id": block.block_id,
            "title": block_title,
            "size": 25,
            "label": f"B-{block.chainId}",
            "image":img_path,
            "shape":'image'
        }


def generate_edges():
    for block in blocks:
        if block.has_live_neighbors:
            for neighbor_block in generate_neighbor_blocks(block):
                neighbor_id = neighbor_block.block_id
                yield {
                    "source": block.block_id,
                    "to": neighbor_id,
                    "title": "Block Neighbors",
                    "label": "",
                }
            for tx in block.transactions:
                yield {
                    "source": block.block_id,
                    "to": tx.tx_id,
                    "title": "Block Transactions",
                    "label": "",
                }
        previous_block = get_block_by_chain_and_height(block.chainId, block.height - 1)
        if previous_block:
            yield {
                "source": previous_block.block_id,
                "to": block.block_id,
                "title": "Previous Block Connection",
                "label": "",
            }


def create_networkx_graph():
    G = nx.Graph()
    # net = Network(bgcolor="#2222", font_color="white")

    for node in generate_nodes():
        node_id = node.pop("id")
        node_label = node.pop("label")
        if not node_label:
            node_label = ""
        try:
            image = node.pop("image")
            shape = node.pop("shape")
        except:
            image, shape = None, None
        if image and shape:
            G.add_node(node_id, label=node_label, image=image, shape=shape, **node)
        else:
            G.add_node(node_id, label=node_label, **node)
        #G.add_node(node_id, label=node_label, image=image, shape=shape, **node)
        # net.add_node(node_id, label=node_label, **node)
    for edge in generate_edges():
        source = edge.pop("source")
        to = edge.pop("to")
        G.add_edge(source, to, **edge)
    
    degree = nx.degree_centrality(G)
    #nx.set_node_attributes(G, degree, "degree_centrality")
    between = nx.betweenness_centrality(G)
    #nx.set_node_attributes(G, between, "betweenness_centrality")
    communities = community_louvain.best_partition(G)
    nx.set_node_attributes(G, communities, "group")
    
    net = Network(height="1700px", bgcolor="#000000", font_color="pink")
    
    net.options.physics.enabled = False
    net.height = "1700px"
    net.width = "100%"
    net.show_buttons(filter_=True)
    net.from_nx(G)
    net.show("kadena.html", notebook=False)


def get_chainweb_info():
    r = requests.get(chainweb_node_structure_url).json()
    return ChainWebInfo(**r)


def get_and_handle_recent_blocks():
    url = "https://backend2.euclabs.net/kadena-indexer-v2/v2/recent-blocks?pageId=0&pageSize=20"
    url = "https://backend2.euclabs.net/kadena-indexer/v2/recent-blocks?pageId=0&pageSize=5"
    response = requests.get(url)
    if response.status_code == 200:
        response_json = response.json()
        for block_data in response_json:
            block_data.update({"creationTime": block_data.get("timestamp")})
        [handle_block(Block(**block_data)) for block_data in response_json]
    else:
        print("incorrect response", response.status_code)
        exit()
    


def on_message(ws: websocket.WebSocketApp, message):
    ...


def on_content_message(ws: websocket.WebSocketApp, message):
    ...


def on_data(ws: websocket.WebSocketApp, data1: str, data2, data3):
    old_tx_count = len(transactions)
    json_data_str = data1.split("\n\n")[-1].replace("\x00", "")
    if json_data_str.startswith("{") and json_data_str.endswith("}"):
        json_data: dict[str, Any] = json.loads(json_data_str)
        if sorted(json_data.keys()) == sorted(tx_keys):
            handle_tx(ws, Transaction(**json_data))
        elif sorted(json_data.keys()) == sorted(block_keys):
            handle_block(Block(**json_data))
        else:
            with open("new_data_schema_found.json", "w") as fp:
                json.dump(json_data, fp)

        new_len = len(transactions)
        if old_tx_count != new_len:
            print("Transactions ", new_len)
            if new_len >= max_nodes:
                ws.close()


def on_error(ws: websocket.WebSocketApp, error):
    print("error", error)


def on_close(ws: websocket.WebSocketApp, close_status_code, close_msg):
    print("closing websocket")


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
    node_structure.nodeGraphHistory = sorted(
        [
            [chain_id, sorted(graph)]
            for chain_id, graph in node_structure.nodeGraphHistory
        ]
    )
    print("getting blocks")
    get_and_handle_recent_blocks()
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(
        "wss://backend2.euclabs.net/kadena-indexer-websockets",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_cont_message=on_content_message,
        on_data=on_data,
    )
    print("running ws")
    ws.run_forever()
    print("creating graph")
    create_networkx_graph()
