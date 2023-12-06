# Group 6.2
import streamlit as st
import pandas as pd
import sqlite3
import re
from datetime import datetime
import pytz

# Create a SQLite database connection
conn = sqlite3.connect('hsg_reporting.db')
c = conn.cursor()

# Insert correct time zone


# Create a table to store submitted data
c.execute('''
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        hsg_email TEXT,
        issue_type TEXT,
        room_number TEXT,
        importance TEXT,
        submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'Pending'
    )
''')
conn.commit()

# HSG Logo on top of the page with spaces afterward
image_path = "hsg-logo.png"
st.image(image_path, use_column_width=True)
st.write("")
st.write("")
st.write("")

# Check whether the specified email address is a real HSG mail address
def is_valid_email(hsg_email):
    if hsg_email:
        hsg_email_pattern = r'^[\w.]+@(student\.)?unisg\.ch$'
        match = re.match(hsg_email_pattern, hsg_email)
        return bool(match)
    else:
        return True
        
def submission_form():
    st.header("Submission Form")

    # Get user input for the submission form
    name = st.text_input("Name:")
    hsg_email = st.text_input("HSG Email Address:")

    # Returning an error when the mail address is invalid
    if not is_valid_email(hsg_email):
        st.error("Invalid mail address. Please check that you have entered your HSG mail address correctly.")

    # File uploader for photos
    uploaded_file = st.file_uploader("Upload a photo", type=["jpg", "jpeg", "png"])

    # Display the uploaded folder
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Photo", use_column_with=True)

    # Room number input
    room_number = st.text_input("Room Number:")

    # Maze Map with a focus on the University of St. Gallen
    maze_map_url = "https://use.mazemap.com/embed.html?v=1&zlevel=1&center=9.373611,47.429708&zoom=14.7&campusid=710"
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
    
    #Comment box
    user_comment = st.text_area("Problem Description:", max_chars=500)

    # When "Submit" button is clicked
    if st.button("Submit"):
        # Überprüfung, ob mindestens ein Issue-Typ ausgewählt wurde
        issue_type_selected = it_problem or missing_material or non_functioning_facilities

        # Überprüfung, ob alle erforderlichen Felder ausgefüllt sind (ohne das optionale Foto)
        all_fields_filled = all([name, hsg_email, room_number, issue_type_selected, user_comment])

        if all_fields_filled and is_valid_email(hsg_email):
            selected_issue_types = []
            if it_problem:
                selected_issue_types.append("IT Problem")
            if missing_material:
                selected_issue_types.append("Missing Material")
            if non_functioning_facilities:
                selected_issue_types.append("Non-functioning Facilities")
            issue_types = ', '.join(selected_issue_types)

            # Import data to the database
            c.execute('''
                INSERT INTO submissions (name, hsg_email, issue_type, room_number, importance)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, hsg_email, issue_types, room_number, importance ))
            conn.commit()
            st.success("Submission Successful!")
        else:
            # Fehlermeldung, wenn nicht alle Bedingungen erfüllt sind
            st.error("Please fill in all required fields and select at least one issue type.")

def submitted_issues():
    st.header("Submitted Issues")

    # Retrieve submitted data from the database
    submitted_data = pd.read_sql('SELECT * FROM submissions', conn)

    # Count total issues
    total_issues = len(submitted_data)

    # Display the counter of total issues
    st.subheader(f"Total Issues: {total_issues}")
    
    # Sort the issues by issue type and importance
    submitted_data = submitted_data.sort_values(by=['issue_type', 'importance'], ascending=[True, False])
    # Rename the columns

    # Change column names
    submitted_data = submitted_data.rename(columns={
        'name': 'NAME',
        'hsg_email': 'HSG MAIL ADDRESS',
        'room_number': 'ROOM NR.',
        'importance': 'IMPORTANCE',
        'submission_time': 'SUBMITTED AT',
        'status': 'STATUS'
    })

    # Set the index to the issue type
    submitted_data = submitted_data.set_index('issue_type')

    # Drop the 'id' column
    submitted_data = submitted_data.drop(columns=['id'])

    # Display the list of submitted issues
    st.subheader("List of Submitted Issues:")
    st.table(submitted_data)

def overwrite_status():
    st.header("Overwrite Status")

    # Retrieve submitted data from the database
    submitted_data = pd.read_sql('SELECT * FROM submissions', conn)

    # Check if the DataFrame is empty
    if submitted_data.empty:
        st.subheader("No submitted issues yet.")
        return

    # Display a selection box to choose the issue to update
    selected_issue_id = st.selectbox("Select Issue ID to Overwrite Status:", submitted_data['id'].tolist())

    # Display the details of the selected issue
    selected_issue = submitted_data[submitted_data['id'] == selected_issue_id].iloc[0]
    st.subheader("Selected Issue Details:")
    st.write(selected_issue)

    # Display the status update form
    new_status_options = ['Pending', 'In Progress', 'Resolved']
    new_status = st.selectbox("Select New Status:", new_status_options)

    # When "Update Status" button is clicked
    if st.button("Update Status"):
        # Update the status and timestamp in the database
        submission_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('''
            UPDATE submissions
            SET status = ?, submission_time = ?
            WHERE id = ?
        ''', (new_status, submission_time, selected_issue_id))
        conn.commit()
        st.success("Status Updated Successfully!")

def main():
    st.title("HSG Reporting Tool")

    # Display the pages on the sidebar
    page = st.sidebar.radio("Select Page:", ['Submission Form', 'Submitted Issues', 'Overwrite Status'])

    if page == 'Submission Form':
        submission_form()
    elif page == 'Submitted Issues':
        submitted_issues()
    elif page == 'Overwrite Status':
        overwrite_status()

if __name__ == "__main__":
    main()