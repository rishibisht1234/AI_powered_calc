import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# --- Load config ---
with open('main/config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# --- Initialize authenticator ---
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

def login_register_page():
    
    # flag for register and login form
    for key in ['authentication_status', 'username', 'name', 'logout', 'show_register']:
        if key not in st.session_state:
            st.session_state[key] = None if key == 'authentication_status' else ""

    if not st.session_state['authentication_status']:

        with st.sidebar:
            if st.button('Login'):
                st.session_state['show_register'] = False
                st.rerun() # Use rerun for a cleaner state switch
            if st.button('Register'):
                st.session_state['show_register'] = True
                st.rerun() # Use rerun for a cleaner state switch
        
        if not st.session_state['show_register']:
            authenticator.login()
            
            # --- NEW CODE START ---
            # Check the authentication status after the login attempt.
            # It will be False if the credentials are wrong.
            if st.session_state["authentication_status"] is False:
                st.error('Username/password is incorrect')
            # --- NEW CODE END ---
            
        if st.session_state['show_register'] == True:
            try:
                email, username, name = authenticator.register_user(pre_authorization=False)
                if email and username and name:
                    st.success('User registered successfully')
                    
                    # Save the new user to the config file
                    with open('main/config.yaml', 'w') as file:
                        yaml.dump(config, file, default_flow_style=False)
                    
                    st.session_state['show_register'] = False
                    st.rerun()
            except Exception as e:
                st.error(e)

    else:
        with st.sidebar:
            # Display the user's first name, not the username
            st.write(f"Welcome {st.session_state['name']}")
            authenticator.logout()