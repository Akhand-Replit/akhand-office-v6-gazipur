import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
import bcrypt

# Database connection function
def get_connection():
    """Create a connection to PostgreSQL database using streamlit secrets."""
    try:
        conn = psycopg2.connect(
            dbname=st.secrets["postgres"]["dbname"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            host=st.secrets["postgres"]["host"],
            port=st.secrets["postgres"]["port"]
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

# Initialize the database schema
def initialize_database():
    """Create necessary tables if they don't exist."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Admin table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                profile_name VARCHAR(100) NOT NULL,
                profile_pic VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Company table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS company (
                id SERIAL PRIMARY KEY,
                company_name VARCHAR(100) NOT NULL,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                profile_pic VARCHAR(255),
                is_active BOOLEAN DEFAULT TRUE,
                created_by INTEGER REFERENCES admin(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Branch table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS branch (
                id SERIAL PRIMARY KEY,
                branch_name VARCHAR(100) NOT NULL,
                company_id INTEGER REFERENCES company(id),
                is_main_branch BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(branch_name, company_id)
            )
            """)
            
            # Employee table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS employee (
                id SERIAL PRIMARY KEY,
                employee_name VARCHAR(100) NOT NULL,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                profile_pic VARCHAR(255),
                role VARCHAR(20) CHECK (role IN ('manager', 'asst_manager', 'employee')),
                company_id INTEGER REFERENCES company(id),
                branch_id INTEGER REFERENCES branch(id),
                is_active BOOLEAN DEFAULT TRUE,
                created_by VARCHAR(20) NOT NULL,
                created_by_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Task table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS task (
                id SERIAL PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                assigned_to VARCHAR(20) NOT NULL, -- 'branch' or 'employee'
                assigned_id INTEGER NOT NULL,
                assigned_by VARCHAR(20) NOT NULL, -- 'company', 'manager', or 'asst_manager'
                assigned_by_id INTEGER NOT NULL,
                is_completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Employee task completion table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS task_completion (
                id SERIAL PRIMARY KEY,
                task_id INTEGER REFERENCES task(id),
                employee_id INTEGER REFERENCES employee(id),
                is_completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Report table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS report (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER REFERENCES employee(id),
                report_date DATE NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Message table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS message (
                id SERIAL PRIMARY KEY,
                sender_type VARCHAR(20) NOT NULL, -- 'admin', 'company', 'manager', 'asst_manager', 'employee'
                sender_id INTEGER NOT NULL,
                receiver_type VARCHAR(20) NOT NULL, -- 'company', 'branch', 'employee'
                receiver_id INTEGER NOT NULL,
                message_text TEXT,
                attachment_link VARCHAR(255),
                is_deleted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Insert default admin if not exists
            cur.execute("""
            INSERT INTO admin (username, profile_name, profile_pic)
            SELECT 'admin', 'System Administrator', 'https://ui-avatars.com/api/?name=Admin&background=random'
            WHERE NOT EXISTS (SELECT 1 FROM admin WHERE username = 'admin')
            """)
            
            conn.commit()
            cur.close()
        except Exception as e:
            st.error(f"Database initialization failed: {e}")
        finally:
            conn.close()

# Company Functions
def create_company(company_name, username, password, profile_pic, admin_id):
    """Create a new company."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Hash the password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cur.execute("""
            INSERT INTO company (company_name, username, password_hash, profile_pic, created_by)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """, (company_name, username, password_hash, profile_pic, admin_id))
            
            company_id = cur.fetchone()[0]
            
            # Create default main branch
            cur.execute("""
            INSERT INTO branch (branch_name, company_id, is_main_branch)
            VALUES ('Main Branch', %s, TRUE)
            """, (company_id,))
            
            conn.commit()
            cur.close()
            return company_id
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to create company: {e}")
            return None
        finally:
            conn.close()
    return None

def get_companies():
    """Get all companies."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
            SELECT id, company_name, username, profile_pic, is_active, created_at
            FROM company
            ORDER BY created_at DESC
            """)
            companies = cur.fetchall()
            cur.close()
            
            return companies
        except Exception as e:
            st.error(f"Failed to get companies: {e}")
            return []
        finally:
            conn.close()
    return []

def toggle_company_status(company_id, is_active):
    """Activate or deactivate a company and related branches and employees."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Update company status
            cur.execute("""
            UPDATE company
            SET is_active = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """, (is_active, company_id))
            
            # Update branch status
            cur.execute("""
            UPDATE branch
            SET is_active = %s, updated_at = CURRENT_TIMESTAMP
            WHERE company_id = %s
            """, (is_active, company_id))
            
            # Update employee status
            cur.execute("""
            UPDATE employee
            SET is_active = %s, updated_at = CURRENT_TIMESTAMP
            WHERE company_id = %s
            """, (is_active, company_id))
            
            conn.commit()
            cur.close()
            return True
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to update company status: {e}")
            return False
        finally:
            conn.close()
    return False

# Branch Functions
def create_branch(branch_name, company_id):
    """Create a new branch."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO branch (branch_name, company_id)
            VALUES (%s, %s)
            RETURNING id
            """, (branch_name, company_id))
            
            branch_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            return branch_id
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to create branch: {e}")
            return None
        finally:
            conn.close()
    return None

def get_branches(company_id):
    """Get all branches for a company."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
            SELECT id, branch_name, is_main_branch, is_active, created_at
            FROM branch
            WHERE company_id = %s
            ORDER BY is_main_branch DESC, created_at DESC
            """, (company_id,))
            branches = cur.fetchall()
            cur.close()
            
            return branches
        except Exception as e:
            st.error(f"Failed to get branches: {e}")
            return []
        finally:
            conn.close()
    return []

def toggle_branch_status(branch_id, is_active):
    """Activate or deactivate a branch and related employees."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Update branch status
            cur.execute("""
            UPDATE branch
            SET is_active = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """, (is_active, branch_id))
            
            # Update employee status
            cur.execute("""
            UPDATE employee
            SET is_active = %s, updated_at = CURRENT_TIMESTAMP
            WHERE branch_id = %s
            """, (is_active, branch_id))
            
            conn.commit()
            cur.close()
            return True
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to update branch status: {e}")
            return False
        finally:
            conn.close()
    return False

# Employee Functions
def create_employee(employee_name, username, password, profile_pic, role, company_id, branch_id, created_by, created_by_id):
    """Create a new employee."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Hash the password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cur.execute("""
            INSERT INTO employee (employee_name, username, password_hash, profile_pic, role, company_id, branch_id, created_by, created_by_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """, (employee_name, username, password_hash, profile_pic, role, company_id, branch_id, created_by, created_by_id))
            
            employee_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            return employee_id
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to create employee: {e}")
            return None
        finally:
            conn.close()
    return None

def get_employees(company_id=None, branch_id=None, role=None):
    """Get employees based on filters."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            query = """
            SELECT e.id, e.employee_name, e.username, e.profile_pic, e.role, e.is_active, b.branch_name
            FROM employee e
            JOIN branch b ON e.branch_id = b.id
            WHERE 1=1
            """
            params = []
            
            if company_id:
                query += " AND e.company_id = %s"
                params.append(company_id)
            
            if branch_id:
                query += " AND e.branch_id = %s"
                params.append(branch_id)
            
            if role:
                query += " AND e.role = %s"
                params.append(role)
            
            query += " ORDER BY e.role, e.created_at DESC"
            
            cur.execute(query, params)
            employees = cur.fetchall()
            cur.close()
            
            return employees
        except Exception as e:
            st.error(f"Failed to get employees: {e}")
            return []
        finally:
            conn.close()
    return []

def toggle_employee_status(employee_id, is_active):
    """Activate or deactivate an employee."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
            UPDATE employee
            SET is_active = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """, (is_active, employee_id))
            
            conn.commit()
            cur.close()
            return True
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to update employee status: {e}")
            return False
        finally:
            conn.close()
    return False

def update_employee_role(employee_id, role):
    """Update employee role."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
            UPDATE employee
            SET role = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """, (role, employee_id))
            
            conn.commit()
            cur.close()
            return True
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to update employee role: {e}")
            return False
        finally:
            conn.close()
    return False

def update_employee_branch(employee_id, branch_id):
    """Update employee branch."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
            UPDATE employee
            SET branch_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """, (branch_id, employee_id))
            
            conn.commit()
            cur.close()
            return True
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to update employee branch: {e}")
            return False
        finally:
            conn.close()
    return False

# Task Functions
def create_task(title, description, assigned_to, assigned_id, assigned_by, assigned_by_id):
    """Create a new task."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO task (title, description, assigned_to, assigned_id, assigned_by, assigned_by_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """, (title, description, assigned_to, assigned_id, assigned_by, assigned_by_id))
            
            task_id = cur.fetchone()[0]
            
            # If assigned to branch, assign to all employees in that branch
            if assigned_to == 'branch':
                cur.execute("""
                INSERT INTO task_completion (task_id, employee_id)
                SELECT %s, id FROM employee
                WHERE branch_id = %s AND is_active = TRUE
                """, (task_id, assigned_id))
            else:  # assigned to employee
                cur.execute("""
                INSERT INTO task_completion (task_id, employee_id)
                VALUES (%s, %s)
                """, (task_id, assigned_id))
            
            conn.commit()
            cur.close()
            return task_id
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to create task: {e}")
            return None
        finally:
            conn.close()
    return None

def get_tasks(company_id=None, branch_id=None, employee_id=None, is_completed=None, assigned_by=None, assigned_by_id=None):
    """Get tasks based on filters."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            query = """
            SELECT t.id, t.title, t.description, t.assigned_to, t.assigned_id, 
                   t.assigned_by, t.assigned_by_id, t.is_completed, t.created_at
            FROM task t
            """
            
            conditions = []
            params = []
            
            if employee_id:
                query += """
                JOIN task_completion tc ON t.id = tc.task_id
                """
                conditions.append("tc.employee_id = %s")
                params.append(employee_id)
            
            if company_id:
                if assigned_by and assigned_by == 'company':
                    conditions.append("t.assigned_by = 'company' AND t.assigned_by_id = %s")
                    params.append(company_id)
                elif assigned_to_company:
                    conditions.append("(t.assigned_to = 'company' AND t.assigned_id = %s)")
                    params.append(company_id)
            
            if branch_id:
                if assigned_to_branch:
                    conditions.append("(t.assigned_to = 'branch' AND t.assigned_id = %s)")
                    params.append(branch_id)
            
            if assigned_by and assigned_by_id:
                conditions.append("t.assigned_by = %s AND t.assigned_by_id = %s")
                params.extend([assigned_by, assigned_by_id])
            
            if is_completed is not None:
                conditions.append("t.is_completed = %s")
                params.append(is_completed)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY t.created_at DESC"
            
            cur.execute(query, params)
            tasks = cur.fetchall()
            cur.close()
            
            return tasks
        except Exception as e:
            st.error(f"Failed to get tasks: {e}")
            return []
        finally:
            conn.close()
    return []

def complete_task(task_id, employee_id):
    """Mark a task as completed by an employee."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Update task completion for the employee
            cur.execute("""
            UPDATE task_completion
            SET is_completed = TRUE, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = %s AND employee_id = %s
            """, (task_id, employee_id))
            
            # Check if all employees have completed this task
            cur.execute("""
            SELECT COUNT(*) AS total, SUM(CASE WHEN is_completed THEN 1 ELSE 0 END) AS completed
            FROM task_completion
            WHERE task_id = %s
            """, (task_id,))
            
            result = cur.fetchone()
            total = result[0]
            completed = result[1]
            
            # If all employees have completed the task, mark the task as completed
            if total == completed:
                cur.execute("""
                UPDATE task
                SET is_completed = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """, (task_id,))
            
            conn.commit()
            cur.close()
            return True
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to complete task: {e}")
            return False
        finally:
            conn.close()
    return False

def manager_complete_task(task_id, branch_id):
    """Manager marks a task as completed for the whole branch."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Update task completion for all employees in branch
            cur.execute("""
            UPDATE task_completion
            SET is_completed = TRUE, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = %s AND employee_id IN (
                SELECT id FROM employee WHERE branch_id = %s
            )
            """, (task_id, branch_id))
            
            # Mark the task as completed
            cur.execute("""
            UPDATE task
            SET is_completed = TRUE, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """, (task_id,))
            
            conn.commit()
            cur.close()
            return True
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to complete task: {e}")
            return False
        finally:
            conn.close()
    return False

# Report Functions
def submit_report(employee_id, report_date, content):
    """Submit a daily report."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Check if a report already exists for this date
            cur.execute("""
            SELECT id FROM report
            WHERE employee_id = %s AND report_date = %s
            """, (employee_id, report_date))
            
            existing_report = cur.fetchone()
            
            if existing_report:
                # Update existing report
                cur.execute("""
                UPDATE report
                SET content = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """, (content, existing_report[0]))
                report_id = existing_report[0]
            else:
                # Create new report
                cur.execute("""
                INSERT INTO report (employee_id, report_date, content)
                VALUES (%s, %s, %s)
                RETURNING id
                """, (employee_id, report_date, content))
                report_id = cur.fetchone()[0]
            
            conn.commit()
            cur.close()
            return report_id
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to submit report: {e}")
            return None
        finally:
            conn.close()
    return None

def get_reports(employee_id=None, branch_id=None, company_id=None, start_date=None, end_date=None):
    """Get reports based on filters."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            query = """
            SELECT r.id, r.employee_id, e.employee_name, e.role, r.report_date, r.content, r.created_at, b.branch_name
            FROM report r
            JOIN employee e ON r.employee_id = e.id
            JOIN branch b ON e.branch_id = b.id
            WHERE 1=1
            """
            params = []
            
            if employee_id:
                query += " AND r.employee_id = %s"
                params.append(employee_id)
            
            if branch_id:
                query += " AND e.branch_id = %s"
                params.append(branch_id)
            
            if company_id:
                query += " AND e.company_id = %s"
                params.append(company_id)
            
            if start_date:
                query += " AND r.report_date >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND r.report_date <= %s"
                params.append(end_date)
            
            query += " ORDER BY r.report_date DESC, e.role"
            
            cur.execute(query, params)
            reports = cur.fetchall()
            cur.close()
            
            return reports
        except Exception as e:
            st.error(f"Failed to get reports: {e}")
            return []
        finally:
            conn.close()
    return []

# Message Functions
def send_message(sender_type, sender_id, receiver_type, receiver_id, message_text, attachment_link=None):
    """Send a message."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO message (sender_type, sender_id, receiver_type, receiver_id, message_text, attachment_link)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """, (sender_type, sender_id, receiver_type, receiver_id, message_text, attachment_link))
            
            message_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            return message_id
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to send message: {e}")
            return None
        finally:
            conn.close()
    return None

def get_messages(receiver_type=None, receiver_id=None, sender_type=None, sender_id=None):
    """Get messages based on filters."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            query = """
            SELECT id, sender_type, sender_id, receiver_type, receiver_id, message_text, attachment_link, is_deleted, created_at
            FROM message
            WHERE is_deleted = FALSE
            """
            params = []
            
            if receiver_type and receiver_id:
                query += " AND receiver_type = %s AND receiver_id = %s"
                params.extend([receiver_type, receiver_id])
            
            if sender_type and sender_id:
                query += " AND sender_type = %s AND sender_id = %s"
                params.extend([sender_type, sender_id])
            
            query += " ORDER BY created_at DESC"
            
            cur.execute(query, params)
            messages = cur.fetchall()
            cur.close()
            
            return messages
        except Exception as e:
            st.error(f"Failed to get messages: {e}")
            return []
        finally:
            conn.close()
    return []

def delete_message(message_id, sender_type, sender_id):
    """Delete a message (soft delete)."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
            UPDATE message
            SET is_deleted = TRUE, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND sender_type = %s AND sender_id = %s
            """, (message_id, sender_type, sender_id))
            
            conn.commit()
            cur.close()
            return True
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to delete message: {e}")
            return False
        finally:
            conn.close()
    return False

# Profile Functions
def update_admin_profile(admin_id, profile_name, profile_pic):
    """Update admin profile."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
            UPDATE admin
            SET profile_name = %s, profile_pic = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """, (profile_name, profile_pic, admin_id))
            
            conn.commit()
            cur.close()
            return True
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to update admin profile: {e}")
            return False
        finally:
            conn.close()
    return False

def update_company_profile(company_id, company_name, profile_pic):
    """Update company profile."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
            UPDATE company
            SET company_name = %s, profile_pic = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """, (company_name, profile_pic, company_id))
            
            conn.commit()
            cur.close()
            return True
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to update company profile: {e}")
            return False
        finally:
            conn.close()
    return False

def update_employee_profile(employee_id, employee_name, profile_pic):
    """Update employee profile."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
            UPDATE employee
            SET employee_name = %s, profile_pic = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """, (employee_name, profile_pic, employee_id))
            
            conn.commit()
            cur.close()
            return True
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to update employee profile: {e}")
            return False
        finally:
            conn.close()
    return False

# Authentication Functions
def verify_admin(username, password):
    """Verify admin credentials."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
            SELECT id, profile_name, profile_pic
            FROM admin
            WHERE username = %s
            """, (username,))
            
            admin = cur.fetchone()
            cur.close()
            
            if admin and password == st.secrets["admin_password"]:
                return {
                    "id": admin[0],
                    "username": username,
                    "profile_name": admin[1],
                    "profile_pic": admin[2],
                    "role": "admin"
                }
            return None
        except Exception as e:
            st.error(f"Failed to verify admin: {e}")
            return None
        finally:
            conn.close()
    return None

def verify_company(username, password):
    """Verify company credentials."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
            SELECT id, company_name, password_hash, profile_pic, is_active
            FROM company
            WHERE username = %s
            """, (username,))
            
            company = cur.fetchone()
            cur.close()
            
            if company and company[4] and bcrypt.checkpw(password.encode('utf-8'), company[2].encode('utf-8')):
                return {
                    "id": company[0],
                    "username": username,
                    "name": company[1],
                    "profile_pic": company[3],
                    "role": "company"
                }
            return None
        except Exception as e:
            st.error(f"Failed to verify company: {e}")
            return None
        finally:
            conn.close()
    return None

def verify_employee(username, password):
    """Verify employee credentials."""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
            SELECT e.id, e.employee_name, e.password_hash, e.profile_pic, e.role, e.is_active, 
                   e.company_id, e.branch_id, c.is_active as company_active, b.is_active as branch_active
            FROM employee e
            JOIN company c ON e.company_id = c.id
            JOIN branch b ON e.branch_id = b.id
            WHERE e.username = %s
            """, (username,))
            
            employee = cur.fetchone()
            cur.close()
            
            if (employee and employee[5] and employee[8] and employee[9] and 
                bcrypt.checkpw(password.encode('utf-8'), employee[2].encode('utf-8'))):
                return {
                    "id": employee[0],
                    "username": username,
                    "name": employee[1],
                    "profile_pic": employee[3],
                    "role": employee[4],
                    "company_id": employee[6],
                    "branch_id": employee[7]
                }
            return None
        except Exception as e:
            st.error(f"Failed to verify employee: {e}")
            return None
        finally:
            conn.close()
    return None
