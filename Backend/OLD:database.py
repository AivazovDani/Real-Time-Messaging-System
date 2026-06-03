from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session, sessionmaker
from pydantic import BaseModel

app = FastAPI(title="Questbook - Yordan")

# Database setup
engine = create_engine("sqlite:///users.db", connect_args={"check_same_thread":False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)


Base.metadata.create_all(engine)

# Pydentic Models (DataClass)

class CreateUser(BaseModel):
    username:str
    password:str

class ResponseUser(BaseModel):
    id:int
    username:str

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

# @app.get("/users/{user_id}", response_model=ResponseUser)
# def get_user(user_id:int, db:Session = Depends(get_db)):
#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user


# @app.post("/users/", response_model=ResponseUser)
# def create_user(user: CreateUser, db:Session = Depends(get_db)):
#     if db.query(User).filter(User.username == user.username).first():
#         raise HTTPException(status_code=400, detail="Username already exists")
    
#     new_user = User(**user.dict())
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
#     return new_user


# @app.put("/users/{user_id}", response_model=ResponseUser)
# def update_user(user_id:int, user:CreateUser, db:Session = Depends(get_db)):
#     db_user = db.query(User).filter(User.id == user_id).first()
#     if not db_user:
#         raise HTTPException(status_code=404, detail="User does not exists")
    
#     for field, value in user.dict().items():
#         setattr(db_user, field, value)

#     db.commit()
#     db.refresh(db_user)
#     return db_user


@app.post("/auth/register", response_model=ResponseUser)
def register(user: CreateUser, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    new_user = User(username=user.username, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/auth/login", response_model=ResponseUser)
def login(user: CreateUser, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or db_user.password != user.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return db_user

