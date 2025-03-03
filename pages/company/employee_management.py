import streamlit as st
from utils.ui import render_page_title, user_status_indicator, clean_url
from utils.db import get_branches, get_employees, create_employee, toggle_employee_status, update_employee_role, update_employee_branch
from utils.auth import check_company

def render_employee_management():
    """Render employee management page for company."""
    if not check_company():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Employee Management", "Create and manage employees", "👥")
    
    # Get active branches for forms
    branches = get_branches(st.session_state.company_id)
    active_branches = [(branch[0], branch[1]) for branch in branches if branch[3]]  # id, name, is_active
    
    # Create employee form
    st.write("### Create New Employee")
    
    with st.container(border=True):
        with st.form("create_employee_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                employee_name = st.text_input("Employee Name", placeholder="Enter employee name")
                username = st.text_input("Username", placeholder="Enter username for login")
                profile_pic = st.text_input("Profile Picture URL", placeholder="Enter profile picture URL")
            
            with col2:
                password = st.text_input("Password", type="password", placeholder="Enter password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
                
                role = st.selectbox("Role", ["manager", "asst_manager", "employee"])
                
                branch = st.selectbox(
                    "Branch",
                    options=active_branches,
                    format_func=lambda x: x[1],
                    index=0 if active_branches else None
                )
            
            submit_button = st.form_submit_button("Create Employee", use_container_width=True)
            
            if submit_button:
                if not employee_name or not username or not password or not branch:
                    st.error("Please fill all required fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    branch_id, branch_name = branch
                    profile_pic_url = clean_url(profile_pic) if profile_pic else f"https://ui-avatars.com/api/?name={employee_name}&background=random"
                    
                    employee_id = create_employee(
                        employee_name, username, password, profile_pic_url, role,
                        st.session_state.company_id, branch_id, "company", st.session_state.user_id
                    )
                    
                    if employee_id:
                        st.success(f"Employee '{employee_name}' created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create employee")
    
    # List employees
    st.write("### Employee List")
    
    # Filtering options
    col1, col2 = st.columns(2)
    
    with col1:
        filter_branch = st.selectbox(
            "Filter by Branch",
            options=[("all", "All Branches")] + active_branches,
            format_func=lambda x: x[1],
            index=0
        )
    
    with col2:
        filter_role = st.selectbox(
            "Filter by Role",
            options=[("all", "All Roles"), ("manager", "Managers"), ("asst_manager", "Assistant Managers"), ("employee", "General Employees")],
            format_func=lambda x: x[1],
            index=0
        )
    
    # Get employees based on filters
    if filter_branch[0] == "all" and filter_role[0] == "all":
        employees = get_employees(company_id=st.session_state.company_id)
    elif filter_branch[0] == "all":
        employees = get_employees(company_id=st.session_state.company_id, role=filter_role[0])
    elif filter_role[0] == "all":
        employees = get_employees(company_id=st.session_state.company_id, branch_id=filter_branch[0])
    else:
        employees = get_employees(company_id=st.session_state.company_id, branch_id=filter_branch[0], role=filter_role[0])
    
    if employees:
        for employee in employees:
            employee_id = employee[0]
            employee_name = employee[1]
            employee_username = employee[2]
            employee_pic = employee[3]
            employee_role = employee[4]
            employee_active = employee[5]
            branch_name = employee[6]
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    if employee_pic:
                        st.image(employee_pic, width=80)
                    else:
                        st.image(f"https://ui-avatars.com/api/?name={employee_name}&background=random", width=80)
                
                with col2:
                    st.write(f"### {employee_name}")
                    st.caption(f"Username: {employee_username}")
                    st.write(f"Role: {employee_role.capitalize()}")
                    st.write(f"Branch: {branch_name}")
                
                with col3:
                    st.markdown(user_status_indicator(employee_active), unsafe_allow_html=True)
                    
                    if employee_active:
                        st.button("Deactivate", key=f"deactivate_{employee_id}", 
                                 on_click=lambda eid=employee_id: toggle_employee_status(eid, False),
                                 type="secondary")
                    else:
                        st.button("Activate", key=f"activate_{employee_id}", 
                                 on_click=lambda eid=employee_id: toggle_employee_status(eid, True),
                                 type="primary")
                    
                    if st.button("Edit", key=f"edit_{employee_id}"):
                        st.session_state.edit_employee_id = employee_id
                        st.session_state.edit_employee_name = employee_name
                        st.session_state.edit_employee_role = employee_role
                        st.session_state.edit_employee_branch = next((branch for branch in branches if branch[1] == branch_name), None)
            
            # Show employee edit form if selected
            if "edit_employee_id" in st.session_state and st.session_state.edit_employee_id == employee_id:
                with st.expander(f"Edit {st.session_state.edit_employee_name}", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_role = st.selectbox(
                            "Update Role",
                            options=["manager", "asst_manager", "employee"],
                            index=["manager", "asst_manager", "employee"].index(st.session_state.edit_employee_role),
                            key=f"role_{employee_id}"
                        )
                        
                        if st.button("Update Role", key=f"update_role_{employee_id}"):
                            if update_employee_role(employee_id, new_role):
                                st.success(f"Role updated to {new_role.capitalize()} successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to update role")
                    
                    with col2:
                        new_branch = st.selectbox(
                            "Transfer to Branch",
                            options=active_branches,
                            format_func=lambda x: x[1],
                            index=next((i for i, branch in enumerate(active_branches) if branch[1] == branch_name), 0),
                            key=f"branch_{employee_id}"
                        )
                        
                        if st.button("Update Branch", key=f"update_branch_{employee_id}"):
                            if update_employee_branch(employee_id, new_branch[0]):
                                st.success(f"Employee transferred to {new_branch[1]} successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to update branch")
    else:
        st.info("No employees found. Create your first employee using the form above.")
