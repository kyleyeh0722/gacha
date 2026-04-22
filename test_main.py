from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from database import Base, get_db
from main import app, init_dummy_data
import models

# 建立獨立的測試用 SQLite 記憶體資料庫
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    init_dummy_data(db)
    
    # 給測試帳號多一點錢
    user = db.query(models.User).filter(models.User.id == 1).first()
    user.gems = 100000
    db.commit()
    
    yield
    Base.metadata.drop_all(bind=engine)
    db.close()

def test_read_main(setup_db):
    response = client.get("/")
    assert response.status_code == 200

def test_get_user(setup_db):
    response = client.get("/user/1")
    assert response.status_code == 200
    assert response.json()["username"] == "TestPlayer"

def test_single_pull(setup_db):
    # Arrange
    initial_gems = client.get("/user/1").json()["gems"]
    
    # Act
    response = client.post("/gacha", json={"user_id": 1, "pull_type": "single"})
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert len(data["results"]) == 1
    assert data["remaining_gems"] == initial_gems - 200

def test_ten_pull_guarantee_sr(setup_db):
    # Arrange
    initial_gems = client.get("/user/1").json()["gems"]
    
    # Act
    response = client.post("/gacha", json={"user_id": 1, "pull_type": "ten"})
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert len(data["results"]) == 10
    assert data["remaining_gems"] == initial_gems - 2000
    
    # 檢查是否至少有一張 SR 或 SSR
    has_sr_or_ssr = any(card["rarity"] in ["SR", "SSR"] for card in data["results"])
    assert has_sr_or_ssr == True

def test_not_enough_gems(setup_db):
    # Arrange: 設定寶石為 0
    db = TestingSessionLocal()
    user = db.query(models.User).filter(models.User.id == 1).first()
    user.gems = 0
    db.commit()
    db.close()
    
    # Act
    response = client.post("/gacha", json={"user_id": 1, "pull_type": "single"})
    
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Not enough gems"

def test_register():
    response = client.post("/register", json={"username": "NewPlayer", "password": "newpassword"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "NewPlayer"
    assert data["gems"] == 10000

def test_login():
    response = client.post("/login", json={"username": "TestPlayer", "password": "testpassword"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "TestPlayer"
    assert "gems" in data

def test_login_invalid():
    response = client.post("/login", json={"username": "TestPlayer", "password": "wrongpassword"})
    assert response.status_code == 401

