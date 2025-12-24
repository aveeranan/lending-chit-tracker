import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'lending.db')

def get_db_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with schema."""
    conn = get_db_connection()

    # Read and execute schema
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())

    # Check if a user exists, if not create default PIN: 1234
    cursor = conn.execute('SELECT COUNT(*) as count FROM users')
    if cursor.fetchone()['count'] == 0:
        pin_hash = generate_password_hash('1234')
        conn.execute('INSERT INTO users (pin_hash) VALUES (?)', (pin_hash,))
        conn.commit()

    conn.close()
    print(f"Database initialized at {DB_PATH}")

def verify_pin(pin):
    """Verify the PIN."""
    conn = get_db_connection()
    cursor = conn.execute('SELECT pin_hash FROM users LIMIT 1')
    row = cursor.fetchone()
    conn.close()

    if row:
        return check_password_hash(row['pin_hash'], pin)
    return False

def update_pin(new_pin):
    """Update the PIN."""
    conn = get_db_connection()
    pin_hash = generate_password_hash(new_pin)
    conn.execute('UPDATE users SET pin_hash = ?', (pin_hash,))
    conn.commit()
    conn.close()

def get_or_create_borrower(name, phone=None):
    """Get existing borrower or create new one."""
    conn = get_db_connection()

    # Try to find existing borrower by name
    cursor = conn.execute('SELECT id FROM borrowers WHERE name = ?', (name,))
    row = cursor.fetchone()

    if row:
        borrower_id = row['id']
    else:
        cursor = conn.execute(
            'INSERT INTO borrowers (name, phone) VALUES (?, ?)',
            (name, phone)
        )
        borrower_id = cursor.lastrowid
        conn.commit()

    conn.close()
    return borrower_id

def create_loan(borrower_name, phone, principal_given, given_date, monthly_rate,
                interest_due_day, document_received, document_type, document_path,
                document_received_date, notes):
    """Create a new loan."""
    borrower_id = get_or_create_borrower(borrower_name, phone)

    conn = get_db_connection()
    cursor = conn.execute('''
        INSERT INTO loans (
            borrower_id, principal_given, outstanding_principal, monthly_rate,
            interest_due_day, given_date, document_received, document_type,
            document_path, document_received_date, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (borrower_id, principal_given, principal_given, monthly_rate,
          interest_due_day, given_date, document_received, document_type,
          document_path, document_received_date, notes))

    loan_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return loan_id

def update_loan(loan_id, borrower_name, phone, principal_given, outstanding_principal,
                given_date, monthly_rate, interest_due_day, document_received,
                document_type, document_path, document_received_date, notes):
    """Update an existing loan."""
    borrower_id = get_or_create_borrower(borrower_name, phone)

    conn = get_db_connection()
    conn.execute('''
        UPDATE loans SET
            borrower_id = ?,
            principal_given = ?,
            outstanding_principal = ?,
            monthly_rate = ?,
            interest_due_day = ?,
            given_date = ?,
            document_received = ?,
            document_type = ?,
            document_path = ?,
            document_received_date = ?,
            notes = ?
        WHERE id = ?
    ''', (borrower_id, principal_given, outstanding_principal, monthly_rate,
          interest_due_day, given_date, document_received, document_type,
          document_path, document_received_date, notes, loan_id))

    conn.commit()
    conn.close()

def get_loans(status=None, search=None):
    """Get all loans with optional filters."""
    conn = get_db_connection()

    query = '''
        SELECT l.*, b.name as borrower_name, b.phone as borrower_phone
        FROM loans l
        JOIN borrowers b ON l.borrower_id = b.id
        WHERE 1=1
    '''
    params = []

    if status:
        query += ' AND l.status = ?'
        params.append(status)

    if search:
        query += ' AND (b.name LIKE ? OR b.phone LIKE ?)'
        search_term = f'%{search}%'
        params.extend([search_term, search_term])

    query += ' ORDER BY l.created_at DESC'

    cursor = conn.execute(query, params)
    loans = cursor.fetchall()
    conn.close()

    return [dict(loan) for loan in loans]

def get_loans_summary():
    """Get summary statistics for all active loans."""
    conn = get_db_connection()

    # Get totals for active loans
    cursor = conn.execute('''
        SELECT
            COUNT(*) as total_loans,
            SUM(principal_given) as total_principal_given,
            SUM(outstanding_principal) as total_outstanding
        FROM loans
        WHERE status = 'Active'
    ''')

    summary = dict(cursor.fetchone())

    # Calculate total Interest Due (Month) for current month for all active loans
    from datetime import datetime
    current_month = datetime.now().strftime('%Y-%m')

    cursor = conn.execute('SELECT * FROM loans WHERE status = "Active"')
    active_loans = [dict(row) for row in cursor.fetchall()]

    total_interest_due_month = 0
    for loan in active_loans:
        interest_due = calculate_interest_due(loan, current_month)
        total_interest_due_month += interest_due

    summary['total_pending_interest'] = total_interest_due_month

    conn.close()
    return summary

def get_loan_by_id(loan_id):
    """Get a specific loan by ID."""
    conn = get_db_connection()
    cursor = conn.execute('''
        SELECT l.*, b.name as borrower_name, b.phone as borrower_phone
        FROM loans l
        JOIN borrowers b ON l.borrower_id = b.id
        WHERE l.id = ?
    ''', (loan_id,))
    loan = cursor.fetchone()
    conn.close()

    return dict(loan) if loan else None

def close_loan(loan_id, close_reason=''):
    """Close a loan."""
    conn = get_db_connection()
    conn.execute('''
        UPDATE loans
        SET status = 'Closed', closed_date = ?, close_reason = ?
        WHERE id = ?
    ''', (datetime.now().strftime('%Y-%m-%d'), close_reason, loan_id))
    conn.commit()
    conn.close()

def add_payment(loan_id, payment_date, interest_month, total_received,
                interest_paid, principal_paid, payment_mode, reference, notes):
    """Add a payment and update outstanding principal."""
    conn = get_db_connection()

    # Insert payment
    conn.execute('''
        INSERT INTO payments (
            loan_id, payment_date, interest_month, total_received,
            interest_paid, principal_paid, payment_mode, reference, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (loan_id, payment_date, interest_month, total_received,
          interest_paid, principal_paid, payment_mode, reference, notes))

    # Update outstanding principal
    conn.execute('''
        UPDATE loans
        SET outstanding_principal = outstanding_principal - ?
        WHERE id = ?
    ''', (principal_paid, loan_id))

    conn.commit()
    conn.close()

def get_payments_by_loan(loan_id):
    """Get all payments for a loan."""
    conn = get_db_connection()
    cursor = conn.execute('''
        SELECT * FROM payments
        WHERE loan_id = ?
        ORDER BY payment_date DESC, interest_month DESC
    ''', (loan_id,))
    payments = cursor.fetchall()
    conn.close()

    return [dict(payment) for payment in payments]

def get_borrowers():
    """Get all borrowers."""
    conn = get_db_connection()
    cursor = conn.execute('SELECT DISTINCT name FROM borrowers ORDER BY name')
    borrowers = cursor.fetchall()
    conn.close()

    return [row['name'] for row in borrowers]

def calculate_interest_due(loan, interest_month):
    """Calculate interest due for a specific month."""
    # Get the opening principal for the month
    # This is the outstanding principal at the start of the month
    # considering all principal payments made before this month

    conn = get_db_connection()

    # Get all principal payments made before or during this month
    cursor = conn.execute('''
        SELECT SUM(principal_paid) as total_principal_paid
        FROM payments
        WHERE loan_id = ? AND interest_month < ?
    ''', (loan['id'], interest_month))

    result = cursor.fetchone()
    total_principal_paid_before = result['total_principal_paid'] or 0

    conn.close()

    # Opening principal for the month
    opening_principal = loan['principal_given'] - total_principal_paid_before

    # Calculate interest
    interest_due = opening_principal * (loan['monthly_rate'] / 100)

    return round(interest_due, 2)

def get_person_history(borrower_name):
    """Get complete payment history for a borrower."""
    conn = get_db_connection()

    # Get all loans for this borrower
    cursor = conn.execute('''
        SELECT l.id, l.principal_given, l.given_date, l.status
        FROM loans l
        JOIN borrowers b ON l.borrower_id = b.id
        WHERE b.name = ?
        ORDER BY l.given_date
    ''', (borrower_name,))

    loans = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # For each loan, get payment history
    history = []
    for loan in loans:
        payments = get_payments_by_loan(loan['id'])
        history.append({
            'loan': loan,
            'payments': payments
        })

    return history

def get_recent_payments_all(months=3):
    """Get payments for all borrowers for the last N months, grouped by month."""
    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    conn = get_db_connection()

    # Calculate the start month (N months ago)
    current_date = datetime.now()
    start_date = current_date - relativedelta(months=months-1)
    start_month = start_date.strftime('%Y-%m')

    # Get all payments from the last N months
    cursor = conn.execute('''
        SELECT
            p.*,
            b.name as borrower_name,
            l.principal_given,
            l.outstanding_principal,
            l.monthly_rate
        FROM payments p
        JOIN loans l ON p.loan_id = l.id
        JOIN borrowers b ON l.borrower_id = b.id
        WHERE p.interest_month >= ?
        ORDER BY p.interest_month DESC, p.payment_date DESC, b.name
    ''', (start_month,))

    payments = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Group payments by month
    payments_by_month = {}
    for payment in payments:
        month = payment['interest_month']
        if month not in payments_by_month:
            payments_by_month[month] = []
        payments_by_month[month].append(payment)

    return payments_by_month

def get_monthly_report(report_month, include_closed=False):
    """Generate monthly report showing who paid and who didn't."""
    conn = get_db_connection()

    # Get all active loans (or all loans if include_closed is True)
    query = '''
        SELECT l.*, b.name as borrower_name
        FROM loans l
        JOIN borrowers b ON l.borrower_id = b.id
        WHERE 1=1
    '''
    params = []

    if not include_closed:
        query += ' AND l.status = "Active"'

    cursor = conn.execute(query, params)
    loans = [dict(row) for row in cursor.fetchall()]

    # For each loan, check if interest was paid for this month
    report = {
        'full_paid': [],
        'partial_paid': [],
        'not_paid': [],
        'totals': {
            'interest_received': 0,
            'principal_received': 0,
            'total_received': 0,
            'interest_pending_month': 0,
            'interest_pending': 0
        }
    }

    for loan in loans:
        # Skip if loan was closed before this month
        if loan['closed_date'] and loan['closed_date'] < report_month:
            continue

        # Check if loan started in or before the report month
        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        loan_start_date = datetime.strptime(loan['given_date'], '%Y-%m-%d')
        report_month_start = datetime.strptime(report_month + '-01', '%Y-%m-%d')
        report_month_end = report_month_start + relativedelta(months=1) - relativedelta(days=1)

        # If loan started after the report month ends, skip it entirely
        if loan_start_date > report_month_end:
            continue

        interest_due = calculate_interest_due(loan, report_month)

        # Get payments for this month
        cursor = conn.execute('''
            SELECT SUM(interest_paid) as interest_paid,
                   SUM(principal_paid) as principal_paid,
                   SUM(total_received) as total_received
            FROM payments
            WHERE loan_id = ? AND interest_month = ?
        ''', (loan['id'], report_month))

        payment_data = cursor.fetchone()
        interest_paid = payment_data['interest_paid'] or 0
        principal_paid = payment_data['principal_paid'] or 0
        total_received = payment_data['total_received'] or 0

        # Calculate pending interest for this month only
        month_pending_interest = interest_due - interest_paid

        # Calculate total pending interest from loan start to report month
        total_pending_interest = calculate_pending_interest(loan['id'], report_month)

        loan_info = {
            'loan_id': loan['id'],
            'borrower_name': loan['borrower_name'],
            'outstanding_principal': loan['outstanding_principal'],
            'monthly_rate': loan['monthly_rate'],
            'interest_due': interest_due,
            'interest_paid': interest_paid,
            'interest_pending_month': month_pending_interest,  # Pending for this month only
            'interest_pending': total_pending_interest,  # Total pending from start
            'principal_paid': principal_paid,
            'total_received': total_received
        }

        # Categorize
        if interest_paid >= interest_due:
            report['full_paid'].append(loan_info)
        elif interest_paid > 0:
            report['partial_paid'].append(loan_info)
            # Add month pending only for partial paid (not fully paid)
            report['totals']['interest_pending_month'] += month_pending_interest
        else:
            report['not_paid'].append(loan_info)
            # Add month pending only for not paid
            report['totals']['interest_pending_month'] += month_pending_interest

        # Update totals (these are for all loans)
        report['totals']['interest_received'] += interest_paid
        report['totals']['principal_received'] += principal_paid
        report['totals']['total_received'] += total_received
        report['totals']['interest_pending'] += total_pending_interest

    conn.close()
    return report

def calculate_pending_interest(loan_id, up_to_month=None):
    """Calculate total pending interest for a loan up to a specific month."""
    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    loan = get_loan_by_id(loan_id)
    if not loan:
        return 0

    conn = get_db_connection()

    # Get all unique months from loan start to up_to_month or current month
    if up_to_month is None:
        up_to_month = datetime.now().strftime('%Y-%m')

    start_date = datetime.strptime(loan['given_date'], '%Y-%m-%d')
    end_date = datetime.strptime(up_to_month + '-01', '%Y-%m-%d')

    # If loan is closed, only calculate up to closed date
    if loan['closed_date']:
        closed_date = datetime.strptime(loan['closed_date'], '%Y-%m-%d')
        if closed_date < end_date:
            end_date = closed_date

    total_due = 0
    total_paid = 0

    current = start_date.replace(day=1)
    while current <= end_date:
        month_str = current.strftime('%Y-%m')

        # Calculate interest due for this month
        interest_due = calculate_interest_due(loan, month_str)
        total_due += interest_due

        # Get interest paid for this month
        cursor = conn.execute('''
            SELECT SUM(interest_paid) as interest_paid
            FROM payments
            WHERE loan_id = ? AND interest_month = ?
        ''', (loan_id, month_str))

        result = cursor.fetchone()
        interest_paid = result['interest_paid'] or 0
        total_paid += interest_paid

        current += relativedelta(months=1)

    conn.close()

    pending = total_due - total_paid
    return round(pending, 2)

# ============================================================================
# CHIT MANAGEMENT - NEW MODULE (India chit member + borrower interest adjustment)
# ============================================================================

# Import all chit functions from the new chit_logic module
from database import chit_logic

# Re-export chit functions for easy access
# These maintain the same interface but use the new business logic

def create_chit_group(name, monthly_installment, start_month, notes=''):
    """Create a new chit group (my membership)."""
    conn = get_db_connection()
    try:
        chit_id = chit_logic.create_chit_group(conn, name, monthly_installment, start_month, notes)
        return chit_id
    finally:
        conn.close()

def update_chit_group(chit_id, name, monthly_installment, start_month, notes=''):
    """Update chit group details."""
    conn = get_db_connection()
    try:
        chit_logic.update_chit_group(conn, chit_id, name, monthly_installment, start_month, notes)
    finally:
        conn.close()

def close_chit_group(chit_id, closed_month):
    """Close a chit group."""
    conn = get_db_connection()
    try:
        chit_logic.close_chit_group(conn, chit_id, closed_month)
    finally:
        conn.close()

def get_chit_groups(status=None):
    """Get all chit groups."""
    conn = get_db_connection()
    try:
        return chit_logic.get_chit_groups(conn, status)
    finally:
        conn.close()

def get_chit_group_by_id(chit_id):
    """Get a specific chit group."""
    conn = get_db_connection()
    try:
        return chit_logic.get_chit_group_by_id(conn, chit_id)
    finally:
        conn.close()

def link_borrower_to_chit(borrower_id, chit_id, notes=''):
    """Link a borrower to a chit group."""
    conn = get_db_connection()
    try:
        chit_logic.link_borrower_to_chit(conn, borrower_id, chit_id, notes)
    finally:
        conn.close()

def unlink_borrower_from_chit(borrower_id, chit_id):
    """Remove borrower-chit link."""
    conn = get_db_connection()
    try:
        chit_logic.unlink_borrower_from_chit(conn, borrower_id, chit_id)
    finally:
        conn.close()

def get_borrower_chit_links(borrower_id=None, chit_id=None):
    """Get borrower-chit links."""
    conn = get_db_connection()
    try:
        return chit_logic.get_borrower_chit_links(conn, borrower_id, chit_id)
    finally:
        conn.close()

def is_borrower_linked_to_chit(borrower_id, chit_id):
    """Check if borrower is linked to chit."""
    conn = get_db_connection()
    try:
        return chit_logic.is_borrower_linked_to_chit(conn, borrower_id, chit_id)
    finally:
        conn.close()

def create_adjustment(borrower_id, interest_month, chit_id, chit_month, amount, notes=''):
    """Create a new adjustment."""
    conn = get_db_connection()
    try:
        adjustment_id = chit_logic.create_adjustment(
            conn, borrower_id, interest_month, chit_id, chit_month, amount, notes
        )
        return adjustment_id
    finally:
        conn.close()

def reverse_adjustment(adjustment_id, notes=''):
    """Reverse an adjustment."""
    conn = get_db_connection()
    try:
        reversal_id = chit_logic.reverse_adjustment(conn, adjustment_id, notes)
        return reversal_id
    finally:
        conn.close()

def get_adjustments(borrower_id=None, chit_id=None, status='ACTIVE'):
    """Get adjustments with filters."""
    conn = get_db_connection()
    try:
        return chit_logic.get_adjustments(conn, borrower_id, chit_id, status)
    finally:
        conn.close()

def get_adjustment_by_id(adjustment_id):
    """Get a specific adjustment."""
    conn = get_db_connection()
    try:
        return chit_logic.get_adjustment_by_id(conn, adjustment_id)
    finally:
        conn.close()

def add_direct_chit_payment(borrower_id, chit_id, chit_month, amount,
                            payment_date, payment_mode='', reference='', notes=''):
    """Add a direct cash payment for chit."""
    conn = get_db_connection()
    try:
        payment_id = chit_logic.add_direct_chit_payment(
            conn, borrower_id, chit_id, chit_month, amount,
            payment_date, payment_mode, reference, notes
        )
        return payment_id
    finally:
        conn.close()

def get_direct_chit_payments(borrower_id=None, chit_id=None):
    """Get direct chit payments."""
    conn = get_db_connection()
    try:
        return chit_logic.get_direct_chit_payments(conn, borrower_id, chit_id)
    finally:
        conn.close()

# Calculation functions
def calculate_interest_received(borrower_id, interest_month):
    """Calculate interest received for borrower + month."""
    conn = get_db_connection()
    try:
        return chit_logic.calculate_interest_received(conn, borrower_id, interest_month)
    finally:
        conn.close()

def calculate_interest_adjusted(borrower_id, interest_month):
    """Calculate interest adjusted for borrower + month."""
    conn = get_db_connection()
    try:
        return chit_logic.calculate_interest_adjusted(conn, borrower_id, interest_month)
    finally:
        conn.close()

def calculate_interest_available(borrower_id, interest_month):
    """Calculate available interest for borrower + month."""
    conn = get_db_connection()
    try:
        return chit_logic.calculate_interest_available(conn, borrower_id, interest_month)
    finally:
        conn.close()

def calculate_chit_due(borrower_id, chit_id, chit_month):
    """Calculate chit due for borrower + chit + month."""
    conn = get_db_connection()
    try:
        return chit_logic.calculate_chit_due(conn, borrower_id, chit_id, chit_month)
    finally:
        conn.close()

def calculate_chit_adjusted_paid(borrower_id, chit_id, chit_month):
    """Calculate total adjusted + paid for chit month."""
    conn = get_db_connection()
    try:
        return chit_logic.calculate_chit_adjusted_paid(conn, borrower_id, chit_id, chit_month)
    finally:
        conn.close()

def calculate_chit_remaining_due(borrower_id, chit_id, chit_month):
    """Calculate remaining due for chit month."""
    conn = get_db_connection()
    try:
        return chit_logic.calculate_chit_remaining_due(conn, borrower_id, chit_id, chit_month)
    finally:
        conn.close()

def get_chit_month_view(borrower_id, chit_id, chit_month):
    """Get complete view of a chit month."""
    conn = get_db_connection()
    try:
        return chit_logic.get_chit_month_view(conn, borrower_id, chit_id, chit_month)
    finally:
        conn.close()

def get_interest_month_view(borrower_id, interest_month):
    """Get complete view of interest for a month."""
    conn = get_db_connection()
    try:
        return chit_logic.get_interest_month_view(conn, borrower_id, interest_month)
    finally:
        conn.close()

def get_borrower_chit_summary(borrower_id):
    """Get summary of all chit payments for a borrower."""
    conn = get_db_connection()
    try:
        return chit_logic.get_borrower_chit_summary(conn, borrower_id)
    finally:
        conn.close()

# ============================================================================
# INDIVIDUAL CHIT MANAGEMENT FUNCTIONS
# ============================================================================

def get_individual_chits(status=None):
    """Get all individual chits with optional status filter."""
    conn = get_db_connection()
    try:
        query = 'SELECT * FROM chits'
        params = []

        if status:
            query += ' WHERE status = ?'
            params.append(status)

        query += ' ORDER BY created_at DESC'

        cursor = conn.execute(query, params)
        chits = [dict(row) for row in cursor.fetchall()]
        return chits
    finally:
        conn.close()

def create_individual_chit(borrower_name, chit_name, total_months, start_date, monthly_amounts, prized_month=None, prize_amount=None, notes=''):
    """Create a new individual chit with monthly schedule."""
    conn = get_db_connection()
    try:
        # Get or create borrower
        cursor = conn.execute('SELECT id FROM borrowers WHERE name = ?', (borrower_name,))
        borrower = cursor.fetchone()

        if borrower:
            borrower_id = borrower['id']
        else:
            cursor = conn.execute('INSERT INTO borrowers (name) VALUES (?)', (borrower_name,))
            borrower_id = cursor.lastrowid

        # Create chit
        cursor = conn.execute('''
            INSERT INTO chits (borrower_id, borrower_name, chit_name, total_months, start_date,
                             prized_month, prize_amount, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (borrower_id, borrower_name, chit_name, total_months, start_date,
              prized_month, prize_amount, notes))

        chit_id = cursor.lastrowid

        # Create monthly schedule
        from dateutil.relativedelta import relativedelta
        from datetime import datetime as dt

        start = dt.strptime(start_date, '%Y-%m-%d')

        for i in range(total_months):
            month_number = i + 1
            due_date = start + relativedelta(months=i)
            due_amount = monthly_amounts[i] if i < len(monthly_amounts) else 0

            conn.execute('''
                INSERT INTO chit_monthly_schedule (chit_id, month_number, due_date, due_amount)
                VALUES (?, ?, ?, ?)
            ''', (chit_id, month_number, due_date.strftime('%Y-%m-%d'), due_amount))

        conn.commit()
        return chit_id
    finally:
        conn.close()

def get_individual_chit_by_id(chit_id):
    """Get a specific individual chit with schedule."""
    conn = get_db_connection()
    try:
        # Get chit details
        cursor = conn.execute('SELECT * FROM chits WHERE id = ?', (chit_id,))
        chit = cursor.fetchone()

        if not chit:
            return None

        chit_dict = dict(chit)

        # Get schedule
        cursor = conn.execute('''
            SELECT * FROM chit_monthly_schedule
            WHERE chit_id = ?
            ORDER BY month_number
        ''', (chit_id,))

        chit_dict['schedule'] = [dict(row) for row in cursor.fetchall()]

        return chit_dict
    finally:
        conn.close()

def update_individual_chit(chit_id, borrower_name, chit_name, start_date, monthly_amounts, prized_month=None, prize_amount=None, notes=''):
    """Update an individual chit."""
    conn = get_db_connection()
    try:
        # Get or create borrower
        cursor = conn.execute('SELECT id FROM borrowers WHERE name = ?', (borrower_name,))
        borrower = cursor.fetchone()

        if borrower:
            borrower_id = borrower['id']
        else:
            cursor = conn.execute('INSERT INTO borrowers (name) VALUES (?)', (borrower_name,))
            borrower_id = cursor.lastrowid

        # Update chit
        conn.execute('''
            UPDATE chits
            SET borrower_id = ?, borrower_name = ?, chit_name = ?, start_date = ?,
                prized_month = ?, prize_amount = ?, notes = ?
            WHERE id = ?
        ''', (borrower_id, borrower_name, chit_name, start_date,
              prized_month, prize_amount, notes, chit_id))

        # Update monthly schedule amounts (only for pending/future months)
        from datetime import datetime as dt
        current_date = dt.now().strftime('%Y-%m-%d')

        cursor = conn.execute('''
            SELECT id, month_number, payment_status, due_date
            FROM chit_monthly_schedule
            WHERE chit_id = ?
            ORDER BY month_number
        ''', (chit_id,))

        schedules = cursor.fetchall()

        for schedule in schedules:
            month_idx = schedule['month_number'] - 1
            if month_idx < len(monthly_amounts):
                # Only update if not paid/adjusted and not in the past
                if schedule['payment_status'] == 'Pending' and schedule['due_date'] >= current_date:
                    conn.execute('''
                        UPDATE chit_monthly_schedule
                        SET due_amount = ?
                        WHERE id = ?
                    ''', (monthly_amounts[month_idx], schedule['id']))

        conn.commit()
    finally:
        conn.close()

def close_individual_chit(chit_id):
    """Close an individual chit."""
    conn = get_db_connection()
    try:
        conn.execute('UPDATE chits SET status = ? WHERE id = ?', ('Closed', chit_id))
        conn.commit()
    finally:
        conn.close()

def get_pending_chit_dues():
    """Get all pending chit dues till current date."""
    from datetime import datetime

    conn = get_db_connection()
    try:
        current_date = datetime.now().strftime('%Y-%m-%d')

        cursor = conn.execute('''
            SELECT
                cms.id,
                c.borrower_id,
                c.borrower_name,
                c.chit_name,
                cms.month_number,
                cms.due_date,
                cms.due_amount,
                cms.paid_amount,
                cms.payment_status,
                (cms.due_amount - cms.paid_amount) as remaining
            FROM chit_monthly_schedule cms
            JOIN chits c ON cms.chit_id = c.id
            WHERE cms.payment_status IN ('Pending', 'Partial')
              AND c.status = 'Active'
              AND (cms.due_amount - cms.paid_amount) > 0
              AND cms.due_date <= ?
            ORDER BY cms.due_date
        ''', (current_date,))

        dues = [dict(row) for row in cursor.fetchall()]
        return dues
    finally:
        conn.close()

def pay_chit_schedule(schedule_id, paid_amount, paid_date, payment_mode='', notes=''):
    """Mark a chit schedule item as paid."""
    conn = get_db_connection()
    try:
        # Get current schedule details
        cursor = conn.execute('''
            SELECT due_amount, paid_amount
            FROM chit_monthly_schedule
            WHERE id = ?
        ''', (schedule_id,))

        schedule = cursor.fetchone()
        if not schedule:
            raise Exception('Schedule item not found')

        new_paid_amount = schedule['paid_amount'] + paid_amount
        due_amount = schedule['due_amount']

        # Determine payment status
        if new_paid_amount >= due_amount:
            payment_status = 'Paid'
        elif new_paid_amount > 0:
            payment_status = 'Partial'
        else:
            payment_status = 'Pending'

        # Update schedule
        conn.execute('''
            UPDATE chit_monthly_schedule
            SET paid_amount = ?,
                paid_date = ?,
                payment_mode = ?,
                payment_status = ?,
                notes = ?
            WHERE id = ?
        ''', (new_paid_amount, paid_date, payment_mode, payment_status, notes, schedule_id))

        conn.commit()
    finally:
        conn.close()

def get_out_of_pocket_payments():
    """Get all out-of-pocket chit payments (showing only the out-of-pocket portion)."""
    conn = get_db_connection()
    try:
        cursor = conn.execute('''
            SELECT
                cms.id,
                c.borrower_name,
                c.chit_name,
                cms.month_number,
                cms.due_date,
                cms.due_amount,
                cms.paid_amount,
                cms.paid_date,
                cms.payment_mode,
                cms.payment_status,
                cms.notes,
                COALESCE((SELECT SUM(adjusted_amount) FROM chit_adjustments WHERE chit_schedule_id = cms.id), 0) as adjusted_amount
            FROM chit_monthly_schedule cms
            JOIN chits c ON cms.chit_id = c.id
            WHERE cms.payment_status IN ('Paid', 'Partial')
              AND cms.paid_amount > 0
            ORDER BY cms.paid_date DESC, c.borrower_name
        ''')

        all_records = [dict(row) for row in cursor.fetchall()]

        # Calculate out-of-pocket amount for each record
        payments = []
        for record in all_records:
            out_of_pocket_amount = record['paid_amount'] - record['adjusted_amount']

            # Only include if there's an actual out-of-pocket payment
            if out_of_pocket_amount > 0:
                record['out_of_pocket_amount'] = out_of_pocket_amount
                payments.append(record)

        return payments
    finally:
        conn.close()

def create_chit_adjustment(schedule_id, loan_id, interest_month, adjusted_amount, notes=''):
    """Create a chit adjustment against loan interest."""
    from datetime import datetime

    conn = get_db_connection()
    try:
        # Get current date for adjustment_date
        adjustment_date = datetime.now().strftime('%Y-%m-%d')

        # Get loan details to calculate available interest
        loan = get_loan_by_id(loan_id)
        if not loan:
            raise Exception('Loan not found')

        # Calculate interest due for the specified month
        interest_due = calculate_interest_due(loan, interest_month)

        # Get already paid interest for this month
        cursor = conn.execute('''
            SELECT COALESCE(SUM(interest_paid), 0) as total_paid
            FROM payments
            WHERE loan_id = ? AND interest_month = ?
        ''', (loan_id, interest_month))

        result = cursor.fetchone()
        already_paid = result['total_paid'] or 0

        # Calculate available interest
        available_interest = interest_due - already_paid

        # Validate that there's enough interest available
        if available_interest <= 0:
            raise Exception(f'No interest available for {interest_month}.\n\nInterest Due: ₹{interest_due:.2f}\nAlready Paid: ₹{already_paid:.2f}\nAvailable Interest: ₹0.00\n\nMax Adjustment Amount: ₹0.00')

        # Get current schedule details first to know chit amount
        cursor = conn.execute('''
            SELECT due_amount, paid_amount, c.chit_name, cms.month_number
            FROM chit_monthly_schedule cms
            JOIN chits c ON cms.chit_id = c.id
            WHERE cms.id = ?
        ''', (schedule_id,))

        schedule = cursor.fetchone()
        if not schedule:
            raise Exception('Schedule item not found')

        chit_due_amount = schedule['due_amount']
        already_paid_chit = schedule['paid_amount']
        remaining_chit_due = chit_due_amount - already_paid_chit
        chit_name = schedule['chit_name']
        month_number = schedule['month_number']

        # Calculate how much can actually be adjusted
        # Limited by both available interest and remaining chit due
        amount_to_adjust = min(available_interest, remaining_chit_due)

        partial_adjustment_msg = None

        # Case 1: Interest is less than chit amount
        if available_interest < remaining_chit_due:
            partial_adjustment_msg = f'Partial Payment - Interest Insufficient\n\n'
            partial_adjustment_msg += f'Chit: {chit_name} Month {month_number}\n'
            partial_adjustment_msg += f'Chit Amount Due: ₹{remaining_chit_due:.2f}\n'
            partial_adjustment_msg += f'Interest Month: {interest_month}\n'
            partial_adjustment_msg += f'Interest Available: ₹{available_interest:.2f}\n\n'
            partial_adjustment_msg += f'Adjusted Amount: ₹{amount_to_adjust:.2f}\n'
            partial_adjustment_msg += f'Remaining to Pay: ₹{remaining_chit_due - amount_to_adjust:.2f}\n\n'
            partial_adjustment_msg += f'The chit has been partially paid using all available interest.\n'
            partial_adjustment_msg += f'You need to pay the remaining ₹{remaining_chit_due - amount_to_adjust:.2f} separately.'
            notes = f'{notes} (Partial: Interest ₹{available_interest:.2f} < Chit ₹{remaining_chit_due:.2f})'.strip()

        # Case 2: Requested more than available interest but chit can be fully paid
        elif adjusted_amount > available_interest:
            partial_adjustment_msg = f'Full Payment - Using Available Interest\n\n'
            partial_adjustment_msg += f'Chit: {chit_name} Month {month_number}\n'
            partial_adjustment_msg += f'Chit Amount: ₹{remaining_chit_due:.2f}\n'
            partial_adjustment_msg += f'Interest Available: ₹{available_interest:.2f}\n\n'
            partial_adjustment_msg += f'Adjusted Amount: ₹{amount_to_adjust:.2f}\n\n'
            partial_adjustment_msg += f'The chit has been fully paid using ₹{amount_to_adjust:.2f} from available interest.'
            notes = f'{notes} (Full payment using available interest)'.strip()

        # Insert adjustment record with actual amount
        cursor = conn.execute('''
            INSERT INTO chit_adjustments (chit_schedule_id, loan_id, interest_month, adjusted_amount, adjustment_date, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (schedule_id, loan_id, interest_month, amount_to_adjust, adjustment_date, notes))

        adjustment_id = cursor.lastrowid

        new_paid_amount = already_paid_chit + amount_to_adjust

        # Determine payment status
        if new_paid_amount >= chit_due_amount:
            payment_status = 'Adjusted'
        elif new_paid_amount > 0:
            payment_status = 'Partial'
        else:
            payment_status = 'Pending'

        # Update schedule with adjusted amount
        conn.execute('''
            UPDATE chit_monthly_schedule
            SET paid_amount = ?,
                payment_status = ?
            WHERE id = ?
        ''', (new_paid_amount, payment_status, schedule_id))

        # Create payment entry for this adjustment
        payment_notes = f'Chit adjustment: {chit_name} Month {month_number}'

        conn.execute('''
            INSERT INTO payments (loan_id, payment_date, interest_month, total_received, interest_paid, principal_paid, payment_mode, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (loan_id, adjustment_date, interest_month, amount_to_adjust, amount_to_adjust, 0.0, 'Adjustment', payment_notes))

        conn.commit()

        # Return adjustment_id and partial adjustment message if applicable
        return {
            'adjustment_id': adjustment_id,
            'partial_adjustment_msg': partial_adjustment_msg
        }
    finally:
        conn.close()


if __name__ == '__main__':
    init_db()
