import streamlit as st
from utils.ui import render_page_title, user_status_indicator
from utils.db import get_branches, create_branch, toggle_branch_status, get_employees
from utils.auth import check_company

def render_branch_management():
    """Render branch management page for company."""
    if not check_company():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Branch Management", "Create and manage branches", "🏛️")
    
    # Create branch form
    st.write("### Create New Branch")
    
    with st.container(border=True):
        with st.form("create_branch_form"):
            branch_name = st.text_input("Branch Name", placeholder="Enter branch name")
            
            submit_button = st.form_submit_button("Create Branch", use_container_width=True)
            
            if submit_button:
                if not branch_name:
                    st.error("Please enter branch name")
                else:
                    branch_id = create_branch(branch_name, st.session_state.company_id)
                    
                    if branch_id:
                        st.success(f"Branch '{branch_name}' created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create branch")
    
    # List branches
    st.write("### Branch List")
    
    branches = get_branches(st.session_state.company_id)
    
    if branches:
        for branch in branches:
            branch_id = branch[0]
            branch_name = branch[1]
            is_main_branch = branch[2]
            is_active = branch[3]
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"### {branch_name}")
                    if is_main_branch:
                        st.caption("Main Branch")
                
                with col2:
                    # Get employees in this branch
                    branch_employees = get_employees(company_id=st.session_state.company_id, branch_id=branch_id)
                    managers = [e for e in branch_employees if e[4] == "manager"]
                    asst_managers = [e for e in branch_employees if e[4] == "asst_manager"]
                    general_employees = [e for e in branch_employees if e[4] == "employee"]
                    
                    st.write(f"**Total Employees:** {len(branch_employees)}")
                    st.write(f"**Managers:** {len(managers)} | **Asst. Managers:** {len(asst_managers)} | **Employees:** {len(general_employees)}")
                
                with col3:
                    st.markdown(user_status_indicator(is_active), unsafe_allow_html=True)
                    
                    if not is_main_branch:  # Can't toggle status of main branch
                        if is_active:
                            st.button("Deactivate", key=f"deactivate_{branch_id}", 
                                     on_click=lambda bid=branch_id: toggle_branch_status(bid, False),
                                     type="secondary")
                        else:
                            st.button("Activate", key=f"activate_{branch_id}", 
                                     on_click=lambda bid=branch_id: toggle_branch_status(bid, True),
                                     type="primary")
                    
                    if st.button("View Details", key=f"view_{branch_id}"):
                        st.session_state.view_branch_id = branch_id
                        st.session_state.view_branch_name = branch_name
            
            # Show branch details if selected
            if "view_branch_id" in st.session_state and st.session_state.view_branch_id == branch_id:
                with st.expander(f"Details for {st.session_state.view_branch_name}", expanded=True):
                    if branch_employees:
                        for employee in branch_employees:
                            employee_id = employee[0]
                            employee_name = employee[1]
                            employee_username = employee[2]
                            employee_pic = employee[3]
                            employee_role = employee[4]
                            employee_active = employee[5]
                            
                            col1, col2, col3 = st.columns([1, 3, 1])
                            
                            with col1:
                                if employee_pic:
                                    st.image(employee_pic, width=60)
                                else:
                                    st.image(f"https://ui-avatars.com/api/?name={employee_name}&background=random", width=60)
                            
                            with col2:
                                st.write(f"**{employee_name}**")
                                st.caption(f"Username: {employee_username}")
                                st.write(f"Role: {employee_role.capitalize()}")
                            
                            with col3:
                                st.markdown(user_status_indicator(employee_active), unsafe_allow_html=True)
                            
                            st.divider()
                    else:
                        st.info("No employees found in this branch")
    else:
        st.info("No branches found. Create your first branch using the form above.")
