from fastapi import FastAPI, Depends, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .database import engine, SessionLocal
from .models import Base, Users
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


class UserResponse(BaseModel):
    name: str
    email: str
    password: str

    class Config:
        orm_mode = True


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@app.post("/register")
def register(user: UserResponse, db: Session = Depends(get_db)):

    user_model = Users()
    user_model.name = user.name
    user_model.email = user.email
    user_model.password = bcrypt.hash(user.password)

    db.add(user_model)
    db.commit()

    json_compatible_item_data = jsonable_encoder(user)
    return JSONResponse(content=json_compatible_item_data)


@app.post("/login")
def login():
    return "logged"
