import streamlit as st
from utils.db import verify_admin, verify_company, verify_employee

def login_user(username, password, role):
    """Login user based on role."""
    if role == "admin":
        user = verify_admin(username, password)
    elif role == "company":
        user = verify_company(username, password)
    else:  # employee, manager, asst_manager
        user = verify_employee(username, password)
    
    if user:
        st.session_state.authenticated = True
        st.session_state.user_id = user["id"]
        st.session_state.username = user["username"]
        st.session_state.user_role = user["role"]
        st.session_state.profile_pic = user["profile_pic"]
        
        if "company_id" in user:
            st.session_state.company_id = user["company_id"]
        
        if "branch_id" in user:
            st.session_state.branch_id = user["branch_id"]
        
        return True
    return False

def logout_user():
    """Logout current user."""
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.company_id = None
    st.session_state.branch_id = None
    st.session_state.profile_pic = None
    st.session_state.current_page = "dashboard"

def check_authentication():
    """Check if user is authenticated."""
    return st.session_state.authenticated

def check_admin():
    """Check if user is an admin."""
    return st.session_state.authenticated and st.session_state.user_role == "admin"

def check_company():
    """Check if user is a company."""
    return st.session_state.authenticated and st.session_state.user_role == "company"

def check_manager():
    """Check if user is a manager."""
    return st.session_state.authenticated and st.session_state.user_role == "manager"

def check_asst_manager():
    """Check if user is an assistant manager."""
    return st.session_state.authenticated and st.session_state.user_role == "asst_manager"

def check_employee():
    """Check if user is a general employee."""
    return st.session_state.authenticated and st.session_state.user_role == "employee"

def check_role_access(required_roles):
    """Check if user has required role access."""
    return st.session_state.authenticated and st.session_state.user_role in required_roles
