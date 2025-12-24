"""
CHIT MODULE BUSINESS LOGIC
India chit member + borrower interest adjustment

All functions implement strict validation according to business rules.
"""

from datetime import datetime


# ============================================================================
# CORE CALCULATION FUNCTIONS (used everywhere for consistency)
# ============================================================================

def calculate_interest_received(conn, borrower_id, interest_month):
    """
    Calculate total interest received from this borrower for the given month.
    Only includes Active loans (excludes Closed loans).

    Returns: float
    """
    cursor = conn.execute('''
        SELECT SUM(p.interest_paid) as total_interest
        FROM payments p
        JOIN loans l ON p.loan_id = l.id
        WHERE l.borrower_id = ?
          AND l.status = 'Active'
          AND p.interest_month = ?
    ''', (borrower_id, interest_month))

    result = cursor.fetchone()
    return result['total_interest'] or 0.0


def calculate_interest_adjusted(conn, borrower_id, interest_month):
    """
    Calculate total interest adjusted for this borrower + interest_month.
    Only includes ACTIVE adjustments (excludes REVERSED).

    Returns: float
    """
    cursor = conn.execute('''
        SELECT SUM(amount) as total_adjusted
        FROM adjustments
        WHERE borrower_id = ?
          AND interest_month = ?
          AND status = 'ACTIVE'
    ''', (borrower_id, interest_month))

    result = cursor.fetchone()
    return result['total_adjusted'] or 0.0


def calculate_interest_available(conn, borrower_id, interest_month):
    """
    Calculate available interest for adjustment.
    available = received - adjusted

    Returns: float
    """
    received = calculate_interest_received(conn, borrower_id, interest_month)
    adjusted = calculate_interest_adjusted(conn, borrower_id, interest_month)
    return received - adjusted


def calculate_chit_due(conn, borrower_id, chit_id, chit_month):
    """
    Calculate chit due for this borrower + chit + month.

    Rules:
    - Returns 0 if chit_month < chit.start_month
    - Returns 0 if chit is Closed and chit_month > closed_month
    - Otherwise returns chit.monthly_installment

    Returns: float
    """
    # Get chit details
    cursor = conn.execute('''
        SELECT monthly_installment, start_month, status, closed_month
        FROM chit_groups
        WHERE id = ?
    ''', (chit_id,))

    chit = cursor.fetchone()
    if not chit:
        return 0.0

    # Check if month is before start
    if chit_month < chit['start_month']:
        return 0.0

    # Check if chit is closed and month is after closed_month
    if chit['status'] == 'Closed' and chit['closed_month']:
        if chit_month > chit['closed_month']:
            return 0.0

    return chit['monthly_installment']


def calculate_chit_adjusted_paid(conn, borrower_id, chit_id, chit_month):
    """
    Calculate total adjusted + paid for this chit month.
    Includes both ACTIVE adjustments and direct_chit_payments.

    Returns: float
    """
    # Sum ACTIVE adjustments
    cursor = conn.execute('''
        SELECT SUM(amount) as total_adjusted
        FROM adjustments
        WHERE borrower_id = ?
          AND chit_id = ?
          AND chit_month = ?
          AND status = 'ACTIVE'
    ''', (borrower_id, chit_id, chit_month))

    adjusted = cursor.fetchone()['total_adjusted'] or 0.0

    # Sum direct payments
    cursor = conn.execute('''
        SELECT SUM(amount) as total_paid
        FROM direct_chit_payments
        WHERE borrower_id = ?
          AND chit_id = ?
          AND chit_month = ?
    ''', (borrower_id, chit_id, chit_month))

    paid = cursor.fetchone()['total_paid'] or 0.0

    return adjusted + paid


def calculate_chit_remaining_due(conn, borrower_id, chit_id, chit_month):
    """
    Calculate remaining due for this chit month.
    remaining = due - adjusted_paid

    Returns: float
    """
    due = calculate_chit_due(conn, borrower_id, chit_id, chit_month)
    adjusted_paid = calculate_chit_adjusted_paid(conn, borrower_id, chit_id, chit_month)
    return max(0.0, due - adjusted_paid)


def get_chit_month_status(conn, borrower_id, chit_id, chit_month):
    """
    Get payment status for a chit month.
    Returns: 'Paid', 'Partial', or 'Unpaid'
    """
    remaining = calculate_chit_remaining_due(conn, borrower_id, chit_id, chit_month)
    adjusted_paid = calculate_chit_adjusted_paid(conn, borrower_id, chit_id, chit_month)

    if remaining == 0 and adjusted_paid > 0:
        return 'Paid'
    elif adjusted_paid > 0:
        return 'Partial'
    else:
        return 'Unpaid'


# ============================================================================
# CHIT GROUP MANAGEMENT
# ============================================================================

def create_chit_group(conn, name, monthly_installment, start_month, notes=''):
    """
    Create a new chit group (my membership).

    Args:
        conn: Database connection
        name: Unique chit group name
        monthly_installment: Fixed monthly amount
        start_month: YYYY-MM format
        notes: Optional notes

    Returns:
        chit_id (int)

    Raises:
        ValueError: If validation fails
    """
    # Validate start_month format
    try:
        datetime.strptime(start_month, '%Y-%m')
    except ValueError:
        raise ValueError('start_month must be in YYYY-MM format')

    if monthly_installment <= 0:
        raise ValueError('monthly_installment must be positive')

    cursor = conn.execute('''
        INSERT INTO chit_groups (name, monthly_installment, start_month, notes)
        VALUES (?, ?, ?, ?)
    ''', (name, monthly_installment, start_month, notes))

    conn.commit()
    return cursor.lastrowid


def update_chit_group(conn, chit_id, name, monthly_installment, start_month, notes=''):
    """
    Update chit group details.
    Cannot change status here - use close_chit_group for that.
    """
    # Validate start_month format
    try:
        datetime.strptime(start_month, '%Y-%m')
    except ValueError:
        raise ValueError('start_month must be in YYYY-MM format')

    if monthly_installment <= 0:
        raise ValueError('monthly_installment must be positive')

    conn.execute('''
        UPDATE chit_groups
        SET name = ?, monthly_installment = ?, start_month = ?, notes = ?
        WHERE id = ?
    ''', (name, monthly_installment, start_month, notes, chit_id))

    conn.commit()


def close_chit_group(conn, chit_id, closed_month):
    """
    Close a chit group.

    Args:
        chit_id: Chit group ID
        closed_month: YYYY-MM format - last valid month

    Raises:
        ValueError: If validation fails
    """
    # Validate closed_month format
    try:
        datetime.strptime(closed_month, '%Y-%m')
    except ValueError:
        raise ValueError('closed_month must be in YYYY-MM format')

    # Check that closed_month >= start_month
    cursor = conn.execute('SELECT start_month FROM chit_groups WHERE id = ?', (chit_id,))
    chit = cursor.fetchone()

    if not chit:
        raise ValueError('Chit group not found')

    if closed_month < chit['start_month']:
        raise ValueError('closed_month cannot be before start_month')

    conn.execute('''
        UPDATE chit_groups
        SET status = 'Closed', closed_month = ?
        WHERE id = ?
    ''', (closed_month, chit_id))

    conn.commit()


def get_chit_groups(conn, status=None):
    """
    Get all chit groups with optional status filter.

    Returns:
        List of dict
    """
    query = 'SELECT * FROM chit_groups WHERE 1=1'
    params = []

    if status:
        query += ' AND status = ?'
        params.append(status)

    query += ' ORDER BY created_at DESC'

    cursor = conn.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def get_chit_group_by_id(conn, chit_id):
    """
    Get a specific chit group.

    Returns:
        dict or None
    """
    cursor = conn.execute('SELECT * FROM chit_groups WHERE id = ?', (chit_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


# ============================================================================
# BORROWER-CHIT LINKS
# ============================================================================

def link_borrower_to_chit(conn, borrower_id, chit_id, notes=''):
    """
    Link a borrower to a chit group.
    This enables adjustments for this borrower + chit combination.

    Raises:
        ValueError: If link already exists
    """
    # Check if link already exists
    cursor = conn.execute('''
        SELECT 1 FROM borrower_chit_links
        WHERE borrower_id = ? AND chit_id = ?
    ''', (borrower_id, chit_id))

    if cursor.fetchone():
        raise ValueError('Borrower is already linked to this chit')

    conn.execute('''
        INSERT INTO borrower_chit_links (borrower_id, chit_id, notes)
        VALUES (?, ?, ?)
    ''', (borrower_id, chit_id, notes))

    conn.commit()


def unlink_borrower_from_chit(conn, borrower_id, chit_id):
    """
    Remove borrower-chit link.

    Raises:
        ValueError: If there are active adjustments
    """
    # Check for active adjustments
    cursor = conn.execute('''
        SELECT COUNT(*) as count
        FROM adjustments
        WHERE borrower_id = ? AND chit_id = ? AND status = 'ACTIVE'
    ''', (borrower_id, chit_id))

    if cursor.fetchone()['count'] > 0:
        raise ValueError('Cannot unlink: active adjustments exist for this borrower-chit combination')

    conn.execute('''
        DELETE FROM borrower_chit_links
        WHERE borrower_id = ? AND chit_id = ?
    ''', (borrower_id, chit_id))

    conn.commit()


def get_borrower_chit_links(conn, borrower_id=None, chit_id=None):
    """
    Get borrower-chit links with optional filters.

    Returns:
        List of dict with borrower and chit details
    """
    query = '''
        SELECT
            bcl.*,
            b.name as borrower_name,
            b.phone as borrower_phone,
            cg.name as chit_name,
            cg.monthly_installment,
            cg.start_month,
            cg.status as chit_status,
            cg.closed_month
        FROM borrower_chit_links bcl
        JOIN borrowers b ON bcl.borrower_id = b.id
        JOIN chit_groups cg ON bcl.chit_id = cg.id
        WHERE 1=1
    '''
    params = []

    if borrower_id:
        query += ' AND bcl.borrower_id = ?'
        params.append(borrower_id)

    if chit_id:
        query += ' AND bcl.chit_id = ?'
        params.append(chit_id)

    query += ' ORDER BY b.name, cg.name'

    cursor = conn.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def is_borrower_linked_to_chit(conn, borrower_id, chit_id):
    """
    Check if borrower is linked to chit.

    Returns:
        bool
    """
    cursor = conn.execute('''
        SELECT 1 FROM borrower_chit_links
        WHERE borrower_id = ? AND chit_id = ?
    ''', (borrower_id, chit_id))

    return cursor.fetchone() is not None


def has_active_loans(conn, borrower_id):
    """
    Check if borrower has at least one active loan.

    Returns:
        bool
    """
    cursor = conn.execute('''
        SELECT 1 FROM loans
        WHERE borrower_id = ? AND status = 'Active'
        LIMIT 1
    ''', (borrower_id,))

    return cursor.fetchone() is not None


# ============================================================================
# ADJUSTMENT CREATION & VALIDATION
# ============================================================================

def create_adjustment(conn, borrower_id, interest_month, chit_id, chit_month, amount, notes=''):
    """
    Create a new adjustment linking interest to chit payment.

    Implements all validation rules:
    1. Borrower must be linked to chit
    2. Chit must be Active (and chit_month within valid range)
    3. Borrower must have at least one Active loan
    4. Amount must be positive
    5. Available interest >= amount
    6. Remaining chit due >= amount
    7. Cannot adjust if chit month is already fully paid

    Args:
        conn: Database connection
        borrower_id: Borrower ID
        interest_month: YYYY-MM source month
        chit_id: Chit group ID
        chit_month: YYYY-MM target month
        amount: Adjustment amount
        notes: Optional notes

    Returns:
        adjustment_id (int)

    Raises:
        ValueError: If any validation fails
    """
    # Validate month formats
    try:
        datetime.strptime(interest_month, '%Y-%m')
        datetime.strptime(chit_month, '%Y-%m')
    except ValueError:
        raise ValueError('Months must be in YYYY-MM format')

    # Validate amount
    if amount <= 0:
        raise ValueError('Amount must be positive')

    # Rule 1: Check borrower-chit link
    if not is_borrower_linked_to_chit(conn, borrower_id, chit_id):
        raise ValueError('Borrower is not linked to this chit group')

    # Rule 2: Check chit status and month validity
    chit = get_chit_group_by_id(conn, chit_id)
    if not chit:
        raise ValueError('Chit group not found')

    if chit['status'] == 'Closed':
        if not chit['closed_month'] or chit_month > chit['closed_month']:
            raise ValueError(f'Chit is closed. Cannot adjust for months after {chit["closed_month"]}')

    if chit_month < chit['start_month']:
        raise ValueError(f'Chit month cannot be before start month ({chit["start_month"]})')

    # Rule 3: Check for active loans
    if not has_active_loans(conn, borrower_id):
        raise ValueError('Borrower has no active loans')

    # Rule 5: Check available interest
    available_interest = calculate_interest_available(conn, borrower_id, interest_month)
    if available_interest < amount:
        raise ValueError(
            f'Insufficient interest available. '
            f'Available: ₹{available_interest:.2f}, Requested: ₹{amount:.2f}'
        )

    # Rule 6 & 7: Check remaining chit due
    remaining_due = calculate_chit_remaining_due(conn, borrower_id, chit_id, chit_month)
    if remaining_due == 0:
        raise ValueError('Chit month is already fully paid')

    if remaining_due < amount:
        raise ValueError(
            f'Amount exceeds remaining due. '
            f'Remaining: ₹{remaining_due:.2f}, Requested: ₹{amount:.2f}'
        )

    # All validations passed - create adjustment
    cursor = conn.execute('''
        INSERT INTO adjustments (
            borrower_id, interest_month, chit_id, chit_month,
            amount, status, notes
        ) VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?)
    ''', (borrower_id, interest_month, chit_id, chit_month, amount, notes))

    conn.commit()
    return cursor.lastrowid


# ============================================================================
# ADJUSTMENT REVERSAL
# ============================================================================

def reverse_adjustment(conn, adjustment_id, notes=''):
    """
    Reverse an adjustment by creating a counter-adjustment.

    Process:
    1. Verify original adjustment exists and is ACTIVE
    2. Create new adjustment with same details but as reversal
    3. Mark original as REVERSED

    Args:
        conn: Database connection
        adjustment_id: ID of adjustment to reverse
        notes: Optional notes for the reversal

    Returns:
        reversal_adjustment_id (int)

    Raises:
        ValueError: If adjustment not found or already reversed
    """
    # Get original adjustment
    cursor = conn.execute('''
        SELECT * FROM adjustments WHERE id = ?
    ''', (adjustment_id,))

    original = cursor.fetchone()
    if not original:
        raise ValueError('Adjustment not found')

    if original['status'] == 'REVERSED':
        raise ValueError('Adjustment is already reversed')

    # Create reversal record
    reversal_notes = f"Reversal of adjustment #{adjustment_id}"
    if notes:
        reversal_notes += f" - {notes}"

    cursor = conn.execute('''
        INSERT INTO adjustments (
            borrower_id, interest_month, chit_id, chit_month,
            amount, status, reversal_of_id, notes
        ) VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
    ''', (
        original['borrower_id'],
        original['chit_month'],  # Reversed: chit_month becomes interest_month
        original['chit_id'],
        original['interest_month'],  # Reversed: interest_month becomes chit_month
        original['amount'],
        adjustment_id,
        reversal_notes
    ))

    reversal_id = cursor.lastrowid

    # Mark original as REVERSED
    conn.execute('''
        UPDATE adjustments
        SET status = 'REVERSED'
        WHERE id = ?
    ''', (adjustment_id,))

    conn.commit()
    return reversal_id


# ============================================================================
# ADJUSTMENT QUERIES
# ============================================================================

def get_adjustments(conn, borrower_id=None, chit_id=None, status='ACTIVE'):
    """
    Get adjustments with optional filters.

    Returns:
        List of dict with full details
    """
    query = '''
        SELECT
            a.*,
            b.name as borrower_name,
            cg.name as chit_name,
            cg.monthly_installment
        FROM adjustments a
        JOIN borrowers b ON a.borrower_id = b.id
        JOIN chit_groups cg ON a.chit_id = cg.id
        WHERE 1=1
    '''
    params = []

    if borrower_id:
        query += ' AND a.borrower_id = ?'
        params.append(borrower_id)

    if chit_id:
        query += ' AND a.chit_id = ?'
        params.append(chit_id)

    if status:
        query += ' AND a.status = ?'
        params.append(status)

    query += ' ORDER BY a.created_at DESC'

    cursor = conn.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def get_adjustment_by_id(conn, adjustment_id):
    """
    Get a specific adjustment with full details.

    Returns:
        dict or None
    """
    cursor = conn.execute('''
        SELECT
            a.*,
            b.name as borrower_name,
            cg.name as chit_name,
            cg.monthly_installment
        FROM adjustments a
        JOIN borrowers b ON a.borrower_id = b.id
        JOIN chit_groups cg ON a.chit_id = cg.id
        WHERE a.id = ?
    ''', (adjustment_id,))

    row = cursor.fetchone()
    return dict(row) if row else None


# ============================================================================
# DIRECT CHIT PAYMENTS (optional)
# ============================================================================

def add_direct_chit_payment(conn, borrower_id, chit_id, chit_month, amount,
                            payment_date, payment_mode='', reference='', notes=''):
    """
    Add a direct cash payment for chit (not from interest adjustment).

    Validates:
    - Borrower is linked to chit
    - Chit is active for this month
    - Amount doesn't exceed remaining due

    Returns:
        payment_id (int)
    """
    # Validate month format
    try:
        datetime.strptime(chit_month, '%Y-%m')
    except ValueError:
        raise ValueError('chit_month must be in YYYY-MM format')

    if amount <= 0:
        raise ValueError('Amount must be positive')

    # Check borrower-chit link
    if not is_borrower_linked_to_chit(conn, borrower_id, chit_id):
        raise ValueError('Borrower is not linked to this chit group')

    # Check chit validity
    chit = get_chit_group_by_id(conn, chit_id)
    if not chit:
        raise ValueError('Chit group not found')

    if chit['status'] == 'Closed':
        if not chit['closed_month'] or chit_month > chit['closed_month']:
            raise ValueError(f'Chit is closed. Cannot pay for months after {chit["closed_month"]}')

    if chit_month < chit['start_month']:
        raise ValueError(f'Chit month cannot be before start month ({chit["start_month"]})')

    # Check remaining due
    remaining_due = calculate_chit_remaining_due(conn, borrower_id, chit_id, chit_month)
    if remaining_due == 0:
        raise ValueError('Chit month is already fully paid')

    if remaining_due < amount:
        raise ValueError(
            f'Amount exceeds remaining due. '
            f'Remaining: ₹{remaining_due:.2f}, Requested: ₹{amount:.2f}'
        )

    cursor = conn.execute('''
        INSERT INTO direct_chit_payments (
            borrower_id, chit_id, chit_month, amount,
            payment_date, payment_mode, reference, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (borrower_id, chit_id, chit_month, amount,
          payment_date, payment_mode, reference, notes))

    conn.commit()
    return cursor.lastrowid


def get_direct_chit_payments(conn, borrower_id=None, chit_id=None):
    """
    Get direct chit payments with optional filters.

    Returns:
        List of dict
    """
    query = '''
        SELECT
            dcp.*,
            b.name as borrower_name,
            cg.name as chit_name
        FROM direct_chit_payments dcp
        JOIN borrowers b ON dcp.borrower_id = b.id
        JOIN chit_groups cg ON dcp.chit_id = cg.id
        WHERE 1=1
    '''
    params = []

    if borrower_id:
        query += ' AND dcp.borrower_id = ?'
        params.append(borrower_id)

    if chit_id:
        query += ' AND dcp.chit_id = ?'
        params.append(chit_id)

    query += ' ORDER BY dcp.payment_date DESC'

    cursor = conn.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


# ============================================================================
# REPORTING & VIEWS
# ============================================================================

def get_chit_month_view(conn, borrower_id, chit_id, chit_month):
    """
    Get complete view of a chit month for a borrower.

    Returns:
        dict with all calculations
    """
    due = calculate_chit_due(conn, borrower_id, chit_id, chit_month)
    adjusted_paid = calculate_chit_adjusted_paid(conn, borrower_id, chit_id, chit_month)
    remaining_due = calculate_chit_remaining_due(conn, borrower_id, chit_id, chit_month)
    status = get_chit_month_status(conn, borrower_id, chit_id, chit_month)

    return {
        'borrower_id': borrower_id,
        'chit_id': chit_id,
        'chit_month': chit_month,
        'due': due,
        'adjusted_paid': adjusted_paid,
        'remaining_due': remaining_due,
        'status': status
    }


def get_interest_month_view(conn, borrower_id, interest_month):
    """
    Get complete view of interest for a borrower + month.

    Returns:
        dict with all calculations
    """
    received = calculate_interest_received(conn, borrower_id, interest_month)
    adjusted = calculate_interest_adjusted(conn, borrower_id, interest_month)
    available = calculate_interest_available(conn, borrower_id, interest_month)

    return {
        'borrower_id': borrower_id,
        'interest_month': interest_month,
        'interest_received': received,
        'interest_adjusted': adjusted,
        'interest_available': available
    }


def get_borrower_chit_summary(conn, borrower_id):
    """
    Get summary of all chit payments for a borrower.

    Returns:
        List of dict with chit details and totals
    """
    # Get all chits linked to this borrower
    links = get_borrower_chit_links(conn, borrower_id=borrower_id)

    summaries = []
    for link in links:
        chit_id = link['chit_id']

        # Calculate total adjusted for this chit
        cursor = conn.execute('''
            SELECT SUM(amount) as total_adjusted
            FROM adjustments
            WHERE borrower_id = ? AND chit_id = ? AND status = 'ACTIVE'
        ''', (borrower_id, chit_id))

        total_adjusted = cursor.fetchone()['total_adjusted'] or 0.0

        # Calculate total direct payments
        cursor = conn.execute('''
            SELECT SUM(amount) as total_paid
            FROM direct_chit_payments
            WHERE borrower_id = ? AND chit_id = ?
        ''', (borrower_id, chit_id))

        total_paid = cursor.fetchone()['total_paid'] or 0.0

        summaries.append({
            'chit_id': chit_id,
            'chit_name': link['chit_name'],
            'monthly_installment': link['monthly_installment'],
            'start_month': link['start_month'],
            'chit_status': link['chit_status'],
            'total_adjusted': total_adjusted,
            'total_paid': total_paid,
            'total_contributed': total_adjusted + total_paid
        })

    return summaries
