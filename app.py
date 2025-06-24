from flask import Flask, request, render_template, redirect, url_for, jsonify
import mysql.connector

app = Flask(__name__)

# MySQL configuration (update with your credentials)
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234SQL05',
    'database': 'student_application_system'
}

# Program mapping from form values to full names
program_mapping = {
    "bsc-cs": "BSc. Computer Science",
    "bsc-it": "BSc. Information Technology",
    "bsc-telecom": "BSc. Telecommunications Engineering"
}

@app.route('/', methods=['GET', 'POST'])
def apply():
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
    return render_template('index.html')

@app.route('/view')
def view():
    return render_template('view.html')

@app.route('/api/students')
def get_students():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT StudentID, Student_Name, Program FROM Student_Information")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    # Convert to list of dictionaries for JSON
    student_list = [{"StudentID": s[0], "Student_Name": s[1], "Program": s[2]} for s in students]
    return jsonify(student_list)

if __name__ == '__main__':
    app.run(debug=True)