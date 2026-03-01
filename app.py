from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = "supersecretkey"

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'hospital_db'

mysql = MySQL(app)

# ------------------------
# 1️⃣ LOGIN PAGE
# ------------------------
@app.route("/")
def home():
    return render_template("login.html")


# ------------------------
# 2️⃣ LOGIN FUNCTION
# ------------------------
@app.route("/", methods=["GET","POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
    user = cur.fetchone()
    cur.close()

    if user:
        role = user[4]

        session["user"] = email
        session["role"] = role

        if role == "admin":
            return redirect("/admin")
        elif role == "doctor":
            return redirect("/doctor")
        elif role == "patient":
            return redirect("/patient")
        elif role == "receptionist":
            return redirect("/receptionist")
        elif role == "pharmacist":
            return redirect("/pharmacist")
    else :
        return "Invalid Login"


# ------------------------
# 3️⃣ 👉 PLACE STEP 4 HERE
# ------------------------
@app.route("/admin")
def admin_dashboard():
    if "user" in session and session["role"] == "admin":

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, name, email, role FROM users")
        users = cur.fetchall()
        cur.close()

        return render_template("admin.html", users=users)

    else:
        return redirect("/")
    
@app.route("/doctor")
def doctor_dashboard():
    if "user" in session and session["role"] == "doctor":

        cur = mysql.connection.cursor()

        # Show only this doctor's appointments
        cur.execute("""
            SELECT id, patient_email, appointment_date, status
            FROM appointments
            WHERE doctor_email = %s
        """, (session["user"],))

        appointments = cur.fetchall()
        cur.close()

        return render_template("doctor.html", appointments=appointments)

    else:
        return redirect("/")

@app.route("/patient")
def patient_dashboard():
    if "user" in session and session["role"] == "patient":
        return render_template("patient.html")
    else:
        return redirect("/")
    
@app.route("/receptionist")
def receptionist_dashboard():

    if "user" in session and session["role"] == "receptionist":

        cur = mysql.connection.cursor()

        cur.execute("""
                    SELECT a.id, a.patient_email, a.doctor_email, a.appointment_date, a.status,
                    b.id as bill_id, b.status as bill_status
                    FROM appointments a
                    LEFT JOIN bills b ON a.id = b.appointment_id
                    """)

        appointments = cur.fetchall()
        cur.close()

        return render_template("receptionist.html", appointments=appointments)

    else:
        return redirect("/")
    
@app.route("/pharmacist")
def pharmacist_dashboard():

    if "user" in session and session["role"] == "pharmacist":

        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT id, patient_email, doctor_email, medicine, status
            FROM prescriptions
        """)
        prescriptions = cur.fetchall()
        cur.close()

        return render_template("pharmacist.html", prescriptions=prescriptions)

    else:
        return redirect("/")

@app.route("/add_user", methods=["POST"])
def add_user():
    if "user" in session and session["role"] == "admin":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, password, role)
        )
        mysql.connection.commit()
        cur.close()

        return "User Added Successfully!"

    else:
        return redirect("/")
    
@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    if "user" in session and session["role"] == "admin":

        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        mysql.connection.commit()
        cur.close()

        return redirect("/admin")

    else:
        return redirect("/")

@app.route("/update_status/<int:appointment_id>/<string:new_status>")
def update_status(appointment_id, new_status):

    if "user" in session and session["role"] == "doctor":

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE appointments
            SET status = %s
            WHERE id = %s
        """, (new_status, appointment_id))

        mysql.connection.commit()
        cur.close()

        return redirect("/doctor")

    else:
        return redirect("/")
    
@app.route("/add_prescription/<int:appointment_id>")
def add_prescription(appointment_id):

    if "user" in session and session["role"] == "doctor":

        return render_template("add_prescription.html", appointment_id=appointment_id)

    else:
        return redirect("/")

@app.route("/save_prescription", methods=["POST"])
def save_prescription():

    if "user" in session and session["role"] == "doctor":

        appointment_id = request.form["appointment_id"]
        medicine = request.form["medicine"]
        notes = request.form["notes"]

        cur = mysql.connection.cursor()

        # Get patient email from appointment
        cur.execute("SELECT patient_email FROM appointments WHERE id=%s", (appointment_id,))
        patient = cur.fetchone()

        if patient:
            patient_email = patient[0]

            cur.execute("""
                INSERT INTO prescriptions 
                (appointment_id, doctor_email, patient_email, medicine, notes)
                VALUES (%s, %s, %s, %s, %s)
            """, (appointment_id, session["user"], patient_email, medicine, notes))

            mysql.connection.commit()

        cur.close()

        return redirect("/doctor")

    else:
        return redirect("/")
# ------------------------
# 4️⃣ LOGOUT
# ------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

#appointment system

@app.route("/book_appointment", methods=["POST"])
def book_appointment():
    if "user" in session and session["role"] == "patient":

        doctor_email = request.form["doctor_email"]
        appointment_date = request.form["appointment_date"]
        patient_email = session["user"]

        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO appointments (patient_email, doctor_email, appointment_date) VALUES (%s, %s, %s)",
            (patient_email, doctor_email, appointment_date)
        )
        mysql.connection.commit()
        cur.close()

        return "Appointment Booked Successfully!"

    else:
        return redirect("/")

@app.route("/view_prescriptions")
def view_prescriptions():

    if "user" in session and session["role"] == "patient":

        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT doctor_email, medicine, notes, status
            FROM prescriptions
            WHERE patient_email = %s
        """, (session["user"],))

        prescriptions = cur.fetchall()
        cur.close()

        return render_template("patient_prescriptions.html", prescriptions=prescriptions)

    else:
        return redirect("/")

@app.route("/mark_dispensed/<int:prescription_id>")
def mark_dispensed(prescription_id):

    if "user" in session and session["role"] == "pharmacist":

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE prescriptions
            SET status = 'Dispensed'
            WHERE id = %s
        """, (prescription_id,))

        mysql.connection.commit()
        cur.close()

        return redirect("/pharmacist")

    else:
        return redirect("/")
    
@app.route("/generate_bill/<int:appointment_id>/<string:patient_email>")
def generate_bill(appointment_id, patient_email):

    if "user" in session and session["role"] == "receptionist":

        cur = mysql.connection.cursor()

        # Check if bill already exists
        cur.execute("SELECT * FROM bills WHERE appointment_id = %s", (appointment_id,))
        existing_bill = cur.fetchone()

        if not existing_bill:
            amount = 500
            cur.execute("""
    SELECT a.id, a.patient_email, a.doctor_email, a.appointment_date, a.status,
           b.id as bill_id
    FROM appointments a
    LEFT JOIN bills b ON a.id = b.appointment_id
            """)

        cur.close()

        return redirect("/receptionist")

    else:
        return redirect("/")
    
@app.route("/view_bills")
def view_bills():

    if "user" in session and session["role"] == "patient":

        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT id, appointment_id, amount, status
            FROM bills
            WHERE patient_email = %s
        """, (session["user"],))

        bills = cur.fetchall()
        cur.close()

        return render_template("patient_bills.html", bills=bills)

    else:
        return redirect("/")

@app.route("/pay_bill/<int:bill_id>")
def pay_bill(bill_id):

    if "user" in session and session["role"] == "patient":

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE bills
            SET status = 'Paid'
            WHERE id = %s
        """, (bill_id,))

        mysql.connection.commit()
        cur.close()

        return redirect("/view_bills")

    else:
        return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)