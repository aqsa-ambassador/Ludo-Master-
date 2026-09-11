import streamlit as st
import random

# ============================================================
# LUDO MASTER — compact, single-screen UI + setup wizard
# ============================================================

st.set_page_config(page_title="Ludo Master", page_icon="🎲", layout="centered")

st.markdown(
    """
    <style>
    .block-container {padding-top: 0.8rem; padding-bottom: 0.5rem; max-width: 460px;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton>button {padding: 0.35rem 0.6rem;}
    h1 {font-size: 1.6rem !important; margin-bottom: 0.2rem !important;}
    h3 {margin-top: 0.2rem !important; margin-bottom: 0.2rem !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

COLORS = ["red", "green", "yellow", "blue"]
HEX = {"red": "#E53935", "green": "#43A047", "yellow": "#FDD835", "blue": "#1E88E5"}
DARK_HEX = {"red": "#8E1E1A", "green": "#245C2A", "yellow": "#9C8A10", "blue": "#0F4C86"}
TEAM_OF = {"red": "A", "yellow": "A", "green": "B", "blue": "B"}

DICE_SKINS = {
    "Classic White": {"bg": "#FFFFFF", "pip": "#111111", "border": "#333333"},
    "Royal Gold": {"bg": "#FFD700", "pip": "#5A3E00", "border": "#8A6A00"},
    "Ruby Red": {"bg": "#D32F2F", "pip": "#FFFFFF", "border": "#7A1010"},
    "Ocean Blue": {"bg": "#1565C0", "pip": "#FFFFFF", "border": "#0B3B75"},
    "Jet Black": {"bg": "#1B1B1B", "pip": "#F5F5F5", "border": "#000000"},
    "Emerald": {"bg": "#2E7D32", "pip": "#FFFFFF", "border": "#154B18"},
}

TOKEN_SHAPES = ["Pin", "Disc", "Diamond", "Star"]

# ---------------- board geometry (built once, symmetrically) ----------------

def rotate(cell):
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


# ---------------- game state ----------------

def start_new_game(mode, colors_in_play, names, is_human, dice_skin, token_shape, commentary_on, groq_key):
    st.session_state.game = {
        "mode": mode,
        "colors": colors_in_play,
        "names": names,
        "is_human": is_human,
        "positions": {c: [-1, -1, -1, -1] for c in COLORS},
        "turn_idx": 0,
        "dice": None,
        "movable": [],
        "consecutive_sixes": 0,
        "awaiting_continue": False,
        "log": [f"Game started. {names[colors_in_play[0]]} ({colors_in_play[0]}) goes first."],
        "winner": None,
    }
    st.session_state.dice_skin = dice_skin
    st.session_state.token_shape = token_shape
    st.session_state.commentary_on = commentary_on
    st.session_state.groq_key = groq_key
    st.session_state.stage = "playing"


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


def check_winner():
    g = st.session_state.game
    if g["mode"] == "team":
        for team in ["A", "B"]:
            members = [c for c in COLORS if TEAM_OF[c] == team]
            if all(all(p == FINISH_POS for p in g["positions"][m]) for m in members):
                names = " & ".join(g["names"][m] for m in members)
                return f"Team {team} ({names})"
        return None
    for c in g["colors"]:
        if all(p == FINISH_POS for p in g["positions"][c]):
            return g["names"][c]
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
    new_p = 0 if p == -1 else p + dice_val
    positions[token_idx] = new_p

    name = g["names"][color]
    msg = f"{name} moved to " + ("HOME! 🏆" if new_p == FINISH_POS else f"pos {new_p}.")
    captured = False
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
                if (START_INDEX[other] + op) % 52 == gi_new:
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
            if other == color or TEAM_OF.get(other) == TEAM_OF.get(color):
                continue
            for op in g["positions"][other]:
                if op != -1 and op <= 51 and (START_INDEX[other] + op) % 52 == gi_new:
                    return True
        return False

    capturing = [i for i in movable if would_capture(i)]
    if capturing:
        return capturing[0]
    if dice_val == 6 and any(positions[i] == -1 for i in movable):
        return next(i for i in movable if positions[i] == -1)
    return max(movable, key=lambda i: positions[i])


def get_groq_commentary(log_line, api_key):
    try:
        import requests
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": "Hype sports commentator for Ludo. One short punchy sentence, max 15 words, at most one emoji."},
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

def token_shape_svg(shape, cx, cy, r, fill, stroke):
    if shape == "Disc":
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    if shape == "Diamond":
        pts = f"{cx},{cy-r*1.3} {cx+r*1.1},{cy} {cx},{cy+r*1.3} {cx-r*1.1},{cy}"
        return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    if shape == "Star":
        import math
        pts = []
        for i in range(10):
            ang = math.pi / 5 * i - math.pi / 2
            rad = r * 1.3 if i % 2 == 0 else r * 0.55
            pts.append(f"{cx+rad*math.cos(ang)},{cy+rad*math.sin(ang)}")
        return f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
    # default: Pin (teardrop)
    return (
        f'<path d="M {cx} {cy+r*1.4} C {cx-r*1.2} {cy+r*0.2} {cx-r*1.1} {cy-r*1.3} {cx} {cy-r*1.3} '
        f'C {cx+r*1.1} {cy-r*1.3} {cx+r*1.2} {cy+r*0.2} {cx} {cy+r*1.4} Z" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>'
        f'<circle cx="{cx}" cy="{cy-r*0.5}" r="{r*0.4}" fill="white" opacity="0.85"/>'
    )


def svg_board(size=360):
    cell = size / 15
    parts = [f'<svg viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg" style="background:#f4f1e8;">']

    def rect(r, c, color, w=1, h=1):
        parts.append(f'<rect x="{c*cell}" y="{r*cell}" width="{w*cell}" height="{h*cell}" fill="{color}" stroke="#555" stroke-width="0.4"/>')

    quad_origin = {"red": (0, 0), "green": (0, 9), "yellow": (9, 9), "blue": (9, 0)}
    for color, (ro, co) in quad_origin.items():
        parts.append(f'<rect x="{co*cell}" y="{ro*cell}" width="{6*cell}" height="{6*cell}" fill="{HEX[color]}22" stroke="#999" stroke-width="0.4"/>')
        parts.append(f'<rect x="{(co+1)*cell}" y="{(ro+1)*cell}" width="{4*cell}" height="{4*cell}" fill="white" stroke="{HEX[color]}" stroke-width="1.2" rx="6"/>')
        for (sr, sc) in BASE_SLOTS[color]:
            cx, cy = (sc + 0.5) * cell, (sr + 0.5) * cell
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{cell*0.26}" fill="{HEX[color]}33" stroke="{HEX[color]}" stroke-width="0.6"/>')

    for gi, (r, c) in enumerate(GLOBAL_CELLS):
        fill = "#FFF3B0" if gi in SAFE_GLOBAL else "#FFFFFF"
        rect(r, c, fill)
        if gi in SAFE_GLOBAL:
            cx, cy = (c + 0.5) * cell, (r + 0.5) * cell
            parts.append(f'<text x="{cx}" y="{cy+4}" font-size="{cell*0.5}" text-anchor="middle">★</text>')

    for color in COLORS:
        for (r, c) in HOME_COLS[color]:
            rect(r, c, HEX[color] + "cc")
    for color in COLORS:
        r, c = GLOBAL_CELLS[START_INDEX[color]]
        rect(r, c, HEX[color])

    tri_colors = [HEX["red"], HEX["green"], HEX["yellow"], HEX["blue"]]
    pts = [
        f"{6*cell},{6*cell} {7.5*cell},{7.5*cell} {6*cell},{9*cell}",
        f"{6*cell},{6*cell} {7.5*cell},{7.5*cell} {9*cell},{6*cell}",
        f"{9*cell},{6*cell} {7.5*cell},{7.5*cell} {9*cell},{9*cell}",
        f"{6*cell},{9*cell} {7.5*cell},{7.5*cell} {9*cell},{9*cell}",
    ]
    for pt, col in zip(pts, tri_colors):
        parts.append(f'<polygon points="{pt}" fill="{col}"/>')
    parts.append(f'<rect x="0" y="0" width="{size}" height="{size}" fill="none" stroke="#222" stroke-width="2"/>')

    g = st.session_state.game
    shape = st.session_state.get("token_shape", "Pin")
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
            parts.append(token_shape_svg(shape, cx, cy, cell * 0.28, HEX[color], DARK_HEX[color]))

    parts.append("</svg>")
    return "".join(parts)


def svg_dice(value, skin_name):
    skin = DICE_SKINS[skin_name]
    s = 70
    pip_positions = {
        1: [(0.5, 0.5)],
        2: [(0.25, 0.25), (0.75, 0.75)],
        3: [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],
        4: [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)],
        5: [(0.25, 0.25), (0.75, 0.25), (0.5, 0.5), (0.25, 0.75), (0.75, 0.75)],
        6: [(0.25, 0.25), (0.75, 0.25), (0.25, 0.5), (0.75, 0.5), (0.25, 0.75), (0.75, 0.75)],
    }
    parts = [f'<svg viewBox="0 0 {s} {s}" xmlns="http://www.w3.org/2000/svg">']
    parts.append(f'<rect x="3" y="3" width="{s-6}" height="{s-6}" rx="12" fill="{skin["bg"]}" stroke="{skin["border"]}" stroke-width="3"/>')
    if value:
        for (px, py) in pip_positions[value]:
            parts.append(f'<circle cx="{px*s}" cy="{py*s}" r="{s*0.075}" fill="{skin["pip"]}"/>')
    parts.append("</svg>")
    return "".join(parts)


# ============================================================
# SETUP WIZARD
# ============================================================

if "stage" not in st.session_state:
    st.session_state.stage = "setup"
    st.session_state.setup_mode = "Classic"
    st.session_state.setup_count = 4
    st.session_state.setup_roles = {c: "Human" for c in COLORS}
    st.session_state.setup_names = {c: c.capitalize() for c in COLORS}
    st.session_state.dice_skin = "Classic White"
    st.session_state.token_shape = "Pin"
    st.session_state.commentary_on = False
    st.session_state.groq_key = ""

if st.session_state.stage == "setup":
    st.title("👑 LUDO MASTER")
    st.caption("Choose color, name & mode — then hit Play")

    mode_choice = st.radio("Select game", ["Classic", "Team Up"], horizontal=True,
                            index=0 if st.session_state.setup_mode == "Classic" else 1)
    st.session_state.setup_mode = mode_choice

    if mode_choice == "Classic":
        st.write("**Players**")
        c1, c2, c3 = st.columns(3)
        for col, n in zip([c1, c2, c3], [2, 3, 4]):
            if col.button(f"{n}P", type="primary" if st.session_state.setup_count == n else "secondary", use_container_width=True):
                st.session_state.setup_count = n
        active_colors = {2: TWO_PLAYER_COLORS, 3: THREE_PLAYER_COLORS, 4: FOUR_PLAYER_COLORS}[st.session_state.setup_count]
    else:
        active_colors = FOUR_PLAYER_COLORS
        st.caption("Team Up: 🔴 Red + 🟡 Yellow  vs  🟢 Green + 🔵 Blue")

    st.write("**Choose color, name & type**")
    for color in active_colors:
        cc1, cc2, cc3 = st.columns([1, 2, 1.3])
        cc1.markdown(f"<div style='width:26px;height:26px;border-radius:50%;background:{HEX[color]};margin-top:6px;'></div>", unsafe_allow_html=True)
        st.session_state.setup_names[color] = cc2.text_input(
            "name", value=st.session_state.setup_names[color], key=f"name_{color}", label_visibility="collapsed"
        )
        st.session_state.setup_roles[color] = cc3.selectbox(
            "role", ["Human", "Computer"],
            index=["Human", "Computer"].index(st.session_state.setup_roles[color]),
            key=f"role_{color}", label_visibility="collapsed",
        )

    st.write("**Select token style**")
    st.session_state.token_shape = st.radio("token", TOKEN_SHAPES, horizontal=True,
                                             index=TOKEN_SHAPES.index(st.session_state.token_shape),
                                             label_visibility="collapsed")

    st.write("**Select dice design**")
    st.session_state.dice_skin = st.selectbox("dice", list(DICE_SKINS.keys()),
                                               index=list(DICE_SKINS.keys()).index(st.session_state.dice_skin),
                                               label_visibility="collapsed")

    with st.expander("🎙️ Optional: AI commentary (Groq)"):
        st.session_state.commentary_on = st.checkbox("Enable commentary", value=st.session_state.commentary_on)
        if st.session_state.commentary_on:
            st.session_state.groq_key = st.text_input("Groq API key", value=st.session_state.groq_key, type="password")

    if st.button("▶️ Play", type="primary", use_container_width=True):
        mode = "team" if mode_choice == "Team Up" else "computer" if "Computer" in st.session_state.setup_roles.values() else "local"
        is_human = {c: (st.session_state.setup_roles[c] == "Human") for c in active_colors}
        names = {c: (st.session_state.setup_names[c] or c.capitalize()) for c in active_colors}
        start_new_game(mode, active_colors, names, is_human, st.session_state.dice_skin,
                        st.session_state.token_shape, st.session_state.commentary_on, st.session_state.groq_key)
        st.rerun()

# ============================================================
# GAME SCREEN (compact, one page)
# ============================================================

else:
    g = st.session_state.game

    top_l, top_r = st.columns([3, 1])
    top_l.markdown("### 👑 Ludo Master")
    if top_r.button("🔄 New", use_container_width=True):
        st.session_state.stage = "setup"
        st.rerun()

    winner = check_winner()
    if winner and not g["winner"]:
        g["winner"] = winner
    if g["winner"]:
        st.success(f"🏆 {g['winner']} wins!")

    st.components.v1.html(f'<div style="max-width:360px;margin:auto;">{svg_board()}</div>', height=370)

    turn_color = current_color()
    disabled = bool(g["winner"])

    row1, row2 = st.columns([1, 1])
    with row1:
        st.markdown(f"**Turn:** <span style='color:{HEX[turn_color]};font-weight:800'>{g['names'][turn_color]}</span>", unsafe_allow_html=True)
        if g["mode"] == "team":
            st.caption(f"Team {TEAM_OF[turn_color]}")
    with row2:
        st.components.v1.html(f'<div style="width:60px;">{svg_dice(g["dice"], st.session_state.dice_skin)}</div>', height=75)

    is_human_turn = g["is_human"].get(turn_color, True)

    if g["dice"] is None and not g.get("awaiting_continue"):
        if st.button("🎲 Roll Dice", disabled=disabled, use_container_width=True):
            roll = random.randint(1, 6)
            g["dice"] = roll
            g["movable"] = movable_tokens(turn_color, roll)
            g["consecutive_sixes"] = g["consecutive_sixes"] + 1 if roll == 6 else 0
            if g["consecutive_sixes"] == 3:
                g["log"].insert(0, f"{g['names'][turn_color]} rolled three 6's — turn forfeited!")
                g["awaiting_continue"] = "forfeit"
            elif not g["movable"]:
                g["log"].insert(0, f"{g['names'][turn_color]} rolled {roll}, no valid move.")
                g["awaiting_continue"] = "extra" if roll == 6 else "pass"
            st.rerun()
    elif g.get("awaiting_continue"):
        reason = g["awaiting_continue"]
        note = "No valid move — you rolled a 6, roll again." if reason == "extra" else \
               "Three 6's in a row — turn passes." if reason == "forfeit" else \
               "No valid move — turn passes."
        st.caption(note)
        if is_human_turn:
            if st.button("➡️ Continue", use_container_width=True):
                give_extra = (reason == "extra")
                g["awaiting_continue"] = False
                next_turn(give_extra=give_extra)
                st.rerun()
        else:
            give_extra = (reason == "extra")
            g["awaiting_continue"] = False
            next_turn(give_extra=give_extra)
            st.rerun()
    else:
        if is_human_turn:
            st.write(f"Rolled **{g['dice']}** — choose a token:")
            btn_cols = st.columns(len(g["movable"])) if g["movable"] else [st]
            for i, idx in enumerate(g["movable"]):
                pos = g["positions"][turn_color][idx]
                label = "Base" if pos == -1 else ("Home!" if pos == FINISH_POS else f"#{pos}")
                target = btn_cols[i] if g["movable"] else st
                if target.button(f"T{idx+1}\n{label}", key=f"mv_{idx}", use_container_width=True):
                    extra = apply_move(turn_color, idx, g["dice"])
                    if st.session_state.commentary_on and st.session_state.groq_key:
                        c = get_groq_commentary(g["log"][0], st.session_state.groq_key)
                        if c:
                            g["log"].insert(0, f"🎙️ {c}")
                    next_turn(give_extra=(extra or g["dice"] == 6))
                    st.rerun()
        else:
            st.info(f"{g['names'][turn_color]} (Computer) is thinking...")
            idx = ai_choose_token(turn_color, g["dice"], g["movable"])
            extra = apply_move(turn_color, idx, g["dice"])
            next_turn(give_extra=(extra or g["dice"] == 6))
            st.rerun()

    with st.expander("📜 Game log"):
        for line in g["log"][:12]:
            st.write("• " + line)
