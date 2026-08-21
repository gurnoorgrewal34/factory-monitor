from fastapi import WebSocket


class WebSocketManager:

    def __init__(self):

        self.connections = set()

    async def connect(
        self,
        websocket: WebSocket
    ):

        await websocket.accept()

        self.connections.add(
            websocket
        )

        print(
            "WEBSOCKET MANAGER -> CONNECTED"
        )

    def disconnect(
        self,
        websocket: WebSocket
    ):

        self.connections.discard(
            websocket
        )

        print(
            "WEBSOCKET MANAGER -> DISCONNECTED"
        )

    async def broadcast(
        self,
        message: dict
    ):

        dead_connections = []

        for websocket in list(
            self.connections
        ):

            try:

                await websocket.send_json(
                    message
                )

            except Exception as exc:

                print(
                    "WEBSOCKET SEND ERROR ->",
                    repr(exc)
                )

                dead_connections.append(
                    websocket
                )

        for websocket in dead_connections:

            self.disconnect(
                websocket
            )