import streamlit as st
import random
import json
import os

# ============================================================
# LUDO KING-STYLE GAME  —  built with a rotationally-symmetric
# board model so all four arms are guaranteed to line up.
# ============================================================

st.set_page_config(page_title="Ludo Master", page_icon="🎲", layout="centered")

COLORS = ["red", "green", "yellow", "blue"]
HEX = {
    "red": "#E53935",
    "green": "#43A047",
    "yellow": "#FDD835",
    "blue": "#1E88E5",
}
DARK_HEX = {
    "red": "#8E1E1A",
    "green": "#245C2A",
    "yellow": "#9C8A10",
    "blue": "#0F4C86",
}

DICE_SKINS = {
    "Classic White": {"bg": "#FFFFFF", "pip": "#111111", "border": "#333333"},
    "Royal Gold": {"bg": "#FFD700", "pip": "#5A3E00", "border": "#8A6A00"},
    "Ruby Red": {"bg": "#D32F2F", "pip": "#FFFFFF", "border": "#7A1010"},
    "Ocean Blue": {"bg": "#1565C0", "pip": "#FFFFFF", "border": "#0B3B75"},
    "Jet Black": {"bg": "#1B1B1B", "pip": "#F5F5F5", "border": "#000000"},
    "Emerald": {"bg": "#2E7D32", "pip": "#FFFFFF", "border": "#154B18"},
}

TEAM_OF = {"red": "A", "yellow": "A", "green": "B", "blue": "B"}

# ---------------- board geometry (built once, symmetrically) ----------------

def rotate(cell):
    """Rotate a (row,col) 90 deg clockwise around the board center (7,7)."""
    r, c = cell
    return (7 + (c - 7), 7 - (r - 7))


RED_QUARTER = [
    (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
    (5, 6), (4, 6), (3, 6), (2, 6), (1, 6), (0, 6),
    (0, 7), (0, 8),
]

RED_HOME_COL = [(7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6)]

QUARTERS = {"red": RED_QUARTER}
HOME_COLS = {"red": RED_HOME_COL}
cur_q, cur_h = RED_QUARTER, RED_HOME_COL
for col in ["green", "yellow", "blue"]:
    cur_q = [rotate(c) for c in cur_q]
    cur_h = [rotate(c) for c in cur_h]
    QUARTERS[col] = cur_q
    HOME_COLS[col] = cur_h

GLOBAL_CELLS = QUARTERS["red"] + QUARTERS["green"] + QUARTERS["yellow"] + QUARTERS["blue"]
START_INDEX = {"red": 0, "green": 13, "yellow": 26, "blue": 39}
SAFE_GLOBAL = {0, 8, 13, 21, 26, 34, 39, 47}

BASE_SLOTS = {
    "red":    [(1, 1), (1, 4), (4, 1), (4, 4)],
    "green":  [(1, 10), (1, 13), (4, 10), (4, 13)],
    "yellow": [(10, 10), (10, 13), (13, 10), (13, 13)],
    "blue":   [(10, 1), (10, 4), (13, 1), (13, 4)],
}

CENTER = (7, 7)

FINISH_POS = 58  # token position value meaning "home / finished"


def cell_of(color, pos, token_idx):
    """Return (row,col) board cell for a token at logical position `pos`."""
    if pos == -1:
        return BASE_SLOTS[color][token_idx]
    if pos == FINISH_POS:
        return CENTER
    if pos <= 51:
        gi = (START_INDEX[color] + pos) % 52
        return GLOBAL_CELLS[gi]
    # home column, pos 52..57
    return HOME_COLS[color][pos - 52]


def is_safe_pos(pos):
    if pos == -1 or pos >= 52:
        return True
    return pos in {(g - 0) for g in range(0)}  # placeholder, replaced below


def global_index_safe(pos, color):
    if pos < 0 or pos > 51:
        return True
    gi = (START_INDEX[color] + pos) % 52
    return gi in SAFE_GLOBAL


# ---------------- game state ----------------

def fresh_state(colors_in_play, human_flags, mode):
    positions = {c: [-1, -1, -1, -1] for c in COLORS}
    return {
        "mode": mode,                     # "computer" | "local" | "team"
        "colors": colors_in_play,         # list of colors actually playing
        "is_human": human_flags,          # dict color -> bool
        "positions": positions,
        "turn_idx": 0,
        "dice": None,
        "movable": [],
        "consecutive_sixes": 0,
        "log": ["Game started. " + colors_in_play[0].capitalize() + " goes first."],
        "winner": None,
        "extra_turn": False,
    }


def start_new_game(mode, num_local_players, dice_skin, commentary_on):
    if mode == "computer":
        colors_in_play = ["red", "green", "yellow", "blue"]
        is_human = {"red": True, "green": False, "yellow": False, "blue": False}
    elif mode == "team":
        colors_in_play = ["red", "green", "yellow", "blue"]
        is_human = {c: True for c in colors_in_play}
    else:  # local pass & play
        colors_in_play = COLORS[:num_local_players]
        is_human = {c: True for c in colors_in_play}

    st.session_state.game = fresh_state(colors_in_play, is_human, mode)
    st.session_state.dice_skin = dice_skin
    st.session_state.commentary_on = commentary_on


def current_color():
    g = st.session_state.game
    return g["colors"][g["turn_idx"]]


def next_turn(give_extra=False):
    g = st.session_state.game
    if give_extra:
        g["dice"] = None
        g["movable"] = []
        return
    g["turn_idx"] = (g["turn_idx"] + 1) % len(g["colors"])
    g["dice"] = None
    g["movable"] = []
    g["consecutive_sixes"] = 0


def team_mates(color):
    team = TEAM_OF[color]
    return [c for c in COLORS if TEAM_OF[c] == team]


def check_winner():
    g = st.session_state.game
    if g["mode"] == "team":
        for team in ["A", "B"]:
            members = [c for c in COLORS if TEAM_OF[c] == team]
            if all(all(p == FINISH_POS for p in g["positions"][m]) for m in members):
                return "Team " + team + " (" + " & ".join(members).title() + ")"
        return None
    else:
        for c in g["colors"]:
            if all(p == FINISH_POS for p in g["positions"][c]):
                return c.capitalize()
        return None


def movable_tokens(color, dice_val):
    g = st.session_state.game
    positions = g["positions"][color]
    movable = []
    for i, p in enumerate(positions):
        if p == -1:
            if dice_val == 6:
                movable.append(i)
        elif p == FINISH_POS:
            continue
        else:
            if p + dice_val <= FINISH_POS:
                movable.append(i)
    return movable


def apply_move(color, token_idx, dice_val):
    g = st.session_state.game
    positions = g["positions"][color]
    p = positions[token_idx]
    if p == -1:
        new_p = 0
    else:
        new_p = p + dice_val
    positions[token_idx] = new_p

    msg = f"{color.capitalize()} moved a token to " + \
          ("HOME! 🏆" if new_p == FINISH_POS else f"position {new_p}.")

    captured = False
    # capture check only on shared track, not safe squares, not home column
    if new_p <= 51 and not global_index_safe(new_p, color):
        gi_new = (START_INDEX[color] + new_p) % 52
        for other in g["colors"]:
            if other == color:
                continue
            if g["mode"] == "team" and TEAM_OF[other] == TEAM_OF[color]:
                continue
            for j, op in enumerate(g["positions"][other]):
                if op == -1 or op == FINISH_POS or op > 51:
                    continue
                gi_other = (START_INDEX[other] + op) % 52
                if gi_other == gi_new:
                    g["positions"][other][j] = -1
                    captured = True
                    msg += f" Captured {other.capitalize()}'s token — sent home!"

    g["log"].insert(0, msg)
    return new_p == FINISH_POS or captured  # earns extra turn


def ai_choose_token(color, dice_val, movable):
    """Simple heuristic AI: prefer capture > exit base > furthest token."""
    g = st.session_state.game
    positions = g["positions"][color]

    def would_capture(idx):
        p = positions[idx]
        new_p = 0 if p == -1 else p + dice_val
        if new_p > 51 or global_index_safe(new_p, color):
            return False
        gi_new = (START_INDEX[color] + new_p) % 52
        for other in g["colors"]:
            if other == color or TEAM_OF.get(other) == TEAM_OF.get(color):
                continue
            for op in g["positions"][other]:
                if op != -1 and op <= 51:
                    gi_other = (START_INDEX[other] + op) % 52
                    if gi_other == gi_new:
                        return True
        return False

    capturing = [i for i in movable if would_capture(i)]
    if capturing:
        return capturing[0]
    if dice_val == 6 and any(positions[i] == -1 for i in movable):
        return next(i for i in movable if positions[i] == -1)
    # otherwise move the token that is furthest along
    return max(movable, key=lambda i: positions[i])


# ---------------- optional Groq commentary ----------------

def get_groq_commentary(log_line, api_key):
    try:
        import requests
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": "You are a hype sports commentator for a Ludo board game. "
                                                   "React to the move in ONE short punchy sentence (max 15 words). "
                                                   "No emojis besides at most one."},
                    {"role": "user", "content": log_line},
                ],
                "max_tokens": 40,
                "temperature": 0.9,
            },
            timeout=6,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        pass
    return None


# ---------------- SVG rendering ----------------

def svg_board(size=480):
    cell = size / 15
    parts = [f'<svg viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg" style="background:#f4f1e8;">']

    def rect(r, c, color, w=1, h=1):
        parts.append(
            f'<rect x="{c*cell}" y="{r*cell}" width="{w*cell}" height="{h*cell}" '
            f'fill="{color}" stroke="#555" stroke-width="0.5"/>'
        )

    # base quadrant backgrounds
    quad_origin = {"red": (0, 0), "green": (0, 9), "yellow": (9, 9), "blue": (9, 0)}
    for color, (ro, co) in quad_origin.items():
        parts.append(
            f'<rect x="{co*cell}" y="{ro*cell}" width="{6*cell}" height="{6*cell}" '
            f'fill="{HEX[color]}22" stroke="#999" stroke-width="0.5"/>'
        )
        parts.append(
            f'<rect x="{(co+1)*cell}" y="{(ro+1)*cell}" width="{4*cell}" height="{4*cell}" '
            f'fill="white" stroke="{HEX[color]}" stroke-width="1.5" rx="6"/>'
        )
        for (sr, sc) in BASE_SLOTS[color]:
            cx, cy = (sc + 0.5) * cell, (sr + 0.5) * cell
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{cell*0.28}" fill="{HEX[color]}33" stroke="{HEX[color]}" stroke-width="0.7"/>')

    # plain background for the 3x3 middle band and cross arms (path track)
    for gi, (r, c) in enumerate(GLOBAL_CELLS):
        fill = "#FFFFFF"
        if gi in SAFE_GLOBAL:
            fill = "#FFF3B0"
        rect(r, c, fill)
        if gi in SAFE_GLOBAL:
            cx, cy = (c + 0.5) * cell, (r + 0.5) * cell
            parts.append(f'<text x="{cx}" y="{cy+4}" font-size="{cell*0.55}" text-anchor="middle">★</text>')

    # home columns
    for color in COLORS:
        for (r, c) in HOME_COLS[color]:
            rect(r, c, HEX[color] + "cc")

    # start squares slightly emphasised
    for color in COLORS:
        r, c = GLOBAL_CELLS[START_INDEX[color]]
        rect(r, c, HEX[color])

    # center home triangle
    cx, cy = 7.5 * cell, 7.5 * cell
    tri_colors = [HEX["red"], HEX["green"], HEX["yellow"], HEX["blue"]]
    pts = [
        f"{6*cell},{6*cell} {7.5*cell},{7.5*cell} {6*cell},{9*cell}",
        f"{6*cell},{6*cell} {7.5*cell},{7.5*cell} {9*cell},{6*cell}",
        f"{9*cell},{6*cell} {7.5*cell},{7.5*cell} {9*cell},{9*cell}",
        f"{6*cell},{9*cell} {7.5*cell},{7.5*cell} {9*cell},{9*cell}",
    ]
    for pt, col in zip(pts, tri_colors):
        parts.append(f'<polygon points="{pt}" fill="{col}"/>')

    # outer border
    parts.append(f'<rect x="0" y="0" width="{size}" height="{size}" fill="none" stroke="#222" stroke-width="2"/>')

    # tokens
    g = st.session_state.game
    occupied = {}
    for color in g["colors"]:
        for idx, pos in enumerate(g["positions"][color]):
            r, c = cell_of(color, pos, idx)
            occupied.setdefault((r, c), []).append((color, idx))

    for (r, c), items in occupied.items():
        n = len(items)
        for k, (color, idx) in enumerate(items):
            offset_x = (k - (n - 1) / 2) * cell * 0.32 if n > 1 else 0
            cx = (c + 0.5) * cell + offset_x
            cy = (r + 0.5) * cell
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{cell*0.30}" fill="{HEX[color]}" stroke="{DARK_HEX[color]}" stroke-width="2"/>')
            parts.append(f'<circle cx="{cx-cell*0.08}" cy="{cy-cell*0.08}" r="{cell*0.08}" fill="#ffffff88"/>')

    parts.append("</svg>")
    return "".join(parts)


def svg_dice(value, skin_name):
    skin = DICE_SKINS[skin_name]
    s = 90
    pip_positions = {
        1: [(0.5, 0.5)],
        2: [(0.25, 0.25), (0.75, 0.75)],
        3: [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],
        4: [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)],
        5: [(0.25, 0.25), (0.75, 0.25), (0.5, 0.5), (0.25, 0.75), (0.75, 0.75)],
        6: [(0.25, 0.25), (0.75, 0.25), (0.25, 0.5), (0.75, 0.5), (0.25, 0.75), (0.75, 0.75)],
    }
    parts = [f'<svg viewBox="0 0 {s} {s}" xmlns="http://www.w3.org/2000/svg">']
    parts.append(f'<rect x="4" y="4" width="{s-8}" height="{s-8}" rx="14" fill="{skin["bg"]}" stroke="{skin["border"]}" stroke-width="4"/>')
    if value:
        for (px, py) in pip_positions[value]:
            parts.append(f'<circle cx="{px*s}" cy="{py*s}" r="{s*0.08}" fill="{skin["pip"]}"/>')
    parts.append("</svg>")
    return "".join(parts)


# ============================================================
# SIDEBAR — setup
# ============================================================

st.sidebar.title("🎲 Ludo Master Setup")

mode_label = st.sidebar.radio(
    "Game mode",
    ["Play vs Computer", "Pass & Play (2-4 players, one device)", "Team Up (2v2)"],
)
mode_map = {
    "Play vs Computer": "computer",
    "Pass & Play (2-4 players, one device)": "local",
    "Team Up (2v2)": "team",
}
mode = mode_map[mode_label]

num_local = 4
if mode == "local":
    num_local = st.sidebar.slider("Number of players", 2, 4, 4)

dice_skin = st.sidebar.selectbox("Dice design", list(DICE_SKINS.keys()))

st.sidebar.markdown("---")
commentary_on = st.sidebar.checkbox("Enable AI commentary (Groq, optional)", value=False)
groq_key_input = ""
if commentary_on:
    groq_key_input = st.sidebar.text_input(
        "Groq API key",
        value=st.secrets.get("GROQ_API_KEY", "") if hasattr(st, "secrets") else "",
        type="password",
        help="Get a free key at console.groq.com. Stored only for this session.",
    )

if st.sidebar.button("🔄 Start New Game", type="primary", use_container_width=True):
    start_new_game(mode, num_local, dice_skin, commentary_on)
    st.session_state.groq_key = groq_key_input

st.sidebar.markdown("---")
st.sidebar.caption(
    "Online matchmaking with strangers isn't included — see the notes below the "
    "board for why, and what to add if you want real-time online play."
)

# ============================================================
# INIT
# ============================================================

if "game" not in st.session_state:
    start_new_game(mode, num_local, dice_skin, commentary_on)
    st.session_state.groq_key = groq_key_input

g = st.session_state.game

# ============================================================
# MAIN
# ============================================================

st.title("👑 LUDO MASTER")

winner = check_winner()
if winner and not g["winner"]:
    g["winner"] = winner

if g["winner"]:
    st.success(f"🏆 {g['winner']} wins! Start a new game from the sidebar to play again.")

col_board, col_side = st.columns([2, 1])

with col_board:
    st.components.v1.html(f'<div style="max-width:480px;margin:auto;">{svg_board()}</div>', height=500)

with col_side:
    turn_color = current_color()
    st.markdown(f"### Turn: :{('red' if turn_color=='red' else 'green' if turn_color=='green' else 'orange' if turn_color=='yellow' else 'blue')}[{turn_color.upper()}]")
    if g["mode"] == "team":
        st.caption(f"Team {TEAM_OF[turn_color]}")

    dice_val = g["dice"]
    st.components.v1.html(f'<div style="width:90px;margin:auto;">{svg_dice(dice_val, st.session_state.dice_skin)}</div>', height=100)

    is_human_turn = g["is_human"].get(turn_color, True)
    disabled = bool(g["winner"])

    if dice_val is None:
        if st.button("🎲 Roll Dice", disabled=disabled, use_container_width=True):
            roll = random.randint(1, 6)
            g["dice"] = roll
            g["movable"] = movable_tokens(turn_color, roll)

            if roll == 6:
                g["consecutive_sixes"] += 1
            else:
                g["consecutive_sixes"] = 0

            if g["consecutive_sixes"] == 3:
                g["log"].insert(0, f"{turn_color.capitalize()} rolled three 6's in a row — turn forfeited!")
                next_turn()
            elif not g["movable"]:
                g["log"].insert(0, f"{turn_color.capitalize()} rolled a {roll} but has no valid move.")
                if roll == 6:
                    pass  # extra turn even with no move, re-roll allowed
                    g["dice"] = None
                else:
                    next_turn()
            st.rerun()
    else:
        if is_human_turn:
            st.write("Choose a token to move:")
            for idx in g["movable"]:
                pos = g["positions"][turn_color][idx]
                label = "Base" if pos == -1 else ("Home!" if pos == FINISH_POS else f"pos {pos}")
                if st.button(f"Token {idx+1} ({label})", key=f"mv_{idx}", use_container_width=True):
                    extra = apply_move(turn_color, idx, dice_val)
                    if st.session_state.get("commentary_on") and st.session_state.get("groq_key"):
                        c = get_groq_commentary(g["log"][0], st.session_state["groq_key"])
                        if c:
                            g["log"].insert(0, f"🎙️ {c}")
                    give_extra = extra or (dice_val == 6)
                    next_turn(give_extra=give_extra)
                    st.rerun()
        else:
            st.info("Computer is thinking...")
            idx = ai_choose_token(turn_color, dice_val, g["movable"])
            extra = apply_move(turn_color, idx, dice_val)
            give_extra = extra or (dice_val == 6)
            next_turn(give_extra=give_extra)
            st.rerun()

st.markdown("---")
st.subheader("Game log")
for line in g["log"][:12]:
    st.write("• " + line)

with st.expander("ℹ️ About the 'Online' and 'Friends' modes"):
    st.markdown(
        """
**Why there's no live online matchmaking here:** Streamlit apps re-run the whole
script on every interaction and don't keep an open, low-latency connection between
different users' browsers. That rules out the kind of real-time matchmaking you see
in the screenshot (168k+ concurrent players, live turns pushed instantly to opponents).

**What Pass & Play / Team Up give you instead:** the full game — 2 to 4 players,
or 2v2 teams — playable together on one device, taking turns. This is genuinely
multiplayer, just not remote/real-time.

**If you want true online play later**, the usual path is:
1. Add a small realtime backend (Firebase Realtime Database / Supabase Realtime,
   or a lightweight Socket.IO server) that stores the shared game state.
2. Have this Streamlit app read/write to that backend instead of `st.session_state`,
   and use `streamlit-autorefresh` (or similar) to poll for the other player's moves
   every 1-2 seconds.
3. For truly instant, low-latency play, move the UI off Streamlit entirely to a
   small React/Flask + WebSocket app — Streamlit isn't built for that.

None of this requires Gemini or Groq — those are language-model APIs, not game
backends. Your Groq key is only used here for the optional one-line commentary.
        """
    )
