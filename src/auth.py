"""Streamlit authentication using credentials configured in .streamlit/secrets.toml."""
import hmac
import streamlit as st


def _users():
    try:
        configured = dict(st.secrets.get('users', {}))
        # Do not accept the placeholder credential copied from the example file.
        return {user: password for user, password in configured.items()
                if password and 'replace-with' not in str(password).lower()
                and 'choose-' not in str(password).lower()}
    except Exception:
        return {}


def require_login():
    users=_users()
    if st.session_state.get('logged_in') and st.session_state.get('user') in users:
        with st.sidebar:
            st.caption(f"Signed in as **{st.session_state['user']}**")
            if st.button('Log out'):
                st.session_state.clear(); st.rerun()
        return
    st.title('Olist Sales & Customer Analytics')
    st.subheader('Sign in')
    if not users:
        st.error('Login is not configured. Create .streamlit/secrets.toml from .streamlit/secrets.toml.example and set your own password.')
        st.code('[users]\nmy_user_id = "choose-a-strong-password"',language='toml')
        st.stop()
    with st.form('login_form'):
        user=st.text_input('User ID')
        password=st.text_input('Password',type='password')
        submitted=st.form_submit_button('Log in')
    if submitted:
        stored=users.get(user)
        if stored is not None and hmac.compare_digest(str(stored),str(password)):
            st.session_state['logged_in']=True; st.session_state['user']=user; st.rerun()
        st.error('Incorrect user ID or password.')
    st.stop()
