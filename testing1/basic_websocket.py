import json, websocket, threading
from typing import Any


WS_URL = "wss://backend2.euclabs.net/kadena-indexer-websockets"


def on_message(ws: websocket.WebSocketApp, message):
    ...


def on_content_message(ws: websocket.WebSocketApp, message):
    ...


def on_data(ws: websocket.WebSocketApp, data1: str, data2, data3):
    json_data_str = data1.split("\n\n")[-1].replace("\x00", "")
    if json_data_str.startswith("{") and json_data_str.endswith("}"):
        json_data: dict[str, Any] = json.loads(json_data_str)
        print([json_data])


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

        subscribe_frame1 = "SUBSCRIBE\nid:sub-0\ndestination:/topic/blocks-v2\n\n\x00"
        ws.send(subscribe_frame1)

        subscribe_frame2 = (
            "SUBSCRIBE\nid:sub-1\ndestination:/topic/transactions-v2\n\n\x00"
        )
        ws.send(subscribe_frame2)

    thread = threading.Thread(target=run)
    thread.start()


def start_socket():
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_cont_message=on_content_message,
        on_data=on_data,
    )
    ws.run_forever()
