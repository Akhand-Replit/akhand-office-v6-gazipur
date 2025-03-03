import streamlit as st
from utils.ui import render_page_title, user_status_indicator, clean_url
from utils.db import get_companies, create_company, toggle_company_status, get_branches, get_employees
from utils.auth import check_admin

def render_company_management():
    """Render company management page for admin."""
    if not check_admin():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Company Management", "Create and manage companies", "🏢")
    
    # Create company form
    st.write("### Create New Company")
    with st.container(border=True):
        with st.form("create_company_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input("Company Name", placeholder="Enter company name")
                profile_pic = st.text_input("Profile Picture URL", placeholder="Enter profile picture URL")
            
            with col2:
                username = st.text_input("Username", placeholder="Enter username for login")
                password = st.text_input("Password", type="password", placeholder="Enter password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
            
            submit_button = st.form_submit_button("Create Company", use_container_width=True)
            
            if submit_button:
                if not company_name or not username or not password:
                    st.error("Please fill all required fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    profile_pic_url = clean_url(profile_pic) if profile_pic else f"https://ui-avatars.com/api/?name={company_name}&background=random"
                    company_id = create_company(company_name, username, password, profile_pic_url, st.session_state.user_id)
                    
                    if company_id:
                        st.success(f"Company '{company_name}' created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create company")
    
    # List companies
    st.write("### Company List")
    
    companies = get_companies()
    
    if companies:
        for company in companies:
            company_id = company[0]
            company_name = company[1]
            username = company[2]
            profile_pic = company[3]
            is_active = company[4]
            created_at = company[5]
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    if profile_pic:
                        st.image(profile_pic, width=80)
                    else:
                        st.image(f"https://ui-avatars.com/api/?name={company_name}&background=random", width=80)
                
                with col2:
                    st.write(f"### {company_name}")
                    st.caption(f"Username: {username}")
                    
                    branches = get_branches(company_id)
                    employees = get_employees(company_id=company_id)
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Branches:** {len(branches)}")
                    with col_b:
                        st.write(f"**Employees:** {len(employees)}")
                
                with col3:
                    st.markdown(user_status_indicator(is_active), unsafe_allow_html=True)
                    
                    if is_active:
                        st.button("Deactivate", key=f"deactivate_{company_id}", 
                                 on_click=lambda cid=company_id: toggle_company_status(cid, False),
                                 type="secondary")
                    else:
                        st.button("Activate", key=f"activate_{company_id}", 
                                 on_click=lambda cid=company_id: toggle_company_status(cid, True),
                                 type="primary")
                    
                    if st.button("View Details", key=f"view_{company_id}"):
                        st.session_state.view_company_id = company_id
                        st.session_state.view_company_name = company_name
            
            # Show company details if selected
            if "view_company_id" in st.session_state and st.session_state.view_company_id == company_id:
                with st.expander(f"Details for {st.session_state.view_company_name}", expanded=True):
                    tab1, tab2 = st.tabs(["Branches", "Employees"])
                    
                    with tab1:
                        branches = get_branches(company_id)
                        if branches:
                            for branch in branches:
                                branch_id = branch[0]
                                branch_name = branch[1]
                                is_main_branch = branch[2]
                                branch_active = branch[3]
                                
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.write(f"**{branch_name}**" + (" (Main Branch)" if is_main_branch else ""))
                                
                                with col2:
                                    st.markdown(user_status_indicator(branch_active), unsafe_allow_html=True)
                                
                                st.divider()
                        else:
                            st.info("No branches found for this company")
                    
                    with tab2:
                        employees = get_employees(company_id=company_id)
                        if employees:
                            for employee in employees:
                                employee_id = employee[0]
                                employee_name = employee[1]
                                employee_username = employee[2]
                                employee_role = employee[4]
                                employee_active = employee[5]
                                branch_name = employee[6]
                                
                                col1, col2, col3 = st.columns([2, 2, 1])
                                
                                with col1:
                                    st.write(f"**{employee_name}**")
                                    st.caption(f"Username: {employee_username}")
                                
                                with col2:
                                    st.write(f"Role: {employee_role.capitalize()}")
                                    st.write(f"Branch: {branch_name}")
                                
                                with col3:
                                    st.markdown(user_status_indicator(employee_active), unsafe_allow_html=True)
                                
                                st.divider()
                        else:
                            st.info("No employees found for this company")
    else:
        st.info("No companies found. Create your first company using the form above.")
