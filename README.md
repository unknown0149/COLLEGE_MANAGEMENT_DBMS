# College Management System

The College Management System is a comprehensive software application designed to streamline and automate various administrative tasks in an educational institution. This system provides features for managing students, teachers, attendance, documents, events, fees, and more, making it an all-in-one solution for college administration.

## Features

- **Multi-User Authentication**: Secure login system with different roles for admin, teachers, and students.
- **Student Management**: Complete student lifecycle management including registration, profile updates, and academic tracking.
- **Teacher Management**: Teacher registration, profile management, and class assignment features.
- **Attendance System**: Comprehensive attendance tracking system for teachers to mark and monitor student attendance.
- **Document Management**: Secure storage and management of academic documents and records.
- **Events Management**: Create and manage college events and notifications.
- **Fee Management**: Track and manage student fees and payment records.
- **Library Management**: Digital library system for managing books and resources.
- **Hostel Management**: Features for managing student hostel accommodations.
- **Exam Management**: Tools for scheduling and managing examinations.
- **Grades Management**: System for recording and tracking student academic performance.
- **User-Friendly Interface**: Clean and intuitive interface for all user roles.

## Getting Started

### Prerequisites

- Python 3.8 or higher: Download and install from [python.org](https://python.org)
- MongoDB: Install MongoDB Community Edition from [mongodb.com](https://www.mongodb.com/try/download/community)
- Modern web browser (Chrome, Firefox, Safari, or Edge)

The following Python packages will be installed automatically via requirements.txt:
- Flask: Web framework
- pymongo: MongoDB driver for Python
- python-dotenv: Environment variable management
- Flask-Login: User session management
- Werkzeug: Utilities for WSGI applications

#### Database Configuration
This project uses MongoDB as its database. Make sure you have MongoDB installed and running on your system.

1. Install MongoDB Community Edition from the official website: https://www.mongodb.com/try/download/community
2. Start the MongoDB service
3. The application will automatically create the required collections in the database


### Installation

1. Clone the repository
2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Unix or MacOS:
   source venv/bin/activate
   ```
3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Usage
1. Start MongoDB service on your machine
2. Run the Flask application:
   ```bash
   python app.py
   ```
   or
   ```bash
   flask run
   ```
3. Open your web browser and visit: http://localhost:5000
4. Login with the following default credentials:
   - Admin:
     - Username: admin
     - Password: admin123
   - Teacher/Student: Register through the admin interface

### Working
To provide an overview of the working of the Attendance Monitoring System based on the mentioned requirements, here's a step-by-step explanation:

#### Admin Registration and Student/Teacher Management:
- The admin has the authority to register teachers and students in the system.
- The admin can update student details as necessary, such as personal information, class/section, etc.

#### Teacher Profile and Class Creation:
-A registered teacher can log in and update their own profile information.
-The teacher can create a class by providing inputs such as class/section, subject name, and date.

#### Student Details Management by Admin:
- The admin has the ability to fetch and update student details, such as personal information or class/section assignment.

#### Marking Attendance by Teachers:
- The teacher can access the attendance portal for a specific class/section and date.
- In the attendance portal, the teacher can mark the attendance by checking the checkboxes corresponding to the students who are present.

#### Attendance Submission and Viewing:
- After marking the attendance, the teacher submits the attendance details.
- Both the teacher and the admin can view the attendance records of students.
- The attendance records provide information about the dates, class/section, and the presence or absence of each student.

#### Attendance Status for Any Class/Section:
- The admin has the capability to view the attendance status for any class/section.
- This feature allows the admin to monitor attendance trends and identify any issues or patterns.

The Attendance Monitoring System enables the admin to manage teachers and students, allows teachers to mark attendance for their classes, and provides a centralized platform for viewing and tracking attendance records. This system streamlines the attendance management process, reduces manual effort, and facilitates efficient monitoring of student attendance.




