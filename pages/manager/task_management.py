import streamlit as st
from utils.ui import render_page_title, task_status_indicator
from utils.db import get_employees, create_task, get_tasks, complete_task, manager_complete_task
from utils.auth import check_manager

def render_task_management():
    """Render task management page for manager."""
    if not check_manager():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Task Management", "Create and manage tasks", "📋")
    
    # Get branch employees for task assignment
    branch_employees = get_employees(branch_id=st.session_state.branch_id)
    
    # Filter out the manager (self)
    branch_employees = [e for e in branch_employees if e[0] != st.session_state.user_id]
    
    # Only active employees can be assigned tasks
    active_employees = [(employee[0], f"{employee[1]} ({employee[4].capitalize()})") for employee in branch_employees if employee[5]]
    
    # Create task form
    st.write("### Create New Task")
    
    with st.container(border=True):
        with st.form("create_task_form"):
            task_title = st.text_input("Task Title", placeholder="Enter task title")
            task_description = st.text_area("Task Description", placeholder="Enter task description")
            
            assign_to = st.radio("Assign To", ["Branch", "Employee"])
            
            if assign_to == "Branch":
                # Task assigned to entire branch
                st.write("This task will be assigned to all employees in your branch.")
                assigned_to = "branch"
                assigned_id = st.session_state.branch_id
            else:  # Employee
                employee = st.selectbox(
                    "Select Employee",
                    options=active_employees,
                    format_func=lambda x: x[1],
                    index=0 if active_employees else None
                )
                assigned_to = "employee"
                assigned_id = employee[0] if employee else None
            
            submit_button = st.form_submit_button("Create Task", use_container_width=True)
            
            if submit_button:
                if not task_title or not task_description:
                    st.error("Please fill all required fields")
                elif assigned_to == "employee" and not assigned_id:
                    st.error("Please select an employee")
                else:
                    task_id = create_task(
                        task_title, task_description, assigned_to, assigned_id, "manager", st.session_state.user_id
                    )
                    
                    if task_id:
                        st.success(f"Task '{task_title}' created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create task")
    
    # View and manage tasks
    st.write("### Task Management")
    
    tab1, tab2, tab3 = st.tabs(["Branch Tasks", "Employee Tasks", "Your Tasks"])
    
    # Branch Tasks Tab
    with tab1:
        branch_tasks = get_tasks(assigned_to="branch", assigned_id=st.session_state.branch_id)
        
        if branch_tasks:
            for task in branch_tasks:
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
                            if assigned_by_id == st.session_state.user_id:
                                st.caption("Assigned by: You")
                            else:
                                st.caption("Assigned by: Another Manager")
                        elif assigned_by == "asst_manager":
                            st.caption("Assigned by: Assistant Manager")
                    
                    with col2:
                        st.markdown(task_status_indicator(is_completed), unsafe_allow_html=True)
                        
                        # Check employee completion status
                        employee_tasks = []
                        for employee in branch_employees:
                            employee_id = employee[0]
                            employee_task = next((t for t in get_tasks(employee_id=employee_id) if t[0] == task_id), None)
                            if employee_task:
                                employee_tasks.append(employee_task)
                        
                        completed_count = sum(1 for t in employee_tasks if t[7])
                        total_count = len(employee_tasks)
                        
                        if not is_completed:
                            st.progress(completed_count / total_count if total_count > 0 else 0)
                            st.write(f"{completed_count}/{total_count} completed")
                            
                            # Manager can mark task as completed for whole branch
                            if st.button("Mark as Completed", key=f"complete_branch_{task_id}"):
                                if manager_complete_task(task_id, st.session_state.branch_id):
                                    st.success("Task marked as completed for all employees!")
                                    st.rerun()
                                else:
                                    st.error("Failed to complete task")
        else:
            st.info("No branch tasks found")
    
    # Employee Tasks Tab
    with tab2:
        # Get all tasks assigned to employees in branch by this manager
        employee_tasks = get_tasks(assigned_by="manager", assigned_by_id=st.session_state.user_id, assigned_to="employee")
        
        if employee_tasks:
            for task in employee_tasks:
                task_id = task[0]
                task_title = task[1]
                task_description = task[2]
                assigned_id = task[4]
                is_completed = task[7]
                
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"### {task_title}")
                        st.write(task_description)
                        
                        # Get employee information
                        employee = next((e for e in branch_employees if e[0] == assigned_id), None)
                        if employee:
                            st.write(f"**Assigned to:** {employee[1]} ({employee[4].capitalize()})")
                    
                    with col2:
                        st.markdown(task_status_indicator(is_completed), unsafe_allow_html=True)
        else:
            st.info("No employee tasks found")
    
    # Your Tasks Tab
    with tab3:
        # Get tasks assigned to manager
        manager_tasks = get_tasks(employee_id=st.session_state.user_id)
        
        if manager_tasks:
            for task in manager_tasks:
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
                            if assigned_by_id == st.session_state.user_id:
                                st.caption("Assigned by: You")
                            else:
                                st.caption("Assigned by: Another Manager")
                    
                    with col2:
                        st.markdown(task_status_indicator(is_completed), unsafe_allow_html=True)
                        
                        if not is_completed:
                            if st.button("Mark as Completed", key=f"complete_own_{task_id}"):
                                if complete_task(task_id, st.session_state.user_id):
                                    st.success("Task marked as completed!")
                                    st.rerun()
                                else:
                                    st.error("Failed to complete task")
        else:
            st.info("No tasks assigned to you")
