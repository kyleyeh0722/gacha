let USER_ID = localStorage.getItem('user_id');

const elements = {
    username: document.getElementById('username'),
    gems: document.getElementById('gems'),
    btnSingle: document.getElementById('btn-single-pull'),
    btnTen: document.getElementById('btn-ten-pull'),
    resultsContainer: document.getElementById('gacha-results'),
    inventoryGrid: document.getElementById('inventory-grid'),
    historyList: document.getElementById('history-list'),
    
    // Auth elements
    authOverlay: document.getElementById('auth-overlay'),
    appContent: document.getElementById('app-content'),
    usernameInput: document.getElementById('username-input'),
    passwordInput: document.getElementById('password-input'),
    btnLogin: document.getElementById('btn-login'),
    btnRegister: document.getElementById('btn-register'),
    authMessage: document.getElementById('auth-message'),
    btnLogout: document.getElementById('btn-logout'),
};

// ================= Auth Logic =================
async function authenticate(action) {
    const username = elements.usernameInput.value.trim();
    const password = elements.passwordInput.value.trim();
    if(!username || !password) {
        elements.authMessage.textContent = '請輸入帳號與密碼';
        return;
    }

    elements.authMessage.textContent = '處理中...';
    try {
        const res = await fetch(`/${action}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "登入/註冊失敗");

        // 登入成功
        USER_ID = data.id;
        localStorage.setItem('user_id', USER_ID);
        
        elements.authMessage.textContent = '';
        elements.authOverlay.style.display = 'none';
        elements.appContent.style.display = 'block';
        
        // 載入資料
        elements.username.textContent = data.username;
        elements.gems.textContent = data.gems;
        fetchInventory();
        fetchHistory();
    } catch (err) {
        elements.authMessage.textContent = err.message;
    }
}

elements.btnLogin.addEventListener('click', () => authenticate('login'));
elements.btnRegister.addEventListener('click', () => authenticate('register'));

elements.btnLogout.addEventListener('click', () => {
    localStorage.removeItem('user_id');
    USER_ID = null;
    elements.appContent.style.display = 'none';
    elements.authOverlay.style.display = 'flex';
    elements.usernameInput.value = '';
    elements.passwordInput.value = '';
});

// ================= Gacha Logic =================
async function fetchUser() {
    if(!USER_ID) return;
    try {
        const res = await fetch(`/user/${USER_ID}`);
        if (!res.ok) {
            elements.btnLogout.click(); // 無效的 User_ID
            return;
        }
        const user = await res.json();
        elements.username.textContent = user.username;
        elements.gems.textContent = user.gems;
        
        elements.authOverlay.style.display = 'none';
        elements.appContent.style.display = 'block';
        fetchInventory();
        fetchHistory();
    } catch (err) {
        console.error(err);
    }
}

async function fetchInventory() {
    try {
        const res = await fetch(`/inventory/${USER_ID}`);
        if (!res.ok) return;
        const inventory = await res.json();
        
        const rarityOrder = { 'SSR': 3, 'SR': 2, 'R': 1 };
        inventory.sort((a, b) => rarityOrder[b.card.rarity] - rarityOrder[a.card.rarity]);

        elements.inventoryGrid.innerHTML = '';
        inventory.forEach(item => {
            const el = document.createElement('div');
            el.className = `card ${item.card.rarity.toLowerCase()} inventory-item`;
            el.innerHTML = `
                <div class="qty">x${item.quantity}</div>
                <div class="rarity">${item.card.rarity}</div>
                <div class="name">${item.card.name}</div>
            `;
            elements.inventoryGrid.appendChild(el);
        });
    } catch (err) {
        console.error(err);
    }
}

async function fetchHistory() {
    try {
        const res = await fetch(`/history/${USER_ID}`);
        if (!res.ok) return;
        const history = await res.json();

        elements.historyList.innerHTML = '';
        if(history.length === 0) {
            elements.historyList.innerHTML = '<li>尚無抽卡紀錄</li>';
            return;
        }

        history.forEach(record => {
            const li = document.createElement('li');
            const date = new Date(record.created_at).toLocaleString('zh-TW');
            const typeText = record.pull_type === 'single' ? '單抽' : '十連';
            li.innerHTML = `
                <span>[${typeText}] <span class="${record.card.rarity.toLowerCase()}">${record.card.rarity}</span> ${record.card.name}</span>
                <span style="font-size: 0.8em; color: #888;">${date}</span>
            `;
            elements.historyList.appendChild(li);
        });
    } catch (err) {
        console.error(err);
    }
}

async function doPull(type) {
    elements.btnSingle.disabled = true;
    elements.btnTen.disabled = true;
    elements.resultsContainer.innerHTML = '抽取中...';

    try {
        const res = await fetch('/gacha', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: USER_ID, pull_type: type })
        });
        
        const data = await res.json();
        if (!res.ok) {
            alert(data.detail || "抽卡失敗");
            elements.resultsContainer.innerHTML = '';
            return;
        }

        elements.gems.textContent = data.remaining_gems;
        elements.resultsContainer.innerHTML = '';
        
        data.results.forEach((card, index) => {
            setTimeout(() => {
                const el = document.createElement('div');
                el.className = `card ${card.rarity.toLowerCase()}`;
                el.innerHTML = `
                    <div class="rarity">${card.rarity}</div>
                    <div class="name">${card.name}</div>
                `;
                elements.resultsContainer.appendChild(el);
            }, index * 100);
        });

        setTimeout(() => {
            fetchInventory();
            fetchHistory();
        }, data.results.length * 100 + 500);

    } catch (err) {
        console.error(err);
        elements.resultsContainer.innerHTML = '發生錯誤';
    } finally {
        setTimeout(() => {
            elements.btnSingle.disabled = false;
            elements.btnTen.disabled = false;
        }, 1000);
    }
}

elements.btnSingle.addEventListener('click', () => doPull('single'));
elements.btnTen.addEventListener('click', () => doPull('ten'));

// 初始啟動邏輯
if (USER_ID) {
    fetchUser();
} else {
    elements.authOverlay.style.display = 'flex';
}
