import random
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from database import engine, Base, get_db
import models, schemas

# Initialize tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Mount static files for frontend
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

# --- Initialize Dummy Data ---
def init_dummy_data(db: Session):
    # Check if cards exist
    if not db.query(models.Card).first():
        cards = [
            models.Card(name="R_Slime", rarity="R"),
            models.Card(name="R_Goblin", rarity="R"),
            models.Card(name="R_Bat", rarity="R"),
            models.Card(name="SR_Knight", rarity="SR"),
            models.Card(name="SR_Mage", rarity="SR"),
            models.Card(name="SR_Archer", rarity="SR"),
            models.Card(name="SSR_Dragon", rarity="SSR"),
            models.Card(name="SSR_DemonLord", rarity="SSR"),
            models.Card(name="SSR_Succubus", rarity="SSR"),
        ]
        db.add_all(cards)
        db.commit()

    # Check if test user exists
    if not db.query(models.User).filter(models.User.id == 1).first():
        user = models.User(id=1, username="TestPlayer", password="testpassword", gems=10000)
        db.add(user)
        db.commit()

@app.on_event("startup")
def startup_event():
    db = next(get_db())
    init_dummy_data(db)

# --- Endpoints ---

@app.post("/register", response_model=schemas.UserResponse)
def register(req: schemas.AuthRequest, db: Session = Depends(get_db)):
    # 檢查是否已存在
    existing = db.query(models.User).filter(models.User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # 建立新使用者
    new_user = models.User(username=req.username, password=req.password, gems=10000)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=schemas.UserResponse)
def login(req: schemas.AuthRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == req.username).first()
    if not user or user.password != req.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    return user

@app.post("/add_gems", response_model=schemas.UserResponse)
def add_gems(req: schemas.AddGemsRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.gems += req.amount
    db.commit()
    db.refresh(user)
    return user

@app.post("/sell_card", response_model=schemas.UserResponse)
def sell_card(req: schemas.SellCardRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    inv_item = db.query(models.Inventory).filter(
        models.Inventory.user_id == req.user_id,
        models.Inventory.card_id == req.card_id
    ).first()
    
    if not inv_item or inv_item.quantity < req.quantity:
        raise HTTPException(status_code=400, detail="Not enough cards to sell")
        
    card = db.query(models.Card).filter(models.Card.id == req.card_id).first()
    
    # 販賣價格邏輯
    prices = {"R": 200, "SR": 1000, "SSR": 10000}
    price = prices.get(card.rarity, 0)
    
    # 更新數量與寶石
    inv_item.quantity -= req.quantity
    user.gems += price * req.quantity
    
    if inv_item.quantity == 0:
        db.delete(inv_item)
        
    db.commit()
    db.refresh(user)
    return user

@app.get("/user/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def pull_random_card(db: Session, forced_min_rarity: str = None):
    # R 60%, SR 38%, SSR 2%
    r_cards = db.query(models.Card).filter(models.Card.rarity == "R").all()
    sr_cards = db.query(models.Card).filter(models.Card.rarity == "SR").all()
    ssr_cards = db.query(models.Card).filter(models.Card.rarity == "SSR").all()
    
    if forced_min_rarity == "SR":
        # Adjust probabilities if SR is forced (SR or SSR)
        # We can just say: SR 95%, SSR 5% for the guaranteed pull
        rand = random.uniform(0, 100)
        if rand < 95:
            return random.choice(sr_cards)
        else:
            return random.choice(ssr_cards)
    
    # Normal pull
    rand = random.uniform(0, 100)
    if rand < 60:
        return random.choice(r_cards)
    elif rand < 98:
        return random.choice(sr_cards)
    else:
        return random.choice(ssr_cards)

@app.post("/gacha", response_model=schemas.PullResponse)
def do_gacha(req: schemas.PullRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    cost = 200 if req.pull_type == "single" else 2000
    pulls_count = 1 if req.pull_type == "single" else 10

    if user.gems < cost:
        raise HTTPException(status_code=400, detail="Not enough gems")

    user.gems -= cost
    db.add(user)

    pulled_cards = []
    
    # Generate cards
    for _ in range(pulls_count):
        card = pull_random_card(db)
        pulled_cards.append(card)
        
    # Check 10-pull guarantee (At least 1 SR or SSR)
    if req.pull_type == "ten":
        has_sr_or_above = any(c.rarity in ["SR", "SSR"] for c in pulled_cards)
        if not has_sr_or_above:
            # Replace the first card with a guaranteed SR/SSR
            pulled_cards[0] = pull_random_card(db, forced_min_rarity="SR")

    # Save to history and inventory
    for card in pulled_cards:
        # History
        history = models.GachaHistory(user_id=user.id, card_id=card.id, pull_type=req.pull_type)
        db.add(history)
        
        # Inventory (stack quantity)
        inv_item = db.query(models.Inventory).filter(
            models.Inventory.user_id == user.id,
            models.Inventory.card_id == card.id
        ).first()
        
        if inv_item:
            inv_item.quantity += 1
        else:
            inv_item = models.Inventory(user_id=user.id, card_id=card.id, quantity=1)
            db.add(inv_item)
            db.flush() # 強制同步到當前 Transaction，讓下一次迴圈能 query 到這筆新資料

    db.commit()

    return {
        "success": True,
        "message": f"Successfully pulled {pulls_count} card(s)",
        "results": pulled_cards,
        "remaining_gems": user.gems
    }

@app.get("/inventory/{user_id}", response_model=List[schemas.InventoryItemResponse])
def get_inventory(user_id: int, db: Session = Depends(get_db)):
    # Needed to import List but it's okay, I'll update the schema or rely on fastapi handling it.
    inventory = db.query(models.Inventory).filter(models.Inventory.user_id == user_id).all()
    return inventory

@app.get("/history/{user_id}", response_model=List[schemas.GachaHistoryResponse])
def get_history(user_id: int, limit: int = 50, db: Session = Depends(get_db)):
    history = db.query(models.GachaHistory).filter(models.GachaHistory.user_id == user_id).order_by(models.GachaHistory.created_at.desc()).limit(limit).all()
    return history
