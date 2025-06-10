-- ─── Създаване на Базата Данни ───────────────────────────────────────────────────
CREATE DATABASE IF NOT EXISTS diary
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE diary;

-- ─── Таблица: users ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') NOT NULL DEFAULT 'user'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Таблица: students ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    `class` VARCHAR(20) NOT NULL,
    date_of_birth DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Таблица: grades ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS grades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject VARCHAR(50) NOT NULL,
    grade TINYINT NOT NULL CHECK (grade BETWEEN 2 AND 6),
    date_given DATE NOT NULL,
    teacher_id INT,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Таблица: absences ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS absences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    date_absent DATE NOT NULL,
    is_justified BOOLEAN DEFAULT FALSE,
    teacher_id INT,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
