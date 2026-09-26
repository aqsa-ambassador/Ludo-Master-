# Ludo Master 🎲 — Streamlit Edition

The game itself is a self-contained HTML/CSS/JS file (`ludo.html`), embedded into
a Streamlit page (`app.py`) so it can be deployed straight from GitHub to
Streamlit Community Cloud.

## Project structure
```
ludo_streamlit/
├── app.py             # Streamlit entry point (embeds the game)
├── requirements.txt   # streamlit
└── ludo.html          # the full game, self-contained
```

## 1. Push to GitHub
```bash
git init
git add .
git commit -m "Ludo Master - Streamlit deploy"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

## 2. Deploy on Streamlit Community Cloud
1. Go to https://share.streamlit.io and sign in with GitHub.
2. Click **New app**.
3. Pick your repo, branch `main`, and set **Main file path** to `app.py`.
4. Click **Deploy**. Streamlit installs `requirements.txt` automatically.

That's it — no server code needed beyond embedding the HTML; all game logic
(dice, movement, AI, win detection) runs client-side in the browser.

## Run locally first (optional)
```bash
pip install -r requirements.txt
streamlit run app.py
```
