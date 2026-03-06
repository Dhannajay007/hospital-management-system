-- Create database
CREATE DATABASE hospital_db;

-- Use database
USE hospital_db;


-- =========================
-- USERS TABLE
-- =========================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(100),
    role VARCHAR(50)
);


-- =========================
-- APPOINTMENTS TABLE
-- =========================
CREATE TABLE appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_email VARCHAR(100),
    doctor_email VARCHAR(100),
    appointment_date DATE,
    status VARCHAR(50)
);


-- =========================
-- PRESCRIPTIONS TABLE
-- =========================
CREATE TABLE prescriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT,
    doctor_email VARCHAR(100),
    patient_email VARCHAR(100),
    medicine TEXT,
    notes TEXT,
    status VARCHAR(50)
);


-- =========================
-- BILLS TABLE
-- =========================
CREATE TABLE bills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT,
    patient_email VARCHAR(100),
    amount INT,
    status VARCHAR(50)
);