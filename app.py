import streamlit as st

# दोनों पेजों को आपस में जोड़ना
page_1 = st.Page("voice_studio.py", title="AI Voice Studio", icon="🎙️", default=True)
page_2 = st.Page("yt_transcribe.py", title="YouTube Transcribe", icon="📝")

# नेविगेशन चालू करना
pg = st.navigation([page_1, page_2])
st.set_page_config(page_title="AI Studio", page_icon="🎙️", layout="centered")

pg.run()
