import streamlit as st
from utils.ui import render_page_title, task_status_indicator
from utils.db import get_tasks, complete_task
from utils.auth import check_employee

def render_tasks():
    """Render tasks page for employee."""
    if not check_employee():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Tasks", "View and complete your assigned tasks", "📋")
    
    # Get tasks assigned to employee
    employee_tasks = get_tasks(employee_id=st.session_state.user_id)
    
    # Filter tasks by status
    tab1, tab2 = st.tabs(["Pending Tasks", "Completed Tasks"])
    
    # Pending Tasks Tab
    with tab1:
        pending_tasks = [t for t in employee_tasks if not t[7]]  # is_completed
        
        if pending_tasks:
            for task in pending_tasks:
                task_id = task[0]
                task_title = task[1]
                task_description = task[2]
                assigned_by = task[5]
                assigned_by_id = task[6]
                created_at = task[8]
                
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"### {task_title}")
                        st.write(task_description)
                        
                        # Show assigned by information
                        if assigned_by == "company":
                            st.caption("Assigned by: Company")
                        elif assigned_by == "manager":
                            st.caption("Assigned by: Branch Manager")
                        elif assigned_by == "asst_manager":
                            st.caption("Assigned by: Assistant Manager")
                        
                        st.caption(f"Assigned on: {created_at}")
                    
                    with col2:
                        st.write("Status:")
                        st.markdown(task_status_indicator(False), unsafe_allow_html=True)
                        
                        if st.button("Mark as Completed", key=f"complete_{task_id}", type="primary"):
                            if complete_task(task_id, st.session_state.user_id):
                                st.success("Task marked as completed!")
                                st.rerun()
                            else:
                                st.error("Failed to complete task")
        else:
            st.info("No pending tasks found. Great job!")
    
    # Completed Tasks Tab
    with tab2:
        completed_tasks = [t for t in employee_tasks if t[7]]  # is_completed
        
        if completed_tasks:
            for task in completed_tasks:
                task_id = task[0]
                task_title = task[1]
                task_description = task[2]
                assigned_by = task[5]
                assigned_by_id = task[6]
                created_at = task[8]
                
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"### {task_title}")
                        st.write(task_description)
                        
                        # Show assigned by information
                        if assigned_by == "company":
                            st.caption("Assigned by: Company")
                        elif assigned_by == "manager":
                            st.caption("Assigned by: Branch Manager")
                        elif assigned_by == "asst_manager":
                            st.caption("Assigned by: Assistant Manager")
                        
                        st.caption(f"Assigned on: {created_at}")
                    
                    with col2:
                        st.write("Status:")
                        st.markdown(task_status_indicator(True), unsafe_allow_html=True)
        else:
            st.info("No completed tasks found yet.")
