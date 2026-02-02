import streamlit as st
import json

st.title("Intelligent Data Dictionary Chat")

question = st.text_input("Ask about your database")

if question:
    with open("metadata.json") as f:
        metadata = json.load(f)

    st.write("Answer (demo):")
    st.json(metadata)
