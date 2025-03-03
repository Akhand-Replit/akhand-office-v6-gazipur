import streamlit as st
from utils.ui import render_navigation, render_page_title, user_status_indicator, task_status_indicator
from utils.db import get_employees, get_tasks
from utils.auth import check_asst_manager

def render_asst_manager_dashboard():
    """Render assistant manager dashboard."""
    if not check_asst_manager():
        st.error("You don't have permission to access this page.")
        return
    
    # Define navigation items for assistant manager
    navigation_items = [
        {"label": "Dashboard", "page": "dashboard", "icon": "🏠"},
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
    elif st.session_state.current_page == "employee_management":
        from pages.asst_manager.employee_management import render_employee_management
        render_employee_management()
    elif st.session_state.current_page == "task_management":
        from pages.asst_manager.task_management import render_task_management
        render_task_management()
    elif st.session_state.current_page == "reports":
        from pages.asst_manager.reports import render_reports
        render_reports()
    elif st.session_state.current_page == "messages":
        from pages.asst_manager.messages import render_messages
        render_messages()
    elif st.session_state.current_page == "profile":
        from pages.asst_manager.profile import render_profile
        render_profile()

def render_dashboard():
    """Render assistant manager dashboard homepage."""
    render_page_title("Assistant Manager Dashboard", "Overview of your branch activities", "🏠")
    
    # Get data for statistics
    branch_employees = get_employees(branch_id=st.session_state.branch_id)
    
    # Filter out managers and assistant managers (including self)
    general_employees = [e for e in branch_employees if e[4] == "employee"]
    
    # Get tasks assigned to this branch
    branch_tasks = get_tasks(branch_id=st.session_state.branch_id)
    completed_tasks = [t for t in branch_tasks if t[7]]  # is_completed
    pending_tasks = [t for t in branch_tasks if not t[7]]  # is_completed
    
    # Get personal tasks assigned to assistant manager
    asst_manager_tasks = get_tasks(employee_id=st.session_state.user_id)
    asst_manager_completed_tasks = [t for t in asst_manager_tasks if t[7]]  # is_completed
    asst_manager_pending_tasks = [t for t in asst_manager_tasks if not t[7]]  # is_completed
    
    # Display statistics
    st.write("### Branch Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        with st.container(border=True):
            st.metric("General Employees", len(general_employees))
    
    with col2:
        with st.container(border=True):
            st.metric("Branch Tasks", len(branch_tasks))
    
    with col3:
        with st.container(border=True):
            st.metric("Completed Tasks", len(completed_tasks))
    
    with col4:
        with st.container(border=True):
            st.metric("Pending Tasks", len(pending_tasks))
    
    # Display employee information
    st.write("### General Employees")
    
    if general_employees:
        with st.container(border=True):
            for employee in general_employees:
                employee_id = employee[0]
                employee_name = employee[1]
                employee_username = employee[2]
                employee_active = employee[5]
                
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**{employee_name}**")
                    st.caption(f"Username: {employee_username}")
                
                with col2:
                    # Get tasks for this employee
                    employee_tasks = get_tasks(employee_id=employee_id)
                    completed = sum(1 for t in employee_tasks if t[7])
                    
                    st.write(f"Tasks: {completed}/{len(employee_tasks)} completed")
                
                with col3:
                    st.markdown(user_status_indicator(employee_active), unsafe_allow_html=True)
                
                st.divider()
    else:
        st.info("No general employees found in your branch")
    
    # Display personal tasks
    st.write("### Your Tasks")
    
    if asst_manager_tasks:
        with st.container(border=True):
            for task in asst_manager_tasks[:5]:
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
        st.info("No personal tasks found")
