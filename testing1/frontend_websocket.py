from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse, FileResponse
from websocket import WebSocketApp
import json
from typing import Any
import threading
import asyncio
from uuid import UUID, uuid4
from pydantic import BaseModel
import os
import requests


block_keys = ["height", "hash", "chainId", "totalTransactions", "creationTime"]
tx_keys = ["requestKey", "chainId", "status", "timestamp", "fromAccount", "toAccount"]

file_path = os.path.abspath(__file__)
file_name = os.path.basename(file_path)
testing_dir = file_path.replace(file_name, "")
node_img_dir = os.path.join(testing_dir, "images")

node_image_paths = ["file:///"+os.path.abspath(os.path.join(node_img_dir, image_name)) for image_name in os.listdir(node_img_dir) if 'block' in image_name.lower()]
tx_node_image_paths = ["file:///"+os.path.abspath(os.path.join(node_img_dir, image_name)) for image_name in os.listdir(node_img_dir) if 'coin' in image_name.lower()]
chainweb_node_structure_url = "https://estats.chainweb.com/info"

class ChainWebInfo(BaseModel):
    nodeApiVersion: float
    nodeChains: list[int]
    nodeGraphHistory: list[list[int | list[list[int | list[int]]]]]
    nodeLatestBehaviorHeight: int
    nodeNumberOfChains: int
    nodeVersion: str

class Transaction(BaseModel):
    id: str | None = None
    group:int|None = None
    requestKey: str
    chainId: int
    status: str
    timestamp: int
    fromAccount: str
    toAccount: str
    has_relationships:bool = False
    relationships:list[str] = []
    ts:int|None = None


class Block(BaseModel):
    id: str | None = None
    group:int|None = None
    height: int
    hash: str
    chainId: int
    totalTransactions: int
    creationTime: int
    has_relationships:bool = False
    relationships:list[str] = []
    ts:int|None = None

class Node(BaseModel):
    ts:int
    id: str
    group:int
    has_relationships:bool
    relationships:list[str]


blocks:list[Block] = []
transactions:list[Block] = []
all_blocks_and_transactions:list[Block|Transaction] = []
def get_chainweb_info():
    r = requests.get(chainweb_node_structure_url).json()
    return ChainWebInfo(**r)

node_structure = get_chainweb_info()
node_structure.nodeGraphHistory = sorted(
    [
        [chain_id, sorted(graph)]
        for chain_id, graph in node_structure.nodeGraphHistory
    ]
)

def get_block_by_chain_and_height(chain_id: int, block_height: int):
    filtered_blocks = filter(
        lambda b: b.chainId == chain_id and b.height == block_height, blocks
    )
    filtered_blocks_list = list(filtered_blocks)
    block = filtered_blocks_list[0] if len(filtered_blocks_list) == 1 else None
    return block

def get_latest_block(chain_id: int, ct: int):
    filtered_blocks = filter(
        lambda b: b.chainId == chain_id, blocks
    )
    filtered_blocks_list = list(filtered_blocks)

    block = filtered_blocks_list[-1] if len(filtered_blocks_list) >=1 else None
    return block

def generate_neighbor_chain_ids(chain_id: int):
    for neighbor_id in node_structure.nodeGraphHistory[-1][-1][chain_id][-1]:
        yield neighbor_id

def prepare_websocket_data(data:dict):
    if len(all_blocks_and_transactions) >= 500:
        if isinstance(all_blocks_and_transactions[0], Block):
            del blocks[0]
        else:
            del transactions[0]
        del all_blocks_and_transactions[0]
    if sorted(data.keys()) == sorted(block_keys):
        block = Block(**data)
        block.group = block.chainId
        block.ts = block.creationTime
        block.id = f"{block.chainId}-{block.height}"
        for neighbor_chain_id in generate_neighbor_chain_ids(block.chainId):
            neighbor_block = get_block_by_chain_and_height(neighbor_chain_id, block.height)
            if neighbor_block:
                block.relationships.append(neighbor_block.id)
                block.has_relationships = True
        previous_block = get_block_by_chain_and_height(block.chainId, block.height-1)
        if previous_block:
            block.relationships.append(previous_block.id)
            block.has_relationships = True
        blocks.append(block)
        all_blocks_and_transactions.append(block)
        return Node(**block.model_dump()).model_dump()         
    elif sorted(data.keys()) == sorted(tx_keys):
        tx = Transaction(**data)
        tx.group = tx.chainId
        tx.ts = tx.timestamp
        tx.id = f"Tx {tx.chainId}-{tx.requestKey}"
        tx_block = get_latest_block(tx.chainId, tx.timestamp)
        if tx_block:
            tx.has_relationships = True
            tx.relationships.append(tx_block.id)
        transactions.append(tx)
        all_blocks_and_transactions.append(tx)
        return Node(**tx.model_dump()).model_dump()
    else:
        ...

class WebSocketManager:
    def __init__(self):
        self.connection_messages:dict[str, list[str]] = {}
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket, connection_id:str):
        await websocket.accept()
        self.connection_messages.update({connection_id:["connected"]})
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket, connection_id):
        self.active_connections.remove(websocket)
        self.connection_messages.pop(connection_id)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection_id, connection_messages in self.connection_messages.items():
            connection_messages.append(message)
            self.connection_messages.update({connection_id:connection_messages})

    async def broadcast_data(self, data: dict):
        for connection in self.active_connections:
            await connection.send_json(data)

    async def get_message(self, connection_id:str):
        messages = self.connection_messages.get(connection_id)
        self.connection_messages.update({connection_id:[]})
        return messages
    
class MyWebSocketApp:
    def __init__(self, url, manager: WebSocketManager):
        self.url = url
        self.manager = manager
        self.ws: WebSocketApp | None = None

    def on_open(self, ws):
        def run(*args):
            connect_frame = (
                "CONNECT\naccept-version:1.2,1.1,1.0\nheart-beat:1000,1000\n\n\x00"
            )
            ws.send(connect_frame)

            subscribe_frame1 = (
                "SUBSCRIBE\nid:sub-0\ndestination:/topic/blocks-v2\n\n\x00"
            )
            ws.send(subscribe_frame1)

            subscribe_frame2 = (
                "SUBSCRIBE\nid:sub-1\ndestination:/topic/transactions-v2\n\n\x00"
            )
            ws.send(subscribe_frame2)

        thread = threading.Thread(target=run)
        thread.start()

    def on_message(self, ws, message):
        # Forward the received message to all connected clients
        json_data_str = message.split("\n\n")[-1].replace("\x00", "")
        if json_data_str.startswith("{") and json_data_str.endswith("}"):
            json_data: dict[str, Any] = json.loads(json_data_str)
            new_block_data = prepare_websocket_data(json_data)
            if new_block_data:
                asyncio.run(self.manager.broadcast(new_block_data))
                
    def start_up(self):
        print("starting")
        self.ws = WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_message=self.on_message,
            # Add other callbacks as needed
        )
        self.ws.run_forever()


manager = WebSocketManager()
my_app = MyWebSocketApp("wss://backend2.euclabs.net/kadena-indexer-websockets", manager)
threading.Thread(target=my_app.start_up).start()

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    id = uuid4()
    await manager.connect(websocket, id)
    try:
        while True:
            for message in await manager.get_message(id):
                await websocket.send_json(message)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        manager.disconnect(websocket, id)

@app.get("/", response_class=HTMLResponse)
async def root():
    with open(r"C:\Users\tanner.martin\Desktop\chainwebsockets\testing1\node_testing.html", 'r') as fp:
        html = fp.read()
    return html

@app.get("/images/blocks/{chain_id}/", response_class=FileResponse)
async def get_block_image(chain_id:int):
    img_path = f"C:\\Users\\tanner.martin\\Desktop\\chainwebsockets\\testing1\\images\\Block {chain_id}.png"
    return FileResponse(img_path, media_type="image/png")
