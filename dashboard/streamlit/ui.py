import streamlit as st
import requests
import json

backendUrl = 'http://127.0.0.1:8000'

def num_of_data():
    rsp = requests.get(f'{backendUrl}/api/num_of_data')
    rst = json.loads(rsp.text)
    return rst['data']

def get_data(page, pageSize):
    rsp = requests.get(f'{backendUrl}/api/data?page={page}&pageSize={pageSize}')
    rst = json.loads(rsp.text)
    return rst['data']

def search_data(q):
    rsp = requests.get(f'{backendUrl}/api/search?q={q}')
    rst = json.loads(rsp.text)
    return rst['data']

numOfData = num_of_data()

st.set_page_config(
    page_title="My Knowledge Base",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/ricky42613/rag_labeler/',
        'Report a bug': "https://github.com/ricky42613/rag_labeler/pulls",
        'About': "# Manage your knowledge base"
    }
)
st.session_state['page_number'] = 1
st.sidebar.title("Setting")
st.sidebar.divider()
query = st.sidebar.text_input('keyword', '')
st.title("🔍 My Knowledge Base")
st.divider()
pageSize = 10
# pageSize = st.sidebar.slider('Page size', 1, 100, 10)
prev, _ ,next = st.columns([2, 8, 2])

if next.button("Next"):
    if st.session_state.page_number + 1 > numOfData:
        st.session_state.page_number = 0
    else:
        st.session_state.page_number += 1

if prev.button("Previous"):
    if st.session_state.page_number - 1 < 1:
        st.session_state.page_number = 1
    else:
        st.session_state.page_number -= 1
if query:
    data = search_data(query)
    st.json(data)
else:
    data = get_data(st.session_state.page_number, pageSize)
    st.json(data)