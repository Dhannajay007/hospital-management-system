-- Create database
CREATE DATABASE IF NOT EXISTS hospital_db;

-- Use database
USE hospital_db;

-- =========================
-- USERS TABLE
-- =========================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL
);

-- =========================
-- REQUESTS TABLE
-- =========================
CREATE TABLE IF NOT EXISTS requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_email VARCHAR(100) NOT NULL,
    doctor_email VARCHAR(100) NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status VARCHAR(50) DEFAULT 'pending'
);

-- =========================
-- PRESCRIPTIONS TABLE
-- =========================
CREATE TABLE IF NOT EXISTS prescriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT,
    doctor_email VARCHAR(100),
    patient_email VARCHAR(100),
    medicine TEXT,
    notes TEXT,
    status VARCHAR(50) DEFAULT 'Pending'
);

-- =========================
-- BILLS TABLE
-- =========================
CREATE TABLE IF NOT EXISTS bills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT,
    patient_email VARCHAR(100),
    amount INT,
    status VARCHAR(50) DEFAULT 'Unpaid',
    UNIQUE KEY unique_bill_appointment (appointment_id)
);
