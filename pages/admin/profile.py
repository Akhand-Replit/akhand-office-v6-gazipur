import streamlit as st
from utils.ui import render_page_title, clean_url
from utils.db import update_admin_profile
from utils.auth import check_admin

def render_profile():
    """Render profile page for admin."""
    if not check_admin():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Admin Profile", "Update your profile information", "👤")
    
    # Profile display and update form
    with st.container(border=True):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(st.session_state.profile_pic, width=200)
        
        with col2:
            st.write("### Profile Information")
            st.write(f"**Username:** {st.session_state.username}")
            
            with st.form("update_profile_form"):
                profile_name = st.text_input("Profile Name", value="System Administrator")
                profile_pic = st.text_input("Profile Picture URL", value=st.session_state.profile_pic)
                
                st.caption("Note: Password cannot be changed as it's stored in Streamlit secrets.")
                
                submit_button = st.form_submit_button("Update Profile", use_container_width=True)
                
                if submit_button:
                    profile_pic_url = clean_url(profile_pic) if profile_pic else f"https://ui-avatars.com/api/?name=Admin&background=random"
                    
                    success = update_admin_profile(st.session_state.user_id, profile_name, profile_pic_url)
                    
                    if success:
                        st.success("Profile updated successfully!")
                        # Update session state
                        st.session_state.profile_pic = profile_pic_url
                        st.rerun()
                    else:
                        st.error("Failed to update profile")
    
    # System Information
    st.write("### System Information")
    
    with st.container(border=True):
        st.write("**Application:** Company Management System")
        st.write("**Streamlit Version:** 1.42.3")
        st.write("**Database:** PostgreSQL")
