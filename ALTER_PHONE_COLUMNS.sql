-- Increase phone column length in teachers table
ALTER TABLE teachers MODIFY COLUMN phone VARCHAR(30);

-- Increase phone column length in students table
ALTER TABLE students MODIFY COLUMN phone VARCHAR(30);

-- Increase phone column length in admins table (if exists)
ALTER TABLE admins MODIFY COLUMN phone VARCHAR(30);
