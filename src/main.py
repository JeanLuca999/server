from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from .database import engine, SessionLocal
from .models import Base, Users, Posts
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

class PostSchema(BaseModel):
    body: str = Field(min_length=1)

class UserResponse(BaseModel):
    name: str
    email: str
    password: str

    class Config:
        orm_mode = True


class UserResponseLogin(BaseModel):
    email: EmailStr 
    password: str

    class Config:
        orm_mode = True


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

# POSTS ROUTES
@app.get("/posts")
def read_posts(db: Session = Depends(get_db)):
    posts = db.query(Posts).all()
    return posts

@app.post("/posts")
def create_posts(post: PostSchema, db: Session = Depends(get_db)):
    post_model = Posts()
    post_model.body = post.body
    db.add(post_model)
    db.commit()
    db.refresh(post_model)
    return post_model

@app.delete("/posts/{post_id}")
def delete_posts(post_id: int, db: Session = Depends(get_db)):
    post_model = db.query(Posts).filter(Posts.id == post_id).first()

    if post_model is None:
        raise(HTTPException(status_code=404, detail=f"PostSchema de ID {post_id} não encontrado!"))

    db.query(PostSchema).filter(PostSchema.id == post_id).delete()
    db.commit()
    return {"message": f"PostSchema {post_id} deletado com sucesso!"}

@app.put("/posts/{post_id}")
def update_posts(post_id: int, post: PostSchema, db: Session = Depends(get_db)):
    post_model = db.query(Posts).filter(Posts.id == post_id).first()
    post_model.body = post.body
    db.commit()
    db.refresh(post_model)

    if post_model is None:
        raise(HTTPException(status_code=404, detail=f"PostSchema de ID {post_id} não encontrado!"))

    return post


# USER ROUTES
@app.get("/users")
def read_users(db: Session = Depends(get_db)):
    users = db.query(Users).all()
    return users


# AUTH ROUTES
@app.post("/register")
def register(user: UserResponse, db: Session = Depends(get_db)):
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
