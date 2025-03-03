import streamlit as st
from utils.ui import render_navigation, render_page_title, user_status_indicator, task_status_indicator
from utils.db import get_branches, get_employees, get_tasks
from utils.auth import check_company

def render_company_dashboard():
    """Render company dashboard."""
    if not check_company():
        st.error("You don't have permission to access this page.")
        return
    
    # Define navigation items for company
    navigation_items = [
        {"label": "Dashboard", "page": "dashboard", "icon": "🏠"},
        {"label": "Branch Management", "page": "branch_management", "icon": "🏛️"},
        {"label": "Employee Management", "page": "employee_management", "icon": "👥"},
        {"label": "Task Management", "page": "task_management", "icon": "📋"},
        {"label": "Reports", "page": "reports", "icon": "📊"},
        {"label": "Messages", "page": "messages", "icon": "✉️"},
        {"label": "Profile", "page": "profile", "icon": "👤"}
    ]
    
    # Render navigation
    render_navigation(st.session_state.current_page, navigation_items)
    
    # Render appropriate page based on current_page
    if st.session_state.current_page == "dashboard":
        render_dashboard()
    elif st.session_state.current_page == "branch_management":
        from pages.company.branch_management import render_branch_management
        render_branch_management()
    elif st.session_state.current_page == "employee_management":
        from pages.company.employee_management import render_employee_management
        render_employee_management()
    elif st.session_state.current_page == "task_management":
        from pages.company.task_management import render_task_management
        render_task_management()
    elif st.session_state.current_page == "reports":
        from pages.company.reports import render_reports
        render_reports()
    elif st.session_state.current_page == "messages":
        from pages.company.messages import render_messages
        render_messages()
    elif st.session_state.current_page == "profile":
        from pages.company.profile import render_profile
        render_profile()

def render_dashboard():
    """Render company dashboard homepage."""
    render_page_title("Company Dashboard", "Overview of your company", "🏠")
    
    # Get data for statistics
    branches = get_branches(st.session_state.company_id)
    
    employees = get_employees(company_id=st.session_state.company_id)
    managers = [e for e in employees if e[4] == "manager"]
    asst_managers = [e for e in employees if e[4] == "asst_manager"]
    general_employees = [e for e in employees if e[4] == "employee"]
    
    tasks = get_tasks(company_id=st.session_state.company_id)
    completed_tasks = [t for t in tasks if t[7]]  # is_completed
    pending_tasks = [t for t in tasks if not t[7]]  # is_completed
    
    # Display statistics
    st.write("### Company Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        with st.container(border=True):
            st.metric("Total Branches", len(branches))
    
    with col2:
        with st.container(border=True):
            st.metric("Total Employees", len(employees))
    
    with col3:
        with st.container(border=True):
            st.metric("Completed Tasks", len(completed_tasks))
    
    with col4:
        with st.container(border=True):
            st.metric("Pending Tasks", len(pending_tasks))
    
    # Display branch information
    st.write("### Branch Information")
    
    if branches:
        col1, col2 = st.columns(2)
        
        with col1:
            with st.container(border=True):
                st.write("#### Branch List")
                for branch in branches:
                    branch_id = branch[0]
                    branch_name = branch[1]
                    is_main_branch = branch[2]
                    is_active = branch[3]
                    
                    st.write(f"**{branch_name}**" + (" (Main Branch)" if is_main_branch else ""))
                    st.markdown(user_status_indicator(is_active), unsafe_allow_html=True)
                    
                    # Count employees in this branch
                    branch_employees = [e for e in employees if e[6] == branch_name]
                    st.write(f"Employees: {len(branch_employees)}")
                    
                    st.divider()
        
        with col2:
            with st.container(border=True):
                st.write("#### Employee Distribution")
                st.write(f"**Managers:** {len(managers)}")
                st.write(f"**Assistant Managers:** {len(asst_managers)}")
                st.write(f"**General Employees:** {len(general_employees)}")
                
                # Create a simple bar chart
                st.bar_chart({
                    "Role": ["Managers", "Assistant Managers", "General Employees"],
                    "Count": [len(managers), len(asst_managers), len(general_employees)]
                })
    else:
        st.info("No branches found. Create your first branch from the Branch Management page.")
    
    # Display recent tasks
    st.write("### Recent Tasks")
    
    if tasks:
        with st.container(border=True):
            for task in tasks[:5]:
                task_id = task[0]
                task_title = task[1]
                task_description = task[2]
                is_completed = task[7]
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{task_title}**")
                    st.caption(task_description[:100] + "..." if len(task_description) > 100 else task_description)
                
                with col2:
                    st.markdown(task_status_indicator(is_completed), unsafe_allow_html=True)
                
                st.divider()
    else:
        st.info("No tasks found. Create your first task from the Task Management page.")
