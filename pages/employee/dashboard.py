import streamlit as st
from utils.ui import render_navigation, render_page_title, task_status_indicator
from utils.db import get_tasks, get_reports
from utils.auth import check_employee

def render_employee_dashboard():
    """Render employee dashboard."""
    if not check_employee():
        st.error("You don't have permission to access this page.")
        return
    
    # Define navigation items for employee
    navigation_items = [
        {"label": "Dashboard", "page": "dashboard", "icon": "🏠"},
        {"label": "Tasks", "page": "tasks", "icon": "📋"},
        {"label": "Reports", "page": "reports", "icon": "📊"},
        {"label": "Messages", "page": "messages", "icon": "✉️"},
        {"label": "Profile", "page": "profile", "icon": "👤"}
    ]
    
    # Render navigation
    render_navigation(st.session_state.current_page, navigation_items)
    
    # Render appropriate page based on current_page
    if st.session_state.current_page == "dashboard":
        render_dashboard()
    elif st.session_state.current_page == "tasks":
        from pages.employee.tasks import render_tasks
        render_tasks()
    elif st.session_state.current_page == "reports":
        from pages.employee.reports import render_reports
        render_reports()
    elif st.session_state.current_page == "messages":
        from pages.employee.messages import render_messages
        render_messages()
    elif st.session_state.current_page == "profile":
        from pages.employee.profile import render_profile
        render_profile()

def render_dashboard():
    """Render employee dashboard homepage."""
    render_page_title("Employee Dashboard", "Your activity overview", "🏠")
    
    # Get tasks assigned to employee
    employee_tasks = get_tasks(employee_id=st.session_state.user_id)
    completed_tasks = [t for t in employee_tasks if t[7]]  # is_completed
    pending_tasks = [t for t in employee_tasks if not t[7]]  # is_completed
    
    # Get reports submitted by employee
    employee_reports = get_reports(employee_id=st.session_state.user_id)
    
    # Display statistics
    st.write("### Your Activity Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        with st.container(border=True):
            st.metric("Total Tasks", len(employee_tasks))
    
    with col2:
        with st.container(border=True):
            st.metric("Completed Tasks", len(completed_tasks))
    
    with col3:
        with st.container(border=True):
            st.metric("Pending Tasks", len(pending_tasks))
    
    with col4:
        with st.container(border=True):
            st.metric("Reports Submitted", len(employee_reports))
    
    # Display pending tasks
    st.write("### Pending Tasks")
    
    if pending_tasks:
        with st.container(border=True):
            for task in pending_tasks[:5]:  # Show top 5 pending tasks
                task_id = task[0]
                task_title = task[1]
                task_description = task[2]
                assigned_by = task[5]
                assigned_by_id = task[6]
                created_at = task[8]
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{task_title}**")
                    st.caption(task_description[:100] + "..." if len(task_description) > 100 else task_description)
                    
                    # Show assigned by information
                    if assigned_by == "company":
                        st.caption("Assigned by: Company")
                    elif assigned_by == "manager":
                        st.caption("Assigned by: Branch Manager")
                    elif assigned_by == "asst_manager":
                        st.caption("Assigned by: Assistant Manager")
                
                with col2:
                    st.write("Status:")
                    st.markdown(task_status_indicator(False), unsafe_allow_html=True)
                
                st.divider()
    else:
        st.info("No pending tasks found. Great job!")
    
    # Display recent reports
    st.write("### Recent Reports")
    
    if employee_reports:
        with st.container(border=True):
            for report in employee_reports[:3]:  # Show top 3 recent reports
                report_id = report[0]
                report_date = report[4]
                content = report[5]
                
                st.write(f"**Report Date:** {report_date}")
                st.caption(content[:150] + "..." if len(content) > 150 else content)
                
                st.divider()
    else:
        st.info("No reports found. Submit your first report from the Reports page.")
