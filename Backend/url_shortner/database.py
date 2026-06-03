from sqlalchemy import DateTime, create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session, sessionmaker
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime, timedelta
import base62
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Request


# initialise my index.html
templates = Jinja2Templates(directory="templates")

# Initialising App
app = FastAPI(title="url-shortner")

# Seting up the database
engine = create_engine("sqlite:///links.db", connect_args={"check_same_thread":False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Create Table
class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True)
    original_url = Column(String, nullable=False)
    short_code = Column(String, nullable=False, unique=True)
    clicks = Column(Integer, default=0)
    time_added = Column(DateTime, default=datetime.utcnow())

Base.metadata.create_all(engine)

# Pydentic models

class CreateUrl(BaseModel):
    original_url:str
    optional_short_code:str

class ResponseUrl(BaseModel):
    short_code:str
    original_url:str

    class Config:
        from_attributes = True

class ResponseClicks(BaseModel):
    clicks: int
    time_added:datetime


# Session Machine
def db_get():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# API Endpoints

@app.get("/", response_class=HTMLResponse)
def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/shorten", response_model=ResponseUrl)
def create_url(url: CreateUrl, db: Session = Depends(db_get)):
    new_url = Link(original_url=url.original_url) # Saving original url to database

    db.add(new_url)
    db.commit()
    db.refresh(new_url)


    new_url.short_code = base62.encode(new_url.id + 1000)
    
    db.commit()
    db.refresh(new_url)

    return new_url # returns dict of short code and original url, then we'll combine them in our frontend


@app.get("/{short_code}")
def redirect(short_code:str, db: Session = Depends(db_get)):
    original_url = db.query(Link).filter(Link.short_code == short_code).first()
    if not original_url:
        raise HTTPException(status_code=404, detail="Url does not exists")
    
    original_url.clicks += 1
    db.commit()

    now = datetime.utcnow()
    expirational_date = original_url.time_added + timedelta(hours=2)

    if now > expirational_date:
        db.delete(original_url)
        db.commit()
        raise HTTPException(status_code=410, detail="Url has expired latly")

    return RedirectResponse(url=original_url)


@app.get("/stats/{short_code}", response_model=ResponseClicks)
def get_analytics(short_code:str, db: Session = Depends(db_get)):
    db_url = db.query(Link).filter(Link.short_code == short_code).first()

    if not db_url:
        raise HTTPException(status_code=404, detail="Url does not exists")
    
    return db_url

@app.post("/custom-shorten", response_model=ResponseUrl)
def create_custom_shorten(url: CreateUrl, db: Session = Depends(db_get)):
    new_url = Link(original_url=url.original_url)
    new_short_code = db.query(Link).filter(Link.short_code == url.optional_short_code).first()

    db.add(new_url)
    db.commit()
    db.refresh(new_url)

    if not new_short_code:
        new_url.short_code = url.optional_short_code
        db.commit()
        db.refresh(new_url)

        return new_url


    else:
        new_url.short_code = base62.encode(new_url.id + 1000)
        db.commit()
        db.refresh(new_url)
        raise HTTPException(status_code=404, detail=f"Short-code {new_short_code} already exists. Your new short-code is {new_url.short_code}")
    
    
    
# Check USer agents
# Dektop mobile
# US
# Language set or null
# NGINX / Cut. Server ?