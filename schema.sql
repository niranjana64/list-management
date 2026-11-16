CREATE DATABASE IF NOT EXISTS list_management_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE list_management_db;

CREATE TABLE IF NOT EXISTS records (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    record_title VARCHAR(200) NOT NULL,
    description TEXT NULL,
    location VARCHAR(100) NOT NULL,
    region ENUM('International', 'North', 'South', 'SouthCentral', 'West') NOT NULL,
    status ENUM('RECEIVED', 'ACKNOWLEDGED', 'WIP', 'TECH-COMPLETED', 'CLOSED')
        NOT NULL DEFAULT 'RECEIVED',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_records_created_at (created_at),
    INDEX idx_records_location (location),
    INDEX idx_records_region (region),
    INDEX idx_records_status (status)
);

INSERT INTO records (record_title, description, location, region, status, created_at)
VALUES
('Website access request', 'Sample record for testing the dashboard.', 'Chennai', 'South', 'RECEIVED', NOW()),
('Email configuration issue', 'Sample record for testing status filters.', 'Bangalore', 'South', 'WIP', DATE_SUB(NOW(), INTERVAL 5 DAY)),
('New user onboarding', 'Sample record for testing location filters.', 'Ahmedabad', 'West', 'ACKNOWLEDGED', DATE_SUB(NOW(), INTERVAL 12 DAY)),
('Application testing', 'Sample completed record.', 'Delhi', 'North', 'TECH-COMPLETED', DATE_SUB(NOW(), INTERVAL 35 DAY)),
('Access closure', 'Sample closed record.', 'Dhaka', 'International', 'CLOSED', DATE_SUB(NOW(), INTERVAL 70 DAY));
