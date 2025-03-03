import streamlit as st
from utils.ui import render_page_title, render_message_card
from utils.db import get_companies, send_message, get_messages, delete_message
from utils.auth import check_admin

def render_messages():
    """Render messages page for admin."""
    if not check_admin():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Messages", "Send and view messages", "✉️")
    
    # Initialize state for message deletion
    if "delete_message_id" not in st.session_state:
        st.session_state.delete_message_id = None
    
    # Process message deletion
    if st.session_state.delete_message_id:
        if delete_message(st.session_state.delete_message_id, "admin", st.session_state.user_id):
            st.success("Message deleted successfully!")
        else:
            st.error("Failed to delete message")
        
        st.session_state.delete_message_id = None
        st.rerun()
    
    # Message composition form
    st.write("### Send Message")
    
    with st.container(border=True):
        with st.form("send_message_form"):
            companies = get_companies()
            company_options = ["Select Company"] + [(company[0], company[1]) for company in companies if company[4]]  # only active companies
            
            selected_company = st.selectbox(
                "Send to Company",
                options=company_options,
                format_func=lambda x: x[1] if isinstance(x, tuple) else x,
                index=0
            )
            
            message_text = st.text_area("Message", placeholder="Type your message here...")
            attachment_link = st.text_input("Attachment Link (Optional)", placeholder="Enter URL for any attachment")
            
            submit_button = st.form_submit_button("Send Message", use_container_width=True)
            
            if submit_button:
                if selected_company == "Select Company":
                    st.error("Please select a company")
                elif not message_text:
                    st.error("Please enter a message")
                else:
                    company_id, company_name = selected_company
                    message_id = send_message("admin", st.session_state.user_id, "company", company_id, message_text, attachment_link)
                    
                    if message_id:
                        st.success(f"Message sent to {company_name} successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to send message")
    
    # Message list
    st.write("### Message History")
    
    # Get sent messages
    sent_messages = get_messages(sender_type="admin", sender_id=st.session_state.user_id)
    
    # Get received messages (replies from companies)
    received_messages = get_messages(receiver_type="admin", receiver_id=st.session_state.user_id)
    
    tab1, tab2 = st.tabs(["Sent Messages", "Received Messages"])
    
    with tab1:
        if sent_messages:
            for message in sent_messages:
                # Get company name for display
                company_id = message[3]  # receiver_id
                company_name = next((company[1] for company in companies if company[0] == company_id), f"Company {company_id}")
                
                render_message_card(
                    message=message,
                    sender_info="You (Admin)",
                    receiver_info=company_name,
                    can_delete=True
                )
        else:
            st.info("No sent messages found")
    
    with tab2:
        if received_messages:
            for message in received_messages:
                # Get company name for display
                company_id = message[1]  # sender_id
                company_name = next((company[1] for company in companies if company[0] == company_id), f"Company {company_id}")
                
                render_message_card(
                    message=message,
                    sender_info=company_name,
                    receiver_info="You (Admin)",
                    can_delete=False
                )
        else:
            st.info("No received messages found")
