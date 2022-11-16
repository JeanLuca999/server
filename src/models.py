from sqlalchemy import Column, Integer, String, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)

    posts = relationship("Posts", back_populates="users")
    events = relationship("Events", back_populates="users")


class Posts(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    body = Column(String)

    users = relationship("Users", back_populates="posts")


class Events(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    location = Column(String)
    date = Column(String)
    owner_id = Column(Integer, ForeignKey('users.id'))

    users = relationship("Users", back_populates="events")
