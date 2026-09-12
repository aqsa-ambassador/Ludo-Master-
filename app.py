import streamlit as st
import streamlit.components.v1 as components
import random
import math

st.set_page_config(
    page_title="Ludo Master",
    page_icon="🎲",
    layout="centered"
)

# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>
.block-container {
    max-width: 520px;
    padding-top: 0.5rem;
}

#MainMenu, footer, header {
    visibility: hidden;
}

.stButton > button {
    border-radius: 12px;
    font-weight: 700;
    min-height: 42px;
}

.turn-box {
    background: #171717;
    color: white;
    padding: 10px;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 10px;
}

.win-box {
    background: #171717;
    color: white;
    padding: 16px;
    border-radius: 14px;
    text-align: center;
    font-size: 20px;
    font-weight: bold;
}

@keyframes blink {
    0%, 100% {
        opacity: 1;
        filter: drop-shadow(0 0 2px white);
    }
    50% {
        opacity: .45;
        filter: drop-shadow(0 0 10px white);
    }
}

.blink {
    animation: blink .7s infinite;
}

.pick-box {
    background: #fff4b8;
    color: #222;
    padding: 8px;
    border-radius: 10px;
    text-align: center;
    font-weight: bold;
    margin: 8px 0;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# CONSTANTS
# ============================================================

COLORS = ["red", "green", "yellow", "blue"]

COLOR = {
    "red": "#E53935",
    "green": "#43A047",
    "yellow": "#FDD835",
    "blue": "#1E88E5"
}

DARK = {
    "red": "#8E1E1A",
    "green": "#245C2A",
    "yellow": "#9C8A10",
    "blue": "#0F4C86"
}

PIN_EMOJI = {
    "red": "🔴",
    "green": "🟢",
    "yellow": "🟡",
    "blue": "🔵"
}

START = {
    "red": 0,
    "green": 13,
    "yellow": 26,
    "blue": 39
}

TEAM = {
    "red": "A",
    "yellow": "A",
    "green": "B",
    "blue": "B"
}

FINISH = 56

BASE = {
    "red": [(1, 1), (1, 4), (4, 1), (4, 4)],
    "green": [(1, 10), (1, 13), (4, 10), (4, 13)],
    "yellow": [(10, 10), (10, 13), (13, 10), (13, 13)],
    "blue": [(10, 1), (10, 4), (13, 1), (13, 4)]
}

PATH = [
    (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
    (5, 6), (4, 6), (3, 6), (2, 6), (1, 6),
    (0, 6), (0, 7), (0, 8),
    (1, 8), (2, 8), (3, 8), (4, 8), (5, 8),
    (6, 9), (6, 10), (6, 11), (6, 12), (6, 13),
    (7, 13), (8, 13),
    (8, 12), (8, 11), (8, 10), (8, 9),
    (9, 8), (10, 8), (11, 8), (12, 8), (13, 8),
    (14, 8), (14, 7), (14, 6),
    (13, 6), (12, 6), (11, 6), (10, 6), (9, 6),
    (8, 5), (8, 4), (8, 3), (8, 2), (8, 1),
    (7, 1), (7, 0), (6, 0), (5, 0), (4, 0),
    (3, 0), (2, 0)
]

HOME = {
    "red": [(7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6)],
    "green": [(1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7)],
    "yellow": [(7, 13), (7, 12), (7, 11), (7, 10), (7, 9), (7, 8)],
    "blue": [(13, 7), (12, 7), (11, 7), (10, 7), (9, 7), (8, 7)]
}

SAFE = {0, 8, 13, 21, 26, 34, 39, 47}


# ============================================================
# SESSION
# ============================================================

if "screen" not in st.session_state:
    st.session_state.screen = "setup"


# ============================================================
# GAME FUNCTIONS
# ============================================================

def current_color():
    game = st.session_state.game
    return game["colors"][game["turn"]]


def next_turn():
    game = st.session_state.game
    game["turn"] += 1

    if game["turn"] >= len(game["colors"]):
        game["turn"] = 0

    game["dice"] = None
    game["movable"] = []


def token_cell(color, position, token_index):
    if position == -1:
        return BASE[color][token_index]

    if position == FINISH:
        return (7, 7)

    if position <= 51:
        global_index = (
            START[color] + position
        ) % 52
        return PATH[global_index]

    return HOME[color][position - 52]


def is_safe(color, position):
    if position < 0 or position > 51:
        return True

    global_index = (
        START[color] + position
    ) % 52

    return global_index in SAFE


def possible_moves(color, dice):
    game = st.session_state.game
    result = []

    for index, position in enumerate(
        game["positions"][color]
    ):
        if position == -1:
            if dice == 6:
                result.append(index)

        elif position < FINISH:
            if position + dice <= FINISH:
                result.append(index)

    return result


def capture(color, new_position):
    game = st.session_state.game

    if new_position > 51:
        return False

    if is_safe(color, new_position):
        return False

    target = (
        START[color] + new_position
    ) % 52

    captured = False

    for other in game["colors"]:

        if other == color:
            continue

        if (
            game["mode"] == "Team Up"
            and TEAM[other] == TEAM[color]
        ):
            continue

        for index, position in enumerate(
            game["positions"][other]
        ):

            if 0 <= position <= 51:

                other_target = (
                    START[other] + position
                ) % 52

                if other_target == target:
                    game["positions"][other][index] = -1
                    captured = True

    return captured


def move_piece(color, index, dice):
    game = st.session_state.game

    old = game["positions"][color][index]

    if old == -1:
        new = 0
        message = (
            f"{game['names'][color]} opened a piece."
        )
    else:
        new = old + dice
        message = (
            f"{game['names'][color]} moved a piece "
            f"{dice} spaces."
        )

    game["positions"][color][index] = new

    if new == FINISH:
        message = (
            f"{game['names'][color]} reached HOME! 🏆"
        )

    if capture(color, new):
        message += " Captured an opponent!"

    game["log"].insert(0, message)


def check_winner():
    game = st.session_state.game

    if game["mode"] == "Team Up":

        for team in ["A", "B"]:

            members = [
                c
                for c in game["colors"]
                if TEAM[c] == team
            ]

            if members:

                finished = True

                for color in members:
                    if not all(
                        p == FINISH
                        for p in game["positions"][color]
                    ):
                        finished = False

                if finished:
                    return (
                        " & ".join(
                            game["names"][c]
                            for c in members
                        )
                        + f" — Team {team}"
                    )

    else:

        for color in game["colors"]:

            if all(
                p == FINISH
                for p in game["positions"][color]
            ):
                return game["names"][color]

    return None


def complete_move(index):
    game = st.session_state.game

    color = current_color()
    dice = game["dice"]

    if dice is None:
        return

    if index not in game["movable"]:
        return

    move_piece(
        color,
        index,
        dice
    )

    game["winner"] = check_winner()

    if game["winner"]:
        return

    if dice == 6:
        game["dice"] = None
        game["movable"] = []
    else:
        next_turn()


# ============================================================
# BOARD - VISUAL HELPERS
# ============================================================

def star_points(cx, cy, r_outer, r_inner):
    """Returns the point list for a 5-point star polygon."""
    points = []

    for i in range(10):
        angle = math.radians(-90 + i * 36)
        r = r_outer if i % 2 == 0 else r_inner
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points.append(f"{x:.2f},{y:.2f}")

    return " ".join(points)


def pin_svg(cx, cy, r, color, dark, active):
    """
    Draws a map-pin / marker shaped token (like the reference
    Ludo app) instead of a plain circle: a rounded head with a
    pointed base, plus a small white highlight dot.
    """
    cls = 'class="blink"' if active else ""
    head_r = r * .62
    head_cy = cy - r * .32
    point_y = cy + r * .8

    return (
        f'<g {cls}>'
        f'<path d="M {cx - head_r:.2f} {head_cy:.2f} '
        f'A {head_r:.2f} {head_r:.2f} 0 1 1 '
        f'{cx + head_r:.2f} {head_cy:.2f} '
        f'Q {cx + head_r * .95:.2f} {head_cy + head_r:.2f} '
        f'{cx:.2f} {point_y:.2f} '
        f'Q {cx - head_r * .95:.2f} {head_cy + head_r:.2f} '
        f'{cx - head_r:.2f} {head_cy:.2f} Z" '
        f'fill="{color}" stroke="{dark}" stroke-width="1.6" />'
        f'<circle cx="{cx:.2f}" cy="{head_cy:.2f}" '
        f'r="{head_r * .4:.2f}" fill="white" opacity=".9" />'
        f'</g>'
    )


def arrow_svg(cx, cy, dx, dy, s, color):
    """Small triangular direction arrow used at start squares."""

    if dx == 1:
        pts = [
            (cx - s, cy - s), (cx - s, cy + s), (cx + s, cy)
        ]
    elif dx == -1:
        pts = [
            (cx + s, cy - s), (cx + s, cy + s), (cx - s, cy)
        ]
    elif dy == 1:
        pts = [
            (cx - s, cy - s), (cx + s, cy - s), (cx, cy + s)
        ]
    else:
        pts = [
            (cx - s, cy + s), (cx + s, cy + s), (cx, cy - s)
        ]

    points = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)

    return f'<polygon points="{points}" fill="{color}" />'


# ============================================================
# BOARD
# ============================================================

def make_board():
    size = 360
    cell = size / 15
    game = st.session_state.game

    html = [
        f"""
        <svg
            viewBox="0 0 {size} {size}"
            xmlns="http://www.w3.org/2000/svg"
            style="width:100%;height:auto;background:#f5f1e8;"
        >
        """
    ]

    # Home areas
    areas = {
        "red": (0, 0),
        "green": (0, 9),
        "yellow": (9, 9),
        "blue": (9, 0)
    }

    for color, (row, col) in areas.items():

        html.append(
            f"""
            <rect
                x="{col * cell}"
                y="{row * cell}"
                width="{6 * cell}"
                height="{6 * cell}"
                fill="{COLOR[color]}33"
                stroke="#555"
                stroke-width="1"
            />
            """
        )

    # Main path
    for index, (row, col) in enumerate(PATH):

        fill = (
            "#FFF1A8"
            if index in SAFE
            else "#FFFFFF"
        )

        html.append(
            f"""
            <rect
                x="{col * cell}"
                y="{row * cell}"
                width="{cell}"
                height="{cell}"
                fill="{fill}"
                stroke="#777"
                stroke-width=".6"
            />
            """
        )

        # Safe-cell star marker
        if index in SAFE:

            cx = (col + .5) * cell
            cy = (row + .5) * cell

            html.append(
                f'<polygon points="'
                f'{star_points(cx, cy, cell * .34, cell * .15)}'
                f'" fill="#F2C744" stroke="#B8901A" '
                f'stroke-width=".6" />'
            )

    # Home paths
    for color in COLORS:

        for row, col in HOME[color]:

            html.append(
                f"""
                <rect
                    x="{col * cell}"
                    y="{row * cell}"
                    width="{cell}"
                    height="{cell}"
                    fill="{COLOR[color]}88"
                    stroke="#777"
                    stroke-width=".6"
                />
                """
            )

    # Home area "cards" behind each player's base pieces,
    # with a colored border and the player's name - similar
    # to the boxed base areas in the reference app.
    for color in COLORS:

        centers = [
            ((c + .5) * cell, (r + .5) * cell)
            for r, c in BASE[color]
        ]

        min_cx = min(c for c, _ in centers)
        max_cx = max(c for c, _ in centers)
        min_cy = min(c for _, c in centers)
        max_cy = max(c for _, c in centers)

        margin = cell * .95

        card_x = min_cx - margin
        card_y = min_cy - margin
        card_w = (max_cx - min_cx) + 2 * margin
        card_h = (max_cy - min_cy) + 2 * margin

        label = color.title()

        if color in game.get("names", {}):
            label = game["names"][color][:10]

        html.append(
            f"""
            <rect
                x="{card_x:.2f}"
                y="{card_y:.2f}"
                width="{card_w:.2f}"
                height="{card_h:.2f}"
                rx="10"
                fill="#FFFFFFCC"
                stroke="{COLOR[color]}"
                stroke-width="3"
            />
            <text
                x="{card_x + card_w / 2:.2f}"
                y="{card_y + 12:.2f}"
                font-size="8"
                font-weight="700"
                text-anchor="middle"
                fill="{DARK[color]}"
            >{label}</text>
            """
        )

    # Base slots (empty piece placeholders)
    for color in COLORS:

        for row, col in BASE[color]:

            html.append(
                f"""
                <circle
                    cx="{(col + .5) * cell}"
                    cy="{(row + .5) * cell}"
                    r="{cell * .27}"
                    fill="{COLOR[color]}15"
                    stroke="{COLOR[color]}"
                    stroke-width="1.4"
                />
                """
            )

    # Starting squares with an entrance direction arrow
    for color in COLORS:

        global_index = START[color]
        next_index = (global_index + 1) % 52

        row, col = PATH[global_index]
        next_row, next_col = PATH[next_index]

        html.append(
            f"""
            <rect
                x="{col * cell}"
                y="{row * cell}"
                width="{cell}"
                height="{cell}"
                fill="{COLOR[color]}"
                stroke="#444"
                stroke-width="1"
            />
            """
        )

        dx = next_col - col
        dy = next_row - row

        html.append(
            arrow_svg(
                (col + .5) * cell,
                (row + .5) * cell,
                dx,
                dy,
                cell * .22,
                "#FFFFFF"
            )
        )

    # Center
    html.append(
        f"""
        <polygon
            points="
            {6 * cell},{6 * cell}
            {7.5 * cell},{7.5 * cell}
            {6 * cell},{9 * cell}
            "
            fill="{COLOR['red']}"
        />

        <polygon
            points="
            {6 * cell},{6 * cell}
            {7.5 * cell},{7.5 * cell}
            {9 * cell},{6 * cell}
            "
            fill="{COLOR['green']}"
        />

        <polygon
            points="
            {9 * cell},{6 * cell}
            {7.5 * cell},{7.5 * cell}
            {9 * cell},{9 * cell}
            "
            fill="{COLOR['yellow']}"
        />

        <polygon
            points="
            {6 * cell},{9 * cell}
            {7.5 * cell},{7.5 * cell}
            {9 * cell},{9 * cell}
            "
            fill="{COLOR['blue']}"
        />
        """
    )

    # Tokens
    active_color = current_color()
    movable = set(game["movable"])

    for color in game["colors"]:

        for index, position in enumerate(
            game["positions"][color]
        ):

            row, col = token_cell(
                color,
                position,
                index
            )

            cx = (col + .5) * cell
            cy = (row + .5) * cell

            active = (
                color == active_color
                and index in movable
                and game["dice"] is not None
                and game["human"].get(color, True)
            )

            html.append(
                pin_svg(
                    cx,
                    cy,
                    cell * .34,
                    COLOR[color],
                    DARK[color],
                    active
                )
            )

    html.append(
        f"""
        <rect
            x="0"
            y="0"
            width="{size}"
            height="{size}"
            fill="none"
            stroke="#222"
            stroke-width="3"
        />
        </svg>
        """
    )

    svg = "".join(html)

    # Strip leading whitespace from every line. Without this,
    # indented lines (4+ spaces) get treated by Streamlit's
    # Markdown parser as a code block, so the SVG is shown as
    # raw text instead of being rendered as an image.
    svg = "\n".join(
        line.strip() for line in svg.splitlines()
    )

    return svg


def render_board():
    """
    Render the SVG board using components.html instead of
    st.markdown. Streamlit's Markdown parser can fail to detect
    multi-line HTML/SVG tags as real HTML (it starts treating
    the content as plain text instead), which is what caused the
    raw SVG code to show up on screen. components.html renders
    the given markup directly inside an iframe, with no Markdown
    parsing involved, so this always renders correctly.
    """
    components.html(
        f"""
        <html>
        <body style="margin:0;padding:0;">
        {make_board()}
        </body>
        </html>
        """,
        height=380,
        scrolling=False
    )


DICE_PIPS = {
    1: [(.5, .5)],
    2: [(.27, .27), (.73, .73)],
    3: [(.27, .27), (.5, .5), (.73, .73)],
    4: [(.27, .27), (.73, .27), (.27, .73), (.73, .73)],
    5: [
        (.27, .27), (.73, .27), (.5, .5),
        (.27, .73), (.73, .73)
    ],
    6: [
        (.27, .22), (.73, .22),
        (.27, .5), (.73, .5),
        (.27, .78), (.73, .78)
    ]
}


def render_dice(value, color):
    """
    Renders an actual dice face with black pips (like a real
    Ludo app) instead of plain 'Dice: 3' text, colored with a
    border matching the current player.
    """
    size = 84
    pip_r = size * .1

    pips = "".join(
        f'<circle cx="{x * size:.1f}" '
        f'cy="{y * size:.1f}" '
        f'r="{pip_r:.1f}" fill="#222" />'
        for x, y in DICE_PIPS.get(value, [])
    )

    svg = (
        f'<svg width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<rect x="3" y="3" width="{size - 6}" '
        f'height="{size - 6}" rx="16" fill="#ffffff" '
        f'stroke="{color}" stroke-width="5" />'
        f'{pips}'
        f'</svg>'
    )

    components.html(
        f'<div style="display:flex;flex-direction:column;'
        f'align-items:center;justify-content:center;'
        f'font-family:sans-serif;">'
        f'{svg}'
        f'<div style="margin-top:4px;font-weight:700;'
        f'color:#eee;">Dice: {value}</div>'
        f'</div>',
        height=size + 34
    )


# ============================================================
# SETUP SCREEN
# ============================================================

if st.session_state.screen == "setup":

    st.title("🎲 Ludo Master")
    st.caption("Mobile Friendly Ludo")

    mode = st.radio(
        "Game Mode",
        ["Classic", "Team Up"],
        horizontal=True
    )

    count = st.selectbox(
        "Number of Players",
        [2, 3, 4],
        index=1
    )

    if count == 2:
        colors = ["red", "yellow"]
    elif count == 3:
        colors = ["red", "green", "yellow"]
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
                ["Human", "Computer"],
                key=f"role_{color}"
            )

            human[color] = (
                role == "Human"
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
                c: [-1, -1, -1, -1]
                for c in COLORS
            },
            "turn": 0,
            "dice": None,
            "movable": [],
            "winner": None,
            "log": [
                f"{names[colors[0]]} goes first."
            ]
        }

        st.session_state.screen = "game"

        st.rerun()


# ============================================================
# GAME SCREEN
# ============================================================

else:

    game = st.session_state.game

    game["winner"] = check_winner()

    if game["winner"]:

        st.title("🎲 Ludo Master")

        st.markdown(
            f"""
            <div class="win-box">
                🏆 {game["winner"]} WINS! 🏆
            </div>
            """,
            unsafe_allow_html=True
        )

        render_board()

        if st.button(
            "🔄 NEW GAME",
            use_container_width=True
        ):

            st.session_state.screen = "setup"
            st.rerun()

        st.stop()

    color = current_color()
    name = game["names"][color]
    is_human = game["human"].get(
        color,
        True
    )

    st.title("🎲 Ludo Master")

    st.markdown(
        f"""
        <div class="turn-box" style="border:2px solid {COLOR[color]};">
            {PIN_EMOJI[color]} <b>{name}</b>
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
        and game["dice"] is None
    ):

        if st.button(
            "🎲 ROLL DICE",
            use_container_width=True
        ):

            dice = random.randint(
                1,
                6
            )

            game["dice"] = dice

            game["movable"] = possible_moves(
                color,
                dice
            )

            game["log"].insert(
                0,
                f"{name} rolled {dice}."
            )

            # One possible piece:
            # automatically move it.
            if len(game["movable"]) == 1:

                complete_move(
                    game["movable"][0]
                )

            # No move and not six:
            # next player's turn.
            elif (
                len(game["movable"]) == 0
                and dice != 6
            ):

                next_turn()

            st.rerun()

    # --------------------------------------------------------
    # COMPUTER
    # --------------------------------------------------------

    if (
        not is_human
        and game["dice"] is None
    ):

        dice = random.randint(
            1,
            6
        )

        game["dice"] = dice

        game["movable"] = possible_moves(
            color,
            dice
        )

        game["log"].insert(
            0,
            f"{name} rolled {dice}."
        )

        if game["movable"]:

            chosen = random.choice(
                game["movable"]
            )

            complete_move(
                chosen
            )

        elif dice != 6:

            next_turn()

        else:

            game["dice"] = None
            game["movable"] = []

        st.rerun()

    # --------------------------------------------------------
    # BOARD
    # --------------------------------------------------------

    render_board()

    # --------------------------------------------------------
    # DICE RESULT
    # --------------------------------------------------------

    if game["dice"] is not None:

        render_dice(game["dice"], COLOR[color])

    # --------------------------------------------------------
    # MULTIPLE MOVES
    # --------------------------------------------------------

    if (
        is_human
        and game["dice"] is not None
        and len(game["movable"]) > 1
    ):

        st.markdown(
            """
            <div class="pick-box">
                ✨ Tap a blinking piece to choose it
            </div>
            """,
            unsafe_allow_html=True
        )

        # Reliable Streamlit fallback controls.
        # No Token 1 / Token 2 text is shown.
        columns = st.columns(
            len(game["movable"])
        )

        for column, index in zip(
            columns,
            game["movable"]
        ):

            with column:

                if st.button(
                    PIN_EMOJI[color],
                    key=(
                        f"move_{color}_"
                        f"{index}_{game['dice']}"
                    ),
                    help="Choose this piece",
                    use_container_width=True
                ):

                    complete_move(index)
                    st.rerun()

    # --------------------------------------------------------
    # SIX WITH NO MOVE
    # --------------------------------------------------------

    if (
        is_human
        and game["dice"] == 6
        and len(game["movable"]) == 0
    ):

        if st.button(
            "🎲 ROLL AGAIN",
            use_container_width=True
        ):

            game["dice"] = None
            game["movable"] = []

            st.rerun()

    # --------------------------------------------------------
    # LOG
    # --------------------------------------------------------

    with st.expander("📜 Game Log"):

        for message in game["log"][:15]:

            st.write(
                "• " + message
            )

    # --------------------------------------------------------
    # NEW GAME
    # --------------------------------------------------------

    if st.button(
        "🔄 NEW GAME",
        use_container_width=True
    ):

        st.session_state.screen = "setup"
        st.rerun()
