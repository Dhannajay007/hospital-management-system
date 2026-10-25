# CityCare Hospital Management System

A college mini project demonstrating a Flask web application backed by MySQL.
It provides separate workflows for administrators, doctors, patients,
receptionists, and pharmacists.

## What the project does

- **Patient:** create an account, book appointments, check appointment status,
  view prescriptions and bills, and mark a demo bill as paid.
- **Doctor:** review assigned appointments, accept or reject them, and add
  prescriptions for accepted patients.
- **Receptionist:** review appointments and generate one bill per appointment.
- **Pharmacist:** review prescriptions and mark them as dispensed.
- **Administrator:** search users and add or delete accounts.

The bill action only changes a status in the database. There is no payment
gateway. The pharmacist workflow tracks dispensing status only; it does not
manage medicine inventory.

## Requirements

- Python 3.10 or newer
- MySQL Server
- `mysql` command-line client (for schema setup)
- On Windows, a compatible `mysqlclient` wheel must be available to pip. If
  installation reports a build error, install the MySQL client build tools
  required by `mysqlclient` for your Python version.

## Setup on Windows

Run these commands from the project directory in PowerShell.

1. Create and activate a virtual environment:

   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use `.\venv\Scripts\python.exe` instead of
   activating the environment.

2. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Create the database tables using a MySQL account with database permissions:

   ```powershell
   Get-Content .\database.sql | mysql -u root -p
   ```

   Enter the MySQL password when prompted. The script creates and selects the
   `hospital_db` database.

4. Set the connection settings and a stable Flask session secret:

   ```powershell
   $env:MYSQL_HOST = "localhost"
   $env:MYSQL_USER = "root"
   $env:MYSQL_PASSWORD = "your-mysql-password"
   $env:MYSQL_DB = "hospital_db"
   $env:SECRET_KEY = "replace-with-a-long-random-secret"
   ```

   These variables are for the current PowerShell window. Do not commit real
   credentials or secrets to Git. If `SECRET_KEY` is omitted, the app generates
   a random value each time it starts, which invalidates existing login
   sessions after a restart.

5. Start the app:

   ```powershell
   python app.py
   ```

6. Open <http://127.0.0.1:5000>.

The app uses Flask's built-in development server. `FLASK_DEBUG=1` enables debug
mode; leave it unset for the normal local demo. This server is not intended
for production deployment.

## Create the first administrator

Public signup only creates patient accounts. Create the first administrator
directly in MySQL using a Werkzeug password hash.

Generate a hash from the activated virtual environment:

```powershell
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('choose-a-strong-password'))"
```

Copy the generated value into this SQL statement and run it against
`hospital_db`:

```sql
INSERT INTO users (name, email, password, role)
VALUES ('Administrator', 'admin@example.com', '<paste-generated-hash>', 'admin');
```

Do not put a plain-text password into the database.

## Verify the project

Run the automated tests from the activated environment:

```powershell
python -m unittest discover -s tests -v
```

The tests use a mocked database and do not require MySQL. For a manual demo,
sign up a patient, then use an administrator account to add doctor,
receptionist, and pharmacist accounts. Log in as each role and try the
workflows listed above. Use test data only.

## Existing database migration

`CREATE TABLE IF NOT EXISTS` in `database.sql` creates missing tables but does
not alter tables that already exist. Back up an existing database before
migrating it.

The current app stores Werkzeug password hashes, which need a
`VARCHAR(255)` column. If the existing `users.password` column is still
`VARCHAR(100)`, run:

```sql
ALTER TABLE users MODIFY password VARCHAR(255) NOT NULL;
```

After widening the column, users with legacy plain-text passwords can log in
once; the app upgrades each password to a hash during that login.

The current schema also prevents more than one bill per appointment. Before
adding that constraint to an existing database, check for duplicate
appointments:

```sql
SELECT appointment_id, COUNT(*)
FROM bills
WHERE appointment_id IS NOT NULL
GROUP BY appointment_id
HAVING COUNT(*) > 1;
```

Resolve any duplicates first. Add the constraint only if it is not already
present:

```sql
ALTER TABLE bills
ADD UNIQUE KEY unique_bill_appointment (appointment_id);
```

## Database tables

- `users` — account details, password hash, and role
- `requests` — patient appointment requests and their status
- `prescriptions` — prescribed medicine, notes, and dispensing status
- `bills` — appointment bill amount and demo payment status

## Security and project scope

The app includes role checks, CSRF tokens for state-changing requests,
parameterized SQL, and password hashing for newly registered accounts. It is
an educational demonstration, not a production-ready healthcare system. Do not
use real patient information. It does not include a payment provider, medicine
stock control, appointment notifications, or production deployment
configuration.
