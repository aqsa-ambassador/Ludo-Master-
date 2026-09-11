import streamlit as st
import random
import time
import math

# ============================================================
# LUDO MASTER — COMPLETE FIXED VERSION
# ============================================================

st.set_page_config(page_title="Ludo Master", page_icon="🎲", layout="centered")

st.markdown("""
<style>
.block-container { padding-top:.6rem; padding-bottom:.4rem; max-width:440px; }
#MainMenu {visibility:hidden;} footer {visibility:hidden;} header {visibility:hidden; height:0;}
.stButton > button { padding:.3rem .5rem; border-radius:8px; font-weight:700; }
h1 { font-size:1.5rem !important; margin-bottom:.1rem !important; }
h3 { margin-top:0 !important; margin-bottom:0 !important; }
div.element-container { margin-bottom:.15rem !important; }
div[data-testid="stExpander"] { margin-top:.2rem !important; }
.game-status { padding:8px; border-radius:10px; text-align:center; background:#161616; color:white; margin:5px 0; }
.winner-box { padding:12px; border-radius:12px; background:#171717; color:white; text-align:center; font-size:1.15rem; font-weight:800; margin:8px 0; }
</style>
""", unsafe_allow_html=True)

COLORS = ["red", "green", "yellow", "blue"]
HEX = {"red":"#E53935", "green":"#43A047", "yellow":"#FDD835", "blue":"#1E88E5"}
DARK_HEX = {"red":"#8E1E1A", "green":"#245C2A", "yellow":"#9C8A10", "blue":"#0F4C86"}
TEAM_OF = {"red":"A", "yellow":"A", "green":"B", "blue":"B"}
DICE_SKINS = {
    "Classic White":{"bg":"#FFFFFF","pip":"#111111","border":"#333333"},
    "Royal Gold":{"bg":"#FFD700","pip":"#5A3E00","border":"#8A6A00"},
    "Ruby Red":{"bg":"#D32F2F","pip":"#FFFFFF","border":"#7A1010"},
    "Ocean Blue":{"bg":"#1565C0","pip":"#FFFFFF","border":"#0B3B75"},
    "Jet Black":{"bg":"#1B1B1B","pip":"#F5F5F5","border":"#000000"},
    "Emerald":{"bg":"#2E7D32","pip":"#FFFFFF","border":"#154B18"},
}
TOKEN_SHAPES = ["Pin", "Disc", "Diamond", "Star"]

# ============================================================
# BOARD GEOMETRY
# ============================================================

def rotate(cell):
    r, c = cell
    return 7 + (c - 7), 7 - (r - 7)

RED_QUARTER = [(6,1),(6,2),(6,3),(6,4),(6,5),(5,6),(4,6),(3,6),(2,6),(1,6),(0,6),(0,7),(0,8)]
RED_HOME_COL = [(7,1),(7,2),(7,3),(7,4),(7,5),(7,6)]

QUARTERS = {"red": RED_QUARTER}
HOME_COLS = {"red": RED_HOME_COL}
cur_q, cur_h = RED_QUARTER, RED_HOME_COL
for color in ["green", "yellow", "blue"]:
    cur_q = [rotate(c) for c in cur_q]
    cur_h = [rotate(c) for c in cur_h]
    QUARTERS[color] = cur_q
    HOME_COLS[color] = cur_h

GLOBAL_CELLS = QUARTERS["red"] + QUARTERS["green"] + QUARTERS["yellow"] + QUARTERS["blue"]
START_INDEX = {"red":0, "green":13, "yellow":26, "blue":39}
SAFE_GLOBAL = {0,8,13,21,26,34,39,47}
BASE_SLOTS = {
    "red":[(1,1),(1,4),(4,1),(4,4)],
    "green":[(1,10),(1,13),(4,10),(4,13)],
    "yellow":[(10,10),(10,13),(13,10),(13,13)],
    "blue":[(10,1),(10,4),(13,1),(13,4)],
}
CENTER = (7,7)
FINISH_POS = 58
TWO_PLAYER_COLORS = ["red", "yellow"]
THREE_PLAYER_COLORS = ["red", "green", "yellow"]
FOUR_PLAYER_COLORS = ["red", "green", "yellow", "blue"]


def cell_of(color, pos, token_idx):
    if pos == -1:
        return BASE_SLOTS[color][token_idx]
    if pos == FINISH_POS:
        return CENTER
    if pos <= 51:
        gi = (START_INDEX[color] + pos) % 52
        return GLOBAL_CELLS[gi]
    return HOME_COLS[color][pos - 52]


def global_index_safe(pos, color):
    if pos < 0 or pos > 51:
        return True
    gi = (START_INDEX[color] + pos) % 52
    return gi in SAFE_GLOBAL

# ============================================================
# GAME STATE
# ============================================================

def start_new_game(mode, colors_in_play, names, is_human, dice_skin, token_shape, commentary_on, groq_key):
    first_color = colors_in_play[0]
    st.session_state.game = {
        "mode": mode,
        "colors": colors_in_play,
        "names": names,
        "is_human": is_human,
        "positions": {c:[-1,-1,-1,-1] for c in COLORS},
        "turn_idx": 0,
        "dice": None,
        "movable": [],
        "consecutive_sixes": 0,
        "awaiting_continue": False,
        "log": [f"Game started. {names[first_color]} ({first_color}) goes first."],
        "winner": None,
        "last_commentary": None,
    }
    st.session_state.dice_skin = dice_skin
    st.session_state.token_shape = token_shape
    st.session_state.commentary_on = commentary_on
    st.session_state.groq_key = groq_key
    st.session_state.stage = "playing"


def current_color():
    return st.session_state.game["colors"][st.session_state.game["turn_idx"]]


def next_turn():
    g = st.session_state.game
    g["turn_idx"] = (g["turn_idx"] + 1) % len(g["colors"])
    g["dice"] = None
    g["movable"] = []
    g["consecutive_sixes"] = 0
    g["awaiting_continue"] = False


def check_winner():
    g = st.session_state.game
    if g["mode"] == "team":
        for team in ["A", "B"]:
            members = [c for c in g["colors"] if TEAM_OF[c] == team]
            if members and all(all(p == FINISH_POS for p in g["positions"][m]) for m in members):
                names = " & ".join(g["names"][m] for m in members)
                return f"Team {team} ({names})"
        return None
    for c in g["colors"]:
        if all(p == FINISH_POS for p in g["positions"][c]):
            return g["names"][c]
    return None


def movable_tokens(color, dice_val):
    positions = st.session_state.game["positions"][color]
    movable = []
    for i, p in enumerate(positions):
        if p == -1:
            if dice_val == 6:
                movable.append(i)
        elif p != FINISH_POS and p + dice_val <= FINISH_POS:
            movable.append(i)
    return movable


def apply_move(color, token_idx, dice_val):
    g = st.session_state.game
    positions = g["positions"][color]
    p = positions[token_idx]
    new_p = 0 if p == -1 else p + dice_val
    positions[token_idx] = new_p
    name = g["names"][color]
    msg = (f"{name} moved token {token_idx + 1} to HOME! 🏆" if new_p == FINISH_POS
           else f"{name} moved token {token_idx + 1} to position {new_p}.")
    captured = False
    if new_p <= 51 and not global_index_safe(new_p, color):
        gi_new = (START_INDEX[color] + new_p) % 52
        for other in g["colors"]:
            if other == color:
                continue
            if g["mode"] == "team" and TEAM_OF[other] == TEAM_OF[color]:
                continue
            for j, op in enumerate(g["positions"][other]):
                if op in (-1, FINISH_POS) or op > 51:
                    continue
                other_gi = (START_INDEX[other] + op) % 52
                if other_gi == gi_new:
                    g["positions"][other][j] = -1
                    captured = True
                    msg += f" Captured {g['names'][other]}'s token!"
    g["log"].insert(0, msg)
    return new_p == FINISH_POS or captured


def ai_choose_token(color, dice_val, movable):
    g = st.session_state.game
    positions = g["positions"][color]
    def would_capture(idx):
        p = positions[idx]
        new_p = 0 if p == -1 else p + dice_val
        if new_p > 51 or global_index_safe(new_p, color):
            return False
        gi_new = (START_INDEX[color] + new_p) % 52
        for other in g["colors"]:
            if other == color or (g["mode"] == "team" and TEAM_OF[other] == TEAM_OF[color]):
                continue
            for op in g["positions"][other]:
                if op != -1 and op <= 51 and (START_INDEX[other] + op) % 52 == gi_new:
                    return True
        return False
    capturing = [i for i in movable if would_capture(i)]
    if capturing:
        return capturing[0]
    if dice_val == 6:
        for i in movable:
            if positions[i] == -1:
                return i
    return max(movable, key=lambda i: positions[i])

# ============================================================
# GROQ COMMENTARY
# ============================================================

def get_groq_commentary(log_line, api_key):
    if not api_key:
        return None
    try:
        import requests
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
            json={
                "model":"llama-3.1-8b-instant",
                "messages":[
                    {"role":"system","content":"You are a hype Ludo commentator. Give one short punchy sentence. Maximum 15 words and at most one emoji."},
                    {"role":"user","content":log_line},
                ],
                "max_tokens":40,
                "temperature":0.9,
            },
            timeout=6,
        )
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        pass
    return None

# ============================================================
# TOKEN SVG
# ============================================================

def token_shape_svg(shape, cx, cy, r, fill, stroke):
    if shape == "Disc":
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    if shape == "Diamond":
        pts = f"{cx},{cy-r*1.3} {cx+r*1.1},{cy} {cx},{cy+r*1.3} {cx-r*1.1},{cy}"
        return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    if shape == "Star":
        pts = []
        for i in range(10):
            ang = math.pi / 5 * i - math.pi / 2
            rad = r * 1.3 if i % 2 == 0 else r * 0.55
            pts.append(f"{cx + rad*math.cos(ang)},{cy + rad*math.sin(ang)}")
        return f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
    return (
        f'<path d="M {cx} {cy+r*1.4} C {cx-r*1.2} {cy+r*0.2} {cx-r*1.1} {cy-r*1.3} {cx} {cy-r*1.3} '
        f'C {cx+r*1.1} {cy-r*1.3} {cx+r*1.2} {cy+r*0.2} {cx} {cy+r*1.4} Z" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>'
        f'<circle cx="{cx}" cy="{cy-r*0.5}" r="{r*0.4}" fill="white" opacity="0.85"/>'
    )

# ============================================================
# BOARD SVG
# ============================================================

def svg_board(size=310):
    cell = size / 15
    parts = [f'<svg viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg" style="background:#f4f1e8; max-width:100%;">']

    def rect(r, c, color, w=1, h=1):
        parts.append(f'<rect x="{c*cell}" y="{r*cell}" width="{w*cell}" height="{h*cell}" fill="{color}" stroke="#555" stroke-width="0.4"/>')

    quad_origin = {"red":(0,0),"green":(0,9),"yellow":(9,9),"blue":(9,0)}
    for color, (ro, co) in quad_origin.items():
        parts.append(f'<rect x="{co*cell}" y="{ro*cell}" width="{6*cell}" height="{6*cell}" fill="{HEX[color]}22" stroke="#999" stroke-width="0.4"/>')
        parts.append(f'<rect x="{(co+1)*cell}" y="{(ro+1)*cell}" width="{4*cell}" height="{4*cell}" fill="white" stroke="{HEX[color]}" stroke-width="1.2" rx="6"/>')
        for sr, sc in BASE_SLOTS[color]:
            cx, cy = (sc+.5)*cell, (sr+.5)*cell
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{cell*.26}" fill="{HEX[color]}33" stroke="{HEX[color]}" stroke-width="0.6"/>')

    for gi, (r, c) in enumerate(GLOBAL_CELLS):
        rect(r, c, "#FFF3B0" if gi in SAFE_GLOBAL else "#FFFFFF")
        if gi in SAFE_GLOBAL:
            cx, cy = (c+.5)*cell, (r+.5)*cell
            parts.append(f'<text x="{cx}" y="{cy+4}" font-size="{cell*.5}" text-anchor="middle">★</text>')

    for color in COLORS:
        for r, c in HOME_COLS[color]:
            rect(r, c, HEX[color] + "cc")

    for color in COLORS:
        r, c = GLOBAL_CELLS[START_INDEX[color]]
        rect(r, c, HEX[color])

    pts = [
        f"{6*cell},{6*cell} {7.5*cell},{7.5*cell} {6*cell},{9*cell}",
        f"{6*cell},{6*cell} {7.5*cell},{7.5*cell} {9*cell},{6*cell}",
        f"{9*cell},{6*cell} {7.5*cell},{7.5*cell} {9*cell},{9*cell}",
        f"{6*cell},{9*cell} {7.5*cell},{7.5*cell} {9*cell},{9*cell}",
    ]
    for pt, col in zip(pts, [HEX["red"],HEX["green"],HEX["yellow"],HEX["blue"]]):
        parts.append(f'<polygon points="{pt}" fill="{col}"/>')

    parts.append(f'<rect x="0" y="0" width="{size}" height="{size}" fill="none" stroke="#222" stroke-width="2"/>')

    g = st.session_state.game
    shape = st.session_state.get("token_shape", "Pin")
    occupied = {}
    for color in g["colors"]:
        for idx, pos in enumerate(g["positions"][color]):
            r, c = cell_of(color, pos, idx)
            occupied.setdefault((r,c), []).append((color,idx))

    for (r,c), items in occupied.items():
        n = len(items)
        for k, (color, idx) in enumerate(items):
            offset_x = (k-(n-1)/2)*cell*.32 if n > 1 else 0
            cx = (c+.5)*cell + offset_x
            cy = (r+.5)*cell
            parts.append(token_shape_svg(shape, cx, cy, cell*.30, HEX[color], DARK_HEX[color]))
            parts.append(f'<text x="{cx}" y="{cy+3}" font-size="{cell*.22}" text-anchor="middle" fill="#222" font-weight="bold">{idx+1}</text>')

    parts.append("</svg>")
    return "".join(parts)

# ============================================================
# DICE SVG
# ============================================================

def dice_svg(value, skin_name, size=64):
    skin = DICE_SKINS[skin_name]
    pip_positions = {
        1:[(.5,.5)], 2:[(.28,.28),(.72,.72)], 3:[(.28,.28),(.5,.5),(.72,.72)],
        4:[(.28,.28),(.72,.28),(.28,.72),(.72,.72)],
        5:[(.28,.28),(.72,.28),(.5,.5),(.28,.72),(.72,.72)],
        6:[(.28,.25),(.72,.25),(.28,.5),(.72,.5),(.28,.75),(.72,.75)]
    }
    parts = [f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">',
             f'<rect x="3" y="3" width="{size-6}" height="{size-6}" rx="12" fill="{skin["bg"]}" stroke="{skin["border"]}" stroke-width="3"/>']
    for x,y in pip_positions.get(value, []):
        parts.append(f'<circle cx="{x*size}" cy="{y*size}" r="{size*.075}" fill="{skin["pip"]}"/>')
    parts.append("</svg>")
    return "".join(parts)

# ============================================================
# SETUP
# ============================================================

if "stage" not in st.session_state:
    st.session_state.stage = "setup"

if st.session_state.stage == "setup":
    st.title("🎲 Ludo Master")
    st.caption("Play Ludo with friends or against Computer AI.")
    st.subheader("Game Mode")
    mode_choice = st.radio("Choose mode", ["Classic", "Team Up"], horizontal=True)
    st.subheader("Players")
    player_count = st.selectbox("Number of players", [2,3,4], index=1)
    colors_in_play = {2:TWO_PLAYER_COLORS, 3:THREE_PLAYER_COLORS, 4:FOUR_PLAYER_COLORS}[player_count]
    names, is_human = {}, {}
    st.subheader("Player Setup")
    for color in colors_in_play:
        c1,c2 = st.columns(2)
        with c1:
            names[color] = st.text_input(f"{color.title()} player", value=f"{color.title()} Player", key=f"name_{color}")
        with c2:
            role = st.selectbox("Type", ["Human","Computer"], key=f"role_{color}")
            is_human[color] = role == "Human"
    st.subheader("Appearance")
    token_shape = st.selectbox("Token shape", TOKEN_SHAPES)
    dice_skin = st.selectbox("Dice design", list(DICE_SKINS.keys()))
    commentary_on = st.checkbox("Enable AI commentary", value=False)
    groq_key = st.text_input("Groq API Key", type="password") if commentary_on else ""
    if st.button("🎮 START GAME", use_container_width=True):
        actual_mode = "team" if mode_choice == "Team Up" else "computer"
        start_new_game(actual_mode, colors_in_play, names, is_human, dice_skin, token_shape, commentary_on, groq_key)
        st.rerun()

# ============================================================
# GAME SCREEN
# ============================================================

elif st.session_state.stage == "playing":
    g = st.session_state.game
    color = current_color()
    player_name = g["names"][color]
    winner = check_winner()
    g["winner"] = winner

    st.title("🎲 Ludo Master")

    if winner:
        st.markdown(f'<div class="winner-box">🏆 {winner} WINS! 🏆</div>', unsafe_allow_html=True)
        st.success("Congratulations!")
        if st.button("🔄 New Game", use_container_width=True):
            st.session_state.stage = "setup"
            st.rerun()
        st.stop()

    st.markdown(f'<div class="game-status">🎯 <b>{player_name}</b> ({color.title()}) — Turn</div>', unsafe_allow_html=True)
    st.markdown(svg_board(330), unsafe_allow_html=True)
    st.write("")

    # AI turn is processed before showing human controls.
    if not g["is_human"][color]:
        if g["dice"] is None:
            with st.spinner(f"{player_name} is rolling..."):
                time.sleep(.5)
                dice_value = random.randint(1,6)
            g["dice"] = dice_value
            g["movable"] = movable_tokens(color, dice_value)
            g["log"].insert(0, f"{player_name} rolled {dice_value}.")
            st.rerun()
        elif g["movable"]:
            dice_value = g["dice"]
            with st.spinner(f"{player_name} is choosing a token..."):
                time.sleep(.5)
                token_idx = ai_choose_token(color, dice_value, g["movable"])
                apply_move(color, token_idx, dice_value)
            winner = check_winner()
            if winner:
                g["winner"] = winner
            elif dice_value != 6:
                next_turn()
            else:
                g["dice"], g["movable"] = None, []
            st.rerun()
        else:
            if g["dice"] != 6:
                next_turn()
            else:
                g["dice"], g["movable"] = None, []
            st.rerun()

    # Human controls
    if g["is_human"][color]:
        dice_value = g["dice"]
        if dice_value is None:
            if st.button("🎲 ROLL DICE", use_container_width=True):
                dice_value = random.randint(1,6)
                g["dice"] = dice_value
                g["movable"] = movable_tokens(color, dice_value)
                g["log"].insert(0, f"{player_name} rolled {dice_value}.")
                if not g["movable"] and dice_value != 6:
                    next_turn()
                st.rerun()
        else:
            st.markdown(dice_svg(dice_value, st.session_state.dice_skin), unsafe_allow_html=True)
            st.write(f"**{player_name} rolled {dice_value}**")
            movable = g["movable"]
            if not movable:
                st.info("No token can move.")
                if st.button("➡️ NEXT TURN", use_container_width=True):
                    next_turn()
                    st.rerun()
            else:
                st.write("Choose a token:")
                cols = st.columns(len(movable))
                for col, token_idx in zip(cols, movable):
                    with col:
                        if st.button(f"Token {token_idx+1}", key=f"move_{color}_{token_idx}", use_container_width=True):
                            apply_move(color, token_idx, dice_value)
                            winner = check_winner()
                            if winner:
                                g["winner"] = winner
                            elif dice_value == 6:
                                g["dice"], g["movable"] = None, []
                            else:
                                next_turn()
                            st.rerun()

    # Commentary
    if st.session_state.get("commentary_on", False) and g["log"]:
        latest = g["log"][0]
        if g.get("last_commentary") != latest:
            comment = get_groq_commentary(latest, st.session_state.get("groq_key", ""))
            if comment:
                g["last_commentary"] = latest
                st.info(f"🎙️ {comment}")

    with st.expander("📜 Game Log"):
        for item in g["log"][:15]:
            st.write(f"• {item}")

    c1,c2 = st.columns(2)
    with c1:
        if st.button("🔄 New Game", use_container_width=True):
            st.session_state.stage = "setup"
            st.rerun()
    with c2:
        if st.button("🗑️ Clear Log", use_container_width=True):
            g["log"] = []
            st.rerun()
