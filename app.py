import streamlit as st
import os
import sys

# Add the current directory to the Python path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Now import the utility modules
from utils.auth import check_authentication, login_user, logout_user
from utils.db import initialize_database
from utils.ui import set_page_config, render_login_form
import streamlit as st

# Initialize database
initialize_database()

# Set page configuration
set_page_config("Company Management System")

# Add custom CSS
try:
    with open("static/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    # Create the directory if it doesn't exist
    os.makedirs("static", exist_ok=True)
    # Create the CSS file if it doesn't exist
    with open("static/style.css", "w") as f:
        f.write("/* Custom styling will be added here */")
    # Now try again
    with open("static/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "company_id" not in st.session_state:
    st.session_state.company_id = None
if "branch_id" not in st.session_state:
    st.session_state.branch_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "profile_pic" not in st.session_state:
    st.session_state.profile_pic = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

# Main application
def main():
    # Check if user is authenticated
    if not st.session_state.authenticated:
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.header("Welcome to Company Management System")
                st.subheader("Please login to continue")
                render_login_form()
    else:
        # Display appropriate dashboard based on user role
        if st.session_state.user_role == "admin":
            from pages.admin.dashboard import render_admin_dashboard
            render_admin_dashboard()
        elif st.session_state.user_role == "company":
            from pages.company.dashboard import render_company_dashboard
            render_company_dashboard()
        elif st.session_state.user_role == "manager":
            from pages.manager.dashboard import render_manager_dashboard
            render_manager_dashboard()
        elif st.session_state.user_role == "asst_manager":
            from pages.asst_manager.dashboard import render_asst_manager_dashboard
            render_asst_manager_dashboard()
        elif st.session_state.user_role == "employee":
            from pages.employee.dashboard import render_employee_dashboard
            render_employee_dashboard()

if __name__ == "__main__":
    main()
