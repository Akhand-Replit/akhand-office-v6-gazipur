import streamlit as st
from utils.ui import render_page_title, clean_url
from utils.db import update_employee_profile
from utils.auth import check_manager

def render_profile():
    """Render profile page for manager."""
    if not check_manager():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Manager Profile", "Update your profile information", "👤")
    
    # Profile display and update form
    with st.container(border=True):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(st.session_state.profile_pic, width=200)
        
        with col2:
            st.write("### Profile Information")
            st.write(f"**Username:** {st.session_state.username}")
            st.write("**Role:** Branch Manager")
            
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
    
    # Account Information
    st.write("### Account Information")
    
    with st.container(border=True):
        st.write("**Account Type:** Employee")
        st.write("**Access Level:** Branch Manager")
        st.write("**Permissions:**")
        st.write("- Create and manage general employees")
        st.write("- Assign tasks to employees and assistant managers")
        st.write("- View and generate reports")
        st.write("- Mark tasks as completed for the entire branch")
        st.write("- Communicate with company and employees")
