import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from fpdf import FPDF
import base64
import io
from utils.ui import render_page_title, format_date, download_pdf
from utils.db import get_branches, get_employees, get_reports
from utils.auth import check_company

def render_reports():
    """Render reports page for company."""
    if not check_company():
        st.error("You don't have permission to access this page.")
        return
    
    render_page_title("Reports", "View and download reports", "📊")
    
    # Get branches and employees for filtering
    branches = get_branches(st.session_state.company_id)
    active_branches = [(branch[0], branch[1]) for branch in branches if branch[3]]  # id, name, is_active
    
    employees = get_employees(company_id=st.session_state.company_id)
    
    # Report filtering options
    st.write("### Filter Reports")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        
        with col1:
            filter_type = st.selectbox(
                "Report Type",
                options=[
                    ("branch", "Branch Reports"),
                    ("role", "Role-based Reports"),
                    ("employee", "Individual Employee Reports")
                ],
                format_func=lambda x: x[1],
                index=0
            )
            
            if filter_type[0] == "branch":
                filter_entity = st.selectbox(
                    "Select Branch",
                    options=[("all", "All Branches")] + active_branches,
                    format_func=lambda x: x[1],
                    index=0
                )
            elif filter_type[0] == "role":
                filter_entity = st.selectbox(
                    "Select Role",
                    options=[
                        ("all", "All Roles"),
                        ("manager", "Managers"),
                        ("asst_manager", "Assistant Managers"),
                        ("employee", "General Employees")
                    ],
                    format_func=lambda x: x[1],
                    index=0
                )
            else:  # employee
                active_employees = [(employee[0], f"{employee[1]} ({employee[4].capitalize()})") for employee in employees if employee[5]]
                filter_entity = st.selectbox(
                    "Select Employee",
                    options=active_employees,
                    format_func=lambda x: x[1],
                    index=0 if active_employees else None
                )
        
        with col2:
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
        
        generate_button = st.button("Generate Report", use_container_width=True, type="primary")
    
    # Generate and display report
    if generate_button:
        # Get reports based on filters
        if filter_type[0] == "branch":
            if filter_entity[0] == "all":
                # Get reports for all branches
                branch_ids = [branch[0] for branch in active_branches]
                reports = []
                for branch_id in branch_ids:
                    branch_reports = get_reports(branch_id=branch_id, company_id=st.session_state.company_id, start_date=start_date, end_date=end_date)
                    reports.extend(branch_reports)
            else:
                # Get reports for specific branch
                branch_id = filter_entity[0]
                reports = get_reports(branch_id=branch_id, company_id=st.session_state.company_id, start_date=start_date, end_date=end_date)
        
        elif filter_type[0] == "role":
            if filter_entity[0] == "all":
                # Get reports for all roles
                reports = get_reports(company_id=st.session_state.company_id, start_date=start_date, end_date=end_date)
            else:
                # Get reports for specific role
                role = filter_entity[0]
                role_employees = [employee[0] for employee in employees if employee[4] == role]
                reports = []
                for employee_id in role_employees:
                    employee_reports = get_reports(employee_id=employee_id, company_id=st.session_state.company_id, start_date=start_date, end_date=end_date)
                    reports.extend(employee_reports)
        
        else:  # employee
            # Get reports for specific employee
            employee_id = filter_entity[0]
            reports = get_reports(employee_id=employee_id, company_id=st.session_state.company_id, start_date=start_date, end_date=end_date)
        
        if reports:
            st.write("### Report Results")
            
            # Convert reports to dataframe for display
            report_data = []
            for report in reports:
                report_id = report[0]
                employee_id = report[1]
                employee_name = report[2]
                employee_role = report[3]
                report_date = report[4]
                content = report[5]
                created_at = report[6]
                branch_name = report[7]
                
                report_data.append({
                    "Report ID": report_id,
                    "Date": report_date,
                    "Employee": employee_name,
                    "Role": employee_role.capitalize(),
                    "Branch": branch_name,
                    "Content": content
                })
            
            df = pd.DataFrame(report_data)
            
            # Display report summary
            with st.container(border=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Reports", len(reports))
                
                with col2:
                    st.metric("Employees", len(set(report[1] for report in reports)))
                
                with col3:
                    st.metric("Branches", len(set(report[7] for report in reports)))
            
            # Display detailed report
            st.dataframe(df, use_container_width=True)
            
            # Generate PDF report
            if st.button("Download as PDF", type="primary"):
                pdf_bytes = generate_pdf_report(df, filter_type, filter_entity, start_date, end_date)
                
                # Determine filename
                if filter_type[0] == "branch":
                    if filter_entity[0] == "all":
                        filename = f"all_branches_report_{start_date}_to_{end_date}.pdf"
                    else:
                        branch_name = next((branch[1] for branch in active_branches if branch[0] == filter_entity[0]), "branch")
                        filename = f"{branch_name}_report_{start_date}_to_{end_date}.pdf"
                elif filter_type[0] == "role":
                    if filter_entity[0] == "all":
                        filename = f"all_roles_report_{start_date}_to_{end_date}.pdf"
                    else:
                        filename = f"{filter_entity[0]}_report_{start_date}_to_{end_date}.pdf"
                else:  # employee
                    employee_name = next((employee[1] for employee in employees if employee[0] == filter_entity[0]), "employee")
                    filename = f"{employee_name}_report_{start_date}_to_{end_date}.pdf"
                
                download_pdf(pdf_bytes, filename)
        else:
            st.info("No reports found for the selected criteria")

def generate_pdf_report(df, filter_type, filter_entity, start_date, end_date):
    """Generate PDF report from dataframe."""
    pdf = FPDF()
    pdf.add_page()
    
    # Set up fonts
    pdf.set_font("Arial", "B", 16)
    
    # Title
    if filter_type[0] == "branch":
        if filter_entity[0] == "all":
            pdf.cell(0, 10, "All Branches Report", ln=True, align="C")
        else:
            pdf.cell(0, 10, f"Branch Report: {filter_entity[1]}", ln=True, align="C")
    elif filter_type[0] == "role":
        if filter_entity[0] == "all":
            pdf.cell(0, 10, "All Roles Report", ln=True, align="C")
        else:
            pdf.cell(0, 10, f"Role Report: {filter_entity[1]}", ln=True, align="C")
    else:  # employee
        pdf.cell(0, 10, f"Employee Report: {filter_entity[1]}", ln=True, align="C")
    
    # Date range
    pdf.set_font("Arial", "I", 12)
    pdf.cell(0, 10, f"Period: {start_date} to {end_date}", ln=True, align="C")
    
    # Summary
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Report Summary", ln=True)
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Total Reports: {len(df)}", ln=True)
    pdf.cell(0, 10, f"Total Employees: {df['Employee'].nunique()}", ln=True)
    pdf.cell(0, 10, f"Total Branches: {df['Branch'].nunique()}", ln=True)
    
    # Add some space
    pdf.ln(10)
    
    # Report details table
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Detailed Reports", ln=True)
    
    # Table header
    pdf.set_font("Arial", "B", 12)
    pdf.cell(25, 10, "Date", border=1)
    pdf.cell(40, 10, "Employee", border=1)
    pdf.cell(30, 10, "Role", border=1)
    pdf.cell(40, 10, "Branch", border=1)
    pdf.cell(0, 10, "Content", border=1, ln=True)
    
    # Table rows
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        # Convert date to string if it's not already
        date_str = str(row["Date"]) if not isinstance(row["Date"], str) else row["Date"]
        
        pdf.cell(25, 10, date_str[:10], border=1)
        pdf.cell(40, 10, row["Employee"][:20], border=1)
        pdf.cell(30, 10, row["Role"], border=1)
        pdf.cell(40, 10, row["Branch"][:20], border=1)
        
        # Handle content - might need to wrap text
        content = row["Content"]
        if len(content) > 60:
            content = content[:57] + "..."
        pdf.cell(0, 10, content, border=1, ln=True)
    
    # Convert PDF to bytes
    pdf_bytes = pdf.output(dest="S").encode("latin1")
    
    return pdf_bytes
