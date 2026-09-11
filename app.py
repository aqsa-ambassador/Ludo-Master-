import streamlit as st
import random
import math

# ============================================================
# LUDO MASTER
# Current Streamlit compatible
# ============================================================

st.set_page_config(
    page_title="Ludo Master",
    page_icon="🎲",
    layout="centered",
)

# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
    .block-container {
        max-width: 480px;
        padding-top: .55rem;
        padding-bottom: .5rem;
    }

    #MainMenu, footer, header {
        visibility: hidden;
    }

    .stButton > button {
        border-radius: 12px;
        font-weight: 700;
        min-height: 42px;
    }

    .status {
        padding: 9px;
        border-radius: 12px;
        background: #171717;
        color: white;
        text-align: center;
        margin: 5px 0 9px;
    }

    .winner {
        padding: 15px;
        border-radius: 14px;
        background: #171717;
        color: white;
        text-align: center;
        font-size: 1.15rem;
        font-weight: 800;
        margin-bottom: 10px;
    }

    .hint {
        text-align: center;
        padding: 8px;
        border-radius: 10px;
        background: #fff5bf;
        color: #222;
        margin: 8px 0;
        font-weight: 700;
    }

    @keyframes tokenBlink {
        0%, 100% {
            opacity: 1;
            filter: drop-shadow(0 0 2px white);
        }

        50% {
            opacity: .45;
            filter: drop-shadow(0 0 12px white);
        }
    }

    .movable-token {
        animation: tokenBlink .7s infinite;
        cursor: pointer;
    }

    .clickable-token {
        cursor: pointer;
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

DARK = {
    "red": "#8E1E1A",
    "green": "#245C2A",
    "yellow": "#9C8A10",
    "blue": "#0F4C86",
}

TEAM = {
    "red": "A",
    "yellow": "A",
    "green": "B",
    "blue": "B",
}

BASE = {
    "red": [
        (1, 1),
        (1, 4),
        (4, 1),
        (4, 4),
    ],
    "green": [
        (1, 10),
        (1, 13),
        (4, 10),
        (4, 13),
    ],
    "yellow": [
        (10, 10),
        (10, 13),
        (13, 10),
        (13, 13),
    ],
    "blue": [
        (10, 1),
        (10, 4),
        (13, 1),
        (13, 4),
    ],
}

START = {
    "red": 0,
    "green": 13,
    "yellow": 26,
    "blue": 39,
}

FINISH = 58

SAFE = {
    0,
    8,
    13,
    21,
    26,
    34,
    39,
    47,
}

RED_PATH = [
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
    (1, 8),
    (2, 8),
    (3, 8),
    (4, 8),
    (5, 8),
    (6, 9),
    (6, 10),
    (6, 11),
    (6, 12),
    (6, 13),
    (7, 13),
    (8, 13),
    (8, 12),
    (8, 11),
    (8, 10),
    (8, 9),
    (9, 8),
    (10, 8),
    (11, 8),
    (12, 8),
    (13, 8),
    (14, 8),
    (14, 7),
    (14, 6),
    (13, 6),
    (12, 6),
    (11, 6),
    (10, 6),
    (9, 6),
    (8, 5),
    (8, 4),
    (8, 3),
    (8, 2),
    (8, 1),
    (7, 1),
    (7, 0),
    (6, 0),
    (5, 0),
    (4, 0),
    (3, 0),
    (2, 0),
]

def rotate(cell):
    r, c = cell
    return (14 - c, r)


PATH = {
    "red": RED_PATH
}

p = RED_PATH

for color in ["green", "yellow", "blue"]:
    p = [rotate(x) for x in p]
    PATH[color] = p


HOME = {
    "red": [
        (7, 1),
        (7, 2),
        (7, 3),
        (7, 4),
        (7, 5),
        (7, 6),
    ],
    "green": [
        (1, 7),
        (2, 7),
        (3, 7),
        (4, 7),
        (5, 7),
        (6, 7),
    ],
    "yellow": [
        (7, 13),
        (7, 12),
        (7, 11),
        (7, 10),
        (7, 9),
        (7, 8),
    ],
    "blue": [
        (13, 7),
        (12, 7),
        (11, 7),
        (10, 7),
        (9, 7),
        (8, 7),
    ],
}

# ============================================================
# GAME HELPERS
# ============================================================

def current_color():
    g = st.session_state.game
    return g["colors"][g["turn"]]


def next_turn():
    g = st.session_state.game

    g["turn"] = (
        g["turn"] + 1
    ) % len(g["colors"])

    g["dice"] = None
    g["movable"] = []


def cell_for_token(color, position, index):
    if position == -1:
        return BASE[color][index]

    if position == FINISH:
        return (7, 7)

    if position <= 51:
        return PATH[color][position]

    return HOME[color][position - 52]


def is_safe(color, position):
    if position < 0 or position > 51:
        return True

    global_position = (
        START[color] + position
    ) % 52

    return global_position in SAFE


# ============================================================
# MOVEMENT
# ============================================================

def get_movable(color, dice):
    g = st.session_state.game
    result = []

    for index, position in enumerate(
        g["positions"][color]
    ):
        if position == -1:
            if dice == 6:
                result.append(index)

        elif position < FINISH:
            if position + dice <= FINISH:
                result.append(index)

    return result


def move_token(color, index, dice):
    g = st.session_state.game

    old_position = g["positions"][color][index]

    if old_position == -1:
        new_position = 0
    else:
        new_position = old_position + dice

    g["positions"][color][index] = new_position

    player_name = g["names"][color]

    if old_position == -1:
        message = (
            f"{player_name} opened a token."
        )

    elif new_position == FINISH:
        message = (
            f"{player_name} reached HOME! 🏆"
        )

    else:
        message = (
            f"{player_name} moved a token "
            f"{dice} spaces."
        )

    # Capture
    if (
        new_position <= 51
        and not is_safe(
            color,
            new_position
        )
    ):
        target = (
            START[color] + new_position
        ) % 52

        for other in g["colors"]:

            if other == color:
                continue

            if (
                g["mode"] == "Team Up"
                and TEAM[other] == TEAM[color]
            ):
                continue

            for other_index, other_position in enumerate(
                g["positions"][other]
            ):

                if (
                    other_position >= 0
                    and other_position <= 51
                ):

                    other_global = (
                        START[other]
                        + other_position
                    ) % 52

                    if other_global == target:
                        g["positions"][other][
                            other_index
                        ] = -1

                        message += (
                            " Captured an opponent!"
                        )

    g["log"].insert(
        0,
        message
    )


def check_winner():
    g = st.session_state.game

    if g["mode"] == "Team Up":

        for team in ["A", "B"]:

            members = [
                c
                for c in g["colors"]
                if TEAM[c] == team
            ]

            if members and all(
                all(
                    position == FINISH
                    for position in g["positions"][color]
                )
                for color in members
            ):
                return (
                    " & ".join(
                        g["names"][color]
                        for color in members
                    )
                    + f" — Team {team}"
                )

    else:

        for color in g["colors"]:

            if all(
                position == FINISH
                for position in g["positions"][color]
            ):
                return g["names"][color]

    return None


# ============================================================
# COMPLETE MOVE
# ============================================================

def complete_move(index):
    g = st.session_state.game

    color = current_color()
    dice = g["dice"]

    if dice is None:
        return

    if index not in g["movable"]:
        return

    move_token(
        color,
        index,
        dice
    )

    g["winner"] = check_winner()

    if g["winner"]:
        return

    # Six = another turn
    if dice == 6:
        g["dice"] = None
        g["movable"] = []

    else:
        next_turn()


# ============================================================
# TOKEN SVG
# ============================================================

def token_svg(
    shape,
    cx,
    cy,
    radius,
    fill,
    stroke,
    active=False,
    click_url=None
):
    css = (
        'class="movable-token"'
        if active
        else ""
    )

    if shape == "Disc":
        token = (
            f'<circle '
            f'cx="{cx}" cy="{cy}" '
            f'r="{radius}" '
            f'fill="{fill}" '
            f'stroke="{stroke}" '
            f'stroke-width="2" '
            f'{css}/>'
        )

    elif shape == "Diamond":

        points = (
            f"{cx},{cy-radius*1.3} "
            f"{cx+radius*1.1},{cy} "
            f"{cx},{cy+radius*1.3} "
            f"{cx-radius*1.1},{cy}"
        )

        token = (
            f'<polygon '
            f'points="{points}" '
            f'fill="{fill}" '
            f'stroke="{stroke}" '
            f'stroke-width="2" '
            f'{css}/>'
        )

    elif shape == "Star":

        points = []

        for i in range(10):

            angle = (
                math.pi * i / 5
                - math.pi / 2
            )

            r = (
                radius * 1.3
                if i % 2 == 0
                else radius * .55
            )

            points.append(
                f"{cx+r*math.cos(angle)},"
                f"{cy+r*math.sin(angle)}"
            )

        token = (
            f'<polygon '
            f'points="{" ".join(points)}" '
            f'fill="{fill}" '
            f'stroke="{stroke}" '
            f'stroke-width="1.5" '
            f'{css}/>'
        )

    else:

        token = (
            f'<path '
            f'd="M {cx} {cy+radius*1.4} '
            f'C {cx-radius*1.2} {cy+radius*.2} '
            f'{cx-radius*1.1} {cy-radius*1.3} '
            f'{cx} {cy-radius*1.3} '
            f'C {cx+radius*1.1} {cy-radius*1.3} '
            f'{cx+radius*1.2} {cy+radius*.2} '
            f'{cx} {cy+radius*1.4} Z" '
            f'fill="{fill}" '
            f'stroke="{stroke}" '
            f'stroke-width="1.8" '
            f'{css}/>'
        )

    if click_url:
        return (
            f'<a href="{click_url}" '
            f'title="Move this piece">'
            f'{token}'
            f'</a>'
        )

    return token


# ============================================================
# BOARD
# ============================================================

def make_board():
    size = 360
    cell = size / 15

    parts = [
        f'<svg '
        f'viewBox="0 0 {size} {size}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;height:auto;'
        f'background:#f4f1e8;">'
    ]

    # Home areas
    origins = {
        "red": (0, 0),
        "green": (0, 9),
        "yellow": (9, 9),
        "blue": (9, 0),
    }

    for color, (
        row,
        col
    ) in origins.items():

        parts.append(
            f'<rect '
            f'x="{col*cell}" '
            f'y="{row*cell}" '
            f'width="{6*cell}" '
            f'height="{6*cell}" '
            f'fill="{HEX[color]}22" '
            f'stroke="#777"/>'
        )

    # Base circles
    for color in COLORS:

        for row, col in BASE[color]:

            parts.append(
                f'<circle '
                f'cx="{(col+.5)*cell}" '
                f'cy="{(row+.5)*cell}" '
                f'r="{cell*.27}" '
                f'fill="{HEX[color]}22" '
                f'stroke="{HEX[color]}" '
                f'stroke-width="2"/>'
            )

    # Main path
    for i, (
        row,
        col
    ) in enumerate(RED_PATH):

        fill = (
            "#FFF0A8"
            if i in SAFE
            else "#FFFFFF"
        )

        parts.append(
            f'<rect '
            f'x="{col*cell}" '
            f'y="{row*cell}" '
            f'width="{cell}" '
            f'height="{cell}" '
            f'fill="{fill}" '
            f'stroke="#777" '
            f'stroke-width=".5"/>'
        )

    # Home paths
    for color in COLORS:

        for row, col in HOME[color]:

            parts.append(
                f'<rect '
                f'x="{col*cell}" '
                f'y="{row*cell}" '
                f'width="{cell}" '
                f'height="{cell}" '
                f'fill="{HEX[color]}88" '
                f'stroke="#777" '
                f'stroke-width=".5"/>'
            )

    # Starting squares
    for color in COLORS:

        row, col = PATH[color][0]

        parts.append(
            f'<rect '
            f'x="{col*cell}" '
            f'y="{row*cell}" '
            f'width="{cell}" '
            f'height="{cell}" '
            f'fill="{HEX[color]}" '
            f'stroke="#444"/>'
        )

    # Center triangles
    parts.append(
        f'<polygon '
        f'points="{6*cell},{6*cell} '
        f'{7.5*cell},{7.5*cell} '
        f'{6*cell},{9*cell}" '
        f'fill="{HEX["red"]}"/>'
    )

    parts.append(
        f'<polygon '
        f'points="{6*cell},{6*cell} '
        f'{7.5*cell},{7.5*cell} '
        f'{9*cell},{6*cell}" '
        f'fill="{HEX["green"]}"/>'
    )

    parts.append(
        f'<polygon '
        f'points="{9*cell},{6*cell} '
        f'{7.5*cell},{7.5*cell} '
        f'{9*cell},{9*cell}" '
        f'fill="{HEX["yellow"]}"/>'
    )

    parts.append(
        f'<polygon '
        f'points="{6*cell},{9*cell} '
        f'{7.5*cell},{7.5*cell} '
        f'{9*cell},{9*cell}" '
        f'fill="{HEX["blue"]}"/>'
    )

    # ========================================================
    # TOKENS
    # ========================================================

    g = st.session_state.game

    active_color = current_color()

    movable_set = set(
        g.get("movable", [])
    )

    shape = g["shape"]

    occupied = {}

    for color in g["colors"]:

        for index, position in enumerate(
            g["positions"][color]
        ):

            cell_position = cell_for_token(
                color,
                position,
                index
            )

            occupied.setdefault(
                cell_position,
                []
            ).append(
                (
                    color,
                    index
                )
            )

    for (
        cell_position,
        tokens
    ) in occupied.items():

        row, col = cell_position

        count = len(tokens)

        for order, (
            color,
            index
        ) in enumerate(tokens):

            offset = (
                (order - (count-1)/2)
                * cell
                * .30
                if count > 1
                else 0
            )

            cx = (
                (col+.5)*cell
                + offset
            )

            cy = (
                (row+.5)*cell
            )

            active = (
                color == active_color
                and index in movable_set
                and g["dice"] is not None
                and g["human"].get(
                    color,
                    True
                )
            )

            click_url = None

            if active:

                # Current Streamlit query parameter API.
                click_url = (
                    f"?move="
                    f"{color}-{index}"
                )

            parts.append(
                token_svg(
                    shape,
                    cx,
                    cy,
                    cell*.30,
                    HEX[color],
                    DARK[color],
                    active,
                    click_url
                )
            )

    parts.append(
        f'<rect '
        f'x="0" y="0" '
        f'width="{size}" '
        f'height="{size}" '
        f'fill="none" '
        f'stroke="#222" '
        f'stroke-width="3"/>'
    )

    parts.append("</svg>")

    return "".join(parts)


# ============================================================
# HANDLE ON-BOARD CLICK
# ============================================================

def handle_board_click():
    """
    Current Streamlit API:
        st.query_params

    No experimental query-param API is used.
    """

    raw = st.query_params.get("move")

    if not raw:
        return False

    try:

        if "game" not in st.session_state:
            st.query_params.clear()
            return False

        color, index_text = raw.split(
            "-",
            1
        )

        index = int(index_text)

        g = st.session_state.game

        if color != current_color():
            st.query_params.clear()
            return False

        if not g["human"].get(
            color,
            True
        ):
            st.query_params.clear()
            return False

        if g["dice"] is None:
            st.query_params.clear()
            return False

        if index not in g["movable"]:
            st.query_params.clear()
            return False

        complete_move(index)

        st.query_params.clear()

        return True

    except Exception:

        st.query_params.clear()

        return False


# ============================================================
# AUTO MOVE IF ONLY ONE
# ============================================================

def auto_move_if_only_one():
    g = st.session_state.game

    if (
        g["dice"] is not None
        and len(g["movable"]) == 1
    ):

        complete_move(
            g["movable"][0]
        )

        return True

    return False


# ============================================================
# INITIAL STATE
# ============================================================

if "stage" not in st.session_state:
    st.session_state.stage = "setup"


# ============================================================
# SETUP
# ============================================================

if st.session_state.stage == "setup":

    st.title("🎲 Ludo Master")

    st.caption(
        "Classic Ludo • Mobile Friendly"
    )

    mode = st.radio(
        "Game Mode",
        [
            "Classic",
            "Team Up"
        ],
        horizontal=True
    )

    player_count = st.selectbox(
        "Number of Players",
        [2, 3, 4],
        index=1
    )

    if player_count == 2:
        colors = [
            "red",
            "yellow"
        ]

    elif player_count == 3:
        colors = [
            "red",
            "green",
            "yellow"
        ]

    else:
        colors = [
            "red",
            "green",
            "yellow",
            "blue"
        ]

    names = {}
    human = {}

    st.subheader("Players")

    for color in colors:

        col1, col2 = st.columns(2)

        with col1:

            names[color] = st.text_input(
                f"{color.title()} Name",
                value=f"{color.title()} Player",
                key=f"name_{color}"
            )

        with col2:

            role = st.selectbox(
                "Type",
                [
                    "Human",
                    "Computer"
                ],
                key=f"role_{color}"
            )

            human[color] = (
                role == "Human"
            )

    shape = st.selectbox(
        "Token Shape",
        [
            "Pin",
            "Disc",
            "Diamond",
            "Star"
        ]
    )

    if st.button(
        "🎮 START GAME",
        use_container_width=True
    ):

        st.session_state.game = {
            "mode": mode,
            "colors": colors,
            "names": names,
            "human": human,
            "positions": {
                color: [
                    -1,
                    -1,
                    -1,
                    -1
                ]
                for color in COLORS
            },
            "turn": 0,
            "dice": None,
            "movable": [],
            "winner": None,
            "shape": shape,
            "log": [
                f"{names[colors[0]]} goes first."
            ]
        }

        st.session_state.stage = "game"

        st.rerun()


# ============================================================
# GAME
# ============================================================

else:

    g = st.session_state.game

    # --------------------------------------------------------
    # Process a board click first
    # --------------------------------------------------------

    if handle_board_click():
        g["winner"] = check_winner()
        st.rerun()

    # --------------------------------------------------------
    # Winner
    # --------------------------------------------------------

    g["winner"] = check_winner()

    if g["winner"]:

        st.title("🎲 Ludo Master")

        st.markdown(
            f"""
            <div class="winner">
                🏆 {g["winner"]} WINS! 🏆
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            make_board(),
            unsafe_allow_html=True
        )

        if st.button(
            "🔄 NEW GAME",
            use_container_width=True
        ):

            st.session_state.stage = "setup"

            st.rerun()

        st.stop()

    # --------------------------------------------------------
    # Current player
    # --------------------------------------------------------

    color = current_color()

    name = g["names"][color]

    is_human = g["human"].get(
        color,
        True
    )

    st.title("🎲 Ludo Master")

    st.markdown(
        f"""
        <div class="status">
            🎯 <b>{name}</b>
            — {color.title()} Turn
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # HUMAN ROLL
    # --------------------------------------------------------

    if (
        is_human
        and g["dice"] is None
    ):

        if st.button(
            "🎲 ROLL DICE",
            use_container_width=True
        ):

            dice = random.randint(
                1,
                6
            )

            g["dice"] = dice

            g["movable"] = get_movable(
                color,
                dice
            )

            g["log"].insert(
                0,
                f"{name} rolled {dice}."
            )

            # EXACTLY ONE MOVE:
            # automatic
            if len(g["movable"]) == 1:

                auto_move_if_only_one()

            # NO MOVE
            elif (
                len(g["movable"]) == 0
                and dice != 6
            ):

                next_turn()

            st.rerun()

    # --------------------------------------------------------
    # COMPUTER TURN
    # --------------------------------------------------------

    if (
        not is_human
        and g["dice"] is None
    ):

        dice = random.randint(
            1,
            6
        )

        g["dice"] = dice

        g["movable"] = get_movable(
            color,
            dice
        )

        g["log"].insert(
            0,
            f"{name} rolled {dice}."
        )

        if g["movable"]:

            index = random.choice(
                g["movable"]
            )

            complete_move(index)

        elif dice != 6:

            next_turn()

        else:

            g["dice"] = None
            g["movable"] = []

        st.rerun()

    # --------------------------------------------------------
    # BOARD
    # --------------------------------------------------------

    st.markdown(
        make_board(),
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # DICE
    # --------------------------------------------------------

    if g["dice"] is not None:

        st.markdown(
            f"""
            <div class="status">
                🎲 Dice: <b>{g["dice"]}</b>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # MULTIPLE MOVABLE TOKENS
    # --------------------------------------------------------

    if (
        is_human
        and g["dice"] is not None
        and len(g["movable"]) > 1
    ):

        st.markdown(
            """
            <div class="hint">
                ✨ Tap a blinking piece on the board
            </div>
            """,
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # NO MOVE
    # --------------------------------------------------------

    if (
        is_human
        and g["dice"] is not None
        and len(g["movable"]) == 0
    ):

        if g["dice"] == 6:

            if st.button(
                "🎲 ROLL AGAIN",
                use_container_width=True
            ):

                g["dice"] = None
                g["movable"] = []

                st.rerun()

        else:

            st.info(
                "No move available."
            )

    # --------------------------------------------------------
    # LOG
    # --------------------------------------------------------

    with st.expander(
        "📜 Game Log"
    ):

        for item in g["log"][:15]:

            st.write(
                "• " + item
            )

    # --------------------------------------------------------
    # CONTROLS
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🔄 New Game",
            use_container_width=True
        ):

            st.session_state.stage = "setup"

            st.rerun()

    with col2:

        if st.button(
            "🗑️ Clear Log",
            use_container_width=True
        ):

            g["log"] = []

            st.rerun()
