import streamlit as st
from utils.ui import render_page_title, task_status_indicator
from utils.db import get_branches, get_employees, create_task, get_tasks
from utils.auth import check_company

def render_task_management():
    """Render task management page for company."""
    if not check_company():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Task Management", "Create and manage tasks", "📋")
    
    # Get active branches and employees for forms
    branches = get_branches(st.session_state.company_id)
    active_branches = [(branch[0], branch[1]) for branch in branches if branch[3]]  # id, name, is_active
    
    employees = get_employees(company_id=st.session_state.company_id)
    active_employees = [(employee[0], employee[1], employee[4], employee[6]) for employee in employees if employee[5]]  # id, name, role, branch_name
    
    # Create task form with tabs
    st.write("### Create New Task")
    
    # Create tabs for branch and employee task creation
    branch_tab, employee_tab = st.tabs(["Branch Tasks", "Employee Tasks"])
    
    # Branch Task Tab
    with branch_tab:
        with st.container(border=True):
            with st.form("create_branch_task_form"):
                task_title = st.text_input("Task Title", placeholder="Enter task title", key="branch_title")
                task_description = st.text_area("Task Description", placeholder="Enter task description", key="branch_desc")
                
                branch = st.selectbox(
                    "Select Branch",
                    options=active_branches,
                    format_func=lambda x: x[1],
                    index=0 if active_branches else None,
                    key="branch_select"
                )
                
                submit_branch_button = st.form_submit_button("Create Task", use_container_width=True)
                
                if submit_branch_button:
                    if not task_title or not task_description or not branch:
                        st.error("Please fill all required fields")
                    else:
                        branch_id, branch_name = branch
                        task_id = create_task(
                            task_title, task_description, "branch", branch_id, "company", st.session_state.user_id
                        )
                        
                        if task_id:
                            st.success(f"Task '{task_title}' assigned to branch '{branch_name}' successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to create task")
    
    # Employee Task Tab
    with employee_tab:
        with st.container(border=True):
            with st.form("create_employee_task_form"):
                task_title = st.text_input("Task Title", placeholder="Enter task title", key="employee_title")
                task_description = st.text_area("Task Description", placeholder="Enter task description", key="employee_desc")
                
                # Add branch filter for employees
                filter_branch = st.selectbox(
                    "Filter by Branch",
                    options=[(-1, "All Branches")] + active_branches,
                    format_func=lambda x: x[1],
                    index=0,
                    key="employee_branch_filter"
                )
                
                # Filter employees based on selected branch
                filtered_employees = []
                if filter_branch[0] == -1:  # All branches
                    filtered_employees = [(emp[0], f"{emp[1]} ({emp[2].capitalize()}) - {emp[3]}") for emp in active_employees]
                else:
                    filtered_employees = [(emp[0], f"{emp[1]} ({emp[2].capitalize()}) - {emp[3]}") 
                                         for emp in active_employees if emp[3] == filter_branch[1]]
                
                # Select employee from filtered list
                employee = st.selectbox(
                    "Select Employee",
                    options=filtered_employees,
                    format_func=lambda x: x[1],
                    index=0 if filtered_employees else None,
                    key="employee_select"
                )
                
                submit_employee_button = st.form_submit_button("Create Task", use_container_width=True)
                
                if submit_employee_button:
                    if not task_title or not task_description or not employee:
                        st.error("Please fill all required fields")
                    else:
                        employee_id, employee_name = employee
                        task_id = create_task(
                            task_title, task_description, "employee", employee_id, "company", st.session_state.user_id
                        )
                        
                        if task_id:
                            st.success(f"Task '{task_title}' assigned to {employee_name} successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to create task")
    
    # List tasks
    st.write("### Task List")
    
    # Filtering options
    col1, col2 = st.columns(2)
    
    with col1:
        filter_status = st.selectbox(
            "Filter by Status",
            options=[("all", "All Tasks"), (True, "Completed"), (False, "Pending")],
            format_func=lambda x: x[1],
            index=0
        )
    
    with col2:
        filter_assigned = st.selectbox(
            "Filter by Assignment",
            options=[("all", "All Assignments"), ("branch", "Assigned to Branches"), ("employee", "Assigned to Employees")],
            format_func=lambda x: x[1],
            index=0
        )
    
    # Get tasks based on filters
    if filter_status[0] == "all" and filter_assigned[0] == "all":
        tasks = get_tasks(assigned_by="company", assigned_by_id=st.session_state.user_id)
    elif filter_status[0] == "all":
        tasks = get_tasks(assigned_by="company", assigned_by_id=st.session_state.user_id, assigned_to=filter_assigned[0])
    elif filter_assigned[0] == "all":
        tasks = get_tasks(assigned_by="company", assigned_by_id=st.session_state.user_id, is_completed=filter_status[0])
    else:
        tasks = get_tasks(assigned_by="company", assigned_by_id=st.session_state.user_id, is_completed=filter_status[0], assigned_to=filter_assigned[0])
    
    if tasks:
        for task in tasks:
            task_id = task[0]
            task_title = task[1]
            task_description = task[2]
            task_assigned_to = task[3]
            task_assigned_id = task[4]
            is_completed = task[7]
            created_at = task[8]
            
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"### {task_title}")
                    st.write(task_description)
                    
                    # Get assigned entity name
                    if task_assigned_to == "branch":
                        branch_name = next((branch[1] for branch in branches if branch[0] == task_assigned_id), f"Branch {task_assigned_id}")
                        st.write(f"**Assigned to Branch:** {branch_name}")
                        
                        # Get employees in this branch
                        branch_employees = [e for e in employees if e[6] == branch_name]
                        completed_count = sum(1 for e in branch_employees if any(t[7] for t in get_tasks(employee_id=e[0], assigned_by="company", assigned_by_id=st.session_state.user_id) if t[0] == task_id))
                        st.progress(completed_count / len(branch_employees) if branch_employees else 0)
                        st.write(f"**Progress:** {completed_count}/{len(branch_employees)} employees completed")
                    else:  # employee
                        employee_name = next((employee[1] for employee in employees if employee[0] == task_assigned_id), f"Employee {task_assigned_id}")
                        employee_role = next((employee[4] for employee in employees if employee[0] == task_assigned_id), "")
                        employee_branch = next((employee[6] for employee in employees if employee[0] == task_assigned_id), "")
                        st.write(f"**Assigned to:** {employee_name} ({employee_role.capitalize()}) - {employee_branch}")
                
                with col2:
                    st.markdown(task_status_indicator(is_completed), unsafe_allow_html=True)
                    
                    if st.button("View Details", key=f"view_{task_id}"):
                        st.session_state.view_task_id = task_id
                        st.session_state.view_task_title = task_title
            
            # Show task details if selected
            if "view_task_id" in st.session_state and st.session_state.view_task_id == task_id:
                with st.expander(f"Details for {st.session_state.view_task_title}", expanded=True):
                    st.write("#### Task Details")
                    st.write(f"**Created At:** {created_at}")
                    st.write(f"**Status:** {'Completed' if is_completed else 'Pending'}")
                    
                    if task_assigned_to == "branch":
                        branch_name = next((branch[1] for branch in branches if branch[0] == task_assigned_id), f"Branch {task_assigned_id}")
                        branch_employees = [e for e in employees if e[6] == branch_name]
                        
                        st.write("#### Employee Status")
                        
                        if branch_employees:
                            for employee in branch_employees:
                                employee_id = employee[0]
                                employee_name = employee[1]
                                employee_role = employee[4]
                                
                                # Check if employee has completed this task
                                employee_tasks = get_tasks(employee_id=employee_id)
                                employee_task = next((t for t in employee_tasks if t[0] == task_id), None)
                                
                                employee_completed = employee_task and employee_task[7]
                                
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.write(f"**{employee_name}** ({employee_role.capitalize()})")
                                
                                with col2:
                                    st.markdown(task_status_indicator(employee_completed), unsafe_allow_html=True)
                                
                                st.divider()
                        else:
                            st.info("No employees found in this branch")
    else:
        st.info("No tasks found. Create your first task using the forms above.")
