-- Borrowers table
CREATE TABLE IF NOT EXISTS borrowers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Loans table
CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    borrower_id INTEGER NOT NULL,
    principal_given REAL NOT NULL,
    outstanding_principal REAL NOT NULL,
    monthly_rate REAL NOT NULL,
    interest_due_day INTEGER DEFAULT 5,
    given_date DATE NOT NULL,
    status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Closed')),
    closed_date DATE,
    close_reason TEXT,
    document_received BOOLEAN DEFAULT 0,
    document_type TEXT,
    document_path TEXT,
    document_received_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (borrower_id) REFERENCES borrowers(id)
);

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER NOT NULL,
    payment_date DATE NOT NULL,
    interest_month TEXT NOT NULL,
    total_received REAL NOT NULL,
    interest_paid REAL NOT NULL,
    principal_paid REAL NOT NULL,
    payment_mode TEXT,
    reference TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_id) REFERENCES loans(id),
    CHECK (total_received = interest_paid + principal_paid)
);

-- User table for PIN authentication
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pin_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDIVIDUAL CHIT MANAGEMENT (Borrower-specific chits with monthly schedules)
-- ============================================================================

-- Individual Chits table (tracks chits given to borrowers)
CREATE TABLE IF NOT EXISTS chits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    borrower_id INTEGER NOT NULL,
    borrower_name TEXT NOT NULL,
    chit_name TEXT NOT NULL,
    total_months INTEGER NOT NULL,
    start_date DATE NOT NULL,
    prized_month INTEGER,
    prize_amount REAL,
    status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Completed', 'Closed')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (borrower_id) REFERENCES borrowers(id)
);

-- Chit Monthly Schedule table
CREATE TABLE IF NOT EXISTS chit_monthly_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chit_id INTEGER NOT NULL,
    month_number INTEGER NOT NULL,
    due_date DATE NOT NULL,
    due_amount REAL NOT NULL,
    payment_status TEXT DEFAULT 'Pending' CHECK(payment_status IN ('Pending', 'Paid', 'Partial', 'Adjusted')),
    paid_amount REAL DEFAULT 0,
    paid_date DATE,
    payment_mode TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chit_id) REFERENCES chits(id),
    UNIQUE(chit_id, month_number)
);

-- Chit Adjustments table (tracks adjustments against loan interest)
CREATE TABLE IF NOT EXISTS chit_adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id INTEGER NOT NULL,
    loan_id INTEGER NOT NULL,
    interest_month TEXT NOT NULL,
    adjusted_amount REAL NOT NULL,
    adjustment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_id) REFERENCES chit_monthly_schedule(id),
    FOREIGN KEY (loan_id) REFERENCES loans(id)
);

-- ============================================================================
-- CHIT MODULE (India chit member + borrower interest adjustment)
-- ============================================================================

-- Chit Groups (my memberships)
CREATE TABLE IF NOT EXISTS chit_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    monthly_installment REAL NOT NULL,
    start_month TEXT NOT NULL,  -- YYYY-MM format
    status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Closed')),
    closed_month TEXT,  -- YYYY-MM format, nullable
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (status = 'Active' OR closed_month IS NOT NULL)  -- Closed chits must have closed_month
);

-- Borrower-Chit Links (which borrowers are in which chits)
CREATE TABLE IF NOT EXISTS borrower_chit_links (
    borrower_id INTEGER NOT NULL,
    chit_id INTEGER NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (borrower_id, chit_id),
    FOREIGN KEY (borrower_id) REFERENCES borrowers(id),
    FOREIGN KEY (chit_id) REFERENCES chit_groups(id)
);

-- Adjustments (bridge between interest and chit + audit trail)
CREATE TABLE IF NOT EXISTS adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    borrower_id INTEGER NOT NULL,
    interest_month TEXT NOT NULL,  -- YYYY-MM source bucket
    chit_id INTEGER NOT NULL,
    chit_month TEXT NOT NULL,  -- YYYY-MM target bucket
    amount REAL NOT NULL CHECK(amount > 0),
    status TEXT DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'REVERSED')),
    reversal_of_id INTEGER,  -- Points to the adjustment being reversed
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (borrower_id) REFERENCES borrowers(id),
    FOREIGN KEY (chit_id) REFERENCES chit_groups(id),
    FOREIGN KEY (reversal_of_id) REFERENCES adjustments(id),
    CHECK (reversal_of_id IS NULL OR reversal_of_id != id)  -- Cannot reverse itself
);

-- Direct Chit Payments (optional - for cash payments not from interest)
CREATE TABLE IF NOT EXISTS direct_chit_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    borrower_id INTEGER NOT NULL,
    chit_id INTEGER NOT NULL,
    chit_month TEXT NOT NULL,  -- YYYY-MM
    amount REAL NOT NULL CHECK(amount > 0),
    payment_date DATE NOT NULL,
    payment_mode TEXT,
    reference TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (borrower_id) REFERENCES borrowers(id),
    FOREIGN KEY (chit_id) REFERENCES chit_groups(id)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_loans_borrower ON loans(borrower_id);
CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status);
CREATE INDEX IF NOT EXISTS idx_payments_loan ON payments(loan_id);
CREATE INDEX IF NOT EXISTS idx_payments_interest_month ON payments(interest_month);
CREATE INDEX IF NOT EXISTS idx_chits_borrower ON chits(borrower_id);
CREATE INDEX IF NOT EXISTS idx_chits_status ON chits(status);
CREATE INDEX IF NOT EXISTS idx_chit_schedule_chit ON chit_monthly_schedule(chit_id);
CREATE INDEX IF NOT EXISTS idx_chit_adjustments_schedule ON chit_adjustments(schedule_id);
CREATE INDEX IF NOT EXISTS idx_chit_adjustments_loan ON chit_adjustments(loan_id);
CREATE INDEX IF NOT EXISTS idx_chit_groups_status ON chit_groups(status);
CREATE INDEX IF NOT EXISTS idx_chit_groups_start_month ON chit_groups(start_month);
CREATE INDEX IF NOT EXISTS idx_borrower_chit_links_borrower ON borrower_chit_links(borrower_id);
CREATE INDEX IF NOT EXISTS idx_borrower_chit_links_chit ON borrower_chit_links(chit_id);
CREATE INDEX IF NOT EXISTS idx_adjustments_borrower ON adjustments(borrower_id);
CREATE INDEX IF NOT EXISTS idx_adjustments_interest_month ON adjustments(interest_month);
CREATE INDEX IF NOT EXISTS idx_adjustments_chit ON adjustments(chit_id);
CREATE INDEX IF NOT EXISTS idx_adjustments_chit_month ON adjustments(chit_month);
CREATE INDEX IF NOT EXISTS idx_adjustments_status ON adjustments(status);
CREATE INDEX IF NOT EXISTS idx_direct_chit_payments_borrower ON direct_chit_payments(borrower_id);
CREATE INDEX IF NOT EXISTS idx_direct_chit_payments_chit ON direct_chit_payments(chit_id);
CREATE INDEX IF NOT EXISTS idx_direct_chit_payments_month ON direct_chit_payments(chit_month);
