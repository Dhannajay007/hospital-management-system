import hmac
import os
import re
import secrets
from datetime import date, time

from flask import Flask, abort, render_template, request, redirect, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

app.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST", "localhost")
app.config["MYSQL_USER"] = os.environ.get("MYSQL_USER", "root")
app.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD", "")
app.config["MYSQL_DB"] = os.environ.get("MYSQL_DB", "hospital_db")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "").lower() in {
    "1",
    "true",
    "yes",
}

mysql = MySQL(app)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def csrf_token():
    token = session.get("csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


@app.context_processor
def inject_csrf_token():
    return {"csrf_token": csrf_token}


@app.before_request
def protect_state_changing_requests():
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        expected_token = session.get("csrf_token")
        provided_token = request.form.get("csrf_token", "")
        if not expected_token or not hmac.compare_digest(expected_token, provided_token):
            abort(400, description="Invalid or missing CSRF token.")


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        is_legacy_password = bool(
            user and not user[3].startswith(("scrypt:", "pbkdf2:"))
        )
        password_matches = bool(
            user
            and (
                hmac.compare_digest(user[3], password)
                if is_legacy_password
                else check_password_hash(user[3], password)
            )
        )
        if password_matches:
            if is_legacy_password:
                cur = mysql.connection.cursor()
                cur.execute(
                    "UPDATE users SET password=%s WHERE id=%s",
                    (generate_password_hash(password), user[0]),
                )
                mysql.connection.commit()
                cur.close()

            session.clear()
            session["user"] = user[2]
            session["role"] = user[4]
            role_routes = {
                "admin": "/admin",
                "doctor": "/doctor",
                "patient": "/patient",
                "receptionist": "/receptionist",
                "pharmacist": "/pharmacist",
            }
            if user[4] in role_routes:
                return redirect(role_routes[user[4]])

        flash("Invalid email or password.")
        return redirect("/login")

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = "patient"

        if not re.fullmatch(r"[A-Za-z ]{1,100}", name):
            flash("Name must contain 1 to 100 letters and spaces.")
            return redirect("/signup")
        if not EMAIL_PATTERN.fullmatch(email) or len(email) > 100:
            flash("Please enter a valid email address.")
            return redirect("/signup")
        if not password.strip() or len(password) > 128:
            flash("Password must contain between 1 and 128 characters.")
            return redirect("/signup")

        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            cur.close()
            flash("Email already exists.")
            return redirect("/signup")

        cur.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, generate_password_hash(password), role),
        )
        mysql.connection.commit()
        cur.close()

        flash("Account created successfully. Please log in.")
        return redirect("/login")

    return render_template("signup.html")


@app.route("/admin")
def admin():
    if "user" not in session or session.get("role") != "admin":
        return redirect("/")

    cur = mysql.connection.cursor()
    search = request.args.get("search", "")

    if search:
        cur.execute(
            "SELECT id, name, email, role FROM users WHERE name LIKE %s OR email LIKE %s ORDER BY id DESC",
            ("%" + search + "%", "%" + search + "%"),
        )
    else:
        cur.execute("SELECT id, name, email, role FROM users ORDER BY id DESC")

    users = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE role='doctor'")
    doctor_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE role='patient'")
    patient_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE role='pharmacist'")
    pharmacist_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE role='receptionist'")
    reception_count = cur.fetchone()[0]
    cur.close()

    return render_template(
        "admin.html",
        users=users,
        total_users=total_users,
        doctor_count=doctor_count,
        patient_count=patient_count,
        pharmacist_count=pharmacist_count,
        reception_count=reception_count,
    )


@app.route("/doctor")
def doctor():
    if "user" not in session or session.get("role") != "doctor":
        return redirect("/")

    doctor_email = session["user"]
    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT COUNT(DISTINCT patient_email) FROM requests WHERE doctor_email=%s AND status='accepted'",
        (doctor_email,),
    )
    total_patients = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM prescriptions WHERE doctor_email=%s",
        (doctor_email,),
    )
    total_prescriptions = cur.fetchone()[0]

    cur.execute(
        "SELECT id, patient_email, doctor_email, appointment_date, appointment_time, status FROM requests WHERE doctor_email=%s ORDER BY id DESC",
        (doctor_email,),
    )
    requests = cur.fetchall()

    cur.execute(
        "SELECT DISTINCT patient_email FROM requests WHERE doctor_email=%s AND status='accepted' ORDER BY patient_email",
        (doctor_email,),
    )
    accepted_patients = cur.fetchall()

    cur.close()

    return render_template(
        "doctor.html",
        requests=requests,
        accepted_patients=accepted_patients,
        total_patients=total_patients,
        total_prescriptions=total_prescriptions,
    )


@app.route("/accept/<int:id>", methods=["POST"])
def accept(id):
    if "user" not in session or session.get("role") != "doctor":
        return redirect("/")

    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE requests SET status='accepted' WHERE id=%s AND doctor_email=%s",
        (id, session["user"]),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/doctor")


@app.route("/reject/<int:id>", methods=["POST"])
def reject(id):
    if "user" not in session or session.get("role") != "doctor":
        return redirect("/")

    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE requests SET status='rejected' WHERE id=%s AND doctor_email=%s",
        (id, session["user"]),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/doctor")


@app.route("/delete_request/<int:id>", methods=["POST"])
def delete_request(id):
    if "user" not in session or session.get("role") != "doctor":
        return redirect("/")

    cur = mysql.connection.cursor()
    cur.execute(
        "DELETE FROM requests WHERE id=%s AND doctor_email=%s",
        (id, session["user"]),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/doctor")


@app.route("/add_prescription", methods=["POST"])
def add_prescription():
    if "user" not in session or session.get("role") != "doctor":
        return redirect("/")

    patient_email = request.form.get("patient_email")
    medicine = request.form.get("medicine")
    notes = request.form.get("notes")
    doctor_email = session["user"]

    if not patient_email or not medicine or not notes:
        flash("Please fill all prescription fields.")
        return redirect("/doctor")

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id FROM requests WHERE patient_email=%s AND doctor_email=%s AND status='accepted' ORDER BY id DESC LIMIT 1",
        (patient_email, doctor_email),
    )
    appointment = cur.fetchone()
    if not appointment:
        cur.close()
        flash("Prescriptions can only be added for your accepted patients.")
        return redirect("/doctor")

    cur.execute(
        "INSERT INTO prescriptions (appointment_id, patient_email, doctor_email, medicine, notes, status) VALUES (%s, %s, %s, %s, %s, 'Pending')",
        (appointment[0], patient_email, doctor_email, medicine, notes),
    )
    mysql.connection.commit()
    cur.close()

    return redirect("/doctor")


@app.route("/patient")
def patient_dashboard():
    if "user" not in session or session.get("role") != "patient":
        return redirect("/")

    patient_email = session["user"]
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, email, role FROM users WHERE role='doctor' ORDER BY id DESC")
    doctors = cur.fetchall()

    cur.execute(
        "SELECT id, doctor_email, appointment_date, status FROM requests WHERE patient_email=%s ORDER BY id DESC",
        (patient_email,),
    )
    requests = cur.fetchall()
    cur.close()

    return render_template("patient.html", doctors=doctors, requests=requests)


@app.route("/receptionist")
def receptionist_dashboard():
    if "user" not in session or session.get("role") != "receptionist":
        return redirect("/")

    cur = mysql.connection.cursor()
    cur.execute(
        """
        SELECT r.id, r.patient_email, r.doctor_email, r.appointment_date, r.status,
               b.id AS bill_id, b.status AS bill_status
        FROM requests r
        LEFT JOIN bills b ON r.id = b.appointment_id
        ORDER BY r.id DESC
        """
    )
    requests = cur.fetchall()
    cur.close()

    return render_template("receptionist.html", requests=requests)


@app.route("/pharmacist")
def pharmacist_dashboard():
    if "user" not in session or session.get("role") != "pharmacist":
        return redirect("/")

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id, patient_email, doctor_email, medicine, status FROM prescriptions ORDER BY id DESC"
    )
    prescriptions = cur.fetchall()
    cur.close()

    return render_template("pharmacist.html", prescriptions=prescriptions)


@app.route("/dispense/<int:id>", methods=["POST"])
def dispense(id):
    if "user" not in session or session.get("role") != "pharmacist":
        return redirect("/")

    cur = mysql.connection.cursor()
    cur.execute("UPDATE prescriptions SET status='dispensed' WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect("/pharmacist")


@app.route("/add_user", methods=["POST"])
def add_user():
    if "user" not in session or session.get("role") != "admin":
        return redirect("/")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role")

    if not re.fullmatch(r"[A-Za-z ]{1,100}", name):
        flash("Name must contain 1 to 100 letters and spaces.")
        return redirect("/admin")
    if not EMAIL_PATTERN.fullmatch(email) or len(email) > 100:
        flash("Please enter a valid email address.")
        return redirect("/admin")
    if not password.strip() or len(password) > 128:
        flash("Password must contain between 1 and 128 characters.")
        return redirect("/admin")
    if role not in {"admin", "doctor", "patient", "receptionist", "pharmacist"}:
        flash("Please select a valid role.")
        return redirect("/admin")

    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cur.fetchone():
        cur.close()
        flash("Email already exists.")
        return redirect("/admin")

    cur.execute(
        "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
        (name, email, generate_password_hash(password), role),
    )
    mysql.connection.commit()
    cur.close()

    flash("User added successfully.")
    return redirect("/admin")


@app.route("/delete_user/<int:id>", methods=["POST"])
def delete_user(id):
    if "user" not in session or session.get("role") != "admin":
        return redirect("/")

    cur = mysql.connection.cursor()
    cur.execute(
        "DELETE FROM users WHERE id=%s AND email<>%s",
        (id, session["user"]),
    )
    deleted = cur.rowcount
    mysql.connection.commit()
    cur.close()
    if deleted == 0:
        flash("Your own account cannot be deleted from this page.")
    return redirect("/admin")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/")


@app.route("/book_appointment", methods=["POST"])
def book_appointment():
    if "user" not in session or session.get("role") != "patient":
        return redirect("/")

    patient_email = session["user"]
    doctor_email = request.form.get("doctor_email")
    appointment_date = request.form.get("appointment_date")
    appointment_time = request.form.get("appointment_time")

    if not doctor_email or not appointment_date or not appointment_time:
        flash("Please choose doctor, date, and time.")
        return redirect("/patient")

    try:
        selected_date = date.fromisoformat(appointment_date)
        time.fromisoformat(appointment_time)
    except ValueError:
        flash("Please enter a valid appointment date and time.")
        return redirect("/patient")
    if selected_date < date.today():
        flash("Appointments cannot be booked for a past date.")
        return redirect("/patient")

    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM users WHERE email=%s AND role='doctor'", (doctor_email,))
    if not cur.fetchone():
        cur.close()
        flash("Please select a valid doctor.")
        return redirect("/patient")

    cur.execute(
        "INSERT INTO requests (patient_email, doctor_email, appointment_date, appointment_time, status) VALUES (%s, %s, %s, %s, 'pending')",
        (patient_email, doctor_email, appointment_date, appointment_time),
    )
    mysql.connection.commit()
    cur.close()

    flash("Appointment booked successfully.")
    return redirect("/patient")


@app.route("/view_prescriptions")
def view_prescriptions():
    if "user" not in session or session.get("role") != "patient":
        return redirect("/")

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id, doctor_email, medicine, status FROM prescriptions WHERE patient_email=%s ORDER BY id DESC",
        (session["user"],),
    )
    prescriptions = cur.fetchall()
    cur.close()

    return render_template("patient_prescriptions.html", prescriptions=prescriptions)


@app.route("/generate_bill/<int:appointment_id>", methods=["POST"])
def generate_bill(appointment_id):
    if "user" not in session or session.get("role") != "receptionist":
        return redirect("/")

    cur = mysql.connection.cursor()
    cur.execute("SELECT patient_email FROM requests WHERE id=%s", (appointment_id,))
    appointment = cur.fetchone()
    if not appointment:
        cur.close()
        flash("Appointment not found.")
        return redirect("/receptionist")

    cur.execute("SELECT * FROM bills WHERE appointment_id=%s", (appointment_id,))
    existing_bill = cur.fetchone()

    if not existing_bill:
        amount = 500
        cur.execute(
            "INSERT INTO bills (appointment_id, patient_email, amount, status) VALUES (%s, %s, %s, 'Unpaid')",
            (appointment_id, appointment[0], amount),
        )
    mysql.connection.commit()
    cur.close()

    return redirect("/receptionist")


@app.route("/view_bills")
def view_bills():
    if "user" not in session or session.get("role") != "patient":
        return redirect("/")

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id, appointment_id, amount, status FROM bills WHERE patient_email=%s ORDER BY id DESC",
        (session["user"],),
    )
    bills = cur.fetchall()
    cur.close()

    return render_template("patient_bills.html", bills=bills)


@app.route("/pay_bill/<int:bill_id>", methods=["POST"])
def pay_bill(bill_id):
    if "user" not in session or session.get("role") != "patient":
        return redirect("/")

    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE bills SET status='Paid' WHERE id=%s AND patient_email=%s AND status='Unpaid'",
        (bill_id, session["user"]),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/view_bills")


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
