# example/st_app.py

import streamlit as st
from streamlit_gsheets import GSheetsConnection

conn = st.connection("gsheets", type=GSheetsConnection)

data = conn.read(worksheet="Testing DATA.1")
st.dataframe(data)