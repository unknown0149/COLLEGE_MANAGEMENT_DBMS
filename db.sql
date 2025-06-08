-- Drop tables to avoid FK conflicts
DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS classes;
DROP TABLE IF EXISTS admins;
DROP TABLE IF EXISTS teachers;
DROP TABLE IF EXISTS exams;
DROP TABLE IF EXISTS grades;
DROP TABLE IF EXISTS fees;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS book_issues;
DROP TABLE IF EXISTS hostels;
DROP TABLE IF EXISTS hostel_rooms;
DROP TABLE IF EXISTS hostel_allocations;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS events;

-- Teachers Table
CREATE TABLE teachers (
    username VARCHAR(50) PRIMARY KEY,
    teacher_name VARCHAR(50),
    password VARCHAR(50),
    email VARCHAR(50),
    phone VARCHAR(15)
);

INSERT INTO teachers VALUES
    ('teacher1','Jenny','password1','jenny@gmail.com','9183885580'),
    ('teacher2','Mary','password2','marys@gmail.com','9801802223');

-- Admins Table
CREATE TABLE admins (
    username VARCHAR(50) PRIMARY KEY,
    admin_name VARCHAR(50),
    password VARCHAR(50),
    email VARCHAR(50),
    phone VARCHAR(15)
);

INSERT INTO admins VALUES
    ('admin1','Will Smith','password1','smithw@gmail.com','9550634682'),
    ('admin2','John Wick','password2','wjohn@gmail.com','8192083447');

-- Classes Table
CREATE TABLE classes (
    class_id INT PRIMARY KEY AUTO_INCREMENT,
    class_name VARCHAR(50),
    teacher_username VARCHAR(50),
    class_date DATE,
    class_sec VARCHAR(10),
    FOREIGN KEY (teacher_username) REFERENCES teachers(username)
);

INSERT INTO classes (class_id, class_name, teacher_username, class_date, class_sec) VALUES
    (1,'Machine Learning','teacher1','2023-05-31','CSE1'),
    (2,'BCT','teacher2','2023-05-31','CSE2');

-- Students Table
CREATE TABLE students (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    student_name VARCHAR(50),
    email VARCHAR(50),
    class_sec VARCHAR(10),
    phone VARCHAR(15)
);

INSERT INTO students VALUES
    (1,'John Doe','john@gmail.com','CSE1','8866443210'),
    (2,'Jane Smith','smithj@gmail.com','CSE1','9313302392');

-- Attendance Table
CREATE TABLE attendance (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT,
    class_id INT,
    date DATE,
    status VARCHAR(10),
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(class_id) REFERENCES classes(class_id)
);

INSERT INTO attendance (id, student_id, class_id, date, status) VALUES
    (1, 1, 1, '2023-05-29', 'present'),
    (2, 1, 2, '2023-05-29', 'absent');

-- Add missing tables for full college management system

CREATE TABLE IF NOT EXISTS exams (
    exam_id INT PRIMARY KEY AUTO_INCREMENT,
    class_id INT,
    exam_name VARCHAR(100),
    exam_date DATE,
    FOREIGN KEY(class_id) REFERENCES classes(class_id)
);

CREATE TABLE IF NOT EXISTS grades (
    grade_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT,
    exam_id INT,
    marks FLOAT,
    grade VARCHAR(5),
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(exam_id) REFERENCES exams(exam_id)
);

CREATE TABLE IF NOT EXISTS fees (
    fee_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT,
    amount DECIMAL(10,2),
    due_date DATE,
    paid BOOLEAN DEFAULT FALSE,
    payment_date DATE,
    FOREIGN KEY(student_id) REFERENCES students(student_id)
);

CREATE TABLE IF NOT EXISTS books (
    book_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(100),
    author VARCHAR(100),
    isbn VARCHAR(20),
    total_copies INT,
    available_copies INT
);

CREATE TABLE IF NOT EXISTS book_issues (
    issue_id INT PRIMARY KEY AUTO_INCREMENT,
    book_id INT,
    student_id INT,
    issue_date DATE,
    return_date DATE,
    returned BOOLEAN DEFAULT FALSE,
    FOREIGN KEY(book_id) REFERENCES books(book_id),
    FOREIGN KEY(student_id) REFERENCES students(student_id)
);

CREATE TABLE IF NOT EXISTS hostels (
    hostel_id INT PRIMARY KEY AUTO_INCREMENT,
    hostel_name VARCHAR(100),
    total_rooms INT
);

CREATE TABLE IF NOT EXISTS hostel_rooms (
    room_id INT PRIMARY KEY AUTO_INCREMENT,
    hostel_id INT,
    room_number VARCHAR(20),
    capacity INT,
    FOREIGN KEY(hostel_id) REFERENCES hostels(hostel_id)
);

CREATE TABLE IF NOT EXISTS hostel_allocations (
    allocation_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT,
    room_id INT,
    allocation_date DATE,
    release_date DATE,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(room_id) REFERENCES hostel_rooms(room_id)
);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200),
    message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    target_role VARCHAR(20)
);

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
);

CREATE TABLE IF NOT EXISTS events (
    event_id INT PRIMARY KEY AUTO_INCREMENT,
    event_name VARCHAR(200),
    event_date DATE,
    description TEXT
);

-- Exams Table dummy data
INSERT INTO exams (exam_id, class_id, exam_name, exam_date) VALUES
    (1, 1, 'Midterm', '2023-06-10'),
    (2, 2, 'Final', '2023-07-15');

-- Grades Table dummy data
INSERT INTO grades (grade_id, student_id, exam_id, marks, grade) VALUES
    (1, 1, 1, 85, 'A'),
    (2, 2, 1, 78, 'B'),
    (3, 1, 2, 90, 'A+');

-- Fees Table dummy data
INSERT INTO fees (fee_id, student_id, amount, due_date, paid, payment_date) VALUES
    (1, 1, 50000.00, '2023-06-01', TRUE, '2023-05-20'),
    (2, 2, 50000.00, '2023-06-01', FALSE, NULL);

-- Books Table dummy data
INSERT INTO books (book_id, title, author, isbn, total_copies, available_copies) VALUES
    (1, 'Introduction to Algorithms', 'Cormen', '9780262033848', 5, 3),
    (2, 'Database Systems', 'Elmasri', '9780133970777', 4, 4);

-- Book Issues Table dummy data
INSERT INTO book_issues (issue_id, book_id, student_id, issue_date, return_date, returned) VALUES
    (1, 1, 1, '2023-06-01', '2023-06-10', TRUE),
    (2, 2, 2, '2023-06-05', NULL, FALSE);

-- Hostels Table dummy data
INSERT INTO hostels (hostel_id, hostel_name, total_rooms) VALUES
    (1, 'Alpha Hostel', 50),
    (2, 'Beta Hostel', 40);

-- Hostel Rooms Table dummy data
INSERT INTO hostel_rooms (room_id, hostel_id, room_number, capacity) VALUES
    (1, 1, 'A101', 2),
    (2, 2, 'B201', 3);

-- Hostel Allocations Table dummy data
INSERT INTO hostel_allocations (allocation_id, student_id, room_id, allocation_date, release_date) VALUES
    (1, 1, 1, '2023-05-20', NULL),
    (2, 2, 2, '2023-05-22', NULL);

-- Notifications Table dummy data
INSERT INTO notifications (notification_id, title, message, target_role) VALUES
    (1, 'Welcome', 'Welcome to the new semester!', 'all'),
    (2, 'Exam Notice', 'Midterm exam on 10th June.', 'student');

-- Documents Table dummy data
INSERT INTO documents (doc_id, uploader_username, doc_title, doc_path, upload_date, doc_type, class_id) VALUES
    (1, 'teacher1', 'Syllabus', '/docs/syllabus.pdf', '2023-05-25', 'note', 1),
    (2, 'teacher2', 'Assignment 1', '/docs/assignment1.pdf', '2023-06-01', 'assignment', 2);

-- Events Table dummy data
INSERT INTO events (event_id, event_name, event_date, description) VALUES
    (1, 'Annual Day', '2023-08-15', 'Annual day celebration with cultural events.'),
    (2, 'Tech Fest', '2023-09-10', 'Technical festival with workshops and competitions.');

-- If you only see admins, attendance, classes, students, teachers,
-- it means the SQL to create the new tables was NOT executed in MySQL.

-- To verify, run this in your MySQL client:
SHOW TABLES;

-- If you do NOT see exams, grades, fees, books, book_issues, hostels, hostel_rooms, hostel_allocations, notifications, documents, events,
-- then you MUST run the CREATE TABLE statements for these tables.

-- Example for one table:
CREATE TABLE IF NOT EXISTS exams (
    exam_id INT PRIMARY KEY AUTO_INCREMENT,
    class_id INT,
    exam_name VARCHAR(100),
    exam_date DATE,
    FOREIGN KEY(class_id) REFERENCES classes(class_id)
);

-- Repeat for all other missing tables as shown in previous responses.

-- After running all CREATE TABLE statements, run SHOW TABLES; again.
-- You should now see all tables in your database.
