from datetime import datetime, timedelta
import json
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from database import SessionLocal, Message, User
import uuid


router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        id = str(uuid.uuid4())
                 
        self.active_connections[id] = websocket

        data = json.dumps({"isMe": True, "data": "Have joined", "username": "You"})

        await self.send_message(websocket, data)

    async def send_message(self, ws: WebSocket, message: str):
        await ws.send_text(message)
    
    def disconnect(self, websocket: WebSocket):
        for id, connection in self.active_connections.items():
            if connection == websocket:
                del self.active_connections[id]
                break

    async def broadcast(self, websocket: WebSocket, data:str):
        decode_data = json.loads(data) # we accept json because we can update it easier

        for connection in self.active_connections.values():
            is_me = False
            if connection == websocket:
                is_me = True

            await connection.send_text(json.dumps({"isMe": is_me, "data": decode_data['message'], "username": decode_data['user']})) # we will combine ${data.username}: ${data.data} in the frontend


manager = ConnectionManager()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id:int):
    await manager.connect(websocket)
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.id == client_id).first()

        if not db_user:
            await websocket.close()
            return
        
        db_user.last_seen = datetime.utcnow()

        db.commit()
        
        history = db.query(Message).order_by(Message.time_send).limit(50).all()

        for message in history:
            history_data = json.dumps({
                "message": message.content,
                "user": message.user.username,
                "isMe": False
            }) # needs to be json because of the broadcast function

            await manager.send_message(websocket, history_data)

        while True:
            data = await websocket.receive_text()

            new_message = Message(content=data, user_id=db_user.id)

            db.add(new_message)
            db.commit()
            db.refresh(new_message)

            message_data = json.dumps({
                "message": data,
                "user": db_user.username
            }) # needs to be json because of the broadcast function

            await manager.broadcast(websocket, message_data)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        db_user.last_seen = datetime.utcnow()
        db.commit()

        leave_data = json.dumps({
            "message": "has left the chat",
            "user": db_user.username
        }) # needs to be json because of the broadcast function

        await manager.broadcast(websocket, leave_data)

    finally:
        db.close()


# Example of a workflow
# you create a dict:
# {"message": "has left", "user": "john"}
#         ↓
# json.dumps() → turns into string
# '{"message": "has left", "user": "john"}'
#         ↓
# passed to broadcast()
#         ↓
# json.loads() → turns back into dict
# {"message": "has left", "user": "john"}
#         ↓
# access with ['message'] and ['user']

# await connection.send_text(json.dumps({"isMe": is_me, "data": decode_data['message'], "username": decode_data['user']}))
# we will combine ${data.username}: ${data.data} in the frontend


