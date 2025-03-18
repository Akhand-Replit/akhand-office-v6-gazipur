import streamlit as st
from utils.ui import render_page_title, task_status_indicator
from utils.db import get_tasks, complete_task, get_connection
from utils.auth import check_employee

def render_tasks():
    """Render tasks page for employee."""
    if not check_employee():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Tasks", "View and complete your assigned tasks", "📋")
    
    # Get tasks assigned to employee
    employee_tasks = get_tasks(employee_id=st.session_state.user_id)
    
    # Get the employee's personal completion status for each task
    conn = get_connection()
    task_completion_status = {}
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
            SELECT task_id, is_completed FROM task_completion
            WHERE employee_id = %s
            """, (st.session_state.user_id,))
            
            completions = cur.fetchall()
            for completion in completions:
                task_completion_status[completion[0]] = completion[1]
            
            cur.close()
        except Exception as e:
            st.error(f"Failed to get task completion status: {e}")
        finally:
            conn.close()
    
    # Check for task completion action
    if "complete_task_id" in st.session_state and st.session_state.complete_task_id:
        task_id = st.session_state.complete_task_id
        if complete_task(task_id, st.session_state.user_id):
            st.success("Task marked as completed!")
            # Clear the task ID and refresh the page data
            st.session_state.complete_task_id = None
            # Refresh tasks list after completion
            employee_tasks = get_tasks(employee_id=st.session_state.user_id)
            # Refresh completion status
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("""
                    SELECT task_id, is_completed FROM task_completion
                    WHERE employee_id = %s
                    """, (st.session_state.user_id,))
                    
                    completions = cur.fetchall()
                    task_completion_status = {}
                    for completion in completions:
                        task_completion_status[completion[0]] = completion[1]
                    
                    cur.close()
                except Exception as e:
                    st.error(f"Failed to refresh task completion status: {e}")
                finally:
                    conn.close()
        else:
            st.error("Failed to complete task")
            st.session_state.complete_task_id = None
    
    # Filter tasks by status
    tab1, tab2 = st.tabs(["Pending Tasks", "Completed Tasks"])
    
    # Pending Tasks Tab
    with tab1:
        # Tasks that the employee hasn't personally completed
        pending_tasks = [t for t in employee_tasks if not task_completion_status.get(t[0], False)]
        
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
                        
                        # Use a button to mark task as complete
                        if st.button("Mark as Completed", key=f"complete_{task_id}", type="primary"):
                            st.session_state.complete_task_id = task_id
                            st.rerun()
        else:
            st.info("No pending tasks found. Great job!")
    
    # Completed Tasks Tab
    with tab2:
        # Tasks that the employee has personally completed
        completed_tasks = []
        for task in employee_tasks:
            task_id = task[0]
            if task_completion_status.get(task_id, False):
                completed_tasks.append(task)
        
        if completed_tasks:
            for task in completed_tasks:
                task_id = task[0]
                task_title = task[1]
                task_description = task[2]
                assigned_to = task[3]
                assigned_by = task[5]
                assigned_by_id = task[6]
                is_completed = task[7]  # Overall task completion status
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
                        
                        # For branch tasks that are not fully completed
                        if assigned_to == "branch" and not is_completed:
                            st.info("You've completed this task, but it's waiting for other employees to complete it as well.")
                    
                    with col2:
                        st.write("Your Status:")
                        st.markdown(task_status_indicator(True), unsafe_allow_html=True)
                        
                        if assigned_to == "branch" and not is_completed:
                            st.write("Overall Status:")
                            st.markdown(task_status_indicator(False), unsafe_allow_html=True)
        else:
            st.info("No completed tasks found yet.")
