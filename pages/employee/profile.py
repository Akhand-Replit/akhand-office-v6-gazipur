import streamlit as st
from utils.ui import render_page_title, clean_url
from utils.db import update_employee_profile, update_employee_password
from utils.auth import check_employee

def render_profile():
    """Render profile page for employee."""
    if not check_employee():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Employee Profile", "Update your profile information", "👤")
    
    # Profile display and update form
    with st.container(border=True):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(st.session_state.profile_pic, width=200)
        
        with col2:
            st.write("### Profile Information")
            st.write(f"**Username:** {st.session_state.username}")
            st.write("**Role:** General Employee")
            
            with st.form("update_profile_form"):
                employee_name = st.text_input("Full Name", value=st.session_state.username)
                profile_pic = st.text_input("Profile Picture URL", value=st.session_state.profile_pic)
                
                st.caption("Note: Username and role cannot be changed.")
                
                submit_button = st.form_submit_button("Update Profile", use_container_width=True)
                
                if submit_button:
                    profile_pic_url = clean_url(profile_pic) if profile_pic else f"https://ui-avatars.com/api/?name={employee_name}&background=random"
                    
                    success = update_employee_profile(st.session_state.user_id, employee_name, profile_pic_url)
                    
                    if success:
                        st.success("Profile updated successfully!")
                        # Update session state
                        st.session_state.profile_pic = profile_pic_url
                        st.rerun()
                    else:
                        st.error("Failed to update profile")
    
    # Password Update Form
    st.write("### Update Password")
    
    with st.container(border=True):
        with st.form("update_password_form"):
            current_password = st.text_input("Current Password", type="password", placeholder="Enter your current password")
            new_password = st.text_input("New Password", type="password", placeholder="Enter your new password")
            confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Confirm your new password")
            
            submit_password = st.form_submit_button("Update Password", use_container_width=True)
            
            if submit_password:
                if not current_password or not new_password or not confirm_password:
                    st.error("Please fill all password fields")
                elif new_password != confirm_password:
                    st.error("New password and confirm password do not match")
                else:
                    success, message = update_employee_password(st.session_state.user_id, current_password, new_password)
                    
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
    
    # Account Information
    st.write("### Account Information")
    
    with st.container(border=True):
        st.write("**Account Type:** Employee")
        st.write("**Access Level:** General Employee")
        st.write("**Permissions:**")
        st.write("- View and complete assigned tasks")
        st.write("- Submit daily reports")
        st.write("- View personal reports")
        st.write("- Communicate with company and managers")
