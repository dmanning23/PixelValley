import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from app import *

def changeLoginStatus(state):
    st.session_state["login_status"] = state
    st.rerun()
    
def authenticate():

    with open('./config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )

    name, auth, user = authenticator.login('Login', 'sidebar')
    if auth:
        st.sidebar.write(f'Welcome {st.session_state["name"]}')
        authenticator.logout('Logout', 'sidebar', key='unique_key')
        
        #Get the user ID... here it is just the index of the user
        if "username" in st.session_state and st.session_state['username'] is not None:
            userId = list(config['credentials']['usernames'].keys()).index(st.session_state['username'])
            st.session_state['userId'] = userId
            
            #Display the main content of the application
            main()
    elif st.session_state["authentication_status"] is None or st.session_state["authentication_status"] is False:

        #add a message to the main screen
        st.warning('Please enter your username and password')

        #Clear out any session stuff we have added
        st.session_state['userId'] = None
        clearSession()

        #the user tried to register
        try:
            #popup the register user widget
            if authenticator.register_user('Register user', location="sidebar", preauthorization=False):
                st.success('User registered successfully')

                #write out the user configuration
                with open('./config.yaml', 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)

                st.rerun()
        except Exception as e:
            st.error(e)

        if st.session_state["authentication_status"] is False:
            #tell the user their username/pwd is wrong
            st.error('Username/password is incorrect')
            
    #if st.session_state["authentication_status"]:
    #    try:
    #        if authenticator.reset_password(st.session_state["username"], 'Reset password'):
    #            st.success('Password modified successfully')
    #    except Exception as e:
    #        st.error(e)

    #if st.session_state["authentication_status"]:
    #    try:
    #        if authenticator.update_user_details(st.session_state["username"], 'Update user details'):
    #            st.success('Entries updated successfully')
    #    except Exception as e:
    #        st.error(e)

if __name__ == "__main__":
    #Initialize the Streamlit page
    st.set_page_config(
        page_title="Pixel Valley - WIP",
        page_icon="🏘")
    authenticate()