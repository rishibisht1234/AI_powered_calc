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

        # st.session_state['show_register']=False
        with st.sidebar:
            if st.button('login'):
                st.session_state['show_register']=False
            if st.button('register'):
                st.session_state['show_register']=True
        
        
        

        if not st.session_state['show_register']:
            try:    
                
                if not authenticator.login():
                    st.error('invalid credentials')
                
            except Exception as e:
                st.error(str(e))
            
        if st.session_state['show_register']==True:
            try:
                email,username,name=authenticator.register_user(password_hint=False,captcha=False)
                if email and username and name:
                    st.write('successfully registered',name)
                    
                    
                    with open('main/config.yaml','w') as file:
                        yaml.dump(config,file,default_flow_style=False)
                    st.session_state['show_register']=False
                    st.rerun()
            except Exception as e:
                st.error(str(e))

    else:
        
        with st.sidebar:
            st.write(f"welcome {config['credentials']['usernames'][st.session_state['username']]['first_name']}")
            authenticator.logout()