import streamlit as st
import random
import time

# ============================================================
# LUDO MASTER — COMPLETE FIXED VERSION
# ============================================================

st.set_page_config(
    page_title="Ludo Master",
    page_icon="🎲",
    layout="centered"
)

# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 0.6rem;
        padding-bottom: 0.4rem;
        max-width: 440px;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden; height: 0;}

    .stButton > button {
        padding: 0.3rem 0.5rem;
        border-radius: 8px;
        font-weight: 700;
    }

    h1 {
        font-size: 1.5rem !important;
        margin-bottom: 0.1rem !important;
    }

    h3 {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }

    div.element-container {
        margin-bottom: 0.15rem !important;
    }

    div[data-testid="stExpander"] {
        margin-top: 0.2rem !important;
    }

    .game-status {
        padding: 8px;
        border-radius: 10px;
        text-align: center;
        background: #161616;
        color: white;
        margin: 5px 0;
    }

    .winner-box {
        padding: 12px;
        border-radius: 12px;
        background: #171717;
        color: white;
        text-align: center;
        font-size: 1.15rem;
        font-weight: 800;
        margin: 8px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# CONSTANTS
# ============================================================

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

TEAM_OF = {
    "red": "A",
    "yellow": "A",
    "green": "B",
    "blue": "B",
}

DICE_SKINS = {
    "Classic White": {
        "bg": "#FFFFFF",
        "pip": "#111111",
        "border": "#333333",
    },
    "Royal Gold": {
        "bg": "#FFD700",
        "pip": "#5A3E00",
        "border": "#8A6A00",
    },
    "Ruby Red": {
        "bg": "#D32F2F",
        "pip": "#FFFFFF",
        "border": "#7A1010",
    },
    "Ocean Blue": {
        "bg": "#1565C0",
        "pip": "#FFFFFF",
        "border": "#0B3B75",
    },
    "Jet Black": {
        "bg": "#1B1B1B",
        "pip": "#F5F5F5",
        "border": "#000000",
    },
    "Emerald": {
        "bg": "#2E7D32",
        "pip": "#FFFFFF",
        "border": "#154B18",
    },
}

TOKEN_SHAPES = [
    "Pin",
    "Disc",
    "Diamond",
    "Star",
]

# ============================================================
# BOARD GEOMETRY
# ============================================================

def rotate(cell):
    r, c = cell
    return (
        7 + (c - 7),
        7 - (r - 7)
    )


RED_QUARTER = [
    (6, 1),
    (6, 2),
    (6, 3),
    (6, 4),
    (6, 5),
    (5, 6),
    (4, 6),
    (3, 6),
    (2, 6),
    (1, 6),
    (0, 6),
    (0, 7),
    (0, 8),
]

RED_HOME_COL = [
    (7, 1),
    (7, 2),
    (7, 3),
    (7, 4),
    (7, 5),
    (7, 6),
]

QUARTERS = {
    "red": RED_QUARTER
}

HOME_COLS = {
    "red": RED_HOME_COL
}

cur_q = RED_QUARTER
cur_h = RED_HOME_COL

for color in ["green", "yellow", "blue"]:
    cur_q = [rotate(c) for c in cur_q]
    cur_h = [rotate(c) for c in cur_h]

    QUARTERS[color] = cur_q
    HOME_COLS[color] = cur_h

GLOBAL_CELLS = (
    QUARTERS["red"]
    + QUARTERS["green"]
    + QUARTERS["yellow"]
    + QUARTERS["blue"]
)

START_INDEX = {
    "red": 0,
    "green": 13,
    "yellow": 26,
    "blue": 39,
}

SAFE_GLOBAL = {
    0, 8, 13, 21, 26, 34, 39, 47
}

BASE_SLOTS = {
    "red": [
        (1, 1),
        (1, 4),
        (4, 1),
        (4, 4)
    ],
    "green": [
        (1, 10),
        (1, 13),
        (4, 10),
        (4, 13)
    ],
    "yellow": [
        (10, 10),
        (10, 13),
        (13, 10),
        (13, 13)
    ],
    "blue": [
        (10, 1),
        (10, 4),
        (13, 1),
        (13, 4)
    ],
}

CENTER = (7, 7)
FINISH_POS = 58

TWO_PLAYER_COLORS = [
    "red",
    "yellow"
]

THREE_PLAYER_COLORS = [
    "red",
    "green",
    "yellow"
]

FOUR_PLAYER_COLORS = [
    "red",
    "green",
    "yellow",
    "blue"
]

# ============================================================
# POSITION HELPERS
# ============================================================

def cell_of(color, pos, token_idx):

    if pos == -1:
        return BASE_SLOTS[color][token_idx]

    if pos == FINISH_POS:
        return CENTER

    if pos <= 51:
        gi = (
            START_INDEX[color] + pos
        ) % 52

        return GLOBAL_CELLS[gi]

    return HOME_COLS[color][pos - 52]


def global_index_safe(pos, color):

    if pos < 0 or pos > 51:
        return True

    gi = (
        START_INDEX[color] + pos
    ) % 52

    return gi in SAFE_GLOBAL


# ============================================================
# GAME STATE
# ============================================================

def start_new_game(
    mode,
    colors_in_play,
    names,
    is_human,
    dice_skin,
    token_shape,
    commentary_on,
    groq_key
):

    first_color = colors_in_play[0]

    st.session_state.game = {
        "mode": mode,
        "colors": colors_in_play,
        "names": names,
        "is_human": is_human,

        "positions": {
            c: [-1, -1, -1, -1]
            for c in COLORS
        },

        "turn_idx": 0,

        "dice": None,

        "movable": [],

        "consecutive_sixes": 0,

        "awaiting_continue": False,

        "log": [
            f"Game started. "
            f"{names[first_color]} "
            f"({first_color}) goes first."
        ],

        "winner": None,

        "last_commentary": None,
    }

    st.session_state.dice_skin = dice_skin
    st.session_state.token_shape = token_shape
    st.session_state.commentary_on = commentary_on
    st.session_state.groq_key = groq_key

    st.session_state.stage = "playing"


def current_color():

    g = st.session_state.game

    return g["colors"][g["turn_idx"]]


def next_turn():

    g = st.session_state.game

    g["turn_idx"] = (
        g["turn_idx"] + 1
    ) % len(g["colors"])

    g["dice"] = None
    g["movable"] = []
    g["consecutive_sixes"] = 0
    g["awaiting_continue"] = False


# ============================================================
# WINNER
# ============================================================

def check_winner():

    g = st.session_state.game

    if g["mode"] == "team":

        for team in ["A", "B"]:

            members = [
                c
                for c in g["colors"]
                if TEAM_OF[c] == team
            ]

            if all(
                all(
                    p == FINISH_POS
                    for p in g["positions"][m]
                )
                for m in members
            ):

                names = " & ".join(
                    g["names"][m]
                    for m in members
                )

                return f"Team {team} ({names})"

        return None

    for c in g["colors"]:

        if all(
            p == FINISH_POS
            for p in g["positions"][c]
        ):

            return g["names"][c]

    return None


# ============================================================
# MOVABLE TOKENS
# ============================================================

def movable_tokens(color, dice_val):

    g = st.session_state.game

    positions = g["positions"][color]

    movable = []

    for i, p in enumerate(positions):

        # Token is in base
        if p == -1:

            if dice_val == 6:
                movable.append(i)

        # Token already finished
        elif p == FINISH_POS:

            continue

        # Token on board
        else:

            if p + dice_val <= FINISH_POS:
                movable.append(i)

    return movable


# ============================================================
# MOVE
# ============================================================

def apply_move(color, token_idx, dice_val):

    g = st.session_state.game

    positions = g["positions"][color]

    p = positions[token_idx]

    new_p = (
        0
        if p == -1
        else p + dice_val
    )

    positions[token_idx] = new_p

    name = g["names"][color]

    if new_p == FINISH_POS:

        msg = (
            f"{name} moved token {token_idx + 1} "
            f"to HOME! 🏆"
        )

    else:

        msg = (
            f"{name} moved token {token_idx + 1} "
            f"to position {new_p}."
        )

    captured = False

    # Capture
    if (
        new_p <= 51
        and not global_index_safe(new_p, color)
    ):

        gi_new = (
            START_INDEX[color] + new_p
        ) % 52

        for other in g["colors"]:

            if other == color:
                continue

            # Don't capture teammate
            if (
                g["mode"] == "team"
                and TEAM_OF[other]
                == TEAM_OF[color]
            ):
                continue

            for j, op in enumerate(
                g["positions"][other]
            ):

                if (
                    op == -1
                    or op == FINISH_POS
                    or op > 51
                ):
                    continue

                other_gi = (
                    START_INDEX[other] + op
                ) % 52

                if other_gi == gi_new:

                    g["positions"][other][j] = -1

                    captured = True

                    msg += (
                        f" Captured "
                        f"{g['names'][other]}'s token!"
                    )

    g["log"].insert(0, msg)

    return (
        new_p == FINISH_POS
        or captured
    )


# ============================================================
# AI
# ============================================================

def ai_choose_token(
    color,
    dice_val,
    movable
):

    g = st.session_state.game

    positions = g["positions"][color]

    # --------------------------------------------------------
    # Check capture possibility
    # --------------------------------------------------------

    def would_capture(idx):

        p = positions[idx]

        new_p = (
            0
            if p == -1
            else p + dice_val
        )

        if (
            new_p > 51
            or global_index_safe(
                new_p,
                color
            )
        ):
            return False

        gi_new = (
            START_INDEX[color]
            + new_p
        ) % 52

        for other in g["colors"]:

            if other == color:
                continue

            if (
                g["mode"] == "team"
                and TEAM_OF[other]
                == TEAM_OF[color]
            ):
                continue

            for op in g["positions"][other]:

                if (
                    op != -1
                    and op <= 51
                ):

                    other_gi = (
                        START_INDEX[other]
                        + op
                    ) % 52

                    if other_gi == gi_new:
                        return True

        return False

    capturing = [
        i
        for i in movable
        if would_capture(i)
    ]

    if capturing:
        return capturing[0]

    # Prefer bringing token out
    if dice_val == 6:

        for i in movable:

            if positions[i] == -1:
                return i

    # Otherwise move furthest token
    return max(
        movable,
        key=lambda i: positions[i]
    )


# ============================================================
# GROQ COMMENTARY
# ============================================================

def get_groq_commentary(
    log_line,
    api_key
):

    if not api_key:
        return None

    try:

        import requests

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",

            headers={
                "Authorization":
                    f"Bearer {api_key}",
                "Content-Type":
                    "application/json",
            },

            json={
                "model":
                    "llama-3.1-8b-instant",

                "messages": [
                    {
                        "role": "system",
                        "content":
                            "You are a hype Ludo commentator. "
                            "Give one short punchy sentence. "
                            "Maximum 15 words and at most one emoji."
                    },
                    {
                        "role": "user",
                        "content": log_line,
                    },
                ],

                "max_tokens": 40,
                "temperature": 0.9,
            },

            timeout=6,
        )

        if response.status_code == 200:

            data = response.json()

            return (
                data["choices"][0]["message"]
                ["content"]
                .strip()
            )

    except Exception:
        pass

    return None


# ============================================================
# TOKEN SVG
# ============================================================

def token_shape_svg(
    shape,
    cx,
    cy,
    r,
    fill,
    stroke
):

    if shape == "Disc":

        return (
            f'<circle cx="{cx}" cy="{cy}" '
            f'r="{r}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="2"/>'
        )

    if shape == "Diamond":

        pts = (
            f"{cx},{cy-r*1.3} "
            f"{cx+r*1.1},{cy} "
            f"{cx},{cy+r*1.3} "
            f"{cx-r*1.1},{cy}"
        )

        return (
            f'<polygon points="{pts}" '
            f'fill="{fill}" '
            f'stroke="{stroke}" '
            f'stroke-width="2"/>'
        )

    if shape == "Star":

        import math

        pts = []

        for i in range(10):

            ang = (
                math.pi / 5 * i
                - math.pi / 2
            )

            rad = (
                r * 1.3
                if i % 2 == 0
                else r * 0.55
            )

            pts.append(
                f"{cx + rad * math.cos(ang)},"
                f"{cy + rad * math.sin(ang)}"
            )

        return (
            f'<polygon points="{" ".join(pts)}" '
            f'fill="{fill}" '
            f'stroke="{stroke}" '
            f'stroke-width="1.5"/>'
        )

    # Default = Pin

    return (
        f'<path d="M {cx} {cy+r*1.4} '
        f'C {cx-r*1.2} {cy+r*0.2} '
        f'{cx-r*1.1} {cy-r*1.3} '
        f'{cx} {cy-r*1.3} '
        f'C {cx+r*1.1} {cy-r*1.3} '
        f'{cx+r*1.2} {cy+r*0.2} '
        f'{cx} {cy+r*1.4} Z" '
        f'fill="{fill}" '
        f'stroke="{stroke}" '
        f'stroke-width="1.8"/>'

        f'<circle cx="{cx}" '
        f'cy="{cy-r*0.5}" '
        f'r="{r*0.4}" '
        f'fill="white" '
        f'opacity="0.85"/>'
    )


# ============================================================
# BOARD SVG
# ============================================================

def svg_board(size=310):

    cell = size / 15

    parts = [
        f'<svg viewBox="0 0 {size} {size}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="background:#f4f1e8;">'
    ]

    def rect(
        r,
        c,
        color,
        w=1,
        h=1
    ):

        parts.append(
            f'<rect x="{c*cell}" '
            f'y="{r*cell}" '
            f'width="{w*cell}" '
            f'height="{h*cell}" '
            f'fill="{color}" '
            f'stroke="#555" '
            f'stroke-width="0.4"/>'
        )

    quad_origin = {
        "red": (0, 0),
        "green": (0, 9),
        "yellow": (9, 9),
        "blue": (9, 0),
    }

    for color, (ro, co) in quad_origin.items():

        parts.append(
            f'<rect x="{co*cell}" '
            f'y="{ro*cell}" '
            f'width="{6*cell}" '
            f'height="{6*cell}" '
            f'fill="{HEX[color]}22" '
            f'stroke="#999" '
            f'stroke-width="0.4"/>'
        )

        parts.append(
            f'<rect x="{(co+1)*cell}" '
            f'y="{(ro+1)*cell}" '
            f'width="{4*cell}" '
            f'height="{4*cell}" '
            f'fill="white" '
            f'stroke="{HEX[color]}" '
            f'stroke-width="1.2" '
            f'rx="6"/>'
        )

        for sr, sc in BASE_SLOTS[color]:

            cx = (sc + 0.5) * cell
            cy = (sr + 0.5) * cell

            parts.append(
                f'<circle cx="{cx}" '
                f'cy="{cy}" '
                f'r="{cell*0.26}" '
                f'fill="{HEX[color]}33" '
                f'stroke="{HEX[color]}" '
                f'stroke-width="0.6"/>'
            )

    # Main path
    for gi, (r, c) in enumerate(
        GLOBAL_CELLS
    ):

        fill = (
            "#FFF3B0"
            if gi in SAFE_GLOBAL
            else "#FFFFFF"
        )

        rect(r, c, fill)

        if gi in SAFE_GLOBAL:

            cx = (c + 0.5) * cell
            cy = (r + 0.5) * cell

            parts.append(
                f'<text x="{cx}" '
                f'y="{cy+4}" '
                f'font-size="{cell*0.5}" '
                f'text-anchor="middle">★</text>'
            )

    # Home paths
    for color in COLORS:

        for r, c in HOME_COLS[color]:

            rect(
                r,
                c,
                HEX[color] + "cc"
            )

    # Start cells
    for color in COLORS:

        r, c = GLOBAL_CELLS[
            START_INDEX[color]
        ]

        rect(
            r,
            c,
            HEX[color]
        )

    # Center triangles
    tri_colors = [
        HEX["red"],
        HEX["green"],
        HEX["yellow"],
        HEX["blue"],
    ]

    pts = [
        f"{6*cell},{6*cell} "
        f"{7.5*cell},{7.5*cell} "
        f"{6*cell},{9*cell}",

        f"{6*cell},{6*cell} "
        f"{7.5*cell},{7.5*cell} "
        f"{9*cell},{6*cell}",

        f"{9*cell},{6*cell} "
        f"{7.5*cell},{7.5*cell} "
        f"{9*cell},{9*cell}",

        f"{6*cell},{9*cell} "
        f"{7.5*cell},{7.5*cell} "
        f"{9*cell},{9*cell}",
    ]

    for pt, col in zip(
        pts,
        tri_colors
    ):

        parts.append(
            f'<polygon points="{pt}" '
            f'fill="{col}"/>'
        )

    # Outer border
    parts.append(
        f'<rect x="0" y="0" '
        f'width="{size}" '
        f'height="{size}" '
        f'fill="none" '
        f'stroke="#222" '
        f'stroke-width="2"/>'
    )

    # Tokens
    g = st.session_state.game

    shape = st.session_state.get(
        "token_shape",
        "Pin"
    )

    occupied = {}

    for color in g["colors"]:

        for idx, pos in enumerate(
            g["positions"][color]
        ):

            r, c = cell_of(
                color,
                pos,
                idx
            )

            occupied.setdefault(
                (r, c),
                []
            ).append(
                (color, idx)
            )

    for (r, c), items in occupied.items():

        n = len(items)

        for k, (color, idx) in enumerate(items):

            if n > 1:

                offset_x = (
                    k - (n - 1) / 2
                ) * cell * 0.32

            else:

                offset_x = 0

            cx = (
                (c + 0.5) * cell
                + offset_x
            )

            cy = (
                (r + 0.5) * cell
            )

            parts.append(
                token_shape_svg(
                    shape,
                    cx,
      
