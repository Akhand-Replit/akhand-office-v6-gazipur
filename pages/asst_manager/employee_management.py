import streamlit as st
from utils.ui import render_page_title, user_status_indicator, clean_url
from utils.db import get_employees, create_employee, toggle_employee_status
from utils.auth import check_asst_manager

def render_employee_management():
    """Render employee management page for assistant manager."""
    if not check_asst_manager():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Employee Management", "Create and manage general employees", "👥")
    
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
                
                # Assistant managers can only create general employees
                st.write("Role: General Employee")
            
            submit_button = st.form_submit_button("Create Employee", use_container_width=True)
            
            if submit_button:
                if not employee_name or not username or not password:
                    st.error("Please fill all required fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    profile_pic_url = clean_url(profile_pic) if profile_pic else f"https://ui-avatars.com/api/?name={employee_name}&background=random"
                    
                    # Create employee with role "employee"
                    employee_id = create_employee(
                        employee_name, username, password, profile_pic_url, "employee",
                        st.session_state.company_id, st.session_state.branch_id, "asst_manager", st.session_state.user_id
                    )
                    
                    if employee_id:
                        st.success(f"Employee '{employee_name}' created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create employee")
    
    # List general employees
    st.write("### General Employees")
    
    # Get employees in assistant manager's branch
    branch_employees = get_employees(branch_id=st.session_state.branch_id)
    
    # Filter out managers and assistant managers (including self)
    general_employees = [e for e in branch_employees if e[4] == "employee"]
    
    if general_employees:
        for employee in general_employees:
            employee_id = employee[0]
            employee_name = employee[1]
            employee_username = employee[2]
            employee_pic = employee[3]
            employee_active = employee[5]
            
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
                    st.write("Role: General Employee")
                
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
    else:
        st.info("No general employees found in your branch")
