-- ===============================================
-- Eagle OCR Vehicle Management Database
-- PostgreSQL SQL Script with JSON support
-- 35 tables with relationships and constraints
-- ===============================================

-- 1. Users (for analysts, officers, admins)
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL, -- e.g., admin, analyst, enforcement
    contact JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Vehicles
CREATE TABLE Vehicles (
    vehicle_id SERIAL PRIMARY KEY,
    plate_number VARCHAR(15) UNIQUE NOT NULL,
    type VARCHAR(20) NOT NULL, -- LCV, Medium, Heavy, Tanker
    capacity_tons NUMERIC(5,2),
    owner_info JSONB,
    registration_date DATE,
    status VARCHAR(20) DEFAULT 'active'
);

-- 3. VehicleTypes (Reference table)
CREATE TABLE VehicleTypes (
    type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(20) UNIQUE NOT NULL,
    description TEXT
);

-- 4. VehicleOwners
CREATE TABLE VehicleOwners (
    owner_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact JSONB,
    address TEXT
);

-- 5. Cameras
CREATE TABLE Cameras (
    camera_id SERIAL PRIMARY KEY,
    zone_id INT REFERENCES CameraZones(zone_id),
    type VARCHAR(20) NOT NULL, -- parking, weighbridge, border
    location JSONB, -- latitude & longitude
    status VARCHAR(20) DEFAULT 'active'
);

-- 6. CameraZones
CREATE TABLE CameraZones (
    zone_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    location JSONB,
    type VARCHAR(20), -- parking, weighbridge, border
    priority INT DEFAULT 1
);

-- 7. WeighbridgePasses
CREATE TABLE WeighbridgePasses (
    pass_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES Vehicles(vehicle_id),
    camera_id INT REFERENCES Cameras(camera_id),
    weight_kg NUMERIC(8,2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fine_applied NUMERIC(10,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'ok',
    additional_info JSONB
);

-- 8. ParkingRecords
CREATE TABLE ParkingRecords (
    parking_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES Vehicles(vehicle_id),
    zone_id INT REFERENCES CameraZones(zone_id),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    fee NUMERIC(10,2) DEFAULT 0,
    payment_status VARCHAR(20) DEFAULT 'unpaid',
    details JSONB
);

-- 9. ParkingFees
CREATE TABLE ParkingFees (
    fee_id SERIAL PRIMARY KEY,
    vehicle_type VARCHAR(20),
    daily_fee NUMERIC(10,2),
    notes TEXT
);

-- 10. Fines
CREATE TABLE Fines (
    fine_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES Vehicles(vehicle_id),
    fine_type VARCHAR(50),
    amount NUMERIC(10,2),
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid BOOLEAN DEFAULT FALSE,
    details JSONB
);

-- 11. FinesAdjustments
CREATE TABLE FinesAdjustments (
    adjustment_id SERIAL PRIMARY KEY,
    fine_id INT REFERENCES Fines(fine_id),
    adjusted_amount NUMERIC(10,2),
    reason TEXT,
    authorized_by INT REFERENCES Users(user_id),
    adjustment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. Payments
CREATE TABLE Payments (
    payment_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES Vehicles(vehicle_id),
    amount NUMERIC(10,2) NOT NULL,
    payment_method INT REFERENCES PaymentMethods(method_id),
    paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

-- 13. PaymentMethods
CREATE TABLE PaymentMethods (
    method_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    fees NUMERIC(5,2),
    notes TEXT
);

-- 14. Taxes
CREATE TABLE Taxes (
    tax_id SERIAL PRIMARY KEY,
    vehicle_type VARCHAR(20),
    basis VARCHAR(50),
    amount NUMERIC(10,2),
    notes TEXT
);

-- 15. BorderCrossings
CREATE TABLE BorderCrossings (
    crossing_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES Vehicles(vehicle_id),
    camera_id INT REFERENCES Cameras(camera_id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    entry_exit VARCHAR(10), -- entry/exit
    country_or_county VARCHAR(50),
    details JSONB
);

-- 16. TrafficIncidents
CREATE TABLE TrafficIncidents (
    incident_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES Vehicles(vehicle_id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    location JSONB,
    description TEXT,
    fine_applied NUMERIC(10,2),
    resolved BOOLEAN DEFAULT FALSE
);

-- 17. VehicleInspections
CREATE TABLE VehicleInspections (
    inspection_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES Vehicles(vehicle_id),
    inspector_id INT REFERENCES Users(user_id),
    inspection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    result VARCHAR(50),
    notes JSONB
);

-- 18. VehicleMaintenance
CREATE TABLE VehicleMaintenance (
    maintenance_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES Vehicles(vehicle_id),
    service_type VARCHAR(50),
    service_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cost NUMERIC(10,2),
    service_provider TEXT,
    details JSONB
);

-- 19. VehicleInsurance
CREATE TABLE VehicleInsurance (
    insurance_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES Vehicles(vehicle_id),
    provider VARCHAR(50),
    policy_number VARCHAR(50),
    start_date DATE,
    end_date DATE,
    coverage_type VARCHAR(50),
    amount NUMERIC(10,2)
);

-- 20. LicensePlates
CREATE TABLE LicensePlates (
    plate_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES Vehicles(vehicle_id),
    plate_number VARCHAR(15) UNIQUE NOT NULL,
    issue_date DATE,
    expiry_date DATE,
    plate_type VARCHAR(20)
);

-- 21. RevenueForecasts
CREATE TABLE RevenueForecasts (
    forecast_id SERIAL PRIMARY KEY,
    month INT,
    year INT,
    projected_parking NUMERIC(12,2),
    projected_fines NUMERIC(12,2),
    projected_taxes NUMERIC(12,2),
    notes JSONB
);

-- 22. VehicleLogs
CREATE TABLE VehicleLogs (
    log_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES Vehicles(vehicle_id),
    event_type VARCHAR(50),
    event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- 23. LorryTypes
CREATE TABLE LorryTypes (
    lorry_type_id SERIAL PRIMARY KEY,
    name VARCHAR(20),
    description TEXT
);

-- 24. CamerasMaintenance
CREATE TABLE CamerasMaintenance (
    maintenance_id SERIAL PRIMARY KEY,
    camera_id INT REFERENCES Cameras(camera_id),
    service_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    service_type VARCHAR(50),
    notes JSONB
);

-- 25. AnalyticsReports
CREATE TABLE AnalyticsReports (
    report_id SERIAL PRIMARY KEY,
    report_type VARCHAR(50),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data JSONB
);

-- 26. UserRoles
CREATE TABLE UserRoles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(20),
    permissions JSONB
);

-- 27. VehicleHistory
CREATE TABLE VehicleHistory (
    history_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES Vehicles(vehicle_id),
    event JSONB,
    event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 28. ComplianceRecords
CREATE TABLE ComplianceRecords (
    compliance_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES Vehicles(vehicle_id),
    type VARCHAR(50),
    status VARCHAR(20),
    details JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 29. Alerts
CREATE TABLE Alerts (
    alert_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES Vehicles(vehicle_id),
    alert_type VARCHAR(50),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE
);

-- 30. Notifications
CREATE TABLE Notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id),
    title VARCHAR(100),
    message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read BOOLEAN DEFAULT FALSE,
    metadata JSONB
);

-- 31. DeviceLogs
CREATE TABLE DeviceLogs (
    log_id SERIAL PRIMARY KEY,
    device_id INT,
    type VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 32. VehicleCategories
CREATE TABLE VehicleCategories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    description TEXT
);

-- 33. WeightLimits
CREATE TABLE WeightLimits (
    limit_id SERIAL PRIMARY KEY,
    vehicle_type VARCHAR(20),
    max_weight NUMERIC(8,2),
    notes TEXT
);

-- 34. ParkingZones
CREATE TABLE ParkingZones (
    zone_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    location JSONB,
    capacity INT
);

-- 35. TaxRecords
CREATE TABLE TaxRecords (
    record_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES Vehicles(vehicle_id),
    tax_id INT REFERENCES Taxes(tax_id),
    amount NUMERIC(12,2),
    paid BOOLEAN DEFAULT FALSE,
    due_date DATE,
    paid_at TIMESTAMP,
    details JSONB
);

-- ===============================================
-- Notes:
-- - All JSONB columns allow flexible data exchange with APIs.
-- - Foreign keys enforce relationships for analytics and reporting.
-- - Designed for real-time and historical analytics integration.
-- ===============================================
