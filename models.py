from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    gems = Column(Integer, default=10000)

class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    rarity = Column(String, index=True) # R, SR, SSR

class Inventory(Base):
    __tablename__ = "inventories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    card_id = Column(Integer, ForeignKey("cards.id"))
    quantity = Column(Integer, default=1)
    
    user = relationship("User")
    card = relationship("Card")

class GachaHistory(Base):
    __tablename__ = "gacha_histories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    card_id = Column(Integer, ForeignKey("cards.id"))
    pull_type = Column(String) # "single" or "ten"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    card = relationship("Card")
