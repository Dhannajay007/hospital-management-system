🏥 Hospital Management System

A complete Multi-Role Hospital Management Web Application built using Flask and MySQL.

This project demonstrates backend logic, authentication, role-based dashboards, and database integration for a real-world hospital workflow system.


---

🚀 Tech Stack

Backend: Python (Flask)

Database: MySQL

Frontend: HTML, CSS, JavaScript

Version Control: Git & GitHub



---

👥 User Roles & Features

🔐 1. Admin

Add / Remove Doctors

Add / Remove Patients

Add / Remove Staff

Manage system users


---

👨‍⚕️ 2. Doctor

View assigned appointments

Accept / Reject appointments

Add prescriptions

View patient details



---

🧑‍🤝‍🧑 3. Patient

Book appointments

View appointment status

View prescriptions

View bills

Track payment status



---

🧾 4. Receptionist

View all appointments

Schedule appointments

Generate bills

View bill status (Paid / Unpaid)



---

💊 5. Pharmacist

View prescriptions

Dispense medicines

Update medicine stock

Track dispensed status



---

🗂️ Project Structure

hospital_management/
│
├── app.py
├── templates/
│   ├── login.html
│   ├── admin.html
│   ├── doctor.html
│   ├── patient.html
│   ├── receptionist.html
│   ├── pharmacist.html
│   ├── add_prescription.html
│   ├── patient_prescriptions.html
│   └── patient_bills.html
│
└── venv/


---

🗄️ Database

MySQL database is used with structured relational tables:

users

appointments

prescriptions

bills

medicines


The system follows proper relational mapping between:

Patients

Doctors

Appointments

Prescriptions

Billing



---

🔒 Authentication System

Role-based login

Session-based authentication

Protected routes

Dashboard access based on user role



---

⚙️ How To Run This Project

1️⃣ Clone Repository

git clone https://github.com/your-username/hospital-management-system.git
cd hospital-management-system

2️⃣ Create Virtual Environment

python -m venv venv

Activate:

Windows:

venv\Scripts\activate

Mac/Linux:

source venv/bin/activate

3️⃣ Install Dependencies

pip install flask mysqlclient

4️⃣ Setup MySQL Database

Create database

Update database credentials in app.py


5️⃣ Run Application

python app.py

Open browser:

http://127.0.0.1:5000

---

screenhots:

for screenshots of our ui please refer to screenshots folder


---

🎯 Future Improvements

Payment Gateway Integration

Email Notifications

Role-based permission enhancements

REST API conversion



---

📌 Learning Outcomes

This project demonstrates:

Backend architecture using Flask

Database design & relational mapping

Session management

Role-based authentication

Real-world workflow simulation



---

👨‍💻 Author

Developed by kanak sharma/jatin singh/omkar shewale/Dhannajay singh

---

note: this is a mini project build by CSE students of watmull institute of technology

