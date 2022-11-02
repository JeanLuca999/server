from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .database import engine, SessionLocal
from .models import Base, Users
from sqlalchemy.orm import Session
import bcrypt
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


class UserResponseCreate(BaseModel):
    name: str
    email: str
    password: str

    class Config:
        orm_mode = True


class UserResponseLogin(BaseModel):
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
def register(user: UserResponseCreate, db: Session = Depends(get_db)):
    if bool(db.query(Users).filter_by(email=user.email).first()):
        raise HTTPException(status_code=422, detail="Este email já foi cadastrado")

    user_model = Users()
    user_model.name = user.name
    user_model.email = user.email
    user_model.password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())

    db.add(user_model)
    db.commit()

    response_json = {"name": user.name, "email": user.email}
    return JSONResponse(content=jsonable_encoder(response_json))


@app.post("/login")
def login(user: UserResponseLogin, db: Session = Depends(get_db)):

    valid_user = db.query(Users).filter_by(email=user.email).first()

    if bool(valid_user) and bcrypt.checkpw(
        user.password.encode("utf-8"), valid_user.password
    ):
        response_json = {
            "name": valid_user.name,
            "email": valid_user.email,
        }
        return JSONResponse(content=jsonable_encoder(response_json))

    raise HTTPException(status_code=422, detail="Usuário inválido")
