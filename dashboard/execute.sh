nohup python -m uvicorn server:app --reload --port 8888 &
nohup streamlit run ui.py &
nohup python -m bytewax.run flow -w 2 &