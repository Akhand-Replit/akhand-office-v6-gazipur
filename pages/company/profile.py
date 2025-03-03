import streamlit as st
from utils.ui import render_page_title, clean_url
from utils.db import update_company_profile
from utils.auth import check_company

def render_profile():
    """Render profile page for company."""
    if not check_company():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Company Profile", "Update your company information", "👤")
    
    # Profile display and update form
    with st.container(border=True):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(st.session_state.profile_pic, width=200)
        
        with col2:
            st.write("### Company Information")
            st.write(f"**Username:** {st.session_state.username}")
            
            with st.form("update_profile_form"):
                company_name = st.text_input("Company Name", value=st.session_state.username)
                profile_pic = st.text_input("Profile Picture URL", value=st.session_state.profile_pic)
                
                st.caption("Note: Username cannot be changed once set.")
                
                submit_button = st.form_submit_button("Update Profile", use_container_width=True)
                
                if submit_button:
                    profile_pic_url = clean_url(profile_pic) if profile_pic else f"https://ui-avatars.com/api/?name={company_name}&background=random"
                    
                    success = update_company_profile(st.session_state.user_id, company_name, profile_pic_url)
                    
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
        st.write("**Account Type:** Company")
        st.write("**Access Level:** Company Management")
        st.write("**Permissions:**")
        st.write("- Create and manage branches")
        st.write("- Create and manage employees")
        st.write("- Assign tasks to branches and employees")
        st.write("- View and generate reports")
        st.write("- Communicate with admin and employees")
