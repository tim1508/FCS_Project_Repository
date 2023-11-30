# Group 6.2
import streamlit as st
import pandas as pd
import sqlite3
import re
from PIL import image

# Create a SQLite database connection
conn = sqlite3.connect('hsg_reporting.db')
c = conn.cursor()

# Create a table to store submitted data
c.execute('''
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        hsg_email TEXT,
        issue_type TEXT,
        room_number TEXT,
        importance TEXT
    )
''')
conn.commit()

def submission_form():
    st.header("HSG Reporting Tool - Submission Form")

    # Get user input for the submission form
    name = st.text_input("Name:")
    hsg_email = st.text_input("HSG Email Address:")

    # Check wheter the specified email address is a real hsg mail address
    def is_valid_email(hsg_email):
        hsg_email_pattern = r'^[\w.]+@(student\.)?unisg\.ch$'
        match = re.match(hsg_email_pattern, hsg_email)
        return bool(match)

    # Returning an error when the mail address is invalid
    if not is_valid_email(hsg_email):
        st.error("Invalid mail address. Please check that you have entered your hsg mail address correctly.")
    
    # File uploader for photos
    uploaded_file = st.file_uploader("Upload a photo", type=["jpg", "jpeg", "png"])

    # Display the uploaded foalder
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Photo", use_column_with=True)

    # Room number input
    room_number = st.text_input("Room Number:")

    # Maze Map with a focus on the University of St. Gallen
    maze_map_url = "http://use.mazemap.com/embed.html?v=1&zlevel=1&center=9.373611,47.429708&zoom=14.7&campusid=710"
    st.markdown(f"""
        <iframe src="{maze_map_url}"
            width="100%" height="420" frameborder="0" marginheight="0" marginwidth="0"
            scrolling="no"></iframe>
    """, unsafe_allow_html=True)

    
    # Issue Type checkboxes
    st.subheader("Issue Type:")
    it_problem = st.checkbox("IT Problem")
    missing_material = st.checkbox("Missing Material")
    non_functioning_facilities = st.checkbox("Non-functioning Facilities")

    # Importance dropdown menu
    importance = st.selectbox("Importance:", ['Low', 'Medium', 'High'])
    
    # Wenn der Benutzer auf "Submit" klickt
    if st.button("Submit"):
        selected_issue_types = []
        if it_problem:
            selected_issue_types.append("IT Problem")
        if missing_material:
            selected_issue_types.append("Missing Material")
        if non_functioning_facilities:
            selected_issue_types.append("Non-functioning Facilities")
            issue_types = ', '.join(selected_issue_types)
        
        # Daten in die Datenbank einfügen
            c.execute('''
                INSERT INTO submissions (name, hsg_email, issue_type, room_number, importance)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, hsg_email, issue_types, room_number, importance))
            conn.commit()
            st.success("Submission Successful!")

        if not (name and hsg_email and room_number and importance and (it_problem or missing_material or non_functioning_facilities)):
            st.error("Please fill out all fields before submitting.")
            if not is_valid_email(hsg_email):
                st.error("Invalid mail address. Please enter your HSG-address.")

            else:
                # Determine the selected issue type(s)
                selected_issue_types = []
                if it_problem:
                    selected_issue_types.append("IT Problem")
                if missing_material:
                    selected_issue_types.append("Missing Material")
                if non_functioning_facilities:
                    selected_issue_types.append("Non-functioning Facilities")

            # Insert the submission into the database
                c.execute('''
                    INSERT INTO submissions (name, hsg_email, issue_type, room_number, importance)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, hsg_email, ', '.join(selected_issue_types), room_number, importance))
                conn.commit()
                st.success("Submission Successful!")

        # Insert the submission into the database
        c.execute('''
            INSERT INTO submissions (name, hsg_email, issue_type, room_number, importance)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, hsg_email, ', '.join(selected_issue_types), room_number, importance))
        conn.commit()
        st.success("Submission Successful!")

def submitted_issues():
    st.header("HSG Reporting Tool - Submitted Issues")

    # Retrieve submitted data from the database
    submitted_data = pd.read_sql('SELECT * FROM submissions', conn)

    # Count total issues
    total_issues = len(submitted_data)

    # Display the counter of total issues
    st.subheader(f"Total Issues: {total_issues}")

    # Sort the issues based on importance in descending order
    submitted_data = submitted_data.sort_values(by=['importance'], ascending=False)

    # Display the list of submitted issues
    st.subheader("List of Submitted Issues:")
    st.table(submitted_data)

def main():
    st.title("HSG Reporting Tool")

    # Display the pages on the same page without a sidebar
    page = st.radio("Select Page:", ['Submission Form', 'Submitted Issues'])

    if page == 'Submission Form':
        submission_form()
    elif page == 'Submitted Issues':
        submitted_issues()

if __name__ == "__main__":
    main()
 