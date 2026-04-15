# 📄 **PRD – PART 1: PRODUCT DEFINITION & FUNCTIONAL REQUIREMENTS**

---

# 🧠 **1. Product Overview**

## 📌 Product Name

**Tech Monopoly**

## 📌 Product Type

* Web-based application
* Real-time multiplayer board game

## 📌 Core Concept

A **modern Monopoly-style game** where:

* Properties = **Tech brands**
* Players = **Emojis**
* Money = **Digital UI currency**
* Gameplay = **Turn-based + real-time sync**

---

# 🎯 **2. Product Goals**

## 🎯 Primary Goal

Build a **fully functional, real-time multiplayer board game system** that includes:

* Game engine (rules + logic)
* Multiplayer synchronization
* Bot player system
* Modern UI/UX

---

## 🎯 Secondary Goals

* Make it **portfolio-level (top 1%)**
* Ensure **scalability & clean architecture**
* Keep system **AI-buildable using this PRD**

---

# 👥 **3. Target Users**

* 👨‍💻 Developers (portfolio project)
* 🎮 Casual players
* 💼 Recruiters evaluating system design

---

# 🎮 **4. Core Gameplay Requirements**

---

## 🎲 4.1 Turn-Based System

* Players take turns in sequence
* Only one player can act at a time
* Turn order is fixed

---

## 🎲 4.2 Dice Mechanics

* Two dice (1–6 each)
* Movement = sum of dice
* Dice roll triggered by player action

---

## 🧍 4.3 Player System

Each player must have:

* Unique ID
* Emoji representation (e.g., 🚀 🤖 😎)
* Current board position (0–39)
* Wallet balance
* Owned properties

---

## 🧭 4.4 Board System

* Total tiles: **40**
* Types:

  * GO
  * Properties (tech brands)
  * Chance/Event
  * Tax
  * Jail
  * Free Parking
  * Go To Jail

---

## 🏢 4.5 Property System

Each property includes:

* Name (tech brand)
* Price
* Rent structure:

  * Base rent
  * Rent with houses (1–4)
  * Rent with hotel
* Color group

---

## 💰 4.6 Economy System

Each player:

* Starts with fixed money (e.g., 1500)

Transactions:

* Buy property
* Pay rent
* Pay tax
* Receive GO reward

---

## 🏁 4.7 Game End Condition

Game ends when:

* Only one player remains (others bankrupt)

Winner:

* Player with highest assets OR last active player

---

# 🌐 **5. Multiplayer Requirements**

---

## 🏠 5.1 Room System

* Create room → generates **room code**
* Join room using code

---

## 👥 5.2 Player Limits

* Minimum: 2 players
* Maximum: 6 players

---

## 🔄 5.3 Real-Time Sync

* All players see same state instantly
* Actions reflect across all clients

---

## 🔐 5.4 Turn Locking

* Only current player can act
* Others are read-only

---

# 🤖 **6. Bot Player Requirements**

---

## 🤖 6.1 Purpose

* Fill empty slots
* Allow solo gameplay

---

## 🤖 6.2 Behavior Rules

* Buy property if:

  * Unowned AND affordable
* Avoid actions if:

  * Money is low
* Pay rent/tax automatically

---

## 🤖 6.3 Execution

* Controlled by backend (not frontend)

---

# 🎨 **7. UI/UX Requirements**

---

## 🎲 7.1 Dice UI

* Two dice displayed
* Rolling animation

---

## 🃏 7.2 Property Cards

* Show:

  * Name
  * Rent levels
  * Upgrade cost

---

## 💰 7.3 Digital Cash UI

* Display wallet balance
* Show animations:

  * +money
  * -money

---

## 🧭 7.4 Board UI

* 40-tile grid layout
* Highlight active player
* Show player positions (emoji)

---

# 🧾 **8. Data Lifecycle Requirements**

---

## 🟢 During Game

* Store game state in database

---

## 🔴 After Game Ends

* Mark game as **finished**
* Delete game data after short duration

---

## ⏱️ Expiry Rule

* Use:

  * `expiresAt` timestamp
* Backend deletes expired games

---

# ⚠️ **9. Non-Functional Requirements**

---

## ⚡ Performance

* Real-time updates < 1 second delay

---

## 🔐 Security

* No client-side game logic trust
* Backend validates all actions

---

## 🧱 Scalability

* Support multiple rooms simultaneously

---

## 🧩 Maintainability

* Modular architecture
* Clear separation:

  * UI
  * Backend
  * DB

---


# 🧠 **1. High-Level Architecture**

## 📌 System Overview

```text
Client (React - Vite + Tailwind)
        ↓
Backend (FastAPI - Game Engine)
        ↓
Database (Firebase - Realtime + Storage)
```

---

## 🎯 Responsibility Split

| Layer    | Responsibility          |
| -------- | ----------------------- |
| Frontend | UI + user interaction   |
| Backend  | Game logic + validation |
| Database | State storage + sync    |

---

# ⚙️ **2. Backend Design (FastAPI – CORE ENGINE)**

👉 This is the **brain of your system**

---

## 🧠 2.1 Responsibilities

Backend MUST handle:

* Game state updates
* Turn validation
* Dice roll generation
* Property transactions
* Rent calculations
* Bot decisions
* Game end detection

---

## ❗ 2.2 Golden Rule

👉 **Frontend NEVER controls game logic**

* ❌ No direct state updates from client
* ✅ All actions go through backend

---

## 🔄 2.3 Request Flow

```text
User Action (Roll Dice)
        ↓
Frontend API Call
        ↓
FastAPI validates & updates state
        ↓
Firebase updated
        ↓
All clients receive updated state
```

---

# ☁️ **3. Database Design (Firebase)**

---

## 🧾 3.1 Collections Overview

### 🏠 `rooms`

Stores game sessions

```json
{
  "roomId": "ABCD123",
  "status": "waiting | playing | finished",
  "players": ["p1", "p2"],
  "gameState": {},
  "createdAt": 123456,
  "expiresAt": 123999
}
```

---

### 👤 `players` (optional separate OR embedded)

```json
{
  "id": "p1",
  "emoji": "🚀",
  "position": 0,
  "money": 1500,
  "properties": [],
  "isBot": false
}
```

---

## 🧠 3.2 Game State (Single Source of Truth)

```json
{
  "players": [],
  "properties": [],
  "currentTurn": 0,
  "dice": [0, 0],
  "phase": "waiting | rolling | moving | buying | ended"
}
```

---

## ❗ 3.3 Important Rule

👉 Entire game must be stored as **ONE state object**

Why?

* Prevent inconsistency
* Easy sync
* Easy debugging

---

# 🔄 **4. Real-Time Sync Mechanism**

---

## ⚡ 4.1 Firebase Listener

Frontend subscribes to:

```text
rooms/{roomId}
```

Whenever data changes:

* UI auto updates

---

## 🔁 4.2 Update Flow

```text
Backend updates Firebase
        ↓
Firebase triggers listeners
        ↓
All clients re-render UI
```

---

## ⚠️ 4.3 Avoid This Mistake

❌ Don’t update Firebase directly from frontend
✅ Always go through backend

---

# 🎲 **5. Game Engine Design**

---

## 🧠 5.1 State Machine Approach

Game phases:

```text
waiting → rolling → moving → action → next_turn → ended
```

---

## 🔁 5.2 Turn Flow

1. Current player rolls dice
2. Backend calculates movement
3. Player lands on tile
4. Tile action triggered:

   * Property → buy/pay rent
   * Tax → deduct
   * Jail → move to jail
5. End turn → next player

---

## ⚠️ 5.3 Turn Locking (CRITICAL)

* Only `currentTurn` player can act
* Backend validates player ID

---

# 🤖 **6. Bot System Architecture**

---

## 🧠 6.1 Execution Location

* Bots run inside **FastAPI backend**

---

## 🔁 6.2 Trigger

* When it's bot’s turn:

  * Backend auto-executes actions

---

## 📜 6.3 Basic Logic

```text
IF property unowned AND money > threshold
    → buy
ELSE
    → skip
```

---

## ⚡ 6.4 Important

* Bots must follow same rules as players
* No special privileges

---

# 🔐 **7. Data Integrity & Security**

---

## 🛡️ 7.1 Backend Validation

Every request must check:

* Is it player’s turn?
* Is action valid?
* Is player alive (not bankrupt)?

---

## 🚫 7.2 Prevent Cheating

* Ignore client-provided values
* Recalculate everything in backend

---

# 🧹 **8. Data Lifecycle Management**

---

## 🟢 During Game

* State updated in Firebase

---

## 🔴 After Game Ends

Update:

```json
{
  "status": "finished",
  "expiresAt": "timestamp"
}
```

---

## ⏱️ Cleanup Strategy

* Background job in FastAPI:

  * Runs periodically
  * Deletes expired rooms

---

# ⚠️ **9. Concurrency Handling**

---

## 🔥 Problem

Multiple users acting at same time

---

## ✅ Solution

* Backend enforces:

  * Turn-based locking
* Use:

  * Atomic updates (Firebase)

---

# 🧩 **10. Scalability Design**

---

## 🏠 Multiple Rooms

* Each room isolated
* No shared state

---

## ⚡ Performance

* Only update changed fields
* Keep state compact

---

# 🚀 **PRD – PART 3: IMPLEMENTATION PLAN & EXECUTION**

---

# 🧠 **1. Development Strategy (STRICT ORDER)**

👉 Follow this order **without skipping**:

---

## 🟢 Phase 1: Backend Game Engine (FastAPI)

### Goal:

Build **core logic first (no UI)**

### Tasks:

* Create game state model
* Implement:

  * Dice roll logic
  * Player movement
  * Turn system
  * Property system
* Add validation layer

👉 Output:

* Fully working game logic via APIs

---

## 🟡 Phase 2: Firebase Integration

### Goal:

Store & sync game state

### Tasks:

* Connect FastAPI → Firebase
* Create `rooms` collection
* Store full game state
* Implement:

  * Create room
  * Join room
  * Update state

---

## 🔵 Phase 3: Frontend UI (React)

### Goal:

Visualize game

### Tasks:

* Build board (40 tiles)
* Render players (emoji)
* Show:

  * Dice
  * Property cards
  * Player wallet
* Connect to Firebase listener

---

## 🟣 Phase 4: Multiplayer Logic

### Goal:

Enable real-time gameplay

### Tasks:

* Room join UI
* Sync game state
* Handle turn-based UI

---

## 🔴 Phase 5: Bot System

### Goal:

Automate gameplay

### Tasks:

* Detect bot turn
* Execute backend logic
* Update Firebase

---

## ⚫ Phase 6: Polish & Optimization

* Animations
* Error handling
* Performance tuning

---

# 🧩 **2. Backend Folder Structure (FastAPI)**

```bash
backend/
│
├── app/
│   ├── main.py
│   ├── routes/
│   │   ├── game.py
│   │   ├── room.py
│   │
│   ├── services/
│   │   ├── game_engine.py
│   │   ├── bot_engine.py
│   │
│   ├── models/
│   │   ├── game_state.py
│   │   ├── player.py
│   │   ├── property.py
│   │
│   ├── db/
│   │   ├── firebase.py
│   │
│   ├── utils/
│   │   ├── dice.py
│   │   ├── helpers.py
│
└── requirements.txt
```

---

# 🎨 **3. Frontend Folder Structure (React)**

```bash
frontend/
│
├── src/
│   ├── components/
│   │   ├── Board.jsx
│   │   ├── Tile.jsx
│   │   ├── Dice.jsx
│   │   ├── Player.jsx
│   │   ├── PropertyCard.jsx
│   │
│   ├── pages/
│   │   ├── Home.jsx
│   │   ├── Game.jsx
│   │
│   ├── services/
│   │   ├── api.js
│   │   ├── firebase.js
│   │
│   ├── store/
│   │   ├── gameStore.js
│
└── main.jsx
```

---

# 🔌 **4. API Design (FastAPI Endpoints)**

---

## 🏠 Room APIs

### ➤ Create Room

```
POST /room/create
```

Response:

```json
{
  "roomId": "ABCD123"
}
```

---

### ➤ Join Room

```
POST /room/join
```

Body:

```json
{
  "roomId": "ABCD123"
}
```

---

---

## 🎮 Game APIs

---

### ➤ Start Game

```
POST /game/start
```

---

### ➤ Roll Dice

```
POST /game/roll-dice
```

Response:

```json
{
  "dice": [3, 5],
  "newPosition": 8
}
```

---

### ➤ Buy Property

```
POST /game/buy
```

---

### ➤ End Turn

```
POST /game/end-turn
```

---

### ➤ Get Game State

```
GET /game/state/{roomId}
```

---

# 🧠 **5. Core Game Engine Functions**

Inside `game_engine.py`:

---

## 🎲 Dice Roll

```python
def roll_dice():
    return random.randint(1,6), random.randint(1,6)
```

---

## 🧍 Move Player

```python
def move_player(player, steps):
    player.position = (player.position + steps) % 40
```

---

## 💰 Handle Rent

```python
def pay_rent(player, owner, amount):
    player.money -= amount
    owner.money += amount
```

---

## 🏠 Buy Property

```python
def buy_property(player, property):
    if player.money >= property.price:
        player.money -= property.price
        property.owner = player.id
```

---

# 🤖 **6. Bot Engine (bot_engine.py)**

```python
def bot_decision(player, state):
    if property_unowned and player.money > property.price:
        return "buy"
    return "skip"
```

---

# ☁️ **7. Firebase Integration (IMPORTANT)**

---

## 🔌 Write Data

```python
db.collection("rooms").document(room_id).set(data)
```

---

## 🔄 Update Data

```python
db.collection("rooms").document(room_id).update(data)
```

---

## 🧹 Delete Data

```python
db.collection("rooms").document(room_id).delete()
```

---

# 🧹 **8. Auto Cleanup Job**

---

## FastAPI Background Task

```python
def cleanup_expired_games():
    # find rooms where expiresAt < now
    # delete them
```

Run:

* Every few minutes

---

# ⚠️ **9. Critical Implementation Rules**

---

## ❗ Rule 1

👉 Backend = single source of truth

---

## ❗ Rule 2

👉 No direct DB writes from frontend

---

## ❗ Rule 3

👉 Every action must validate:

* Turn
* Player
* Game state

---

## ❗ Rule 4

👉 Keep game state minimal & structured

---

