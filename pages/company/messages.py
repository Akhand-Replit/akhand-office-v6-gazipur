import streamlit as st
from utils.ui import render_page_title, render_message_card
from utils.db import get_branches, get_employees, send_message, get_messages, delete_message
from utils.auth import check_company

def render_messages():
    """Render messages page for company."""
    if not check_company():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Messages", "Send and view messages", "✉️")
    
    # Initialize state for message deletion
    if "delete_message_id" not in st.session_state:
        st.session_state.delete_message_id = None
    
    # Process message deletion
    if st.session_state.delete_message_id:
        if delete_message(st.session_state.delete_message_id, "company", st.session_state.user_id):
            st.success("Message deleted successfully!")
        else:
            st.error("Failed to delete message")
        
        st.session_state.delete_message_id = None
        st.rerun()
    
    # Get branches and employees for messaging
    branches = get_branches(st.session_state.company_id)
    active_branches = [(branch[0], branch[1]) for branch in branches if branch[3]]
    
    employees = get_employees(company_id=st.session_state.company_id)
    active_employees = [(employee[0], f"{employee[1]} ({employee[4].capitalize()})") for employee in employees if employee[5]]
    
    # Tabs for different message types
    tab1, tab2, tab3 = st.tabs(["Admin Messages", "Branch Messages", "Employee Messages"])
    
    # Admin Messages Tab
    with tab1:
        st.write("### Messages from Admin")
        
        # Get messages from admin
        admin_messages = get_messages(receiver_type="company", receiver_id=st.session_state.user_id)
        
        if admin_messages:
            for message in admin_messages:
                render_message_card(
                    message=message,
                    sender_info="Admin",
                    receiver_info="You (Company)",
                    can_delete=False
                )
            
            # Reply to admin form
            with st.container(border=True):
                st.write("### Reply to Admin")
                
                with st.form("reply_admin_form"):
                    message_text = st.text_area("Message", placeholder="Type your reply to admin here...")
                    attachment_link = st.text_input("Attachment Link (Optional)", placeholder="Enter URL for any attachment")
                    
                    submit_button = st.form_submit_button("Send Reply", use_container_width=True)
                    
                    if submit_button:
                        if not message_text:
                            st.error("Please enter a message")
                        else:
                            # Get admin ID (should be 1 for default admin)
                            admin_id = 1
                            
                            message_id = send_message("company", st.session_state.user_id, "admin", admin_id, message_text, attachment_link)
                            
                            if message_id:
                                st.success("Reply sent to Admin successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to send reply")
        else:
            st.info("No messages from Admin found")
    
    # Branch Messages Tab
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Send Message to Branch")
            
            with st.form("send_branch_form"):
                branch = st.selectbox(
                    "Select Branch",
                    options=active_branches,
                    format_func=lambda x: x[1],
                    index=0 if active_branches else None
                )
                
                branch_message = st.text_area("Message", placeholder="Type your message to branch here...", key="branch_message")
                branch_attachment = st.text_input("Attachment Link (Optional)", placeholder="Enter URL for any attachment", key="branch_attachment")
                
                submit_branch = st.form_submit_button("Send to Branch", use_container_width=True)
                
                if submit_branch:
                    if not branch:
                        st.error("Please select a branch")
                    elif not branch_message:
                        st.error("Please enter a message")
                    else:
                        branch_id, branch_name = branch
                        
                        # Send message to all employees in branch
                        branch_employees = [e for e in employees if e[6] == branch_name and e[5]]  # active employees
                        
                        if branch_employees:
                            for employee in branch_employees:
                                send_message("company", st.session_state.user_id, "employee", employee[0], branch_message, branch_attachment)
                            
                            st.success(f"Message sent to all employees in {branch_name} successfully!")
                            st.rerun()
                        else:
                            st.warning(f"No active employees found in {branch_name}")
        
        with col2:
            st.write("### Branch Message History")
            
            # Get sent messages to branches (actually to employees in branches)
            branch_messages = []
            for branch in branches:
                branch_id = branch[0]
                branch_name = branch[1]
                
                branch_employees = [e for e in employees if e[6] == branch_name]
                
                for employee in branch_employees:
                    employee_id = employee[0]
                    messages = get_messages(sender_type="company", sender_id=st.session_state.user_id, receiver_type="employee", receiver_id=employee_id)
                    
                    for message in messages:
                        # Add to list if not already added (avoid duplicates)
                        if not any(msg[0] == message[0] for msg in branch_messages):
                            branch_messages.append(message)
            
            if branch_messages:
                for message in branch_messages[:5]:  # Show only latest 5 messages
                    render_message_card(
                        message=message,
                        sender_info="You (Company)",
                        receiver_info="Branch Employees",
                        can_delete=True
                    )
            else:
                st.info("No branch messages found")
    
    # Employee Messages Tab
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Send Message to Employee")
            
            with st.form("send_employee_form"):
                employee = st.selectbox(
                    "Select Employee",
                    options=active_employees,
                    format_func=lambda x: x[1],
                    index=0 if active_employees else None
                )
                
                employee_message = st.text_area("Message", placeholder="Type your message to employee here...", key="employee_message")
                employee_attachment = st.text_input("Attachment Link (Optional)", placeholder="Enter URL for any attachment", key="employee_attachment")
                
                submit_employee = st.form_submit_button("Send to Employee", use_container_width=True)
                
                if submit_employee:
                    if not employee:
                        st.error("Please select an employee")
                    elif not employee_message:
                        st.error("Please enter a message")
                    else:
                        employee_id, employee_name = employee
                        
                        message_id = send_message("company", st.session_state.user_id, "employee", employee_id, employee_message, employee_attachment)
                        
                        if message_id:
                            st.success(f"Message sent to {employee_name} successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to send message")
        
        with col2:
            st.write("### Employee Message History")
            
            # Get sent messages to individual employees
            employee_messages = []
            for employee in employees:
                employee_id = employee[0]
                
                messages = get_messages(sender_type="company", sender_id=st.session_state.user_id, receiver_type="employee", receiver_id=employee_id)
                
                for message in messages:
                    # Only add direct messages, not branch messages
                    if not any(msg[0] == message[0] for msg in employee_messages):
                        employee_messages.append(message)
            
            if employee_messages:
                for message in employee_messages[:5]:  # Show only latest 5 messages
                    employee_id = message[4]  # receiver_id
                    employee_name = next((employee[1] for employee in employees if employee[0] == employee_id), f"Employee {employee_id}")
                    
                    render_message_card(
                        message=message,
                        sender_info="You (Company)",
                        receiver_info=f"{employee_name}",
                        can_delete=True
                    )
            else:
                st.info("No direct employee messages found")
