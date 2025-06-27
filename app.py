from flask import Flask, request, render_template, redirect, url_for, jsonify, session
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# MySQL configuration using environment variables
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_DATABASE')
}

# Validate required environment variables
required_vars = ['SECRET_KEY', 'DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_DATABASE']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Program mapping from form values to full names
program_mapping = {
    "bsc-cs": "BSc. Computer Science",
    "bsc-it": "BSc. Information Technology",
    "bsc-telecom": "BSc. Telecommunications Engineering"
}

# Function to check if user is logged in
def is_logged_in():
    return session.get('logged_in')

# Login route
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        serial_number = request.form['serial-number']
        pin = request.form['pin']
        try:
            pin = int(pin)  # Convert pin to integer
        except ValueError:
            return render_template('login.html', error="Invalid PIN. Please enter a number.")

        # Connect to database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM login WHERE SerialNumber = %s AND Pin = %s", (serial_number, pin))
            user = cursor.fetchone()
            if user:
                session['logged_in'] = True
                return redirect(url_for('apply'))
            else:
                return render_template('login.html', error="Invalid Serial Number or PIN.")
        except Error as e:
            print(f"Error: {e}")
            return render_template('login.html', error="An error occurred. Please try again.")
        finally:
            cursor.close()
            conn.close()
    return render_template('login.html')

# Apply route (protected)
@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if not is_logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Extract form data
        first_name = request.form['first-name']
        last_name = request.form['last-name']
        student_name = f"{first_name} {last_name}"
        dob = request.form['dob']
        nationality = request.form['nationality']
        email = request.form['email']
        phone = request.form['phone']
        gender = request.form['gender']
        program_code = request.form['program']
        program_full_name = program_mapping.get(program_code, "")

        # Connect to database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        try:
            # Insert into Programs to get StudentID
            cursor.execute("INSERT INTO Programs (Program) VALUES (%s)", (program_full_name,))
            student_id = cursor.lastrowid

            # Insert into Student_Information
            cursor.execute("""
                INSERT INTO Student_Information 
                (StudentID, Student_Name, Telephone, Email, Gender, Date_of_Birth, Nationality, Program)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (student_id, student_name, phone, email, gender, dob, nationality, program_full_name))

            conn.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return "An error occurred while submitting the application."
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('view'))
    return render_template('apply.html')

# View route (protected)
@app.route('/view')
def view():
    if not is_logged_in():
        return redirect(url_for('login'))
    return render_template('view.html')

# API to get students (protected)
@app.route('/api/students')
def get_students():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT StudentID, Student_Name, Program FROM Student_Information")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    # Convert to list of dictionaries for JSON
    student_list = [{"StudentID": s[0], "Student_Name": s[1], "Program": s[2]} for s in students]
    return jsonify(student_list)

# Logout route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)