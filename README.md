# 📰 NewsDesk v1.0

A lightweight desktop news reader with RSS aggregation, local storage, and bilingual reading support.

---

## ✨ Features

- 🗞 Collects latest news from multiple international RSS sources (BBC, Guardian, Fox News, etc.)
- 💾 Local SQLite database for offline access
- 🌐 English / Chinese bilingual reading modes
- 🔄 One-click fetch and auto-refresh of news list
- 🎛 Simple and clean desktop UI
- 🖥 Windows EXE & 📱 Android APK support

---

## 🧠 Design Philosophy

NewsDesk is designed to be:

- **Simple** – no accounts, no cloud dependency
- **Local-first** – all data stored locally
- **Fast** – minimal dependencies, lightweight UI
- **Practical** – focused on reading, not distraction

This project intentionally avoids over-engineering and heavy frameworks.

---

## 🛠 Tech Stack

- **Python 3.10+**
- **Flet 0.28.3** (UI framework)
- **SQLite** (local database)
- **feedparser** (RSS fetching)
- **PyInstaller** (Windows packaging)

---

## 📦 Installation & Usage

### ▶ Windows (EXE)

1. Download `NewsDesk.exe`
2. Double-click to run  
3. No Python or extra dependencies required

> On first run, a local `news.db` file will be created automatically.

---

### ▶ Android (APK)

1. Install `app-release.apk`
2. Allow installation from unknown sources if prompted
3. Open the app and start reading

> All data is stored inside the app sandbox.

---

## 🔄 Fetch Latest News

- Click the ⚙ Settings button
- Select **Fetch latest news**
- News list will refresh automatically after fetching

---

## 📁 Project Structure

```text
.
├── app_flet.py              # Main UI application
├── news_fetch_and_store.py  # RSS fetching & database storage
├── core/                    # Data, settings, translation logic
├── gui/                     # UI helpers (theme, i18n)
├── requirements.txt         # Locked dependencies for v1.0
└── README.md
