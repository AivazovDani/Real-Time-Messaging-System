from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dataclasses import dataclass
from typing import Dict
import uuid # this library generates unique id's
import json

templates = Jinja2Templates(directory="templates") # instead of using react we use Jinja2Templates

@dataclass
class ConnectionManager:
    def __init__(self) -> None:
        self.active_connection: dict = {} # we'll track connections by id: websocket


    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        id = str(uuid.uuid4()) # we make the id string

        self.active_connection[id] = websocket

        data = json().dumps({"isMe": True, "data": "Have joined", "username": "You"}) # we use json cause it's easier to add anythong later

        await self.send_message(websocket, data)

    async def send_message(self, ws: WebSocket, message: str):
        await ws.send_text(message)

    async def broadcast(self, websocet: WebSocket, data:str):
        decode_data = json.loads(data)

        for connection in self.active_connection:
            is_me = False
            if connection == websocet:
                is_me = True

            await connection.send_text(json.dumps({"isMe": is_me, "data": decode_data['message'], "username": decode_data['user']}))

    async def disconnect(self, websocket: WebSocket):
        id = self.find_id(WebSocket)
        del self.active_connection[id]

    # def find_id(self, websocket: WebSocket):
    #     ## iterate and get the id of this websocket


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"requests": request, "title": "ChatApp"})

connection_manager = ConnectionManager()



@app.websocket("/message")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)

    try:
        while True:
            # Recieve the text fromt the users
            data = await websocket.receive_text()
            await connection_manager.broadcast(websocket, data)

    except WebSocketDisconnect:
        return RedirectResponse("/")










    # await websocket.accept()
    # while True:
    #     data = await websocket.receive_text()
    #     await websocket.send_text(f"Message text was: {data}")


