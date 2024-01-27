import streamlit as st
import requests
import json
import pandas as pd

backendUrl = 'http://fastapi:8888'

def num_of_data():
    rsp = requests.get(f'{backendUrl}/api/num_of_data')
    rst = json.loads(rsp.text)
    return rst['data']

def get_data(page, pageSize):
    rsp = requests.get(f'{backendUrl}/api/data?page={page}&pageSize={pageSize}')
    rst = json.loads(rsp.text)
    return rst['data']

def search_data(q, tags=[]):
    rsp = requests.get(f'{backendUrl}/api/search?q={q}&tags={",".join(tags)}')
    rst = json.loads(rsp.text)
    return rst['data']

def delete_data():
    edited_rows = st.session_state["data_editor"]["edited_rows"]
    rows_to_delete = []
    for idx, value in edited_rows.items():
        if value["selected"] is True:
            rows_to_delete.append(idx)
    if len(rows_to_delete) == 0:
        return
    data = json.loads(st.session_state["data"])
    delIds = ','.join([str(item['recId']) for idx, item in enumerate(data) if idx in rows_to_delete])
    rsp = requests.delete(f'{backendUrl}/api/data?recIds={delIds}')
    rst = json.loads(rsp.text)
    if rst['status'] == 200:
        print(f'delete: {delIds}')

def update_data():
    data = json.loads(st.session_state["data"])
    edited_rows = st.session_state["data_editor"]["edited_rows"]
    for idx, item in edited_rows.items():
        newItem = data[idx]
        updated = []
        for field in item:
            if field == 'selected':
                continue
            updated.append(field)
            newItem[field] = item[field]
        if len(updated):
            rsp = requests.put(f'{backendUrl}/api/data', json=newItem)
            rst = json.loads(rsp.text)
            print(f'update recId {newItem["recId"]}: ', rst)
        for field in updated:
            del st.session_state["data_editor"]["edited_rows"][idx][field]

def get_tags():
    rsp = requests.get(f'{backendUrl}/api/tags')
    rst = json.loads(rsp.text)
    if rst['status'] == 200:
        return rst['tags']
    return []


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
st.session_state["query"] = st.sidebar.text_input('keyword', '')
st.session_state["tags"] = get_tags()
st.session_state["selected_tags"] = st.sidebar.multiselect(
    'Tags',
    st.session_state["tags"]
)
st.title("🔍 My Knowledge Base")
pageSize = 10
# pageSize = st.sidebar.slider('Page size', 1, 100, 10)
prev, _ ,next = st.columns([2, 8, 2])

if next.button("Next"):
    if st.session_state.page_number + 1 > num_of_data():
        st.session_state.page_number = 0
    else:
        st.session_state.page_number += 1

if prev.button("Previous"):
    if st.session_state.page_number - 1 < 1:
        st.session_state.page_number = 1
    else:
        st.session_state.page_number -= 1
st.divider()
if st.button("Delete"):
    delete_data()
    if st.session_state["query"]:
        st.session_state["data"] = search_data(st.session_state["query"])
    else:
        st.session_state["data"] = get_data(st.session_state.page_number, pageSize)

if st.session_state["query"] or len(st.session_state["selected_tags"]) > 0:
    st.session_state["data"] = search_data(st.session_state["query"], st.session_state["selected_tags"])
else:
    st.session_state["data"] = get_data(st.session_state.page_number, pageSize)

df = pd.DataFrame(eval(st.session_state["data"]))
modified_df = df.copy()
modified_df["selected"] = False
# Make Delete be the first column
st.session_state['renderDf'] = modified_df[["selected"] + modified_df.columns[:-1].tolist()]
st.data_editor(st.session_state['renderDf'] , key="data_editor", hide_index=True, disabled=["recId", "content", "url", "user"], on_change=update_data)

