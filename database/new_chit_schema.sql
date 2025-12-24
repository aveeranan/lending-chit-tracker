-- NEW CHIT MODULE SCHEMA (India chit member + borrower interest adjustment)
-- This replaces the old chit tables with the new business logic

-- Drop old chit tables
DROP TABLE IF EXISTS chit_adjustments;
DROP TABLE IF EXISTS chit_monthly_schedule;
DROP TABLE IF EXISTS chits;
DROP INDEX IF EXISTS idx_chits_borrower;
DROP INDEX IF EXISTS idx_chits_status;
DROP INDEX IF EXISTS idx_chit_schedule_chit;
DROP INDEX IF EXISTS idx_chit_adjustments_schedule;
DROP INDEX IF EXISTS idx_chit_adjustments_loan;

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
