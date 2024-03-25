import streamlit as st
from app import *

if __name__ == "__main__":
    #Initialize the Streamlit page
    st.set_page_config(
        page_title="Pixel Valley - WIP",
        page_icon="🏘")
    st.session_state['userId'] = 0
    main()