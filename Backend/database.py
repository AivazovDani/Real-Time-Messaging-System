from datetime import datetime, timedelta
from typing import List
from sqlalchemy import DateTime, create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session, relationship, sessionmaker
from pydantic import BaseModel
from websocket import router

app = FastAPI(title="Test - Yordan")
app.include_router(router)

# DataBase Set-up
engine = create_engine("sqlite:///users_test.db", connect_args={"check_same_thread":False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Create the table
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    last_seen = Column(DateTime, default=datetime)

    messages = relationship('Message', back_populates='user')


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    time_send = Column(DateTime, default=datetime)

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='messages')



Base.metadata.create_all(engine)


# Pydentic models for input and output


class CreateUser(BaseModel):
    username:str
    password:str

class ResponseUser(BaseModel):
    id:int
    username:str

    class Config:
        from_attributes = True

class UpdateUsername(BaseModel):
    username:str

class CreateMessage(BaseModel):
    content:str

class MessageUser(BaseModel):
    username: str

    class Config:
        from_attributes = True

class ResponseContent(BaseModel):
    id:int
    content:str
    user: MessageUser
    time_send: datetime

    class Config:
        from_attributes = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# API Endpoints

@app.get("/")
def main():
    return "App is running"

@app.post("/auth/register", response_model=ResponseUser)
def register(user: CreateUser, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    new_user = User(username=user.username, password=user.password)
    db.add(new_user)
    existing_user.last_seen = datetime.utcnow()
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/auth/login", response_model=ResponseUser)
def login(user: CreateUser, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or db_user.password != user.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    db_user.last_seen = datetime.utcnow()
    return db_user


@app.put("/users/me/username", response_model=ResponseUser)
def update_username(user_id: int,user: UpdateUsername, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    db_user.username = user.username

    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/{user_id}", response_model=ResponseUser)
def return_profile(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db_user




@app.post("/message/{user_id}", response_model=ResponseContent)
def create_message(user_id:int, message: CreateMessage, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User do not exists man")
    
    new_message = Message(content=message.content, user_id=db_user.id)

    db.add(new_message)
    db_user.last_seen = datetime.utcnow()
    db.commit()
    db.refresh(new_message)
    return new_message


@app.get("/messages/{user_id}", response_model=List[ResponseContent])
def response_message_per_user(user_id:int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User do not exists man")

    user_messages = db_user.messages
    return user_messages


@app.get("/messages", response_model=List[ResponseContent])
def response_message_for_all_users(db: Session = Depends(get_db)):
    db_messages = db.query(Message).all()

    return db_messages

@app.get("/all-users", response_model=List[ResponseUser])
def all_users(db: Session = Depends(get_db)):
    db_users = db.query(User).all()

    return db_users


@app.get("/users/active", response_model=List[ResponseUser])
def all_active(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    five_minutes_ago = now - timedelta(minutes=5)


    active_users = db.query(User).filter(User.last_seen > five_minutes_ago).all()

    return active_users


    


