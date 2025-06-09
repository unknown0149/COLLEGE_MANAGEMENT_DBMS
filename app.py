from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import sqlite3
from datetime import date
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'my_secret_key' #Add your secret key here  
db = mysql.connector.connect(
    host='localhost',
    user='root', # your username here
    password='root', # your password here
    database='attendance_db' # changed from 'test_db' to your actual db name
)

UPLOAD_FOLDER = 'static/uploads/documents'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        cur = db.cursor()
        try:
            if role == 'teacher':
                cur.execute("SELECT * FROM teachers WHERE username = %s AND password = %s", (username, password))
                user = cur.fetchone()
                print("Teacher login:", user)
                if user:
                    session['loggedin'] = True
                    session['username'] = user[0]
                    session['role'] = 'teacher'
                    cur.close()
                    return redirect('/teacher/dashboard')
                else:
                    cur.close()
                    error = 'Invalid teacher credentials.'
                    return render_template('login.html', error=error)
            elif role == 'admin':
                # Debug prints
                print(f"Login attempt - Username: {username}, Password: {password}")
                
                # First check if admin exists
                cur.execute("SELECT * FROM admins")
                all_admins = cur.fetchall()
                print("All admins in database:", all_admins)
                
                # Try login
                cur.execute("SELECT * FROM admins WHERE username = %s AND password = %s", (username, password))
                user = cur.fetchone()
                print("Login query result:", user)
                
                if user:
                    session['loggedin'] = True
                    session['username'] = user[0]
                    session['role'] = 'admin'
                    cur.close()
                    return redirect('/admin/admin_dashboard')
                else:
                    cur.close()
                    error = 'Invalid admin credentials'
                    return render_template('login.html', error=error)
            elif role == 'student':
                try:
                    student_id = int(username)
                except ValueError:
                    cur.close()
                    error = 'Student ID must be a number'
                    return render_template('login.html', error=error)
                # Use student_id and phone for login
                cur.execute("SELECT * FROM students WHERE student_id = %s AND phone = %s", (student_id, password))
                user = cur.fetchone()
                print("Student login:", user)
                if user:
                    session['loggedin'] = True
                    session['username'] = user[0]
                    session['role'] = 'student'
                    cur.close()
                    return redirect('/student/dashboard')
                else:
                    cur.close()
                    error = 'Invalid student credentials.'
                    return render_template('login.html', error=error)
        except Exception as e:
            cur.close()
            error = f"Database error: {e}"
            return render_template('login.html', error=error)
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form['username']
        name = request.form['name']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        cursor = db.cursor()
        query = "SELECT username FROM teachers WHERE username = %s"
        cursor.execute(query, (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            error_message = "Username already exists. Please choose a different one."
            return render_template('teacher_registration.html', error=error_message)
        insert_query = "INSERT INTO teachers (username, teacher_name, password, email, phone) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (username, name, password, email, phone))
        db.commit()
        return render_template('teacher_registration.html', message="Teacher successfully registered.")
    return render_template('teacher_registration.html')

@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == "POST":
        student_id = request.form['student_id']
        name = request.form['name']
        class_sec = request.form['class_sec']
        email = request.form['email']
        phone = request.form['phone']
        cursor = db.cursor()
        query = "SELECT student_id FROM students WHERE student_id = %s"
        cursor.execute(query, (student_id,))
        existing_user = cursor.fetchone()
        if existing_user:
            error_message = "Invalid student_id"
            return render_template('student_registration.html', error=error_message)
        insert_query = "INSERT INTO students (student_id, student_name, class_sec, email, phone) VALUES ( %s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (student_id, name, class_sec, email, phone))
        db.commit()
        return render_template('student_registration.html', message="Student successfully registered.")
    return render_template('student_registration.html')

@app.route('/get_student',methods=['POST','GET'])
def get_student():
    if request.method=='POST':
        student_id=request.form['student_id']
        cur = db.cursor()
        cur.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
        student = cur.fetchone()
        if student:
            message="Fetched student details"
            return render_template('update_student.html', student=student, msg=message)
        else:
            error = "Invalid Student ID"
            return render_template('update_student.html', err=error)
    return render_template('update_student.html') 

@app.route('/update_student', methods=['GET', 'POST'])
def update_student():
    if request.method == 'POST':
        student_id = request.form['student_id']
        new_name = request.form['new_name']
        new_email = request.form['new_email']
        new_phone = request.form['new_phone']
        cur = db.cursor()
        cur.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
        student = cur.fetchone()
        if student:
            cur.execute("UPDATE students SET student_name = %s, email = %s, phone = %s WHERE student_id = %s",(new_name, new_email, new_phone, student_id))
            db.commit()
            message = "Student ID " +str(student_id)+" details have been successfully updated."
            return render_template('update_student.html', student=student, message=message)
        else:
            error = "Invalid Student ID"
            return render_template('update_student.html', error=error)
    return render_template('update_student.html')

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'loggedin' in session and session['role'] == 'teacher':
        cur = db.cursor()
        cur.execute("SELECT * FROM classes WHERE teacher_username = %s", (session['username'],))
        classes = cur.fetchall()
        cur.execute("SELECT event_name, event_date, description FROM events ORDER BY event_date DESC")
        events = cur.fetchall()
        cur.execute("SELECT f.fee_id, s.student_name, f.amount, f.due_date, f.paid FROM fees f JOIN students s ON f.student_id = s.student_id")
        fees = cur.fetchall()
        cur.close()
        return render_template('teacher_dashboard.html', classes=classes, events=events, fees=fees)
    else:
        return redirect('/')
    
@app.route('/teacher/teacher_profile')
def teacher_profile():
    cur = db.cursor()
    cur.execute("SELECT teacher_name, email, phone FROM teachers WHERE username = %s", (session['username'],))
    profile_data = cur.fetchone()
    cur.close()
    return render_template('teacher_profile.html', profile_data=profile_data)

@app.route('/teacher/update_profile', methods=['POST'])
def update_profile():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    cur = db.cursor()
    cur.execute("UPDATE teachers SET teacher_name = %s, email = %s, phone = %s WHERE username = %s",(name, email, phone, session['username']))
    db.commit()
    cur.close()
    return redirect('/teacher/teacher_profile')

# View assigned classes and students
@app.route('/teacher/classes')
def teacher_classes():
    if 'loggedin' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
        
    cur = db.cursor()
    # Get all classes for this teacher
    cur.execute("""
        SELECT c.*, COUNT(s.student_id) as student_count 
        FROM classes c 
        LEFT JOIN students s ON c.class_sec = s.class_sec 
        WHERE c.teacher_username = %s 
        GROUP BY c.class_id
    """, (session['username'],))
    classes = cur.fetchall()
    
    class_students = []
    for c in classes:
        # Get students for each class section
        cur.execute("""
            SELECT student_id, student_name 
            FROM students 
            WHERE class_sec = %s 
            ORDER BY student_name
        """, (c[4],))  # c[4] is class_sec
        students = cur.fetchall()
        class_students.append({'class': c, 'students': students})
    
    cur.close()
    return render_template('teacher_classes.html', class_students=class_students)

@app.route("/teacher/mark_attendance/<int:class_id>", methods=['GET', 'POST'])
def mark_attendance(class_id):
    if 'loggedin' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    cur = db.cursor()
    cur.execute("SELECT class_name, class_sec, class_date FROM classes WHERE class_id = %s", (class_id,))
    class_info = cur.fetchone()
    if not class_info:
        cur.close()
        return "Class not found", 404
    class_name, class_sec, class_date = class_info
    cur.execute("SELECT student_id, student_name FROM students WHERE class_sec = %s", (class_sec,))
    students = cur.fetchall()
    if request.method == 'POST':
        attendance_data = request.form.getlist('attendance')
        cur.execute("DELETE FROM attendance WHERE class_id = %s AND date = %s", (class_id, class_date))
        for student in students:
            status = 'present' if str(student[0]) in attendance_data else 'absent'
            cur.execute("INSERT INTO attendance (class_id, student_id, date, status) VALUES (%s, %s, %s, %s)",
                        (class_id, student[0], class_date, status))
        db.commit()
        cur.close()
        flash('Attendance marked successfully!', 'success')
        return redirect(url_for('mark_attendance', class_id=class_id))
    cur.close()
    return render_template('mark_attendance.html', students=students, class_date=class_date, class_name=class_name, class_sec=class_sec, class_id=class_id)

@app.route('/admin/admin_dashboard')
def admin_dashboard():
    if 'loggedin' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

@app.route('/admin/notifications', methods=['GET', 'POST'])
def admin_notifications():
    if 'loggedin' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    cur = db.cursor(dictionary=True)
    if request.method == 'POST':
        title = request.form['title']
        message = request.form['message']
        target_role = request.form['target_role']
        cur.execute("""
            INSERT INTO notifications (title, message, target_role, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (title, message, target_role))
        db.commit()
        flash('Notification sent successfully!')
    
    cur.execute("SELECT * FROM notifications ORDER BY created_at DESC")
    notifications = cur.fetchall()
    cur.close()
    return render_template('admin_notifications.html', notifications=notifications)

@app.route('/admin/hostels', methods=['GET', 'POST'])
def admin_hostels():
    if 'loggedin' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    cur = db.cursor(dictionary=True)
    if request.method == 'POST':
        hostel_name = request.form['hostel_name']
        total_rooms = request.form['total_rooms']
        cur.execute("""
            INSERT INTO hostels (hostel_name, total_rooms, available_rooms)
            VALUES (%s, %s, %s)
        """, (hostel_name, total_rooms, total_rooms))
        db.commit()
        flash('Hostel added successfully!')
    
    cur.execute("SELECT * FROM hostels")
    hostels = cur.fetchall()
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    cur.close()
    return render_template('admin_hostels.html', hostels=hostels, students=students)

@app.route('/admin/allocate_room', methods=['POST'])
def allocate_room():
    if 'loggedin' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    hostel_id = request.form['hostel_id']
    student_id = request.form['student_id']
    room_number = request.form['room_number']
    
    cur = db.cursor()
    # Check if room is available
    cur.execute("SELECT available_rooms FROM hostels WHERE hostel_id = %s", (hostel_id,))
    hostel = cur.fetchone()
    
    if hostel and hostel[0] > 0:
        cur.execute("""
            INSERT INTO hostel_allocations (hostel_id, student_id, room_number, allocation_date)
            VALUES (%s, %s, %s, CURDATE())
        """, (hostel_id, student_id, room_number))
        
        cur.execute("""
            UPDATE hostels 
            SET available_rooms = available_rooms - 1 
            WHERE hostel_id = %s
        """, (hostel_id,))
        
        db.commit()
        flash('Room allocated successfully!')
    else:
        flash('No rooms available in this hostel!')
    
    cur.close()
    return redirect(url_for('admin_hostels'))

# Attendance Report
@app.route("/admin/get_attendance_report", methods=['GET', 'POST'])
def get_attendance_report():
    if 'loggedin' in session and session['role'] == 'admin':
        cur = db.cursor()
        if request.method == 'POST':
            class_sec = request.form.get('class_sec')
            class_date = request.form.get('class_date')
            class_name = request.form.get('class_name')
            cur.execute("SELECT student_id, student_name FROM students WHERE class_sec = %s", (class_sec,))
            students = cur.fetchall()
            cur.execute("""
                SELECT a.student_id, a.status 
                FROM attendance a
                JOIN classes c ON a.class_id = c.class_id
                WHERE c.class_sec = %s AND a.date = %s AND c.class_name = %s
            """, (class_sec, class_date, class_name))
            attendance = cur.fetchall()
            attendance_dict = {row[0]: row[1] for row in attendance}
            cur.close()
            return render_template(
                'attendance_report.html',
                class_sec=class_sec,
                class_date=class_date,
                class_name=class_name,
                students=students,
                attendance=attendance_dict
            )
        else:
            cur.execute("SELECT DISTINCT class_sec FROM classes")
            secs = cur.fetchall()
            cur.execute("SELECT DISTINCT class_name FROM classes")
            class_names = cur.fetchall()
            cur.close()
            return render_template('attendance_report.html', class_secs=secs, class_names=class_names)
    else:
        return redirect('/admin/login')

@app.route('/admin/admin_profile')
def admin_profile():
    cur = db.cursor()
    cur.execute("SELECT admin_name, email, phone FROM admins WHERE username = %s", (session['username'],))
    profile_data = cur.fetchone()
    cur.close()
    return render_template('admin_profile.html', profile_data=profile_data)

@app.route('/admin/update_admin_profile', methods=['POST'])
def update_admin_profile():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    cur = db.cursor()
    cur.execute("UPDATE admins SET admin_name = %s, email = %s, phone = %s WHERE username = %s",(name, email, phone, session['username']))
    db.commit()
    cur.close()
    return redirect('/admin/admin_profile')
    
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect('/')

@app.route('/teacher/mark_attendance_students/<int:class_id>', methods=['GET', 'POST'])
def mark_attendance_students(class_id):
    if 'loggedin' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT class_name, class_sec FROM classes WHERE class_id = %s", (class_id,))
    class_row = cur.fetchone()
    if not class_row:
        cur.close()
        return "Class not found", 404
        
    # Get students in this class section
    cur.execute("""
        SELECT student_id, student_name 
        FROM students 
        WHERE class_sec = %s
    """, (class_row['class_sec'],))
    students = cur.fetchall()
    
    if request.method == 'POST':
        today = date.today()
        # Delete existing attendance for today
        cur.execute("DELETE FROM attendance WHERE class_id = %s AND date = %s", (class_id, today))
        
        # Insert new attendance
        for student in students:
            status = request.form.get(f'attendance_{student["student_id"]}', 'absent')
            cur.execute("""
                INSERT INTO attendance (student_id, class_id, date, status)
                VALUES (%s, %s, %s, %s)
            """, (student['student_id'], class_id, today, status))
        db.commit()
        flash('Attendance marked successfully')
        return redirect(url_for('teacher_dashboard'))

    cur.close()
    return render_template('mark_attendance_students.html', 
                         students=students, 
                         class_info=class_row)

@app.route('/teacher/view_attendance/<int:class_id>', methods=['GET', 'POST'])
def view_attendance(class_id):
    if 'loggedin' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT class_name, class_sec FROM classes WHERE class_id = %s", (class_id,))
    class_row = cur.fetchone()
    if not class_row:
        cur.close()
        return "Class not found", 404
    class_name = class_row['class_name']
    class_sec = class_row['class_sec']
    cur.execute("SELECT DISTINCT class_date FROM attendance WHERE class_id = %s ORDER BY class_date DESC", (class_id,))
    dates = [row['class_date'] for row in cur.fetchall()]
    selected_date = request.form.get('attendance_date') if request.method == 'POST' else (dates[0] if dates else None)
    attendance_records = []
    if selected_date:
        cur.execute("""
            SELECT s.student_id, s.student_name, a.status
            FROM students s
            LEFT JOIN attendance a ON s.student_id = a.student_id AND a.class_id = %s AND a.class_date = %s
            WHERE s.class_sec = %s
            ORDER BY s.student_id
        """, (class_id, selected_date, class_sec))
        attendance_records = cur.fetchall()
    cur.close()
    return render_template('view_attendance.html', class_name=class_name, class_sec=class_sec, dates=dates, selected_date=selected_date, attendance_records=attendance_records)

@app.route('/student/dashboard')
def student_dashboard():
    if 'loggedin' in session and session['role'] == 'student':
        cur = db.cursor()
        cur.execute("SELECT * FROM students WHERE student_id = %s", (session['username'],))
        student = cur.fetchone()
        # Use only columns that exist in your attendance table
        cur.execute("""
            SELECT id, class_id, status
            FROM attendance
            WHERE student_id = %s
            ORDER BY id DESC
        """, (session['username'],))
        attendance_rows = cur.fetchall()
        attendance = []
        for row in attendance_rows:
            cur.execute("SELECT class_name FROM classes WHERE class_id = %s", (row[1],))
            class_name = cur.fetchone()
            attendance.append((row[0], class_name[0] if class_name else '', row[2]))
        cur.execute("SELECT amount, due_date, paid, payment_date FROM fees WHERE student_id = %s", (session['username'],))
        fees = cur.fetchall()
        cur.execute("SELECT event_name, event_date, description FROM events ORDER BY event_date DESC")
        events = cur.fetchall()
        cur.close()
        return render_template('student_dashboard.html', student=student, attendance=attendance, fees=fees, events=events)
    else:
        return redirect('/login')

# Ensure all required tables exist at app startup (for development/demo only)
def ensure_tables():
    cur = db.cursor()
    
    # Create tables if they don't exist (remove all DROP TABLE statements)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        username VARCHAR(50) PRIMARY KEY,
        teacher_name VARCHAR(50),
        password VARCHAR(50),
        email VARCHAR(50),
        phone VARCHAR(15)
    )""")
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        username VARCHAR(50) PRIMARY KEY,
        admin_name VARCHAR(50),
        password VARCHAR(50),
        email VARCHAR(50),
        phone VARCHAR(15)
    )""")

    # Check if teachers table is empty before inserting defaults
    cur.execute("SELECT COUNT(*) FROM teachers")
    if cur.fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO teachers (username, teacher_name, password, email, phone) VALUES 
        ('teacher1', 'Jenny', 'password1', 'jenny@gmail.com', '9183885580'),
        ('teacher2', 'Mary', 'password2', 'marys@gmail.com', '9801802223')
        """)
        print("Default teachers created")

    # Check if admins table is empty before inserting defaults
    cur.execute("SELECT COUNT(*) FROM admins")
    if cur.fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO admins (username, admin_name, password, email, phone) VALUES 
        ('admin1', 'Will Smith', 'password1', 'smithw@gmail.com', '9550634682'),
        ('admin2', 'John Wick', 'password2', 'wjohn@gmail.com', '8192083447')
        """)
        print("Default admins created")
    
    # Create classes table if not exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS classes (
        class_id INT PRIMARY KEY AUTO_INCREMENT,
        class_name VARCHAR(50),
        teacher_username VARCHAR(50),
        class_date DATE,
        class_sec VARCHAR(10),
        FOREIGN KEY (teacher_username) REFERENCES teachers(username)
    )""")
    
    # For students table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id INT PRIMARY KEY AUTO_INCREMENT,
        student_name VARCHAR(50),
        email VARCHAR(50),
        class_sec VARCHAR(10),
        phone VARCHAR(15)
    )""")

    # Only insert default students if table is empty
    cur.execute("SELECT COUNT(*) FROM students")
    if cur.fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO students (student_name, email, class_sec, phone)
        VALUES
        ('John Doe', 'john@gmail.com', 'CSE1', '8866443210'),
        ('Jane Smith', 'smithj@gmail.com', 'CSE1', '9313302392')
        """)
        print("Default students created")

    # Drop and recreate attendance table with correct schema
    cur.execute("DROP TABLE IF EXISTS attendance")
    cur.execute("""
    CREATE TABLE attendance (
        id INT PRIMARY KEY AUTO_INCREMENT,
        student_id INT,
        class_id INT,
        date DATE,
        status VARCHAR(10),
        FOREIGN KEY(student_id) REFERENCES students(student_id),
        FOREIGN KEY(class_id) REFERENCES classes(class_id)
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS books (
        book_id INT PRIMARY KEY AUTO_INCREMENT,
        title VARCHAR(100),
        author VARCHAR(100),
        isbn VARCHAR(20),
        total_copies INT,
        available_copies INT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS book_issues (
        issue_id INT PRIMARY KEY AUTO_INCREMENT,
        book_id INT,
        student_id INT,
        issue_date DATE,
        return_date DATE,
        returned BOOLEAN DEFAULT FALSE,
        FOREIGN KEY(book_id) REFERENCES books(book_id),
        FOREIGN KEY(student_id) REFERENCES students(student_id)
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS hostels (
        hostel_id INT PRIMARY KEY AUTO_INCREMENT,
        hostel_name VARCHAR(100),
        total_rooms INT,
        available_rooms INT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS hostel_allocations (
        allocation_id INT PRIMARY KEY AUTO_INCREMENT,
        student_id INT,
        hostel_id INT,
        room_number VARCHAR(10),
        allocation_date DATE,
        FOREIGN KEY(student_id) REFERENCES students(student_id),
        FOREIGN KEY(hostel_id) REFERENCES hostels(hostel_id)
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id INT PRIMARY KEY AUTO_INCREMENT,
        title VARCHAR(200),
        message TEXT,
        target_role VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        doc_id INT PRIMARY KEY AUTO_INCREMENT,
        doc_title VARCHAR(200),
        doc_type VARCHAR(50),
        doc_path VARCHAR(255),
        uploader_username VARCHAR(50),
        upload_date DATE,
        class_id INT,
        FOREIGN KEY(uploader_username) REFERENCES teachers(username),
        FOREIGN KEY(class_id) REFERENCES classes(class_id)
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS exams (
        exam_id INT PRIMARY KEY AUTO_INCREMENT,
        exam_name VARCHAR(100),
        exam_date DATE,
        class_id INT,
        FOREIGN KEY (class_id) REFERENCES classes(class_id)
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS grades (
        grade_id INT PRIMARY KEY AUTO_INCREMENT,
        student_id INT,
        exam_id INT,
        marks FLOAT,
        grade VARCHAR(2),
        FOREIGN KEY (student_id) REFERENCES students(student_id),
        FOREIGN KEY (exam_id) REFERENCES exams(exam_id)
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        event_id INT PRIMARY KEY AUTO_INCREMENT,
        event_name VARCHAR(100),
        event_date DATE,
        description TEXT
    )""")

    db.commit()
    cur.close()

# Call this function at startup
ensure_tables()

@app.route('/teacher/add_class', methods=['GET', 'POST'])
def add_class():
    if 'loggedin' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        class_name = request.form['class_name']
        class_sec = request.form['class_sec']
        class_date = request.form['class_date']
        teacher_username = session['username']
        
        cur = db.cursor()
        cur.execute("""
            INSERT INTO classes (class_name, teacher_username, class_date, class_sec)
            VALUES (%s, %s, %s, %s)
        """, (class_name, teacher_username, class_date, class_sec))
        db.commit()
        cur.close()
        flash('Class added successfully!', 'success')
        return redirect(url_for('teacher_classes'))
        
    return render_template('add_class.html')

# Add new route for viewing students in class
@app.route('/teacher/students_in_class/<int:class_id>')
def students_in_class(class_id):
    if 'loggedin' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
        
    cur = db.cursor(dictionary=True)
    
    # Get class details
    cur.execute("SELECT * FROM classes WHERE class_id = %s AND teacher_username = %s", 
                (class_id, session['username']))
    class_info = cur.fetchone()
    
    if not class_info:
        cur.close()
        return "Class not found", 404
        
    # Get students in this class
    cur.execute("""
        SELECT student_id, student_name, email, phone 
        FROM students 
        WHERE class_sec = %s
        ORDER BY student_name
    """, (class_info['class_sec'],))
    
    students = cur.fetchall()
    cur.close()
    
    return render_template('students_in_class.html', 
                         class_info=class_info, 
                         students=students)

@app.route('/admin/exams', methods=['GET', 'POST'])
def admin_exams():
    if 'loggedin' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    cur = db.cursor(dictionary=True)
    if request.method == 'POST':
        class_id = request.form['class_id']
        exam_name = request.form['exam_name']
        exam_date = request.form['exam_date']
        
        cur.execute("""
            INSERT INTO exams (class_id, exam_name, exam_date)
            VALUES (%s, %s, %s)
        """, (class_id, exam_name, exam_date))
        db.commit()
        flash('Exam added successfully!')
    
    cur.execute("SELECT e.*, c.class_name FROM exams e JOIN classes c ON e.class_id = c.class_id")
    exams = cur.fetchall()
    cur.execute("SELECT class_id, class_name FROM classes")
    classes = cur.fetchall()
    cur.close()
    
    return render_template('admin_exams.html', exams=exams, classes=classes)

@app.route('/admin/grades', methods=['GET', 'POST'])
def admin_grades():
    if 'loggedin' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    cur = db.cursor(dictionary=True)
    
    if request.method == 'POST':
        student_id = request.form['student_id']
        exam_id = request.form['exam_id']
        marks = request.form['marks']
        grade = request.form['grade']
        
        cur.execute("""
            INSERT INTO grades (student_id, exam_id, marks, grade)
            VALUES (%s, %s, %s, %s)
        """, (student_id, exam_id, marks, grade))
        db.commit()
        flash('Grade added successfully!')
    
    # Fetch all required data
    cur.execute("""
        SELECT g.*, s.student_name, e.exam_name 
        FROM grades g 
        JOIN students s ON g.student_id = s.student_id 
        JOIN exams e ON g.exam_id = e.exam_id
        ORDER BY s.student_name
    """)
    grades = cur.fetchall()
    
    cur.execute("SELECT student_id, student_name FROM students ORDER BY student_name")
    students = cur.fetchall()
    
    cur.execute("SELECT exam_id, exam_name FROM exams ORDER BY exam_name")
    exams = cur.fetchall()
    
    cur.close()
    return render_template('admin_grades.html', grades=grades, students=students, exams=exams)

@app.route('/admin/fees', methods=['GET', 'POST'])
def admin_fees():
    if 'loggedin' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    cur = db.cursor(dictionary=True)
    if request.method == 'POST':
        student_id = request.form['student_id']
        amount = request.form['amount']
        due_date = request.form['due_date']
        
        cur.execute("""
            INSERT INTO fees (student_id, amount, due_date, paid)
            VALUES (%s, %s, %s, FALSE)
        """, (student_id, amount, due_date))
        db.commit()
        flash('Fee record added successfully!')
    
    cur.execute("""
        SELECT f.*, s.student_name 
        FROM fees f 
        JOIN students s ON f.student_id = s.student_id
    """)
    fees = cur.fetchall()
    cur.execute("SELECT student_id, student_name FROM students")
    students = cur.fetchall()
    cur.close()
    
    return render_template('admin_fees.html', fees=fees, students=students)

@app.route('/admin/books', methods=['GET', 'POST'])
def admin_books():
    if 'loggedin' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    cur = db.cursor(dictionary=True)
    
    if request.method == 'POST':
        if request.form.get('action') == 'issue':
            # Handle book issue
            book_id = request.form['book_id']
            student_id = request.form['student_id']
            issue_date = request.form['issue_date']
            
            # Check if book is available
            cur.execute("SELECT available_copies FROM books WHERE book_id = %s", (book_id,))
            book = cur.fetchone()
            if book and book['available_copies'] > 0:
                cur.execute("""
                    INSERT INTO book_issues (book_id, student_id, issue_date)
                    VALUES (%s, %s, %s)
                """, (book_id, student_id, issue_date))
                
                cur.execute("""
                    UPDATE books 
                    SET available_copies = available_copies - 1 
                    WHERE book_id = %s
                """, (book_id,))
                db.commit()
                flash('Book issued successfully!')
            else:
                flash('Book not available!')
        else:
            # Handle adding new book
            title = request.form['title']
            author = request.form['author']
            isbn = request.form['isbn']
            copies = int(request.form['copies'])
            
            cur.execute("""
                INSERT INTO books (title, author, isbn, total_copies, available_copies)
                VALUES (%s, %s, %s, %s, %s)
            """, (title, author, isbn, copies, copies))
            db.commit()
            flash('Book added successfully!')
    
    cur.execute("SELECT * FROM books ORDER BY title")
    books = cur.fetchall()
    
    cur.execute("SELECT student_id, student_name FROM students ORDER BY student_name")
    students = cur.fetchall()
    
    cur.close()
    return render_template('admin_books.html', books=books, students=students)

@app.route('/admin/events', methods=['GET', 'POST'])
def admin_events():
    if 'loggedin' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    cur = db.cursor(dictionary=True)
    
    if request.method == 'POST':
        if request.form.get('action') == 'delete':
            # Handle event deletion
            event_id = request.form['event_id']
            cur.execute("DELETE FROM events WHERE event_id = %s", (event_id,))
            flash('Event deleted successfully!')
        else:
            # Handle event addition
            event_name = request.form['event_name']
            event_date = request.form['event_date']
            description = request.form['description']
            
            cur.execute("""
                INSERT INTO events (event_name, event_date, description)
                VALUES (%s, %s, %s)
            """, (event_name, event_date, description))
            flash('Event added successfully!')
        
        db.commit()
    
    cur.execute("SELECT * FROM events ORDER BY event_date DESC")
    events = cur.fetchall()
    cur.close()
    
    return render_template('admin_events.html', events=events)

@app.route('/admin/documents', methods=['GET', 'POST'])
def admin_documents():
    if 'loggedin' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    cur = db.cursor(dictionary=True)
    
    if request.method == 'POST':
        if 'document' not in request.files:
            flash('No file selected')
            return redirect(request.url)
            
        file = request.files['document']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            title = request.form['title']
            doc_type = request.form['doc_type']
            class_id = request.form['class_id']
            
            cur.execute("""
                INSERT INTO documents (doc_title, doc_type, doc_path, class_id, upload_date)
                VALUES (%s, %s, %s, %s, CURDATE())
            """, (title, doc_type, filepath, class_id))
            db.commit()
            flash('Document uploaded successfully!')
    
    cur.execute("""
        SELECT d.*, c.class_name 
        FROM documents d 
        JOIN classes c ON d.class_id = c.class_id 
        ORDER BY d.upload_date DESC
    """)
    documents = cur.fetchall()
    
    cur.execute("SELECT class_id, class_name FROM classes")
    classes = cur.fetchall()
    
    cur.close()
    return render_template('admin_documents.html', documents=documents, classes=classes)
