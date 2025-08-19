
import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Docs Q&A RAG", layout="wide")
st.title("Docs Q&A RAG")
st.write("Ask questions about QuickNode Streams documentation and get answers with citations.")

q = st.text_input("Your question", placeholder="What is a Solana Stake Program Filter")

if st.button("Ask") and q:
    try:
        resp = requests.post(f"{API_URL}/ask", json={"question": q}, timeout=180)
        if resp.status_code == 200:
            st.markdown("### Answer")
            st.write(resp.json()["answer"])
        else:
            st.error(f"Error {resp.status_code}: {resp.text}")
    except Exception as e:
        st.error(str(e))
