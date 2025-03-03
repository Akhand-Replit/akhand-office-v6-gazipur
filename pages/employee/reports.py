import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from fpdf import FPDF
import base64
import io
from utils.ui import render_page_title, format_date, download_pdf
from utils.db import get_reports, submit_report
from utils.auth import check_employee

def render_reports():
    """Render reports page for employee."""
    if not check_employee():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Reports", "Submit and view your reports", "📊")
    
    # Reports tabs
    tab1, tab2 = st.tabs(["Submit Report", "View Reports"])
    
    # Submit Report Tab
    with tab1:
        st.write("### Submit Daily Report")
        
        with st.container(border=True):
            with st.form("submit_report_form"):
                today = datetime.now().date()
                report_date = st.date_input("Report Date", value=today, max_value=today)
                report_content = st.text_area("Report Content", placeholder="Enter your daily report here...", height=200)
                
                submit_button = st.form_submit_button("Submit Report", use_container_width=True)
                
                if submit_button:
                    if not report_content:
                        st.error("Please enter report content")
                    else:
                        report_id = submit_report(st.session_state.user_id, report_date, report_content)
                        
                        if report_id:
                            st.success(f"Report for {report_date} submitted successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to submit report")
    
    # View Reports Tab
    with tab2:
        st.write("### View Your Reports")
        
        # Filter options
        date_range = st.selectbox(
            "Date Range",
            options=[
                ("daily", "Daily"),
                ("weekly", "Weekly"),
                ("monthly", "Monthly"),
                ("yearly", "Yearly"),
                ("custom", "Custom Range")
            ],
            index=0
        )
        
        today = datetime.now().date()
        
        if date_range == "daily":
            selected_date = st.date_input("Select Date", value=today)
            start_date = selected_date
            end_date = selected_date
        elif date_range == "weekly":
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
            st.write(f"Week: {format_date(str(start_date))} to {format_date(str(end_date))}")
        elif date_range == "monthly":
            start_date = today.replace(day=1)
            next_month = start_date.replace(day=28) + timedelta(days=4)
            end_date = next_month.replace(day=1) - timedelta(days=1)
            st.write(f"Month: {format_date(str(start_date))} to {format_date(str(end_date))}")
        elif date_range == "yearly":
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
            st.write(f"Year: {start_date.year}")
        else:  # custom
            date_range = st.date_input("Select Date Range", value=[today, today], key="custom_range")
            if len(date_range) == 2:
                start_date = date_range[0]
                end_date = date_range[1]
            else:
                start_date = date_range[0]
                end_date = date_range[0]
        
        generate_button = st.button("Generate Report", type="primary", use_container_width=True)
        
        if generate_button:
            # Get employee's reports
            reports = get_reports(employee_id=st.session_state.user_id, start_date=start_date, end_date=end_date)
            
            if reports:
                st.write("### Your Reports")
                
                # Convert reports to dataframe for display
                report_data = []
                for report in reports:
                    report_id = report[0]
                    report_date = report[4]
                    content = report[5]
                    created_at = report[6]
                    
                    report_data.append({
                        "Report ID": report_id,
                        "Date": report_date,
                        "Content": content,
                        "Submitted On": created_at
                    })
                
                df = pd.DataFrame(report_data)
                
                # Display report summary
                with st.container(border=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Total Reports", len(reports))
                    
                    with col2:
                        st.metric("Date Range", f"{start_date} to {end_date}")
                
                # Display detailed report
                for _, row in df.iterrows():
                    with st.container(border=True):
                        st.write(f"**Report Date:** {row['Date']}")
                        st.caption(f"Submitted on: {row['Submitted On']}")
                        st.write("**Content:**")
                        st.write(row["Content"])
                
                # Generate PDF report
                if st.button("Download as PDF", type="primary"):
                    pdf_bytes = generate_pdf_report(df, start_date, end_date)
                    filename = f"my_reports_{start_date}_to_{end_date}.pdf"
                    download_pdf(pdf_bytes, filename)
            else:
                st.info("No reports found for the selected date range")

def generate_pdf_report(df, start_date, end_date):
    """Generate PDF report from dataframe."""
    pdf = FPDF()
    pdf.add_page()
    
    # Set up fonts
    pdf.set_font("Arial", "B", 16)
    
    # Title
    pdf.cell(0, 10, "Your Reports", ln=True, align="C")
    
    # Date range
    pdf.set_font("Arial", "I", 12)
    pdf.cell(0, 10, f"Period: {start_date} to {end_date}", ln=True, align="C")
    
    # Summary
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Report Summary", ln=True)
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Total Reports: {len(df)}", ln=True)
    
    # Add some space
    pdf.ln(10)
    
    # Report details
    for _, row in df.iterrows():
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Report Date: {row['Date']}", ln=True)
        
        pdf.set_font("Arial", "", 12)
        
        # Handle multi-line content
        content = row["Content"]
        content_lines = content.split("\n")
        
        for line in content_lines:
            # Wrap long lines
            while len(line) > 75:
                pdf.multi_cell(0, 10, line[:75])
                line = line[75:]
            pdf.multi_cell(0, 10, line)
        
        # Add separator
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
    
    # Convert PDF to bytes
    pdf_bytes = pdf.output(dest="S").encode("latin1")
    
    return pdf_bytes
