from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from .database import engine, SessionLocal
from .models import Base, Users, Posts, Events
from sqlalchemy.orm import Session
import bcrypt
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy import event

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


def _fk_pragma_on_connect(dbapi_con, con_record):
    dbapi_con.execute('pragma foreign_keys=ON')


Base.metadata.create_all(bind=engine)

event.listen(engine, 'connect', _fk_pragma_on_connect)


class EventSchema(BaseModel):
    title: str
    description: str
    location: str
    date: str
    owner_id: int = Field(gt=0, lt=10000000000000000)

    class Config:
        orm_mode = True


class PostSchema(BaseModel):
    body: str = Field(min_length=1)
    owner_id: int = Field(gt=0, lt=10000000000000000)

    class Config:
        orm_mode = True


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

# EVENTS ROUTES
@app.get("/events")
def get_events(db: Session = Depends(get_db)):
    events = db.query(Posts).all()

    for event in events:
        event_user = db.query(Users).filter(Users.id == event.owner_id).first()

        user_fields = {
            "name": event_user.name,
            "email": event_user.email,
        }

        event.user = user_fields

    return events


@app.post("/events")
def create_event(event: EventSchema, db: Session = Depends(get_db)):
    owner_exists = db.query(Users).filter(Users.id == event.owner_id).first()

    if owner_exists:
        event_model = Events()
        event_model.title = event.title
        event_model.description = event.description
        event_model.location = event.location
        event_model.date = event.date
        event_model.owner_id = event.owner_id
        db.add(event_model)
        db.commit()
        db.refresh(event_model)
        return event_model
    else:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")


@app.delete("/events/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Events).filter(Events.id == event_id).first()

    if event:
        db.delete(event)
        db.commit()
        return {"message": "Evento deletado com sucesso"}
    else:
        raise HTTPException(status_code=404, detail="Evento não encontrado")


@app.put("/events/{event_id}")
def update_event(event_id: int, event: EventSchema, db: Session = Depends(get_db)):
    event_exists = db.query(Events).filter(Events.id == event_id).first()

    if event_exists:
        event_exists.title = event.title
        event_exists.description = event.description
        event_exists.location = event.location
        event_exists.date = event.date
        event_exists.owner_id = event.owner_id
        db.commit()
        db.refresh(event_exists)
        return event_exists
    else:
        raise HTTPException(status_code=404, detail="Evento não encontrado")


# POSTS ROUTES
@app.get("/posts")
def get_posts(db: Session = Depends(get_db)):
    posts = db.query(Posts).all()

    for post in posts:
        post_user = db.query(Users).filter(Users.id == post.owner_id).first()

        user_fields = {
            "name": post_user.name,
            "email": post_user.email,
        }

        post.user = user_fields

    return posts


@app.get("/posts/user/{user_id}")
def read_users_post(user_id: int, db: Session = Depends(get_db)):
    posts = db.query(Posts).filter_by(owner_id=user_id).all()

    for post in posts:
        post_user = db.query(Users).filter(Users.id == post.owner_id).first()

        user_fields = {
            "name": post_user.name,
            "email": post_user.email,
        }

        post.user = user_fields

    return posts


@app.post("/posts")
def create_posts(post: PostSchema, db: Session = Depends(get_db)):
    owner_exists = db.query(Users).filter_by(id=post.owner_id).first()
    if owner_exists:
        post_model = Posts()
        post_model.body = post.body
        post_model.owner_id = post.owner_id
        db.add(post_model)
        db.commit()
        db.refresh(post_model)
        return post_model
    else:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")


@app.delete("/posts/{post_id}")
def delete_posts(post_id: int, db: Session = Depends(get_db)):
    post_model = db.query(Posts).filter(Posts.id == post_id).first()

    if post_model is None:
        raise (HTTPException(status_code=404,
               detail=f"PostSchema de ID {post_id} não encontrado!"))

    db.query(Posts).filter(Posts.id == post_id).delete()
    db.commit()
    return {"message": f"Post {post_id} deletado com sucesso!"}


@app.put("/posts/{post_id}")
def update_posts(post_id: int, post: PostSchema, db: Session = Depends(get_db)):
    post_model = db.query(Posts).filter(Posts.id == post_id).first()
    post_model.body = post.body
    db.commit()
    db.refresh(post_model)

    if post_model is None:
        raise (HTTPException(status_code=404,
               detail=f"PostSchema de ID {post_id} não encontrado!"))

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
        raise HTTPException(
            status_code=422, detail="Este email já foi cadastrado")

    user_model = Users()
    user_model.name = user.name
    user_model.email = user.email
    user_model.password = bcrypt.hashpw(
        user.password.encode("utf-8"), bcrypt.gensalt())

    db.add(user_model)
    db.commit()

    response_json = {"id": user_model.id,
                     "name": user.name, "email": user.email}
    return JSONResponse(content=jsonable_encoder(response_json))


@app.post("/login")
def login(user: UserResponseLogin, db: Session = Depends(get_db)):

    valid_user = db.query(Users).filter_by(email=user.email).first()

    if bool(valid_user) and bcrypt.checkpw(
        user.password.encode("utf-8"), valid_user.password
    ):
        response_json = {
            "id": valid_user.id,
            "name": valid_user.name,
            "email": valid_user.email,
        }
        return JSONResponse(content=jsonable_encoder(response_json))

    raise HTTPException(status_code=422, detail="Usuário inválido")
