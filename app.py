# Group 6.2
import pandas as pd
import sqlite3
import re
from datetime import datetime
import pytz
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import smtplib  
# Added import for sending emails
import streamlit as st


# Create a SQLite database connection
conn = sqlite3.connect('hsg_reporting.db')
c = conn.cursor()

# Insert correct time zone
st.time_zone = 'Europe/Zurich'

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
        status TEXT DEFAULT 'Pending',
        user_comment TEXT 
    )
''')
conn.commit()

# HSG Logo on top of the page with spaces afterward
image_path = "HSG-logo-new.png"
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
    uploaded_file = st.file_uploader("Upload a photo:", type=["jpg", "jpeg", "png"])

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
    lighting_issues = st.checkbox("Lighting issues")
    sanitary_problems = st.checkbox("Sanitary problems")
    havc_issues = st.checkbox("Heating, ventilation or air conditioning issues")
    cleaning_needs = st.checkbox("Cleaning needs due to heavy soiling")
    network_internet_problems = st.checkbox("Network/internet problems")
    it_equipment = st.checkbox("Issues with/lack of IT equipment")
    
    # Importance dropdown menu
    importance = st.selectbox("Importance:", ['Low', 'Medium', 'High'])
    
    # Comment box
    user_comment = st.text_area("Problem Description:", max_chars=500)

    # When "Submit" button is clicked
    if st.button("Submit"):
        # Checking that at least one issue type is selected
        issue_type_selected = lighting_issues or sanitary_problems or havc_issues or cleaning_needs or network_internet_problems or it_equipment
        # Checking if all required fields are filled out
        all_fields_filled = all([name, hsg_email, room_number, issue_type_selected, user_comment])

        if all_fields_filled and is_valid_email(hsg_email):
            selected_issue_types = []
            if lighting_issues:
                selected_issue_types.append("Lighting issues")
            if sanitary_problems:
                selected_issue_types.append("Sanitary problems")
            if havc_issues:
                selected_issue_types.append("Heating, ventilation or air conditioning issues")
            if cleaning_needs:
                selected_issue_types.append("Cleaning needs due to heavy soiling")
            if network_internet_problems:
                selected_issue_types.append("Network/internet problems")
            if it_equipment:
                selected_issue_types.append("Issues with/lack of IT equipment")
            issue_types = ', '.join(selected_issue_types)

            # Implement 'Europe/Zurich' as the standard time zone for the application
            desired_time_zone = pytz.timezone('Europe/Zurich')

            # Implement datetime.now() with the selected time zone (Zurich)
            submission_time = datetime.now(desired_time_zone).strftime("%Y-%m-%d %H:%M:%S")

            # Import data to the database
            c.execute('''
                INSERT INTO submissions (name, hsg_email, issue_type, room_number, importance, submission_time, user_comment)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, hsg_email, issue_types, room_number, importance, submission_time, user_comment))
            conn.commit()
            st.success("Submission Successful!")
        else:
            # Error if not all fields are filled out
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
        'status': 'STATUS',
        'user_comment': 'PROBLEM DESCRIPTION'
    })

    # Set the index to the issue type
    submitted_data = submitted_data.set_index('issue_type')

    # Drop the 'id' column
    submitted_data = submitted_data.drop(columns=['id'])

    # Display the list of submitted issues
    st.subheader("List of Submitted Issues:")
    st.table(submitted_data)

   # Create a bar chart for the number of issues per issue type
    st.subheader("Number of Issues by Issue Type")
    issue_type_counts = submitted_data.index.value_counts()

    # Set the color to dark green
    color = 'darkgreen'

    fig, ax = plt.subplots()
    shortened_labels = [label[:20] for label in issue_type_counts.index]
    issue_type_counts.plot(kind='bar', ax=ax, color=color)
    ax.set_xticklabels(shortened_labels, rotation=45, ha='right')  # Rotate and align x-axis labels
    ax.set_xlabel("Issue Type")
    ax.set_ylabel("Number of Issues")
    st.pyplot(fig)


    # Create a time series plot for the number of issues submitted per day
    st.subheader("Issues Submitted per Day")
    submitted_data['SUBMITTED AT'] = pd.to_datetime(submitted_data['SUBMITTED AT'])
    submitted_data['Date'] = submitted_data['SUBMITTED AT'].dt.date
    issues_per_day = submitted_data.groupby('Date').size()

    # Set the color to dark green
    color = 'darkgreen'

    fig, ax = plt.subplots()
    ax.bar(issues_per_day.index, issues_per_day.values, width=0.7, align='center', color=color, alpha=0.7)  # Adjusted width and added alpha for transparency
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

    # Adjust spacing between bars
    bar_width = 1  # Adjust the width based on your preference
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))  # Set the interval to control spacing
    ax.xaxis.set_minor_locator(mdates.DayLocator())

    # Rotate the date labels for better readability
    plt.xticks(rotation=45, ha='right')

    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Issues Submitted")
    ax.set_title("Issues Submitted per Day")

    # Add grid lines for better visualization
    ax.grid(axis='y', linestyle='--', alpha=1)

    # Add a background color for better contrast
    ax.set_facecolor('#f0f0f0')  # Light gray background color

    st.pyplot(fig)

    # Create a bar chart for the number of issues per importance level
    st.subheader("Number of Issues by Importance Level")
    importance_counts = submitted_data['IMPORTANCE'].value_counts()

    # Set the color to dark green
    color = 'darkgreen'

    fig, ax = plt.subplots()
    importance_counts.plot(kind='bar', ax=ax, color=color, alpha=1)
    ax.set_xlabel("Importance Level")
    ax.set_ylabel("Number of Issues")
    ax.set_title("Number of Issues by Importance Level")
    st.pyplot(fig)

    # Create a pie chart for the distribution of statuses
    st.subheader("Distribution of Statuses")
    status_counts = submitted_data['STATUS'].value_counts()

    # Set the colors to dark green and a few shades
    colors = ['darkgreen', 'forestgreen', 'limegreen', 'mediumseagreen']

    fig, ax = plt.subplots()
    ax.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', startangle=90, colors=colors, wedgeprops=dict(width=0.3))
    ax.axis('equal')  # Equal aspect ratio ensures the pie chart is circular.
    ax.set_title("Distribution of Statuses")

    # Add a circle in the middle for a donut chart look
    centre_circle = plt.Circle((0,0),0.70,fc='white')
    ax.add_artist(centre_circle)

    # Add a legend for better readability
    ax.legend(status_counts.index, loc='upper right')

    st.pyplot(fig)

# Set a password for accessing the "Overwrite Status" page
correct_password = "Group62"

def overwrite_status():
    st.header("Overwrite Status")

    # Password protection for the "Overwrite Status" page
    entered_password = st.sidebar.text_input("Enter Password", "", type="password")

    if entered_password != correct_password:
        st.warning("Incorrect password. Please enter the correct password to access this page.")
        return

    # Continue with the rest of the function if the correct password is entered
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
        # Implement 'Europe/Zurich' as the standard time zone for the application
        desired_time_zone = pytz.timezone('Europe/Zurich')

        # Implement datetime.now() with the selected time zone (Zurich)
        submission_time = datetime.now(desired_time_zone).strftime("%Y-%m-%d %H:%M:%S")

        # Update the status and timestamp in the database
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
