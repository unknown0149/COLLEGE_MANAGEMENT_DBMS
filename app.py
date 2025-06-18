# app.py
# Your main Flask application, now fully connected to MongoDB.

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson.objectid import ObjectId # Crucial for working with MongoDB's unique IDs
from datetime import date, datetime, timedelta
import os
import json
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import sys
from utils.report_generator import generate_pdf_report, generate_docx_report

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Ensure all paths are absolute
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.secret_key = os.getenv('FLASK_SECRET_KEY')
if not app.secret_key:
    print("Warning: FLASK_SECRET_KEY not set in .env file. Using default key (not recommended for production).")
    app.secret_key = 'your_super_secret_key'

# --- MongoDB Configuration ---
MONGO_URI = os.getenv('MONGO_URI')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')

# Validate MongoDB settings
if not MONGO_URI:
    print("Error: MONGO_URI not set in .env file")
    sys.exit(1)

if not MONGO_DB_NAME:
    print("Error: MONGO_DB_NAME not set in .env file")
    sys.exit(1)

# Initialize MongoDB connection with error handling
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Validate connection
    client.admin.command('ismaster')
    db = client[MONGO_DB_NAME]
    print(f"Successfully connected to MongoDB database: {MONGO_DB_NAME}")
except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    print(f"Could not connect to MongoDB: {e}")
    sys.exit(1)

# --- Collection References ---
# These variables directly reference your MongoDB collections
teachers_collection = db.teachers
admins_collection = db.admins
classes_collection = db.classes
students_collection = db.students
exams_collection = db.exams
notifications_collection = db.notifications
documents_collection = db.documents
events_collection = db.events
hostels_collection = db.hostels
books_collection = db.books

# --- Upload Folder Configuration ---
UPLOAD_FOLDER = 'static/uploads/documents'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'} # Added image extensions
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Ensure the upload directory exists

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Helper Function to convert ObjectId and Dates for JSON/Templates ---
# MongoDB stores dates as datetime objects, but Flask's Jinja2 templates
# and JSON responses often need them as strings. This function helps.
def serialize_doc(doc):
    if not doc:
        return None
    
    # Create a copy to avoid modifying the original document in the PyMongo cache
    doc_copy = doc.copy() 
    
    # Convert MongoDB's ObjectId to a string for display in templates
    if '_id' in doc_copy:
        doc_copy['_id'] = str(doc_copy['_id'])
    
    # Handle embedded documents (arrays of sub-documents)
    if 'attendance' in doc_copy and isinstance(doc_copy['attendance'], list):
        for item in doc_copy['attendance']:
            if 'class_ref' in item and isinstance(item['class_ref'], ObjectId):
                item['class_ref'] = str(item['class_ref'])
            if 'date' in item and isinstance(item['date'], (date, datetime)):
                item['date'] = item['date']

    if 'grades' in doc_copy and isinstance(doc_copy['grades'], list):
        for item in doc_copy['grades']:
            if 'exam_ref' in item and isinstance(item['exam_ref'], ObjectId):
                item['exam_ref'] = str(item['exam_ref'])
            if 'exam_date' in item and isinstance(item['exam_date'], (date, datetime)):
                item['exam_date'] = item['exam_date'].isoformat()

    if 'fees' in doc_copy and isinstance(doc_copy['fees'], list):
        for item in doc_copy['fees']:
            if 'due_date' in item and isinstance(item['due_date'], (date, datetime)):
                item['due_date'] = item['due_date'].isoformat()
            if 'payment_date' in item and isinstance(item['payment_date'], (date, datetime)):
                item['payment_date'] = item['payment_date'].isoformat()

    if 'book_issues' in doc_copy and isinstance(doc_copy['book_issues'], list):
        for item in doc_copy['book_issues']:
            if 'book_ref' in item and isinstance(item['book_ref'], ObjectId):
                item['book_ref'] = str(item['book_ref'])
            if 'issue_date' in item and isinstance(item['issue_date'], (date, datetime)):
                item['issue_date'] = item['issue_date'].isoformat()
            if 'return_date' in item and isinstance(item['return_date'], (date, datetime)):
                item['return_date'] = item['return_date'].isoformat()

    if 'hostel_allocation' in doc_copy and isinstance(doc_copy['hostel_allocation'], dict):
        if 'hostel_ref' in doc_copy['hostel_allocation'] and isinstance(doc_copy['hostel_allocation']['hostel_ref'], ObjectId):
            doc_copy['hostel_allocation']['hostel_ref'] = str(doc_copy['hostel_allocation']['hostel_ref'])
        if 'allocation_date' in doc_copy['hostel_allocation'] and isinstance(doc_copy['hostel_allocation']['allocation_date'], (date, datetime)):
            doc_copy['hostel_allocation']['allocation_date'] = doc_copy['hostel_allocation']['allocation_date'].isoformat()
        if 'release_date' in doc_copy['hostel_allocation'] and isinstance(doc_copy['hostel_allocation']['release_date'], (date, datetime)):
            doc_copy['hostel_allocation']['release_date'] = doc_copy['hostel_allocation']['release_date'].isoformat()

    # Handle direct ObjectId references and dates in the main document
    if 'teacher_ref' in doc_copy and isinstance(doc_copy['teacher_ref'], ObjectId):
        doc_copy['teacher_ref'] = str(doc_copy['teacher_ref'])
    if 'class_ref' in doc_copy and isinstance(doc_copy['class_ref'], ObjectId):
        doc_copy['class_ref'] = str(doc_copy['class_ref'])
    if 'uploader_ref' in doc_copy and isinstance(doc_copy['uploader_ref'], ObjectId):
        doc_copy['uploader_ref'] = str(doc_copy['uploader_ref'])
    
    # Dates
    for date_field in ['class_date', 'created_at', 'upload_date', 'event_date', 'exam_date',
                       'due_date', 'payment_date', 'start_date', 'end_date', 'updated_at']:
        if date_field in doc_copy and isinstance(doc_copy[date_field], (date, datetime)):
            doc_copy[date_field] = doc_copy[date_field].isoformat()

    return doc_copy

# --- Routes ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        role = request.form['role']

        user = None
        try:
            if role == 'teacher':
                user = teachers_collection.find_one({'username': username, 'password': password})
                if user:
                    session['loggedin'] = True
                    session['username'] = user['username']
                    session['role'] = 'teacher'
                    session['user_mongo_id'] = str(user['_id'])
                    return redirect('/teacher/dashboard')
                else:
                    error = 'Invalid teacher credentials.'
            elif role == 'admin':
                user = admins_collection.find_one({'username': username, 'password': password})
                if user:
                    session['loggedin'] = True
                    session['username'] = user['username']
                    session['role'] = 'admin'
                    session['user_mongo_id'] = str(user['_id'])
                    return redirect('/admin/admin_dashboard')
                else:
                    error = 'Invalid admin credentials'
            elif role == 'student':
                try:
                    student_id_int = int(username) # MySQL's student_id is an integer
                except ValueError:
                    error = 'Student ID must be a number'
                    return render_template('login.html', error=error)
                
                # Check against 'old_student_id' which stores the MySQL ID
                user = students_collection.find_one({'old_student_id': student_id_int, 'phone': password})
                
                if user:
                    session['loggedin'] = True
                    session['username'] = user['old_student_id'] # Keep old_student_id as username for consistency
                    session['role'] = 'student'
                    session['user_mongo_id'] = str(user['_id']) # Store MongoDB's actual _id
                    return redirect('/student/dashboard')
                else:
                    error = 'Invalid student credentials.'
        except Exception as e:
            error = f"Database error: {e}"
        return render_template('login.html', error=error)
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form['username'].strip()
        name = request.form['name'].strip()
        password = request.form['password'].strip()
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()
        
        existing_user = teachers_collection.find_one({'username': username})
        if existing_user:
            error_message = "Username already exists. Please choose a different one."
            return render_template('teacher_registration.html', error=error_message)
        
        new_teacher = {
            "username": username,
            "teacher_name": name,
            "password": password,
            "email": email,
            "phone": phone
        }
        teachers_collection.insert_one(new_teacher)
        flash("Teacher successfully registered.", 'success')
        return redirect(url_for('register')) # Redirect to GET request to clear form
    return render_template('teacher_registration.html')

@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == "POST":
        try:
            student_id_int = int(request.form['student_id']) # MySQL's student_id
        except ValueError:
            flash("Student ID must be a number.", 'danger')
            return render_template('student_registration.html')
            
        name = request.form['name'].strip()
        class_sec = request.form['class_sec'].strip()
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()

        existing_student = students_collection.find_one({'old_student_id': student_id_int})
        if existing_student:
            error_message = "Student ID already exists. Please use a different one."
            return render_template('student_registration.html', error=error_message)
        
        new_student = {
            "old_student_id": student_id_int, # Keep for compatibility with old login
            "student_name": name,
            "class_sec": class_sec,
            "email": email,
            "phone": phone,
            "attendance": [], # Initialize as empty arrays/documents for embedded data
            "grades": [],
            "fees": [],
            "book_issues": [],
            "hostel_allocation": None 
        }
        students_collection.insert_one(new_student)
        flash("Student successfully registered.", 'success')
        return redirect(url_for('student_register'))
    return render_template('student_registration.html')

@app.route('/get_student',methods=['POST','GET'])
def get_student():
    if request.method=='POST':
        student_id_str = request.form['student_id'].strip()
        try:
            student_id_int = int(student_id_str)
        except ValueError:
            flash("Student ID must be a number.", 'danger')
            return render_template('update_student.html')
        
        # Find student by old_student_id (MySQL ID)
        student = students_collection.find_one({'old_student_id': student_id_int})
        
        if student:
            # Serialize the document for template rendering
            student_data = serialize_doc(student)
            flash("Fetched student details", 'success')
            return render_template('update_student.html', student=student_data)
        else:
            flash(f"Student with ID {student_id_int} not found.", 'danger')
            return render_template('update_student.html')
    return render_template('update_student.html') 

@app.route('/update_student', methods=['POST'])
def update_student():
    if request.method == 'POST':
        student_id_str = request.form['student_id'].strip()
        new_name = request.form['new_name'].strip()
        new_email = request.form['new_email'].strip()
        new_phone = request.form['new_phone'].strip()
        
        try:
            student_id_int = int(student_id_str)
        except ValueError:
            flash("Student ID must be a number.", 'danger')
            return redirect(url_for('get_student')) # Redirect back to get_student to re-fetch
        
        # Find student by old_student_id (MySQL ID)
        student = students_collection.find_one({'old_student_id': student_id_int})
        
        if student:
            students_collection.update_one(
                {'old_student_id': student_id_int}, # Filter by the old_student_id
                {'$set': {
                    "student_name": new_name,
                    "email": new_email,
                    "phone": new_phone
                }}
            )
            # Fetch the updated student to display current info
            updated_student = students_collection.find_one({'old_student_id': student_id_int})
            flash(f"Student ID {student_id_int} details have been successfully updated.", 'success')
            return render_template('update_student.html', student=serialize_doc(updated_student))
        else:
            flash(f"Student with ID {student_id_int} not found.", 'danger')
            return redirect(url_for('get_student'))

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'loggedin' in session and session['role'] == 'teacher':
        teacher_username = session['username']
        # Find classes taught by this teacher by referencing the teacher's MongoDB _id
        teacher_doc = teachers_collection.find_one({'username': teacher_username})
        
        if not teacher_doc:
            flash("Teacher not found.", 'danger')
            return redirect(url_for('login'))

        teacher_mongo_id = teacher_doc['_id']
        
        # Find classes where teacher_ref matches the teacher's _id
        classes = list(classes_collection.find({'teacher_ref': teacher_mongo_id}))
          # Get upcoming events for teachers
        current_date = datetime.now()
        events_query = {
            'event_date': {'$gte': current_date},
            'is_active': True,
            '$or': [
                {'target_role': 'all'},
                {'target_role': 'teacher'}
            ]
        }
        events = list(events_collection.find(events_query).sort('event_date', 1).limit(5))
        
        # Prepare data for template
        classes = [serialize_doc(cls) for cls in classes]
        events = [
            {
                'title': e['title'],
                'date': e['event_date'].strftime('%Y-%m-%d'),
                'description': e['description']
            }
            for e in events
        ]

        return render_template('teacher_dashboard.html', 
                             username=teacher_username, 
                             classes=classes,
                             events=events)
    else:
        return redirect(url_for('login'))

@app.route('/teacher/classes')
def teacher_classes():
    if 'loggedin' in session and session['role'] == 'teacher':
        teacher_username = session['username']
        teacher_doc = teachers_collection.find_one({'username': teacher_username})
        if not teacher_doc:
            flash("Teacher not found.", 'danger')
            return redirect(url_for('login'))
        teacher_mongo_id = teacher_doc['_id']
        classes = list(classes_collection.find({'teacher_ref': teacher_mongo_id}))
        classes = [serialize_doc(cls) for cls in classes]
        return render_template('teacher_classes.html', username=teacher_username, classes=classes)
    else:
        return redirect(url_for('login'))

@app.route('/teacher/add_class', methods=['GET', 'POST'])
def add_class():
    if 'loggedin' in session and session['role'] == 'teacher':
        if request.method == 'POST':
            class_name = request.form['class_name'].strip()
            teacher_username = session['username']
            
            teacher_doc = teachers_collection.find_one({'username': teacher_username})
            if not teacher_doc:
                flash("Teacher not found.", 'danger')
                return redirect(url_for('login'))

            teacher_mongo_id = teacher_doc['_id'] # Get the MongoDB _id of the teacher

            new_class = {
                "class_name": class_name,
                "teacher_ref": teacher_mongo_id, # Store reference to teacher's _id
                "class_date": datetime.now(), # Or allow teacher to input
                "description": request.form.get('description', '').strip()
            }
            classes_collection.insert_one(new_class)
            flash('Class added successfully!', 'success')
            return redirect(url_for('teacher_dashboard'))
        return render_template('add_class.html')
    else:
        return redirect(url_for('login'))

@app.route('/teacher/view_class/<class_id>')
def view_class(class_id):
    if 'loggedin' in session and session['role'] == 'teacher':
        try:
            class_doc = classes_collection.find_one({'_id': ObjectId(class_id)})
            if not class_doc:
                flash("Class not found.", 'danger')
                return redirect(url_for('teacher_dashboard'))

            # Get students who belong to this class section
            class_name = class_doc.get('class_name', '')
            students = list(students_collection.find({'class_sec': class_name}))
            
            # Get attendance records for display
            students_with_attendance = []
            for student in students:
                attendance_records = []
                if 'attendance' in student:
                    # Filter attendance records for this class
                    attendance_records = [
                        record for record in student['attendance'] 
                        if record.get('class_ref') == ObjectId(class_id)
                    ]
                    # Sort by date
                    attendance_records.sort(key=lambda x: x['date'], reverse=True)
                
                student_data = serialize_doc(student)
                student_data['attendance_records'] = attendance_records
                students_with_attendance.append(student_data)

            return render_template('view_class.html', 
                                 class_data=serialize_doc(class_doc), 
                                 students=students_with_attendance)
        except Exception as e:
            flash(f"Error: {str(e)}", 'danger')
            return redirect(url_for('teacher_dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/teacher/mark_attendance/<class_id>', methods=['GET', 'POST'])
def mark_attendance(class_id):
    if 'loggedin' in session and session['role'] == 'teacher':
        try:
            class_doc = classes_collection.find_one({'_id': ObjectId(class_id)})
            if not class_doc:
                flash("Class not found.", 'danger')
                return redirect(url_for('teacher_dashboard'))

            if request.method == 'POST':
                attendance_date_str = request.form.get('attendance_date')
                try:
                    attendance_date = datetime.strptime(attendance_date_str, '%Y-%m-%d')
                except ValueError:
                    flash("Invalid date format. Please use YYYY-MM-DD.", 'danger')
                    return redirect(url_for('mark_attendance', class_id=class_id))

                # Get all students in this class section
                class_name = class_doc.get('class_name', '')
                students = list(students_collection.find({'class_sec': class_name}))
                
                for student in students:
                    status_key = f"status_{student['_id']}"
                    if status_key in request.form:
                        status = request.form[status_key]
                        
                        # Prepare attendance record
                        new_attendance_record = {
                            "date": attendance_date,
                            "status": status,
                            "class_ref": ObjectId(class_id)
                        }
                        
                        # First, try to update existing record if it exists
                        result = students_collection.update_one(
                            {
                                '_id': student['_id'],
                                'attendance': {
                                    '$elemMatch': {
                                        'date': attendance_date,
                                        'class_ref': ObjectId(class_id)
                                    }
                                }
                            },
                            {'$set': {'attendance.$.status': status}}
                        )

                        # If no existing record was updated, insert new one
                        if result.modified_count == 0:
                            students_collection.update_one(
                                {'_id': student['_id']},
                                {'$push': {'attendance': new_attendance_record}}
                            )
                
                flash('Attendance marked successfully!', 'success')
                return redirect(url_for('view_class', class_id=class_id))

            # GET request: Display students for attendance marking
            class_name = class_doc.get('class_name', '')
            students = list(students_collection.find({'class_sec': class_name}))
            today = datetime.now().date()
            for student in students:
                if 'attendance' in student:
                    today_record = next(
                        (record for record in student['attendance']
                         if record.get('date').date() == today and 
                         record.get('class_ref') == ObjectId(class_id)),
                        None
                    )
                    if today_record:
                        student['today_status'] = today_record['status']

            return render_template('mark_attendance.html', 
                                 class_data=serialize_doc(class_doc), 
                                 students=[serialize_doc(s) for s in students],
                                 today_date=datetime.now().strftime('%Y-%m-%d'))

        except Exception as e:
            flash(f"Error: {str(e)}", 'danger')
            return redirect(url_for('teacher_dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/teacher/add_exam', methods=['GET', 'POST'])
def add_exam():
    if 'loggedin' in session and session['role'] == 'teacher':
        teacher_username = session['username']
        teacher_doc = teachers_collection.find_one({'username': teacher_username})
        if not teacher_doc:
            flash("Teacher not found.", 'danger')
            return redirect(url_for('login'))
        
        teacher_mongo_id = teacher_doc['_id']

        if request.method == 'POST':
            exam_name = request.form['exam_name'].strip()
            exam_date_str = request.form['exam_date']
            class_sec = request.form['class_sec'].strip()
            subject = request.form['subject'].strip()

            try:
                exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d')
            except ValueError:
                flash("Invalid date format. Please use YYYY-MM-DD.", 'danger')
                return render_template('add_exam.html')
            
            new_exam = {
                "exam_name": exam_name,
                "exam_date": exam_date,
                "class_sec": class_sec,
                "subject": subject,
                "teacher_ref": teacher_mongo_id # Link exam to the teacher who added it
            }
            exams_collection.insert_one(new_exam)
            flash('Exam added successfully!', 'success')
            return redirect(url_for('add_exam'))
        
        return render_template('add_exam.html')
    else:
        return redirect(url_for('login'))

@app.route('/teacher/view_exams')
def view_exams():
    if 'loggedin' in session and session['role'] == 'teacher':
        teacher_username = session['username']
        teacher_doc = teachers_collection.find_one({'username': teacher_username})
        if not teacher_doc:
            flash("Teacher not found.", 'danger')
            return redirect(url_for('login'))
        
        teacher_mongo_id = teacher_doc['_id']
        
        # Fetch exams linked to this teacher
        exams = list(exams_collection.find({'teacher_ref': teacher_mongo_id}).sort('exam_date', -1))
        exams = [serialize_doc(exam) for exam in exams]
        return render_template('view_exams.html', exams=exams)
    else:
        return redirect(url_for('login'))

@app.route('/teacher/enter_grades/<exam_id>', methods=['GET', 'POST'])
def enter_grades(exam_id):
    if 'loggedin' in session and session['role'] == 'teacher':
        try:
            exam_obj_id = ObjectId(exam_id)
            exam = exams_collection.find_one({'_id': exam_obj_id})
            if not exam:
                flash("Exam not found.", 'danger')
                return redirect(url_for('view_exams'))

            # Fetch students belonging to the class_sec for this exam
            students_in_class = list(students_collection.find({'class_sec': exam['class_sec']}))
            students_in_class = [serialize_doc(s) for s in students_in_class]

            if request.method == 'POST':
                for student_id_str, grade_str in request.form.items():
                    if student_id_str.startswith('grade_'):
                        student_mongo_id = ObjectId(student_id_str.replace('grade_', ''))
                        try:
                            grade = float(grade_str) if grade_str else None
                            if grade is not None:
                                if grade < 0 or grade > 100:
                                    flash(f"Invalid grade value for a student. Grade must be between 0 and 100.", 'warning')
                                    continue
                                    
                                # Calculate letter grade based on marks
                                letter_grade = 'F'
                                if grade >= 90:
                                    letter_grade = 'A+'
                                elif grade >= 80:
                                    letter_grade = 'A'
                                elif grade >= 70:
                                    letter_grade = 'B+'
                                elif grade >= 60:
                                    letter_grade = 'B'
                                elif grade >= 50:
                                    letter_grade = 'C'

                                new_grade_record = {
                                    "exam_ref": exam_obj_id,
                                    "exam_name": exam['exam_name'],
                                    "exam_date": exam['exam_date'],
                                    "subject": exam['subject'],
                                    "grade": letter_grade,
                                    "marks": grade
                                }

                                # Update existing grade or add new one
                                result = students_collection.update_one(
                                    {
                                        '_id': student_mongo_id,
                                        'grades': {
                                            '$elemMatch': {
                                                'exam_ref': exam_obj_id
                                            }
                                        }
                                    },
                                    {'$set': {'grades.$': new_grade_record}}
                                )

                                # If no existing grade was updated, add new one
                                if result.modified_count == 0:
                                    students_collection.update_one(
                                        {'_id': student_mongo_id},
                                        {'$push': {'grades': new_grade_record}}
                                    )

                        except ValueError:
                            flash(f"Invalid grade format. Grade must be a number.", 'warning')
                            continue

                flash("Grades entered successfully!", 'success')
                return redirect(url_for('view_exams'))
            
            # Get existing grades for all students
            for student in students_in_class:
                if 'grades' in student:
                    existing_grade = next(
                        (grade for grade in student['grades'] 
                         if str(grade.get('exam_ref')) == exam_id),
                        None
                    )
                    student['current_grade'] = existing_grade['grade'] if existing_grade else None
                else:
                    student['current_grade'] = None

            return render_template('enter_grades.html', exam=serialize_doc(exam), students=students_in_class)
            
        except Exception as e:
            flash(f"Error: {str(e)}", 'danger')
            return redirect(url_for('view_exams'))
    else:
        return redirect(url_for('login'))

@app.route('/teacher/upload_document', methods=['GET', 'POST'])
def upload_document():
    if 'loggedin' in session and session['role'] == 'teacher':
        if request.method == 'POST':
            # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part', 'danger')
                return redirect(request.url)
            file = request.files['file']
            # if user does not select file, browser also submit an empty part without filename
            if file.filename == '':
                flash('No selected file', 'danger')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                uploader_username = session['username']
                uploader_doc = teachers_collection.find_one({'username': uploader_username})
                if not uploader_doc:
                    flash("Uploader not found.", 'danger')
                    return redirect(url_for('login'))
                
                uploader_mongo_id = uploader_doc['_id']

                new_document = {
                    "document_name": filename,
                    "file_path": os.path.join('uploads/documents', filename), # Store relative path for template
                    "upload_date": datetime.now(),
                    "uploader_ref": uploader_mongo_id, # Link to the teacher's _id
                    "description": request.form.get('description', '').strip()
                }
                documents_collection.insert_one(new_document)
                flash('Document uploaded successfully!', 'success')
                return redirect(url_for('upload_document'))
            else:
                flash('Allowed file types are pdf, doc, docx, txt, jpg, jpeg, png', 'danger')
                return redirect(request.url)
        return render_template('upload_document.html')
    else:
        return redirect(url_for('login'))

@app.route('/teacher/view_documents')
def view_documents():
    if 'loggedin' in session and session['role'] == 'teacher':
        teacher_username = session['username']
        teacher_doc = teachers_collection.find_one({'username': teacher_username})
        if not teacher_doc:
            flash("Teacher not found.", 'danger')
            return redirect(url_for('login'))
        
        teacher_mongo_id = teacher_doc['_id']
        
        # Only show documents uploaded by the current teacher
        documents = list(documents_collection.find({'uploader_ref': teacher_mongo_id}).sort('upload_date', -1))
        documents = [serialize_doc(doc) for doc in documents]
        return render_template('view_documents.html', documents=documents)
    else:
        return redirect(url_for('login'))

# --- Admin Routes ---

@app.route('/admin/admin_dashboard')
def admin_dashboard():
    if 'loggedin' in session and session['role'] == 'admin':
        total_teachers = teachers_collection.count_documents({})
        total_students = students_collection.count_documents({})
        total_classes = classes_collection.count_documents({})
        total_exams = exams_collection.count_documents({})
        total_notifications = notifications_collection.count_documents({})
        total_documents = documents_collection.count_documents({})
        total_events = events_collection.count_documents({})
        total_hostels = hostels_collection.count_documents({})
        total_books = books_collection.count_documents({})
        return render_template('admin_dashboard.html',
                               username=session['username'],
                               total_teachers=total_teachers,
                               total_students=total_students,
                               total_classes=total_classes,
                               total_exams=total_exams,
                               total_notifications=total_notifications,
                               total_documents=total_documents,
                               total_events=total_events,
                               total_hostels=total_hostels,
                               total_books=total_books)
    else:
        return redirect(url_for('login'))

@app.route('/admin/view_teachers')
def view_teachers():
    if 'loggedin' in session and session['role'] == 'admin':
        teachers = list(teachers_collection.find({}))
        teachers = [serialize_doc(t) for t in teachers]
        return render_template('view_teachers.html', teachers=teachers)
    else:
        return redirect(url_for('login'))

@app.route('/admin/view_students')
def view_students():
    if 'loggedin' in session and session['role'] == 'admin':
        students = list(students_collection.find({}))
        students = [serialize_doc(s) for s in students]
        return render_template('view_students.html', students=students)
    else:
        return redirect(url_for('login'))

@app.route('/admin/view_classes')
def admin_view_classes():
    if 'loggedin' in session and session['role'] == 'admin':
        classes_data = list(classes_collection.find({}))
        for cls in classes_data:
            if 'teacher_ref' in cls and isinstance(cls['teacher_ref'], ObjectId):
                teacher = teachers_collection.find_one({'_id': cls['teacher_ref']})
                if teacher:
                    cls['teacher_name'] = teacher.get('teacher_name', 'Unknown')
            else:
                cls['teacher_name'] = 'No Teacher Assigned'
                
        classes_data = [serialize_doc(cls) for cls in classes_data]
        return render_template('admin_view_classes.html', classes=classes_data)
    else:
        return redirect(url_for('login'))

@app.route('/admin/view_all_exams')
def admin_view_all_exams():
    if 'loggedin' in session and session['role'] == 'admin':
        exams = list(exams_collection.find({}))
        for exam in exams:
            if 'teacher_ref' in exam and isinstance(exam['teacher_ref'], ObjectId):
                teacher = teachers_collection.find_one({'_id': exam['teacher_ref']})
                if teacher:
                    exam['teacher_name'] = teacher.get('teacher_name', 'Unknown')
            else:
                exam['teacher_name'] = 'No Teacher Assigned'
                
        exams = [serialize_doc(exam) for exam in exams]
        return render_template('admin_view_all_exams.html', exams=exams)
    else:
        return redirect(url_for('login'))



@app.route('/admin/view_notifications')
def admin_view_notifications():
    if 'loggedin' in session and session['role'] == 'admin':
        notifications = list(notifications_collection.find({}).sort('created_at', -1))
        notifications = [serialize_doc(n) for n in notifications]
        return render_template('admin_view_notifications.html', notifications=notifications)
    else:
        return redirect(url_for('login'))

@app.route('/admin/notification/edit/<notification_id>', methods=['POST'])
def admin_edit_notification(notification_id):
    if 'loggedin' in session and session['role'] == 'admin':
        try:
            title = request.form.get('title')
            message = request.form.get('message')
            target_role = request.form.get('target_role', 'all')
            
            notifications_collection.update_one(
                {'_id': ObjectId(notification_id)},
                {
                    '$set': {
                        'title': title,
                        'message': message,
                        'target_role': target_role,
                        'updated_at': datetime.now()
                    }
                }
            )
            flash('Notification updated successfully!', 'success')
        except Exception as e:
            flash(f'Error updating notification: {str(e)}', 'danger')
        
        return redirect(url_for('admin_view_notifications'))
    return redirect(url_for('login'))

@app.route('/admin/notification/delete/<notification_id>', methods=['POST'])
def admin_delete_notification(notification_id):
    if 'loggedin' in session and session['role'] == 'admin':
        try:
            notifications_collection.delete_one({'_id': ObjectId(notification_id)})
            flash('Notification deleted successfully!', 'success')
        except Exception as e:
            flash(f'Error deleting notification: {str(e)}', 'danger')
        
        return redirect(url_for('admin_view_notifications'))
    return redirect(url_for('login'))

@app.route('/admin/add_notification', methods=['GET', 'POST'])
def admin_add_notification():
    if 'loggedin' in session and session['role'] == 'admin':
        if request.method == 'POST':
            title = request.form.get('title')
            message = request.form.get('message')
            target_role = request.form.get('target_role', 'all')
            
            new_notification = {
                'title': title,
                'message': message,
                'target_role': target_role,
                'created_at': datetime.now(),
                'is_active': True
            }
            
            notifications_collection.insert_one(new_notification)
            flash('Notification added successfully!', 'success')
            return redirect(url_for('admin_view_notifications'))
            
        return render_template('add_notification.html')
    return redirect(url_for('login'))

@app.route('/admin/manage_hostels', methods=['GET', 'POST'])
def manage_hostels():
    if 'loggedin' in session and session['role'] == 'admin':
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'add':
                hostel_name = request.form.get('hostel_name')
                total_rooms = int(request.form.get('total_rooms', 0))
                room_capacity = int(request.form.get('room_capacity', 0))
                
                new_hostel = {
                    'hostel_name': hostel_name,
                    'total_rooms': total_rooms,
                    'room_capacity': room_capacity,
                    'available_rooms': total_rooms,
                    'created_at': datetime.now()
                }
                hostels_collection.insert_one(new_hostel)
                flash('Hostel added successfully!', 'success')
                
            elif action == 'edit':
                hostel_id = request.form.get('hostel_id')
                hostel_name = request.form.get('hostel_name')
                total_rooms = int(request.form.get('total_rooms', 0))
                room_capacity = int(request.form.get('room_capacity', 0))
                
                hostels_collection.update_one(
                    {'_id': ObjectId(hostel_id)},
                    {
                        '$set': {
                            'hostel_name': hostel_name,
                            'total_rooms': total_rooms,
                            'room_capacity': room_capacity,
                            'updated_at': datetime.now()
                        }
                    }
                )
                flash('Hostel updated successfully!', 'success')
                
            elif action == 'delete':
                hostel_id = request.form.get('hostel_id')
                hostels_collection.delete_one({'_id': ObjectId(hostel_id)})
                flash('Hostel deleted successfully!', 'success')
                
        hostels = list(hostels_collection.find())
        return render_template('manage_hostels.html', hostels=[serialize_doc(h) for h in hostels])
    else:
        return redirect(url_for('login'))

@app.route('/admin/manage_library', methods=['GET', 'POST'])
def manage_library():
    if 'loggedin' in session and session['role'] == 'admin':
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'add':
                book_title = request.form.get('book_title')
                author = request.form.get('author')
                isbn = request.form.get('isbn')
                copies = int(request.form.get('copies', 1))
                
                new_book = {
                    'title': book_title,
                    'author': author,
                    'isbn': isbn,
                    'total_copies': copies,
                    'available_copies': copies,
                    'added_date': datetime.now()
                }
                books_collection.insert_one(new_book)
                flash('Book added successfully!', 'success')
                
            elif action == 'edit':
                book_id = request.form.get('book_id')
                book_title = request.form.get('book_title')
                author = request.form.get('author')
                isbn = request.form.get('isbn')
                copies = int(request.form.get('copies', 1))
                
                books_collection.update_one(
                    {'_id': ObjectId(book_id)},
                    {
                        '$set': {
                            'title': book_title,
                            'author': author,
                            'isbn': isbn,
                            'total_copies': copies,
                            'updated_at': datetime.now()
                        }
                    }
                )
                flash('Book updated successfully!', 'success')
                
            elif action == 'delete':
                book_id = request.form.get('book_id')
                books_collection.delete_one({'_id': ObjectId(book_id)})
                flash('Book deleted successfully!', 'success')
                
        books = list(books_collection.find())
        return render_template('manage_library.html', books=[serialize_doc(b) for b in books])
    else:
        return redirect(url_for('login'))

@app.route('/admin/exams', methods=['GET', 'POST'])
def admin_exams():
    if 'loggedin' in session and session['role'] == 'admin':
        if request.method == 'POST':
            class_id = request.form.get('class_id')
            exam_name = request.form.get('exam_name')
            exam_date_str = request.form.get('exam_date')
            subject = request.form.get('subject')

            if not all([class_id, exam_name, exam_date_str, subject]):
                flash('All fields are required', 'danger')
                return redirect(url_for('admin_exams'))

            try:
                exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d')
                
                # Get class info
                class_info = list(students_collection.distinct('class_sec'))
                if not class_info:
                    flash('No classes found', 'danger')
                    return redirect(url_for('admin_exams'))

                new_exam = {
                    "exam_name": exam_name,
                    "exam_date": exam_date,
                    "class_sec": class_id,
                    "subject": subject
                }

                exams_collection.insert_one(new_exam)
                flash('Exam created successfully', 'success')
                return redirect(url_for('admin_exams'))
            except Exception as e:
                flash(f'Error creating exam: {str(e)}', 'danger')
                return redirect(url_for('admin_exams'))

        # GET request - fetch classes and exams
        classes = list(students_collection.distinct('class_sec'))
        exams = list(exams_collection.find({}).sort('exam_date', -1))
        
        # Add class name to each exam
        for exam in exams:
            exam['class_name'] = exam.get('class_sec', 'Unknown Class')

        return render_template('admin_exams.html',
                             classes=classes,
                             exams=[serialize_doc(e) for e in exams])
    else:
        return redirect(url_for('login'))

@app.route('/admin/grades', methods=['GET', 'POST'])
def admin_grades():
    if 'loggedin' in session and session['role'] == 'admin':
        if request.method == 'POST':
            student_id = request.form.get('student_id')
            exam_id = request.form.get('exam_id')
            marks = float(request.form.get('marks'))
            grade = request.form.get('grade')

            if not all([student_id, exam_id, marks, grade]):
                flash('All fields are required', 'danger')
                return redirect(url_for('admin_grades'))

            try:
                # Get student and exam info
                student = students_collection.find_one({'_id': ObjectId(student_id)})
                exam = exams_collection.find_one({'_id': ObjectId(exam_id)})

                if not student or not exam:
                    flash('Student or exam not found', 'danger')
                    return redirect(url_for('admin_grades'))

                # Create new grade record
                new_grade = {
                    'exam_ref': exam['_id'],
                    'exam_name': exam['exam_name'],
                    'exam_date': exam['exam_date'],
                    'subject': exam['subject'],
                    'grade': grade,
                    'marks': marks
                }

                # Update or add the grade
                if 'grades' not in student:
                    students_collection.update_one(
                        {'_id': ObjectId(student_id)},
                        {'$set': {'grades': [new_grade]}})
                else:
                    # Check if grade for this exam exists
                    existing_grade = next(
                        (g for g in student['grades'] if str(g.get('exam_ref')) == exam_id),
                        None
                    )
                    if existing_grade:
                        students_collection.update_one(
                            {
                                '_id': ObjectId(student_id),
                                'grades.exam_ref': ObjectId(exam_id)
                            },
                            {
                                '$set': {
                                    'grades.$.grade': grade,
                                    'grades.$.marks': marks
                                }
                            }
                        )
                    else:
                        students_collection.update_one(
                            {'_id': ObjectId(student_id)},
                            {'$push': {'grades': new_grade}}
                        )

                flash('Grade added/updated successfully', 'success')
                return redirect(url_for('admin_grades'))

            except Exception as e:
                flash(f'Error: {str(e)}', 'danger')
                return redirect(url_for('admin_grades'))

        # GET request handling
        students = list(students_collection.find({}))
        exams = list(exams_collection.find({}))
        
        # Get all grades
        grades_data = []
        for student in students:
            if 'grades' in student:
                for grade in student['grades']:
                    grades_data.append({
                        'student_name': student['student_name'],
                        'exam_name': grade['exam_name'],
                        'grade': grade['grade'],
                        'marks': grade.get('marks', 'N/A'),
                        'grade_id': str(grade.get('exam_ref'))
                    })

        return render_template('admin_grades.html',
                             students=[serialize_doc(s) for s in students],
                             exams=[serialize_doc(e) for e in exams],
                             grades=grades_data)
    else:
        return redirect(url_for('login'))

@app.route('/admin/hostel/allocate', methods=['POST'])
def allocate_room():
    if 'loggedin' in session and session['role'] == 'admin':
        student_id = request.form.get('student_id')
        hostel_id = request.form.get('hostel_id')
        room_number = request.form.get('room_number')
        try:
            student = students_collection.find_one({'_id': ObjectId(student_id)})
            hostel = hostels_collection.find_one({'_id': ObjectId(hostel_id)})
            if student and hostel:
                if hostel['current_occupancy'] < hostel['capacity']:
                    students_collection.update_one(
                        {'_id': ObjectId(student_id)},
                        {'$set': {
                            'hostel_allocation': {
                                'hostel_ref': ObjectId(hostel_id),
                                'room_number': room_number,
                                'allocation_date': datetime.now()
                            }
                        }}
                    )
                    hostels_collection.update_one(
                        {'_id': ObjectId(hostel_id)},
                        {'$inc': {'current_occupancy': 1}}
                    )
                    flash(f"Room {room_number} allocated successfully.", 'success')
                else:
                    flash("Hostel is at full capacity.", 'danger')
            else:
                flash("Student or hostel not found.", 'danger')
        except Exception as e:
            flash(f"Error in allocation: {str(e)}", 'danger')
        return redirect(url_for('manage_hostels'))
    else:
        return redirect(url_for('login'))

@app.route('/admin/hostel/<hostel_id>/allocations')
def view_hostel_allocations(hostel_id):
    if 'loggedin' in session and session['role'] == 'admin':
        try:
            hostel = hostels_collection.find_one({'_id': ObjectId(hostel_id)})
            if not hostel:
                flash("Hostel not found.", 'danger')
                return redirect(url_for('manage_hostels'))
            
            students_allocated = list(students_collection.find(
                {'hostel_allocation.hostel_ref': ObjectId(hostel_id)}
            ))
            students_data = [serialize_doc(s) for s in students_allocated]
            hostel_data = serialize_doc(hostel)
            
            return render_template('hostel_allocations.html', 
                                 hostel=hostel_data, 
                                 students=students_data)
        except Exception as e:
            flash(f"Error: {str(e)}", 'danger')
            return redirect(url_for('manage_hostels'))
    else:
        return redirect(url_for('login'))

@app.route('/admin/events', methods=['GET', 'POST'])
def admin_events():
    if 'loggedin' in session and session['role'] == 'admin':
        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')
            event_date_str = request.form.get('event_date')
            target_role = request.form.get('target_role', 'all')
            
            try:
                event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
                new_event = {
                    'title': title,
                    'description': description,
                    'event_date': event_date,
                    'target_role': target_role,
                    'is_active': True,
                    'created_at': datetime.now()
                }
                events_collection.insert_one(new_event)
                flash('Event added successfully!', 'success')
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD', 'danger')
            
        events = list(events_collection.find().sort('event_date', 1))
        return render_template('admin_events.html', events=[serialize_doc(e) for e in events])
    return redirect(url_for('login'))

@app.route('/admin/fees')
def admin_fees():
    if 'loggedin' in session and session['role'] == 'admin':
        students = list(students_collection.find({'fees': {'$exists': True}}))
        students_data = [serialize_doc(s) for s in students]
        return render_template('admin_fees.html', students=students_data)
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/teacher/profile')
def teacher_profile():
    if 'loggedin' in session and session['role'] == 'teacher':
        teacher_username = session['username']
        teacher = teachers_collection.find_one({'username': teacher_username})
        if teacher:
            return render_template('teacher_profile.html', teacher=serialize_doc(teacher))
    return redirect(url_for('login'))

@app.route('/teacher/view_attendance/<class_id>', methods=['GET', 'POST'])
def view_attendance(class_id):
    if 'loggedin' in session and session['role'] in ['teacher', 'admin']:
        try:
            class_doc = classes_collection.find_one({'_id': ObjectId(class_id)})
            if not class_doc:
                flash("Class not found.", 'danger')
                return redirect(url_for('teacher_dashboard'))

            # Get students in this class
            class_name = class_doc.get('class_name', '')
            students = list(students_collection.find({'class_sec': class_name}))

            # Get all unique dates for this class
            all_dates = set()
            for student in students:
                if 'attendance' in student:
                    for record in student['attendance']:
                        if record.get('class_ref') == ObjectId(class_id):
                            all_dates.add(record['date'].date())
            
            dates = sorted(list(all_dates), reverse=True)
            
            # If no date is selected, use the most recent date
            selected_date = request.form.get('attendance_date')
            if selected_date:
                selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
            elif dates:
                selected_date = dates[0]
            
            attendance_records = []
            if selected_date:
                for student in students:
                    record = {
                        'student_id': student.get('old_student_id', ''),
                        'student_name': student.get('student_name', ''),
                        'status': 'not_marked'
                    }
                    
                    if 'attendance' in student:
                        # Find attendance for selected date
                        attendance = next(
                            (a for a in student['attendance']
                             if a.get('date').date() == selected_date and 
                             a.get('class_ref') == ObjectId(class_id)),
                            None
                        )
                        if attendance:
                            record['status'] = attendance['status']
                    
                    attendance_records.append(record)

            return render_template('view_attendance.html',
                                class_name=class_name,
                                dates=[d.strftime('%Y-%m-%d') for d in dates],
                                selected_date=selected_date.strftime('%Y-%m-%d') if selected_date else None,
                                attendance_records=attendance_records)

        except Exception as e:
            flash(f"Error: {str(e)}", 'danger')
            return redirect(url_for('teacher_dashboard' if session['role'] == 'teacher' else 'admin_dashboard'))
    return redirect(url_for('login'))

@app.route('/admin/view_attendance')
def admin_view_attendance():
    if 'loggedin' in session and session['role'] == 'admin':
        # Get all classes
        classes = list(classes_collection.find())
        classes_data = []
        
        for class_doc in classes:
            class_name = class_doc.get('class_name', '')
            
            # Get students in this class
            students = list(students_collection.find({'class_sec': class_name}))
            
            total_students = len(students)
            total_attendance = 0
            total_present = 0
            
            for student in students:
                if 'attendance' in student:
                    # Count attendance records for this class
                    class_attendance = [
                        record for record in student['attendance']
                        if 'class_ref' in record and record['class_ref'] == class_doc['_id']
                    ]
                    total_attendance += len(class_attendance)
                    total_present += len([
                        record for record in class_attendance
                        if record['status'] == 'present'
                    ])
            
            attendance_percentage = 0
            if total_attendance > 0:
                attendance_percentage = (total_present / total_attendance) * 100
            
            class_data = {
                '_id': class_doc['_id'],
                'class_name': class_name,
                'total_students': total_students,
                'total_attendance': total_attendance,
                'attendance_percentage': round(attendance_percentage, 2)
            }
            classes_data.append(class_data)
            
        return render_template('admin_view_attendance.html', classes=classes_data)
    return redirect(url_for('login'))

@app.route('/student/report', methods=['GET', 'POST'])
def student_report():
    if 'loggedin' in session and session['role'] == 'student':
        if request.method == 'POST':
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                flash("Invalid date format. Please use YYYY-MM-DD.", 'danger')
                return redirect(url_for('student_report'))
            
            student_mongo_id = session['user_mongo_id']
            student = students_collection.find_one({'_id': ObjectId(student_mongo_id)})
            
            if not student:
                flash("Student not found.", 'danger')
                return redirect(url_for('student_dashboard'))
            
            # Filter attendance records within date range
            attendance_records = []
            if 'attendance' in student and isinstance(student['attendance'], list):
                for record in student['attendance']:
                    if start_date.date() <= record['date'].date() <= end_date.date():
                        class_name = 'N/A'
                        if 'class_ref' in record:
                            class_doc = classes_collection.find_one({'_id': record['class_ref']})
                            if class_doc:
                                class_name = class_doc['class_name']
                        
                        attendance_records.append({
                            'date': record['date'].isoformat(),
                            'status': record['status'],
                            'class_name': class_name
                        })
            
            return render_template('attendance_report.html', 
                                 attendance=attendance_records,
                                 start_date=start_date_str,
                                 end_date=end_date_str)
        return render_template('student_attendance.html')
    else:
        return redirect(url_for('login'))

# Admin routes for managing hostels
@app.route('/admin/hostels')
def admin_hostels():
    if 'loggedin' in session and session['role'] == 'admin':
        hostels = list(hostels_collection.find({}))
        hostels = [serialize_doc(h) for h in hostels]
        return render_template('admin_hostels.html', hostels=hostels)
    else:
        return redirect(url_for('login'))

# Admin route for managing documents
@app.route('/admin/documents')
def admin_documents():
    if 'loggedin' in session and session['role'] == 'admin':
        documents = list(documents_collection.find({}).sort('upload_date', -1))
        for doc in documents:
            if 'uploader_ref' in doc and isinstance(doc['uploader_ref'], ObjectId):
                uploader = teachers_collection.find_one({'_id': doc['uploader_ref']})
                if not uploader:
                    uploader = admins_collection.find_one({'_id': doc['uploader_ref']})
                doc['uploader_name'] = uploader['teacher_name'] if uploader and 'teacher_name' in uploader else \
                                    uploader['username'] if uploader and 'username' in uploader else 'N/A'
            else:
                doc['uploader_name'] = 'N/A'
        documents = [serialize_doc(doc) for doc in documents]
        return render_template('admin_documents.html', documents=documents)
    else:
        return redirect(url_for('login'))

# Admin route for managing books/library
@app.route('/admin/books')
def admin_books():
    if 'loggedin' in session and session['role'] == 'admin':
        books = list(books_collection.find({}))
        books = [serialize_doc(b) for b in books]
        students_with_books = list(students_collection.find({'book_issues': {'$exists': True}}))
        students_with_books = [serialize_doc(s) for s in students_with_books]
        return render_template('admin_books.html', 
                             books=books,
                             students_with_books=students_with_books)
    else:
        return redirect(url_for('login'))

# Add this with other student routes
@app.route('/student/dashboard')
def student_dashboard():
    if 'loggedin' in session and session['role'] == 'student':
        student_id = session['user_mongo_id']
        student = students_collection.find_one({'_id': ObjectId(student_id)})
        
        if not student:
            flash("Student not found.", 'danger')
            return redirect(url_for('login'))
        
        # Get recent attendance
        attendance_records = []
        if 'attendance' in student:
            attendance_records = sorted(
                student['attendance'],
                key=lambda x: x['date'],
                reverse=True
            )[:5]
        
        # Get recent grades
        grades = []
        if 'grades' in student:
            grades = sorted(
                student['grades'],
                key=lambda x: x['exam_date'],
                reverse=True
            )
        
        # Get notifications for students
        notifications = list(notifications_collection.find({
            'is_active': True,
            '$or': [
                {'target_role': 'all'},
                {'target_role': 'student'}
            ]
        }).sort('created_at', -1).limit(5))
        
        return render_template('student_dashboard.html',
                             student=serialize_doc(student),
                             attendance=attendance_records,
                             grades=grades,
                             notifications=[serialize_doc(n) for n in notifications])
    else:
        return redirect(url_for('login'))

@app.route('/student/attendance')
def student_attendance():
    if 'loggedin' in session and session['role'] == 'student':
        student_id = session['user_mongo_id']
        student = students_collection.find_one({'_id': ObjectId(student_id)})
        
        if not student:
            flash("Student not found.", 'danger')
            return redirect(url_for('student_dashboard'))
        
        attendance_records = []
        if 'attendance' in student:
            attendance_records = sorted(
                student['attendance'],
                key=lambda x: x['date'],
                reverse=True
            )
            
            # Get class details for each attendance record
            for record in attendance_records:
                if 'class_ref' in record:
                    class_doc = classes_collection.find_one({'_id': record['class_ref']})
                    if class_doc:
                        record['class_name'] = class_doc.get('class_name', 'Unknown Class')
        
        return render_template('student_attendance.html',
                             student=serialize_doc(student),
                             attendance=attendance_records)
    else:
        return redirect(url_for('login'))

@app.route('/student/grades')
def student_grades():
    if 'loggedin' in session and session['role'] == 'student':
        student_id = session['user_mongo_id']
        student = students_collection.find_one({'_id': ObjectId(student_id)})
        
        if not student:
            flash("Student not found.", 'danger')
            return redirect(url_for('student_dashboard'))
        
        grades = []
        if 'grades' in student:
            grades = sorted(
                student['grades'],
                key=lambda x: x['exam_date'],
                reverse=True
            )
        
        return render_template('view_grades.html',
                             student=serialize_doc(student),
                             grades=grades)
    else:
        return redirect(url_for('login'))

@app.route('/student/profile')
def student_profile():
    if 'loggedin' in session and session['role'] == 'student':
        student_id = session['user_mongo_id']
        student = students_collection.find_one({'_id': ObjectId(student_id)})
        
        if not student:
            flash("Student not found.", 'danger')
            return redirect(url_for('student_dashboard'))
        
        return render_template('student_profile.html',
                             student=serialize_doc(student))
    else:
        return redirect(url_for('login'))
@app.route('/notifications', methods=['GET'])
def get_notifications():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    user_role = session['role']
    
    # Query for notifications relevant to the user's role
    query = {
        'is_active': True,
        '$or': [
            {'target_role': 'all'},
            {'target_role': user_role}
        ]
    }
    
    notifications = list(notifications_collection.find(query).sort('created_at', -1).limit(5))
    notifications = [serialize_doc(n) for n in notifications]
    
    return render_template('notifications.html', notifications=notifications)

# --- Debug Routes (Remove in production) ---
@app.route('/debug/create_test_event')
def create_test_event():
    if not app.debug:
        return "Debug routes only available in debug mode", 403
        
    # Create a test event for today
    current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    test_event = {
        "title": "Test Event",
        "description": "This is a test event created for debugging",
        "event_date": current_date,
        "target_role": "student",
        "created_at": datetime.now(),
        "is_active": True
    }
    
    try:
        result = events_collection.insert_one(test_event)
        return {
            "status": "success",
            "message": "Test event created",
            "event_id": str(result.inserted_id)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error creating event: {str(e)}"
        }

@app.route('/debug/list_events')
def list_events():
    if not app.debug:
        return "Debug routes only available in debug mode", 403
        
    current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    events_query = {
        'event_date': {'$gte': current_date},
        '$or': [
            {'target_role': 'all'},
            {'target_role': 'student'}
        ]
    }
    
    try:
        events = list(events_collection.find(events_query))
        return {
            "status": "success",
            "query": events_query,
            "current_date": current_date.isoformat(),
            "event_count": len(events),
            "events": [{
                "id": str(e["_id"]),
                "title": e["title"],
                "date": e["event_date"].isoformat(),
                "target_role": e["target_role"]
            } for e in events]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error listing events: {str(e)}"
        }

if __name__ == '__main__':
    # --- Ensure MongoDB Collection Schema Validation ---
    
    # Students Collection Validation
    student_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["old_student_id", "student_name", "email", "class_sec", "phone"],
            "properties": {
                "old_student_id": {"bsonType": "int"},
                "student_name": {"bsonType": "string"},
                "email": {"bsonType": "string"},
                "class_sec": {"bsonType": "string"},
                "phone": {"bsonType": "string"},
                "attendance": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "required": ["date", "status", "class_ref"],
                        "properties": {
                            "date": {"bsonType": "date"},
                            "status": {"enum": ["present", "absent"]},
                            "class_ref": {"bsonType": "objectId"}
                        }
                    }
                },
                "fees": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "required": ["amount", "due_date", "is_paid"],
                        "properties": {
                            "amount": {"bsonType": "number"},
                            "due_date": {"bsonType": "date"},
                            "is_paid": {"bsonType": "bool"},
                            "payment_date": {"bsonType": "date"}
                        }
                    }
                }
            }
        }
    }

    # Events Collection Validation
    event_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["title", "event_date", "description", "target_role", "created_at"],
            "properties": {
                "title": {"bsonType": "string"},
                "event_date": {"bsonType": "date"},
                "description": {"bsonType": "string"},
                "target_role": {"enum": ["all", "student", "teacher"]},
                "created_at": {"bsonType": "date"},
                "is_active": {"bsonType": "bool"}
            }
        }
    }

    # Notifications Collection Validation
    notification_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["title", "message", "target_role", "created_at", "created_by"],
            "properties": {
                "title": {"bsonType": "string"},
                "message": {"bsonType": "string"},
                "target_role": {"enum": ["all", "student", "teacher"]},
                "created_at": {"bsonType": "date"},
                "created_by": {"bsonType": "objectId"},
                "is_active": {"bsonType": "bool"}
            }
        }
    }

    # Apply validators to collections
    try:
        db.command("collMod", "students", validator=student_validator)
        db.command("collMod", "events", validator=event_validator)
        db.command("collMod", "notifications", validator=notification_validator)
    except Exception as e:
        print(f"Error setting up schema validation: {str(e)}")

    # --- Ensure MongoDB Indices ---
    # These are background operations and safe to run on startup
    try:
        students_collection.create_index("old_student_id", unique=True)
        students_collection.create_index("email", unique=True)
        students_collection.create_index("class_sec")
        students_collection.create_index([("attendance.date", 1), ("attendance.class_ref", 1)])
        
        events_collection.create_index([("event_date", 1), ("target_role", 1)])
        events_collection.create_index("is_active")
        
        notifications_collection.create_index([("created_at", -1), ("target_role", 1)])
        notifications_collection.create_index("is_active")
        
        teachers_collection.create_index("username", unique=True)
        teachers_collection.create_index("email", unique=True)
        
        admins_collection.create_index("username", unique=True)
        
        classes_collection.create_index([("teacher_ref", 1), ("class_name", 1)])

        print("MongoDB schema validation and indices setup complete.")
    except Exception as e:
        print(f"Error setting up indices: {str(e)}")

    try:
        # Run the app with threaded=False to avoid the socket error on Windows
        app.run(threaded=False, debug=True)
    except Exception as e:
        print(f"Error starting app: {str(e)}")