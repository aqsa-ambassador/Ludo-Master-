import streamlit as st
import pathlib

st.set_page_config(page_title="Ludo Master", page_icon="🎲", layout="wide")

html_path = pathlib.Path(__file__).parent / "ludo.html"
html_code = html_path.read_text(encoding="utf-8")

st.components.v1.html(html_code, height=900, scrolling=True)
