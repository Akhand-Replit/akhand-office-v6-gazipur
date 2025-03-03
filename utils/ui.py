import streamlit as st
from datetime import datetime
import base64
from PIL import Image
import io
import streamlit_extras.colored_header as colored_header
from utils.auth import login_user, logout_user

def set_page_config(title="Company Management System"):
    """Set page configuration."""
    st.set_page_config(
        page_title=title,
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def render_login_form():
    """Render login form."""
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username", placeholder="Enter your username")
        
        with col2:
            password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            role = st.selectbox("Login as", ["admin", "company", "employee"])
        
        submit_button = st.form_submit_button("Login", use_container_width=True)
        
        if submit_button:
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                success = login_user(username, password, role)
                if success:
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")

def render_navigation(current_page, navigation_items):
    """Render navigation menu."""
    with st.sidebar:
        if st.session_state.profile_pic:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(st.session_state.profile_pic, width=60)
            with col2:
                st.write(f"**{st.session_state.username}**")
                st.caption(f"Role: {st.session_state.user_role.capitalize()}")
        else:
            st.write(f"**{st.session_state.username}**")
            st.caption(f"Role: {st.session_state.user_role.capitalize()}")
        
        st.divider()
        
        for item in navigation_items:
            label = item["label"]
            page = item["page"]
            icon = item.get("icon", "📄")
            
            if current_page == page:
                if st.sidebar.button(
                    f"{icon} {label}",
                    key=f"nav_{page}",
                    help=f"Navigate to {label}",
                    type="primary",
                    use_container_width=True
                ):
                    set_current_page(page)
            else:
                if st.sidebar.button(
                    f"{icon} {label}",
                    key=f"nav_{page}",
                    help=f"Navigate to {label}",
                    use_container_width=True
                ):
                    set_current_page(page)
        
        st.sidebar.divider()
        
        if st.sidebar.button("Logout", key="logout", use_container_width=True):
            logout_user()
            st.rerun()

def set_current_page(page):
    """Set current page in session state."""
    st.session_state.current_page = page
    st.rerun()

def render_page_title(title, description=None, icon=None):
    """Render page title with optional description."""
    colored_header.colored_header(
        label=title if not icon else f"{icon} {title}",
        description=description if description else "",
        color_name="blue-green"
    )
    st.divider()

def download_pdf(data, filename="download.pdf"):
    """Generate download button for PDF."""
    base64_pdf = base64.b64encode(data).decode('utf-8')
    download_button = f'<a href="data:application/pdf;base64,{base64_pdf}" download="{filename}" class="button">Download PDF</a>'
    st.markdown(download_button, unsafe_allow_html=True)

def format_date(date_str):
    """Format date string to a more readable format."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%B %d, %Y")
    except:
        return date_str

def format_datetime(datetime_str):
    """Format datetime string to a more readable format."""
    try:
        datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        return datetime_obj.strftime("%B %d, %Y %I:%M %p")
    except:
        try:
            datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")
            return datetime_obj.strftime("%B %d, %Y %I:%M %p")
        except:
            return datetime_str

def get_status_color(status):
    """Get color based on status."""
    if status.lower() == "active" or status.lower() == "completed" or status is True:
        return "green"
    elif status.lower() == "inactive" or status.lower() == "pending" or status is False:
        return "red"
    else:
        return "blue"

def user_status_indicator(is_active):
    """Render status indicator for user."""
    status = "Active" if is_active else "Inactive"
    color = get_status_color(status)
    return f"<span style='color: {color}; font-weight: bold;'>{status}</span>"

def task_status_indicator(is_completed):
    """Render status indicator for task."""
    status = "Completed" if is_completed else "Pending"
    color = get_status_color(status)
    return f"<span style='color: {color}; font-weight: bold;'>{status}</span>"

def format_attachment_display(attachment_link):
    """Format attachment link for display."""
    if not attachment_link:
        return ""
    
    if attachment_link.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        return f"<a href='{attachment_link}' target='_blank'><img src='{attachment_link}' width='100'></a>"
    else:
        file_name = attachment_link.split('/')[-1]
        return f"<a href='{attachment_link}' target='_blank'>{file_name}</a>"

def set_delete_message_id(msg_id):
    """Helper function to set message ID for deletion."""
    st.session_state.delete_message_id = msg_id

def render_message_card(message, sender_info=None, receiver_info=None, can_delete=False):
    """Render a message card."""
    with st.container():
        cols = st.columns([3, 7])
        
        with cols[0]:
            st.write(f"**From:** {sender_info if sender_info else message[1]}")
            st.write(f"**To:** {receiver_info if receiver_info else message[3]}")
            st.caption(f"**Date:** {format_datetime(str(message[8]))}")
            
            if can_delete and not message[7]:  # is_deleted
                if st.button("Delete", key=f"delete_msg_{message[0]}"):
                    st.session_state.delete_message_id = message[0]
        
        with cols[1]:
            st.write(message[5])  # message_text
            if message[6]:  # attachment_link
                st.markdown(format_attachment_display(message[6]), unsafe_allow_html=True)
        
        st.divider()

def get_initials(name):
    """Get initials from name."""
    if not name:
        return "NA"
    
    words = name.split()
    initials = "".join(word[0].upper() for word in words if word)
    return initials if initials else "NA"

def generate_placeholder_image(name, size=100):
    """Generate a placeholder image with initials."""
    initials = get_initials(name)
    
    # Create a basic image
    img = Image.new('RGB', (size, size), color=(100, 149, 237))
    
    # Draw initials
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, or use default
    try:
        font = ImageFont.truetype("arial.ttf", size=int(size/2))
    except:
        font = ImageFont.load_default()
    
    # Position text in center
    text_width, text_height = draw.textsize(initials, font=font)
    position = ((size-text_width)/2, (size-text_height)/2)
    
    # Draw text
    draw.text(position, initials, font=font, fill=(255, 255, 255))
    
    # Convert to base64 for display
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

def clean_url(url):
    """Clean URL to ensure it's valid."""
    if not url:
        return None
    
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return url
