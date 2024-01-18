import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth

app_name = 'streamlit-app'
cred = credentials.Certificate("streamlit-app-afe93-firebase-adminsdk-u6cf0-153e2b5eb7.json")

# Check if the app is already initialized, and initialize only if it's not
if not firebase_admin._apps.get(app_name):
    firebase_admin.initialize_app(cred, name=app_name)

# Function to check if the user is authenticated
def is_user_authenticated(email, password):
    try:
        # Retrieve the user by email
        user = auth.get_user_by_email(email)

        # Compare the provided password with the stored hash (not implemented here)
        # Note: This part should involve secure password verification mechanisms

        return user.uid
    except Exception as e:
        return None

# Function to set authentication status in session state
def set_authenticated_status(authenticated, user_id=None):
    st.session_state.authenticated = authenticated
    st.session_state.user_id = user_id

# Function to check authentication status in session state
def check_authenticated_status():
    return getattr(st.session_state, 'authenticated', False), getattr(st.session_state, 'user_id', None)

st.sidebar.header("Working Hours Calculator --v 1.2")

# Check authentication status in session state
is_authenticated, user_id = check_authenticated_status()

# Check if the user is logged in
if is_authenticated:
    st.sidebar.header(f"Welcome, {user_id}!")

    # Logout Button
    if st.sidebar.button("Logout"):
        # Clear the authentication status in session state
        set_authenticated_status(False)

        # Optional: Redirect to a specific page or perform additional actions on logout

    # Dashboard
    st.subheader("Dashboard")
    st.write("Welcome to the Dashboard!")
    # You can add more content and controls for the dashboard here
else:
    # Registration Form
    st.subheader("Registration Form")
    user_name_reg = st.text_input("Enter your Username for registration", key="usr_name_reg")
    user_email_reg = st.text_input("Enter your email for registration")
    if "@" and "." not in user_email_reg:
        st.warning("Email format invalid")
    else:
        pass
    user_password_reg = st.text_input("Password for registration", type="password")
    user_conf_password_reg = st.text_input("Confirm Password for registration", type="password")

    if st.button("Register"):
        try:
            user = auth.create_user(email=user_email_reg, password=user_password_reg, uid=user_name_reg)
            st.success("Registration Successful!")
            st.write("Please login using the registered credentials")
            st.balloons()
        except Exception as e:
            st.error(f"Registration failed: {e}")

    # Login Area
    st.sidebar.subheader("Login")
    user_email_login = st.sidebar.text_input("Email for login", key="lo_email")
    user_password_login = st.sidebar.text_input("Password for login", type="password", key="lo_pwd")

    login_btn = st.sidebar.button("Login")

    if login_btn:
        user_id = is_user_authenticated(user_email_login, user_password_login)
        if user_id:
            st.success("Login Successful!")

            # Set the authentication status in session state
            set_authenticated_status(True, user_id)
        else:
            st.error("Login failed: Invalid credentials")
