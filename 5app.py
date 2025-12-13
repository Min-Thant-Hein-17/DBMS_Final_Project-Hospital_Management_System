import streamlit as st
import pandas as pd
import psycopg2
from dotenv import load_dotenv
import os

# --- 1. Load Environment Variables ---
# This loads variables from your .env file (which is IGNORED by git!)
load_dotenv()

# --- 2. Database Connection Function ---
@st.cache_resource
def init_connection():
    """Initializes and returns a PostgreSQL connection object."""
    try:
        # Load credentials from environment variables
        # The Streamlit hosting environment must also be configured with these secrets
        conn = psycopg2.connect(
            host=os.getenv("PGHOST"),
            database=os.getenv("PGDATABASE"),
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD"),
            port=os.getenv("PGPORT", "5432") # Use 5432 as default if PGPORT is missing
        )
        return conn
    except Exception as e:
        st.error(f"Error connecting to the database. Check your Streamlit secrets or local .env file. Error: {e}")
        return None

# --- 3. Run Query Function ---
@st.cache_data(ttl=60) # Cache data for 60 seconds to speed up the app
def run_query(query):
    """Runs a SQL query and returns the results as a Pandas DataFrame."""
    conn = init_connection()
    if conn is None:
        return pd.DataFrame() # Return empty DataFrame on connection failure
    
    with conn.cursor() as cur:
        try:
            cur.execute(query)
            # Fetch column names
            column_names = [desc[0] for desc in cur.description]
            # Fetch data
            data = cur.fetchall()
            return pd.DataFrame(data, columns=column_names)
        except Exception as e:
            st.error(f"Error executing query. Check your SQL syntax: {e}")
            return pd.DataFrame()


# --- 4. Streamlit App Layout and Logic ---
st.set_page_config(
    page_title="Hospital Management System Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏥 Hospital Management System Dashboard")

# Check database connection
conn = init_connection()
if conn is not None:
    st.sidebar.success("Database Connection: Live")
else:
    st.sidebar.error("Database Connection: Failed")


# --- Sidebar Navigation ---
st.sidebar.header("Navigation")
menu = ["Overview", "Patients", "Doctors", "Appointments"]
choice = st.sidebar.radio("Select Dashboard View", menu)


# --- 5. Display Content based on Selection (Updated Queries) ---

if choice == "Overview":
    st.header("System Overview")
    
    # Example 1: Total Patients Count
    st.subheader("Key Metrics")
    # Query uses the correct table name 'patient'
    total_patients_query = "SELECT COUNT(*) FROM patient;" 
    total_patients_df = run_query(total_patients_query)
    
    total_patients = total_patients_df.iloc[0, 0] if not total_patients_df.empty else "N/A"
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Patients", value=total_patients)

    # Example 2: Show Recent Appointments
    st.subheader("Recent Appointments")
    recent_appointments_query = """
    SELECT 
        a.appointment_id, 
        p.patient_name,         -- Updated to use 'patient_name'
        d.doctor_name,          -- Updated to use 'doctor_name'
        a.date_of_appointment   -- Updated to use 'date_of_appointment'
    FROM appointment a          -- Updated to use table 'appointment'
    JOIN patient p ON a.patient_id = p.patient_id  -- Updated to table 'patient'
    JOIN doctor d ON a.doctor_id = d.doctor_id    -- Updated to table 'doctor'
    ORDER BY a.date_of_appointment DESC 
    LIMIT 10;
    """
    recent_appointments_df = run_query(recent_appointments_query)
    st.dataframe(recent_appointments_df, use_container_width=True)


elif choice == "Patients":
    st.header("Patient Management")
    
    # Query uses the correct table name 'patient' and column names
    patient_query = "SELECT patient_id, patient_name, age, gender, address, phone_number FROM patient;" 
    patients_df = run_query(patient_query)
    
    if not patients_df.empty:
        st.dataframe(patients_df, use_container_width=True)
    else:
        st.info("No patient data available.")


elif choice == "Doctors":
    st.header("Doctor Directory")
    
    # Query uses the correct table name 'doctor' and column names
    doctor_query = "SELECT doctor_id, doctor_name, specialization, email FROM doctor;" 
    doctors_df = run_query(doctor_query)
    
    if not doctors_df.empty:
        st.dataframe(doctors_df, use_container_width=True)
    else:
        st.info("No doctor data available.")


elif choice == "Appointments":
    st.header("All Appointments")
    
    all_appointments_query = """
    SELECT 
        a.appointment_id, 
        p.patient_name,           -- Updated column name
        d.doctor_name,            -- Updated column name
        a.date_of_appointment,    -- Updated column name
        a.patient_case            -- Using 'patient_case' as a status/detail column
    FROM appointment a 
    JOIN patient p ON a.patient_id = p.patient_id
    JOIN doctor d ON a.doctor_id = d.doctor_id
    ORDER BY a.date_of_appointment;
    """
    all_appointments_df = run_query(all_appointments_query)
    
    if not all_appointments_df.empty:
        st.dataframe(all_appointments_df, use_container_width=True)
    else:
        st.info("No appointment data available.")