# 作業：設計 Skill + 打造遊戲抽卡系統

> **繳交方式**：將你的 GitHub repo 網址貼到作業繳交區
> **作業性質**：個人作業

---

## 作業目標

使用 Antigravity Skill 引導 AI，完成一個具備前後端與資料庫的「遊戲抽卡系統」。
重點不只是「讓程式跑起來」，而是透過設計 Skill，學會用結構化的方式與 AI 協作開發，並體驗資料庫關聯、狀態保留與前端互動特效。

---

## 繳交項目

你的 GitHub repo 需要包含以下內容：

### 1. Skill 設計（`.agents/skills/`）

為以下五個開發階段＋提交方式各設計一個 SKILL.md：

| 資料夾名稱        | 對應指令          | 說明                                                                           |
| ----------------- | ----------------- | ------------------------------------------------------------------------------ |
| `prd/`          | `/prd`          | 產出 `docs/PRD.md`                                                           |
| `architecture/` | `/architecture` | 產出 `docs/ARCHITECTURE.md`                                                  |
| `models/`       | `/models`       | 產出 `docs/MODELS.md`                                                        |
| `implement/`    | `/implement`    | 產出程式碼（**需指定**：HTML 前端 + FastAPI + SQLite 後端）              |
| `test/`         | `/test`         | 產出手動測試清單                                                               |
| `commit/`       | `/commit`       | 自動 commit + push（**需指定**：使用者與 email 使用 Antigravity 預設值） |

### 2. 開發文件（`docs/`）

用你設計的 Skill 產出的文件，需包含：

- `docs/PRD.md`
- `docs/ARCHITECTURE.md`
- `docs/MODELS.md`


### 3. 程式碼

一個可執行的抽卡系統，需支援以下功能：

| 功能           | 說明                                       | 是否完成 |
| -------------- | ------------------------------------------ | -------- |
| 單抽,十抽       | 可選擇抽卡方式                              | O        |
| 抽卡記錄        | 儲存過去抽卡紀錄                            |    O      |
| 卡片倉庫        | 可顯示以獲取卡牌                            |   O       |
| 放大檢視卡片    | 可放大檢視卡片                              |    O      |
| 販賣卡片        | 可販賣卡片獲取抽卡資源                       |      O    |
| 登入，註冊，登出 |    提供登入，註冊，登出 功能                 |    O      |

### 4. 系統截圖（`screenshots/`）

在 `screenshots/` 資料夾放入以下截圖：

<img width="1896" height="906" alt="螢幕擷取畫面 2026-04-22 112120" src="https://github.com/user-attachments/assets/6df6253e-62d9-44cd-a079-e70bf8389a76" />
<img width="1738" height="901" alt="螢幕擷取畫面 2026-04-22 112213" src="https://github.com/user-attachments/assets/709c173d-7603-4995-89d1-884d0c441fc2" />
<img width="865" height="849" alt="螢幕擷取畫面 2026-04-22 112227" src="https://github.com/user-attachments/assets/c5c98311-8af1-443a-bf4c-cff98f27d74d" />

### 5. 心得報告（本 README.md 下方）

在本 README 的**心得報告**區填寫。

---

## 專案結構範例

```
your-repo/
├── .agents/
│   └── skills/
│       ├── prd/SKILL.md
│       ├── architecture/SKILL.md
│       ├── models/SKILL.md
│       ├── implement/SKILL.md
│       ├── test/SKILL.md
│       └── commit/SKILL.md
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   └── MODELS.md
├── templates/
│   └── index.html
├── screenshots/
│   ├── chat.png
│   ├── history.png
│   └── skill.png
├── app.py
├── requirements.txt
├── .env.example
└── README.md          ← 本檔案（含心得報告）
```

---

## 啟動方式

```bash
# 1. 建立虛擬環境
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. 安裝套件
pip install -r requirements.txt

# 3. 設定環境變數
cp .env.example .env
# 編輯 .env，填入 GEMINI_API_KEY

# 4. 啟動伺服器
uvicorn app:app --reload
# 開啟瀏覽器：http://localhost:8000
```

---

## 心得報告

**姓名**：葉書愷
**學號**：d1150493

### 問題與反思

**Q1. 你設計的哪一個 Skill 效果最好？為什麼？哪一個效果最差？你認為原因是什麼？**

> **效果最好的 Skill**：`implement/` (全端實作)
> **原因**：我明確指定了「純 HTML 前端 + FastAPI + SQLite 後端」的技術棧。由於框架非常具體，且沒有依賴過多複雜的第三方函式庫，AI 在生成路由與前後端串接程式碼時，幾乎是一次到位，大幅減少了 Debug 的時間。
>
> **效果最差的 Skill**：`models/` (資料庫模型)
> **原因**：當初在定義 Schema 時，沒有預料到 FastAPI (Pydantic V2) 的版本變更細節。雖然結構都有出來，但因為缺乏對 Pydantic `from_attributes = True` 等參數的詳細規範，導致開發初期發生了一些序列化的報錯，這也讓我知道設定檔與相容性規範在 Skill 中是非常重要的。

---

**Q2. 在用 AI 產生程式碼的過程中，你遇到什麼問題是 AI 沒辦法自己解決、需要你介入處理的？**

> 1. **資料庫交易 (Transaction) 邏輯問題**：
> 在實作「十連抽」功能時，如果同一次抽卡抽到兩張相同的卡片，由於沒有加上 `db.flush()`，導致系統查不到剛存進去的卡，進而在倉庫中產生重複且無法堆疊的卡片紀錄。這是屬於較深層的 ORM 邏輯盲區，需要我發現後請 AI 去排查修正。
> 2. **測試環境狀態污染**：
> 在執行 `test_main.py` 時，有一個測試 (`test_not_enough_gems`) 把寶石扣光了，這導致後續執行的 `test_login` 驗證寶石數量時報錯。這讓我意識到測試用的資料庫在各個 Test Case 之間並沒有完全隔離，需要介入調整測試驗證條件與資料庫建立腳本。
> 3. **UI/UX 的感官判斷**：
> 雖然 AI 可以產出基本的版面，但要達到「好玩、有質感」的抽卡體驗，包含「卡牌放大檢視」、「發光邊框特效」與「動畫時間差」，這些都需要我提出非常具體的美術風格要求（如 Glassmorphism、3D Flip 動畫）並來回微調，才能讓畫面變得有吸引力。
