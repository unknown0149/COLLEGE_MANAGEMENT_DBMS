from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = 'my_secret_key' #Add your secret key here  
db = mysql.connector.connect(
    host='localhost',
    user='root', # your username here
    password='aryan0149', # your password here
    database='attendance_db' # changed from 'test_db' to your actual db name
)

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
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        cur = db.cursor()
        try:
            if role == 'teacher':
                cur.execute("SELECT * FROM teachers WHERE username = %s AND password = %s", (username, password))
                user = cur.fetchone()
                if user:
                    session['loggedin'] = True
                    session['username'] = user[0]
                    session['role'] = 'teacher'
                    cur.close()
                    return redirect('/teacher/dashboard')
                else:
                    cur.close()
                    error = 'Invalid login credentials.'
                    return render_template('login.html', error=error)
            elif role == 'admin':
                cur.execute("SELECT * FROM admins WHERE username = %s AND password = %s", (username, password))
                user = cur.fetchone()
                if user:
                    session['loggedin'] = True
                    session['username'] = user[0]
                    session['role'] = 'admin'
                    cur.close()
                    return redirect('/admin/admin_dashboard')
                else:
                    cur.close()
                    error = 'Invalid login credentials'
                    return render_template('login.html', error=error)
            elif role == 'student':
                # student_id is int, so cast username to int for query
                try:
                    student_id = int(username)
                except ValueError:
                    cur.close()
                    error = 'Student ID must be a number'
                    return render_template('login.html', error=error)
                cur.execute("SELECT * FROM students WHERE student_id = %s AND phone = %s", (student_id, password))
                user = cur.fetchone()
                if user:
                    session['loggedin'] = True
                    session['username'] = user[0]
                    session['role'] = 'student'
                    cur.close()
                    return redirect('/student/dashboard')
                else:
                    cur.close()
                    error = 'Invalid login credentials'
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
    cur.execute("SELECT * FROM classes WHERE teacher_username = %s", (session['username'],))
    classes = cur.fetchall()
    class_students = []
    for c in classes:
        cur.execute("SELECT student_id, student_name FROM students WHERE class_sec = %s", (c[4],))
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
    if 'loggedin' in session and session['role'] == 'admin':
        return render_template('admin_dashboard.html')
    else:
        return redirect('/')

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
    class_name = class_row['class_name']
    class_sec = class_row['class_sec']
    cur.execute("SELECT student_id, student_name FROM students WHERE class_sec = %s", (class_sec,))
    students = cur.fetchall()
    today = date.today().isoformat()
    students_data = []
    for student in students:
        # Use the correct column name 'class_date' instead of 'date'
        cur.execute("SELECT status FROM attendance WHERE student_id = %s AND class_id = %s AND class_date = %s", (student['student_id'], class_id, today))
        row = cur.fetchone()
        today_status = row['status'] if row else None
        students_data.append({
            'id': student['student_id'],
            'name': student['student_name'],
            'today_status': today_status
        })
    if request.method == 'POST':
        for student in students_data:
            status = request.form.get(f'attendance_{student["id"]}')
            cur.execute("SELECT id FROM attendance WHERE student_id = %s AND class_id = %s AND class_date = %s", (student['id'], class_id, today))
            row = cur.fetchone()
            if row:
                cur.execute("UPDATE attendance SET status = %s WHERE id = %s", (status, row['id']))
            else:
                cur.execute("INSERT INTO attendance (student_id, class_id, class_date, status) VALUES (%s, %s, %s, %s)",
                            (student['id'], class_id, today, status))
        db.commit()
        cur.close()
        flash('Attendance submitted successfully!', 'success')
        return redirect(url_for('mark_attendance_students', class_id=class_id))
    cur.close()
    return render_template('teacher_mark_attendance_students.html', students=students_data, class_name=class_name)

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
    # Exams
    cur.execute("""
    CREATE TABLE IF NOT EXISTS exams (
        exam_id INT PRIMARY KEY AUTO_INCREMENT,
        class_id INT,
        exam_name VARCHAR(100),
        exam_date DATE,
        FOREIGN KEY(class_id) REFERENCES classes(class_id)
    )""")
    # Grades
    cur.execute("""
    CREATE TABLE IF NOT EXISTS grades (
        grade_id INT PRIMARY KEY AUTO_INCREMENT,
        student_id INT,
        exam_id INT,
        marks FLOAT,
        grade VARCHAR(5),
        FOREIGN KEY(student_id) REFERENCES students(student_id),
        FOREIGN KEY(exam_id) REFERENCES exams(exam_id)
    )""")
    # Fees
    cur.execute("""
    CREATE TABLE IF NOT EXISTS fees (
        fee_id INT PRIMARY KEY AUTO_INCREMENT,
        student_id INT,
        amount DECIMAL(10,2),
        due_date DATE,
        paid BOOLEAN DEFAULT FALSE,
        payment_date DATE,
        FOREIGN KEY(student_id) REFERENCES students(student_id)
    )""")
    # Books
    cur.execute("""
    CREATE TABLE IF NOT EXISTS books (
        book_id INT PRIMARY KEY AUTO_INCREMENT,
        title VARCHAR(100),
        author VARCHAR(100),
        isbn VARCHAR(20),
        total_copies INT,
        available_copies INT
    )""")
    # Book Issues
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
    # Hostels
    cur.execute("""
    CREATE TABLE IF NOT EXISTS hostels (
        hostel_id INT PRIMARY KEY AUTO_INCREMENT,
        hostel_name VARCHAR(100),
        total_rooms INT
    )""")
    # Hostel Rooms
    cur.execute("""
    CREATE TABLE IF NOT EXISTS hostel_rooms (
        room_id INT PRIMARY KEY AUTO_INCREMENT,
        hostel_id INT,
        room_number VARCHAR(20),
        capacity INT,
        FOREIGN KEY(hostel_id) REFERENCES hostels(hostel_id)
    )""")
    # Hostel Allocations
    cur.execute("""
    CREATE TABLE IF NOT EXISTS hostel_allocations (
        allocation_id INT PRIMARY KEY AUTO_INCREMENT,
        student_id INT,
        room_id INT,
        allocation_date DATE,
        release_date DATE,
        FOREIGN KEY(student_id) REFERENCES students(student_id),
        FOREIGN KEY(room_id) REFERENCES hostel_rooms(room_id)
    )""")
    # Notifications
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id INT PRIMARY KEY AUTO_INCREMENT,
        title VARCHAR(200),
        message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        target_role VARCHAR(20)
    )""")
    # Documents
    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        doc_id INT PRIMARY KEY AUTO_INCREMENT,
        uploader_username VARCHAR(50),
        doc_title VARCHAR(200),
        doc_path VARCHAR(255),
        upload_date DATE,
        doc_type VARCHAR(50),
        class_id INT,
        FOREIGN KEY(uploader_username) REFERENCES teachers(username),
        FOREIGN KEY(class_id) REFERENCES classes(class_id)
    )""")
    # Events
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        event_id INT PRIMARY KEY AUTO_INCREMENT,
        event_name VARCHAR(200),
        event_date DATE,
        description TEXT
    )""")
    cur.close()

# Call this function at startup
ensure_tables()
