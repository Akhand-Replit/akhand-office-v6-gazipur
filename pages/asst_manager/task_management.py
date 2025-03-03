import streamlit as st
from utils.ui import render_page_title, task_status_indicator
from utils.db import get_employees, create_task, get_tasks, complete_task
from utils.auth import check_asst_manager

def render_task_management():
    """Render task management page for assistant manager."""
    if not check_asst_manager():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Task Management", "Create and manage tasks", "📋")
    
    # Get branch employees for task assignment
    branch_employees = get_employees(branch_id=st.session_state.branch_id)
    
    # Filter out managers and assistant managers (including self)
    general_employees = [e for e in branch_employees if e[4] == "employee"]
    
    # Only active employees can be assigned tasks
    active_employees = [(employee[0], employee[1]) for employee in general_employees if employee[5]]
    
    # Create task form
    st.write("### Create New Task")
    
    with st.container(border=True):
        with st.form("create_task_form"):
            task_title = st.text_input("Task Title", placeholder="Enter task title")
            task_description = st.text_area("Task Description", placeholder="Enter task description")
            
            employee = st.selectbox(
                "Assign to Employee",
                options=active_employees,
                format_func=lambda x: x[1],
                index=0 if active_employees else None
            )
            
            submit_button = st.form_submit_button("Create Task", use_container_width=True)
            
            if submit_button:
                if not task_title or not task_description:
                    st.error("Please fill all required fields")
                elif not employee:
                    st.error("Please select an employee")
                else:
                    employee_id, employee_name = employee
                    
                    task_id = create_task(
                        task_title, task_description, "employee", employee_id, "asst_manager", st.session_state.user_id
                    )
                    
                    if task_id:
                        st.success(f"Task '{task_title}' assigned to {employee_name} successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create task")
    
    # View and manage tasks
    st.write("### Task Management")
    
    tab1, tab2 = st.tabs(["Assigned Tasks", "Your Tasks"])
    
    # Assigned Tasks Tab
    with tab1:
        # Get tasks assigned by this assistant manager
        assigned_tasks = get_tasks(assigned_by="asst_manager", assigned_by_id=st.session_state.user_id)
        
        if assigned_tasks:
            for task in assigned_tasks:
                task_id = task[0]
                task_title = task[1]
                task_description = task[2]
                assigned_to = task[3]
                assigned_id = task[4]
                is_completed = task[7]
                
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"### {task_title}")
                        st.write(task_description)
                        
                        # Get employee information
                        if assigned_to == "employee":
                            employee = next((e for e in general_employees if e[0] == assigned_id), None)
                            if employee:
                                st.write(f"**Assigned to:** {employee[1]}")
                    
                    with col2:
                        st.markdown(task_status_indicator(is_completed), unsafe_allow_html=True)
        else:
            st.info("No assigned tasks found")
    
    # Your Tasks Tab
    with tab2:
        # Get tasks assigned to assistant manager
        asst_manager_tasks = get_tasks(employee_id=st.session_state.user_id)
        
        if asst_manager_tasks:
            for task in asst_manager_tasks:
                task_id = task[0]
                task_title = task[1]
                task_description = task[2]
                assigned_by = task[5]
                assigned_by_id = task[6]
                is_completed = task[7]
                
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"### {task_title}")
                        st.write(task_description)
                        
                        # Get assigner information
                        if assigned_by == "company":
                            st.caption("Assigned by: Company")
                        elif assigned_by == "manager":
                            st.caption("Assigned by: Branch Manager")
                    
                    with col2:
                        st.markdown(task_status_indicator(is_completed), unsafe_allow_html=True)
                        
                        if not is_completed:
                            if st.button("Mark as Completed", key=f"complete_{task_id}"):
                                if complete_task(task_id, st.session_state.user_id):
                                    st.success("Task marked as completed!")
                                    st.rerun()
                                else:
                                    st.error("Failed to complete task")
        else:
            st.info("No tasks assigned to you")
