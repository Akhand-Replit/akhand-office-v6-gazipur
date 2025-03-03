import streamlit as st
from utils.ui import render_page_title, render_message_card
from utils.db import get_employees, send_message, get_messages, delete_message
from utils.auth import check_employee

def render_messages():
    """Render messages page for employee."""
    if not check_employee():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Messages", "View and send messages", "✉️")
    
    # Initialize state for message deletion
    if "delete_message_id" not in st.session_state:
        st.session_state.delete_message_id = None
    
    # Process message deletion
    if st.session_state.delete_message_id:
        if delete_message(st.session_state.delete_message_id, "employee", st.session_state.user_id):
            st.success("Message deleted successfully!")
        else:
            st.error("Failed to delete message")
        
        st.session_state.delete_message_id = None
        st.rerun()
    
    # Get branch employees for messaging
    branch_employees = get_employees(branch_id=st.session_state.branch_id)
    
    # Filter out self
    branch_employees = [e for e in branch_employees if e[0] != st.session_state.user_id]
    
    # Get managers and assistant managers for sending messages
    managers = [e for e in branch_employees if e[4] in ["manager", "asst_manager"]]
    
    # Only active managers can receive messages
    active_managers = [(employee[0], f"{employee[1]} ({employee[4].capitalize()})") for employee in managers if employee[5]]
    
    # Tabs for different message types
    tab1, tab2, tab3 = st.tabs(["Company Messages", "Manager Messages", "Send Message"])
    
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
                    receiver_info="You (Employee)",
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
                            message_id = send_message("employee", st.session_state.user_id, "company", st.session_state.company_id, message_text, attachment_link)
                            
                            if message_id:
                                st.success("Reply sent to Company successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to send reply")
        else:
            st.info("No messages from Company found")
    
    # Manager Messages Tab
    with tab2:
        st.write("### Messages from Managers")
        
        # Get messages from managers and assistant managers
        manager_messages = get_messages(receiver_type="employee", receiver_id=st.session_state.user_id, sender_type="manager")
        asst_manager_messages = get_messages(receiver_type="employee", receiver_id=st.session_state.user_id, sender_type="asst_manager")
        
        # Combine messages
        all_manager_messages = sorted(manager_messages + asst_manager_messages, key=lambda x: x[8], reverse=True)
        
        if all_manager_messages:
            for message in all_manager_messages:
                sender_type = message[1]  # sender_type
                sender_id = message[2]  # sender_id
                
                # Get sender name
                sender_info = "Manager"
                if sender_type == "manager":
                    manager = next((e for e in managers if e[0] == sender_id and e[4] == "manager"), None)
                    if manager:
                        sender_info = f"{manager[1]} (Manager)"
                else:  # asst_manager
                    asst_manager = next((e for e in managers if e[0] == sender_id and e[4] == "asst_manager"), None)
                    if asst_manager:
                        sender_info = f"{asst_manager[1]} (Assistant Manager)"
                
                render_message_card(
                    message=message,
                    sender_info=sender_info,
                    receiver_info="You (Employee)",
                    can_delete=False
                )
        else:
            st.info("No messages from Managers found")
    
    # Send Message Tab
    with tab3:
        st.write("### Send Message to Manager")
        
        with st.container(border=True):
            with st.form("send_manager_form"):
                manager = st.selectbox(
                    "Select Manager",
                    options=active_managers,
                    format_func=lambda x: x[1],
                    index=0 if active_managers else None
                )
                
                manager_message = st.text_area("Message", placeholder="Type your message to manager here...")
                manager_attachment = st.text_input("Attachment Link (Optional)", placeholder="Enter URL for any attachment")
                
                submit_manager = st.form_submit_button("Send Message", use_container_width=True)
                
                if submit_manager:
                    if not manager:
                        st.error("Please select a manager")
                    elif not manager_message:
                        st.error("Please enter a message")
                    else:
                        manager_id, manager_name = manager
                        
                        # Determine receiver type based on role
                        manager_role = next((e[4] for e in managers if e[0] == manager_id), None)
                        receiver_type = manager_role
                        
                        message_id = send_message("employee", st.session_state.user_id, receiver_type, manager_id, manager_message, manager_attachment)
                        
                        if message_id:
                            st.success(f"Message sent to {manager_name} successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to send message")
        
        # Message history
        st.write("### Sent Messages History")
        
        # Get sent messages
        sent_messages = get_messages(sender_type="employee", sender_id=st.session_state.user_id)
        
        if sent_messages:
            for message in sent_messages[:5]:  # Show only latest 5 messages
                receiver_type = message[3]  # receiver_type
                receiver_id = message[4]  # receiver_id
                
                # Get receiver name
                receiver_info = "Unknown"
                if receiver_type == "company":
                    receiver_info = "Company"
                elif receiver_type == "manager":
                    manager = next((e for e in managers if e[0] == receiver_id and e[4] == "manager"), None)
                    if manager:
                        receiver_info = f"{manager[1]} (Manager)"
                elif receiver_type == "asst_manager":
                    asst_manager = next((e for e in managers if e[0] == receiver_id and e[4] == "asst_manager"), None)
                    if asst_manager:
                        receiver_info = f"{asst_manager[1]} (Assistant Manager)"
                
                render_message_card(
                    message=message,
                    sender_info="You (Employee)",
                    receiver_info=receiver_info,
                    can_delete=True
                )
        else:
            st.info("No sent messages found")
