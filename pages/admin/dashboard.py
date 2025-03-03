import streamlit as st
from utils.ui import render_navigation, render_page_title, user_status_indicator
from utils.db import get_companies, get_branches, get_employees
from utils.auth import check_admin

def render_admin_dashboard():
    """Render admin dashboard."""
    if not check_admin():
        st.error("You don't have permission to access this page.")
        return
    
    # Define navigation items for admin
    navigation_items = [
        {"label": "Dashboard", "page": "dashboard", "icon": "🏠"},
        {"label": "Company Management", "page": "company_management", "icon": "🏢"},
        {"label": "Messages", "page": "messages", "icon": "✉️"},
        {"label": "Profile", "page": "profile", "icon": "👤"}
    ]
    
    # Render navigation
    render_navigation(st.session_state.current_page, navigation_items)
    
    # Render appropriate page based on current_page
    if st.session_state.current_page == "dashboard":
        render_dashboard()
    elif st.session_state.current_page == "company_management":
        from pages.admin.company_management import render_company_management
        render_company_management()
    elif st.session_state.current_page == "messages":
        from pages.admin.messages import render_messages
        render_messages()
    elif st.session_state.current_page == "profile":
        from pages.admin.profile import render_profile
        render_profile()

def render_dashboard():
    """Render admin dashboard homepage."""
    render_page_title("Admin Dashboard", "Overview of system statistics", "🏠")
    
    # Get data for statistics
    companies = get_companies()
    
    # Initialize counts
    total_companies = len(companies)
    active_companies = sum(1 for company in companies if company[4])  # is_active
    inactive_companies = total_companies - active_companies
    
    total_branches = 0
    total_employees = 0
    
    # Count branches and employees
    for company in companies:
        company_id = company[0]
        branches = get_branches(company_id)
        total_branches += len(branches)
        
        employees = get_employees(company_id=company_id)
        total_employees += len(employees)
    
    # Display statistics
    st.write("### System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        with st.container(border=True):
            st.metric("Total Companies", total_companies)
    
    with col2:
        with st.container(border=True):
            st.metric("Active Companies", active_companies)
    
    with col3:
        with st.container(border=True):
            st.metric("Total Branches", total_branches)
    
    with col4:
        with st.container(border=True):
            st.metric("Total Employees", total_employees)
    
    # Display recent companies
    st.write("### Recent Companies")
    
    if companies:
        with st.container(border=True):
            for i, company in enumerate(companies[:5]):
                company_id = company[0]
                company_name = company[1]
                username = company[2]
                is_active = company[4]
                
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**{company_name}**")
                    st.caption(f"Username: {username}")
                
                with col2:
                    branches = get_branches(company_id)
                    employees = get_employees(company_id=company_id)
                    st.write(f"Branches: {len(branches)}")
                    st.write(f"Employees: {len(employees)}")
                
                with col3:
                    st.markdown(user_status_indicator(is_active), unsafe_allow_html=True)
                
                if i < len(companies[:5]) - 1:
                    st.divider()
    else:
        st.info("No companies found. Create your first company from the Company Management page.")
