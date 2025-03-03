import streamlit as st
from utils.ui import render_page_title, render_message_card
from utils.db import get_employees, send_message, get_messages, delete_message
from utils.auth import check_manager

def render_messages():
    """Render messages page for manager."""
    if not check_manager():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Messages", "Send and view messages", "✉️")
    
    # Initialize state for message deletion
    if "delete_message_id" not in st.session_state:
        st.session_state.delete_message_id = None
    
    # Process message deletion
    if st.session_state.delete_message_id:
        if delete_message(st.session_state.delete_message_id, "manager", st.session_state.user_id):
            st.success("Message deleted successfully!")
        else:
            st.error("Failed to delete message")
        
        st.session_state.delete_message_id = None
        st.rerun()
    
    # Get branch employees for messaging
    branch_employees = get_employees(branch_id=st.session_state.branch_id)
    
    # Filter out the manager (self)
    branch_employees = [e for e in branch_employees if e[0] != st.session_state.user_id]
    
    # Only active employees can receive messages
    active_employees = [(employee[0], f"{employee[1]} ({employee[4].capitalize()})") for employee in branch_employees if employee[5]]
    
    # Tabs for different message types
    tab1, tab2 = st.tabs(["Company Messages", "Employee Messages"])
    
    # Company Messages Tab
    with tab1:
        st.write("### Messages from Company")
        
        # Get messages from company
        company_messages = get_messages(receiver_type="employee", receiver_id=st.session_state.user_id, sender_type="company")
        
        if company_messages:
            for message in company_messages:
                render_message_card(
                    message=message,
                    sender_info="Company",
                    receiver_info="You (Manager)",
                    can_delete=False
                )
            
            # Reply to company form
            with st.container(border=True):
                st.write("### Reply to Company")
                
                with st.form("reply_company_form"):
                    message_text = st.text_area("Message", placeholder="Type your reply to company here...")
                    attachment_link = st.text_input("Attachment Link (Optional)", placeholder="Enter URL for any attachment")
                    
                    submit_button = st.form_submit_button("Send Reply", use_container_width=True)
                    
                    if submit_button:
                        if not message_text:
                            st.error("Please enter a message")
                        else:
                            message_id = send_message("manager", st.session_state.user_id, "company", st.session_state.company_id, message_text, attachment_link)
                            
                            if message_id:
                                st.success("Reply sent to Company successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to send reply")
        else:
            st.info("No messages from Company found")
    
    # Employee Messages Tab
    with tab2:
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
                
                employee_message = st.text_area("Message", placeholder="Type your message to employee here...")
                employee_attachment = st.text_input("Attachment Link (Optional)", placeholder="Enter URL for any attachment")
                
                submit_employee = st.form_submit_button("Send to Employee", use_container_width=True)
                
                if submit_employee:
                    if not employee:
                        st.error("Please select an employee")
                    elif not employee_message:
                        st.error("Please enter a message")
                    else:
                        employee_id, employee_name = employee
                        
                        message_id = send_message("manager", st.session_state.user_id, "employee", employee_id, employee_message, employee_attachment)
                        
                        if message_id:
                            st.success(f"Message sent to {employee_name} successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to send message")
        
        with col2:
            st.write("### Message History")
            
            # Get sent messages to employees
            sent_messages = get_messages(sender_type="manager", sender_id=st.session_state.user_id)
            
            # Get received messages from employees
            received_messages = get_messages(receiver_type="manager", receiver_id=st.session_state.user_id, sender_type="employee")
            
            if sent_messages or received_messages:
                # Combine and sort by date
                all_messages = sorted(sent_messages + received_messages, key=lambda x: x[8], reverse=True)
                
                for message in all_messages[:10]:  # Show only latest 10 messages
                    sender_type = message[1]  # sender_type
                    sender_id = message[2]  # sender_id
                    receiver_type = message[3]  # receiver_type
                    receiver_id = message[4]  # receiver_id
                    
                    if sender_type == "manager" and sender_id == st.session_state.user_id:
                        # Sent by manager (self)
                        employee_id = receiver_id
                        employee_name = next((e[1] for e in branch_employees if e[0] == employee_id), f"Employee {employee_id}")
                        
                        render_message_card(
                            message=message,
                            sender_info="You (Manager)",
                            receiver_info=employee_name,
                            can_delete=True
                        )
                    else:
                        # Received from employee
                        employee_id = sender_id
                        employee_name = next((e[1] for e in branch_employees if e[0] == employee_id), f"Employee {employee_id}")
                        
                        render_message_card(
                            message=message,
                            sender_info=employee_name,
                            receiver_info="You (Manager)",
                            can_delete=False
                        )
            else:
                st.info("No messages found")
