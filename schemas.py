from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class UserResponse(BaseModel):
    id: int
    username: str
    gems: int

    class Config:
        orm_mode = True

class CardResponse(BaseModel):
    id: int
    name: str
    rarity: str

    class Config:
        orm_mode = True

class InventoryItemResponse(BaseModel):
    id: int
    card: CardResponse
    quantity: int

    class Config:
        orm_mode = True

class GachaHistoryResponse(BaseModel):
    id: int
    card: CardResponse
    pull_type: str
    created_at: datetime

    class Config:
        orm_mode = True

class PullRequest(BaseModel):
    user_id: int
    pull_type: str # "single" or "ten"

class PullResponse(BaseModel):
    success: bool
    message: str
    results: List[CardResponse]
    remaining_gems: int
