from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import os
import csv
import shutil
from datetime import datetime
from functools import wraps
from database import db_manager

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize database
db_manager.init_db()

def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Redirect to login or loans page."""
    if 'logged_in' in session:
        return redirect(url_for('loans'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        pin = request.form.get('pin')
        if db_manager.verify_pin(pin):
            session['logged_in'] = True
            return redirect(url_for('loans'))
        return render_template('login.html', error='Invalid PIN')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout."""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/loans')
@login_required
def loans():
    """Loans page."""
    return render_template('loans.html')

@app.route('/payments')
@login_required
def payments():
    """Payments page."""
    return render_template('payments.html')

@app.route('/person-history')
@login_required
def person_history():
    """Person history page."""
    return render_template('person_history.html')

@app.route('/monthly-report')
@login_required
def monthly_report():
    """Monthly report page."""
    return render_template('monthly_report.html')

@app.route('/chits')
@login_required
def chits():
    """Chits management page."""
    return render_template('chits.html')

@app.route('/out-of-pocket')
@login_required
def out_of_pocket():
    """Out-of-pocket payments page."""
    return render_template('out_of_pocket.html')

# API Endpoints

@app.route('/api/loans', methods=['GET'])
@login_required
def api_get_loans():
    """Get all loans with optional filters."""
    status = request.args.get('status')
    search = request.args.get('search')
    loans = db_manager.get_loans(status, search)
    return jsonify(loans)

@app.route('/api/loans/summary', methods=['GET'])
@login_required
def api_get_loans_summary():
    """Get summary statistics for loans."""
    summary = db_manager.get_loans_summary()
    return jsonify(summary)

@app.route('/api/loans', methods=['POST'])
@login_required
def api_create_loan():
    """Create a new loan."""
    data = request.json

    try:
        loan_id = db_manager.create_loan(
            borrower_name=data['borrower_name'],
            phone=data.get('phone'),
            principal_given=float(data['principal_given']),
            given_date=data['given_date'],
            monthly_rate=float(data['monthly_rate']),
            interest_due_day=int(data.get('interest_due_day', 5)),
            document_received=data.get('document_received', False),
            document_type=data.get('document_type'),
            document_path=data.get('document_path'),
            document_received_date=data.get('document_received_date'),
            notes=data.get('notes')
        )
        return jsonify({'success': True, 'loan_id': loan_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/loans/<int:loan_id>', methods=['GET'])
@login_required
def api_get_loan(loan_id):
    """Get a specific loan."""
    loan = db_manager.get_loan_by_id(loan_id)
    if loan:
        # Add pending interest
        loan['pending_interest'] = db_manager.calculate_pending_interest(loan_id)
        return jsonify(loan)
    return jsonify({'error': 'Loan not found'}), 404

@app.route('/api/loans/<int:loan_id>', methods=['PUT'])
@login_required
def api_update_loan(loan_id):
    """Update a loan."""
    data = request.json

    try:
        db_manager.update_loan(
            loan_id=loan_id,
            borrower_name=data['borrower_name'],
            phone=data.get('phone'),
            principal_given=float(data['principal_given']),
            outstanding_principal=float(data['outstanding_principal']),
            given_date=data['given_date'],
            monthly_rate=float(data['monthly_rate']),
            interest_due_day=int(data.get('interest_due_day', 5)),
            document_received=data.get('document_received', False),
            document_type=data.get('document_type'),
            document_path=data.get('document_path'),
            document_received_date=data.get('document_received_date'),
            notes=data.get('notes')
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/loans/<int:loan_id>/close', methods=['POST'])
@login_required
def api_close_loan(loan_id):
    """Close a loan."""
    data = request.json
    close_reason = data.get('close_reason', '')

    try:
        db_manager.close_loan(loan_id, close_reason)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/loans/<int:loan_id>/interest-due', methods=['GET'])
@login_required
def api_get_interest_due(loan_id):
    """Calculate interest due for a specific month."""
    interest_month = request.args.get('month')
    loan = db_manager.get_loan_by_id(loan_id)

    if not loan:
        return jsonify({'error': 'Loan not found'}), 404

    interest_due = db_manager.calculate_interest_due(loan, interest_month)
    return jsonify({'interest_due': interest_due})

@app.route('/api/payments', methods=['POST'])
@login_required
def api_add_payment():
    """Add a new payment."""
    data = request.json

    # Validate that interest_paid + principal_paid = total_received
    total = float(data['total_received'])
    interest = float(data['interest_paid'])
    principal = float(data['principal_paid'])

    if abs((interest + principal) - total) > 0.01:
        return jsonify({
            'success': False,
            'error': 'Interest paid + Principal paid must equal Total received'
        }), 400

    try:
        db_manager.add_payment(
            loan_id=int(data['loan_id']),
            payment_date=data['payment_date'],
            interest_month=data['interest_month'],
            total_received=total,
            interest_paid=interest,
            principal_paid=principal,
            payment_mode=data.get('payment_mode'),
            reference=data.get('reference'),
            notes=data.get('notes')
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/payments/<int:loan_id>', methods=['GET'])
@login_required
def api_get_payments(loan_id):
    """Get all payments for a loan."""
    payments = db_manager.get_payments_by_loan(loan_id)
    return jsonify(payments)

@app.route('/api/borrowers', methods=['GET'])
@login_required
def api_get_borrowers():
    """Get all borrowers."""
    borrowers = db_manager.get_borrowers()
    return jsonify(borrowers)

@app.route('/api/person-history/<borrower_name>', methods=['GET'])
@login_required
def api_get_person_history(borrower_name):
    """Get person history."""
    history = db_manager.get_person_history(borrower_name)
    return jsonify(history)

@app.route('/api/recent-payments', methods=['GET'])
@login_required
def api_get_recent_payments():
    """Get recent payments for all borrowers."""
    months = int(request.args.get('months', 3))
    payments = db_manager.get_recent_payments_all(months)
    return jsonify(payments)

@app.route('/api/monthly-report', methods=['GET'])
@login_required
def api_get_monthly_report():
    """Get monthly report."""
    report_month = request.args.get('month')
    include_closed = request.args.get('include_closed', 'false') == 'true'

    report = db_manager.get_monthly_report(report_month, include_closed)
    return jsonify(report)

@app.route('/api/export/loans', methods=['GET'])
@login_required
def api_export_loans():
    """Export loans to CSV."""
    loans = db_manager.get_loans()

    # Create CSV
    csv_path = '/tmp/loans_export.csv'
    with open(csv_path, 'w', newline='') as csvfile:
        if loans:
            fieldnames = loans[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(loans)

    return send_file(csv_path, as_attachment=True, download_name=f'loans_{datetime.now().strftime("%Y%m%d")}.csv')

@app.route('/api/export/payments', methods=['GET'])
@login_required
def api_export_payments():
    """Export all payments to CSV."""
    conn = db_manager.get_db_connection()
    cursor = conn.execute('''
        SELECT p.*, b.name as borrower_name
        FROM payments p
        JOIN loans l ON p.loan_id = l.id
        JOIN borrowers b ON l.borrower_id = b.id
        ORDER BY p.payment_date DESC
    ''')
    payments = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Create CSV
    csv_path = '/tmp/payments_export.csv'
    with open(csv_path, 'w', newline='') as csvfile:
        if payments:
            fieldnames = payments[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(payments)

    return send_file(csv_path, as_attachment=True, download_name=f'payments_{datetime.now().strftime("%Y%m%d")}.csv')

@app.route('/api/backup', methods=['GET'])
@login_required
def api_backup_database():
    """Backup database."""
    backup_path = f'/tmp/lending_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    shutil.copy(db_manager.DB_PATH, backup_path)
    return send_file(backup_path, as_attachment=True)

@app.route('/api/restore', methods=['POST'])
@login_required
def api_restore_database():
    """Restore database from backup."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    try:
        # Save backup of current database
        backup_path = f'{db_manager.DB_PATH}.backup'
        shutil.copy(db_manager.DB_PATH, backup_path)

        # Restore from uploaded file
        file.save(db_manager.DB_PATH)

        return jsonify({'success': True})
    except Exception as e:
        # Restore backup if something went wrong
        if os.path.exists(backup_path):
            shutil.copy(backup_path, db_manager.DB_PATH)
        return jsonify({'success': False, 'error': str(e)}), 400

# ============================================================================
# INDIVIDUAL CHIT MANAGEMENT (Borrower-specific chits with monthly schedules)
# ============================================================================

@app.route('/api/chits', methods=['GET'])
@login_required
def api_get_individual_chits():
    """Get all individual chits with optional status filter."""
    status = request.args.get('status')
    chits = db_manager.get_individual_chits(status)
    return jsonify(chits)

@app.route('/api/chits', methods=['POST'])
@login_required
def api_create_individual_chit():
    """Create a new individual chit with monthly schedule."""
    data = request.json

    try:
        chit_id = db_manager.create_individual_chit(
            borrower_name=data['borrower_name'],
            chit_name=data['chit_name'],
            total_months=int(data['total_months']),
            start_date=data['start_date'],
            monthly_amounts=data['monthly_amounts'],
            prized_month=data.get('prized_month'),
            prize_amount=data.get('prize_amount'),
            notes=data.get('notes', '')
        )
        return jsonify({'success': True, 'chit_id': chit_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/chits/<int:chit_id>', methods=['GET'])
@login_required
def api_get_individual_chit(chit_id):
    """Get a specific individual chit with schedule."""
    chit = db_manager.get_individual_chit_by_id(chit_id)
    if chit:
        return jsonify(chit)
    return jsonify({'error': 'Chit not found'}), 404

@app.route('/api/chits/<int:chit_id>', methods=['PUT'])
@login_required
def api_update_individual_chit(chit_id):
    """Update an individual chit."""
    data = request.json

    try:
        db_manager.update_individual_chit(
            chit_id=chit_id,
            borrower_name=data['borrower_name'],
            chit_name=data['chit_name'],
            start_date=data['start_date'],
            monthly_amounts=data['monthly_amounts'],
            prized_month=data.get('prized_month'),
            prize_amount=data.get('prize_amount'),
            notes=data.get('notes', '')
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/chits/<int:chit_id>/close', methods=['POST'])
@login_required
def api_close_individual_chit(chit_id):
    """Close an individual chit."""
    try:
        db_manager.close_individual_chit(chit_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/pending-chit-dues', methods=['GET'])
@login_required
def api_get_pending_chit_dues():
    """Get all pending chit dues."""
    dues = db_manager.get_pending_chit_dues()
    return jsonify(dues)

@app.route('/api/chit-schedule/<int:schedule_id>/pay', methods=['POST'])
@login_required
def api_pay_chit_schedule(schedule_id):
    """Mark a chit schedule item as paid."""
    data = request.json

    try:
        db_manager.pay_chit_schedule(
            schedule_id=schedule_id,
            paid_amount=float(data['paid_amount']),
            paid_date=data['paid_date'],
            payment_mode=data.get('payment_mode', ''),
            notes=data.get('notes', '')
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/out-of-pocket-payments', methods=['GET'])
@login_required
def api_get_out_of_pocket_payments():
    """Get all out-of-pocket chit payments."""
    payments = db_manager.get_out_of_pocket_payments()
    return jsonify(payments)

@app.route('/api/chit-adjustments', methods=['POST'])
@login_required
def api_create_chit_adjustment():
    """Create a chit adjustment against loan interest."""
    data = request.json

    try:
        print(f"Creating chit adjustment with data: {data}")  # Debug log
        result = db_manager.create_chit_adjustment(
            schedule_id=int(data['schedule_id']),
            loan_id=int(data['loan_id']),
            interest_month=data['interest_month'],
            adjusted_amount=float(data['adjusted_amount']),
            notes=data.get('notes', '')
        )

        response = {
            'success': True,
            'adjustment_id': result['adjustment_id']
        }

        # Include partial adjustment message if present
        if result.get('partial_adjustment_msg'):
            response['partial_adjustment_msg'] = result['partial_adjustment_msg']

        return jsonify(response)
    except Exception as e:
        print(f"Error creating chit adjustment: {str(e)}")  # Debug log
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400

# ============================================================================
# CHIT MODULE API (India chit member + borrower interest adjustment)
# ============================================================================

# Chit Group Management
@app.route('/api/chit-groups', methods=['GET'])
@login_required
def api_get_chit_groups():
    """Get all chit groups."""
    status = request.args.get('status')
    chit_groups = db_manager.get_chit_groups(status)
    return jsonify(chit_groups)

@app.route('/api/chit-groups', methods=['POST'])
@login_required
def api_create_chit_group():
    """Create a new chit group."""
    data = request.json

    try:
        chit_id = db_manager.create_chit_group(
            name=data['name'],
            monthly_installment=float(data['monthly_installment']),
            start_month=data['start_month'],
            notes=data.get('notes', '')
        )
        return jsonify({'success': True, 'chit_id': chit_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/chit-groups/<int:chit_id>', methods=['GET'])
@login_required
def api_get_chit_group(chit_id):
    """Get a specific chit group."""
    chit_group = db_manager.get_chit_group_by_id(chit_id)
    if chit_group:
        return jsonify(chit_group)
    return jsonify({'error': 'Chit group not found'}), 404

@app.route('/api/chit-groups/<int:chit_id>', methods=['PUT'])
@login_required
def api_update_chit_group(chit_id):
    """Update a chit group."""
    data = request.json

    try:
        db_manager.update_chit_group(
            chit_id=chit_id,
            name=data['name'],
            monthly_installment=float(data['monthly_installment']),
            start_month=data['start_month'],
            notes=data.get('notes', '')
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/chit-groups/<int:chit_id>/close', methods=['POST'])
@login_required
def api_close_chit_group(chit_id):
    """Close a chit group."""
    data = request.json

    try:
        db_manager.close_chit_group(chit_id, data['closed_month'])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# Borrower-Chit Links
@app.route('/api/borrower-chit-links', methods=['GET'])
@login_required
def api_get_borrower_chit_links():
    """Get borrower-chit links."""
    borrower_id = request.args.get('borrower_id', type=int)
    chit_id = request.args.get('chit_id', type=int)

    links = db_manager.get_borrower_chit_links(borrower_id, chit_id)
    return jsonify(links)

@app.route('/api/borrower-chit-links', methods=['POST'])
@login_required
def api_create_borrower_chit_link():
    """Link a borrower to a chit."""
    data = request.json

    try:
        db_manager.link_borrower_to_chit(
            borrower_id=int(data['borrower_id']),
            chit_id=int(data['chit_id']),
            notes=data.get('notes', '')
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/borrower-chit-links/<int:borrower_id>/<int:chit_id>', methods=['DELETE'])
@login_required
def api_delete_borrower_chit_link(borrower_id, chit_id):
    """Unlink a borrower from a chit."""
    try:
        db_manager.unlink_borrower_from_chit(borrower_id, chit_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# Adjustments (Interest → Chit)
@app.route('/api/adjustments', methods=['GET'])
@login_required
def api_get_adjustments():
    """Get adjustments with filters."""
    borrower_id = request.args.get('borrower_id', type=int)
    chit_id = request.args.get('chit_id', type=int)
    status = request.args.get('status', 'ACTIVE')

    adjustments = db_manager.get_adjustments(borrower_id, chit_id, status)
    return jsonify(adjustments)

@app.route('/api/adjustments', methods=['POST'])
@login_required
def api_create_adjustment():
    """Create a new adjustment."""
    data = request.json

    try:
        adjustment_id = db_manager.create_adjustment(
            borrower_id=int(data['borrower_id']),
            interest_month=data['interest_month'],
            chit_id=int(data['chit_id']),
            chit_month=data['chit_month'],
            amount=float(data['amount']),
            notes=data.get('notes', '')
        )
        return jsonify({'success': True, 'adjustment_id': adjustment_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/adjustments/<int:adjustment_id>', methods=['GET'])
@login_required
def api_get_adjustment(adjustment_id):
    """Get a specific adjustment."""
    adjustment = db_manager.get_adjustment_by_id(adjustment_id)
    if adjustment:
        return jsonify(adjustment)
    return jsonify({'error': 'Adjustment not found'}), 404

@app.route('/api/adjustments/<int:adjustment_id>/reverse', methods=['POST'])
@login_required
def api_reverse_adjustment(adjustment_id):
    """Reverse an adjustment."""
    data = request.json

    try:
        reversal_id = db_manager.reverse_adjustment(
            adjustment_id=adjustment_id,
            notes=data.get('notes', '')
        )
        return jsonify({'success': True, 'reversal_id': reversal_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# Direct Chit Payments
@app.route('/api/direct-chit-payments', methods=['GET'])
@login_required
def api_get_direct_chit_payments():
    """Get direct chit payments."""
    borrower_id = request.args.get('borrower_id', type=int)
    chit_id = request.args.get('chit_id', type=int)

    payments = db_manager.get_direct_chit_payments(borrower_id, chit_id)
    return jsonify(payments)

@app.route('/api/direct-chit-payments', methods=['POST'])
@login_required
def api_add_direct_chit_payment():
    """Add a direct chit payment."""
    data = request.json

    try:
        payment_id = db_manager.add_direct_chit_payment(
            borrower_id=int(data['borrower_id']),
            chit_id=int(data['chit_id']),
            chit_month=data['chit_month'],
            amount=float(data['amount']),
            payment_date=data['payment_date'],
            payment_mode=data.get('payment_mode', ''),
            reference=data.get('reference', ''),
            notes=data.get('notes', '')
        )
        return jsonify({'success': True, 'payment_id': payment_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# Calculations & Views
@app.route('/api/interest-view/<int:borrower_id>/<interest_month>', methods=['GET'])
@login_required
def api_get_interest_view(borrower_id, interest_month):
    """Get interest calculations for a borrower + month."""
    try:
        view = db_manager.get_interest_month_view(borrower_id, interest_month)
        return jsonify(view)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/chit-month-view/<int:borrower_id>/<int:chit_id>/<chit_month>', methods=['GET'])
@login_required
def api_get_chit_month_view(borrower_id, chit_id, chit_month):
    """Get chit calculations for a borrower + chit + month."""
    try:
        view = db_manager.get_chit_month_view(borrower_id, chit_id, chit_month)
        return jsonify(view)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/borrower-chit-summary/<int:borrower_id>', methods=['GET'])
@login_required
def api_get_borrower_chit_summary(borrower_id):
    """Get chit summary for a borrower."""
    try:
        summary = db_manager.get_borrower_chit_summary(borrower_id)
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Validation Helpers
@app.route('/api/validate-adjustment', methods=['POST'])
@login_required
def api_validate_adjustment():
    """Validate an adjustment before creating it."""
    data = request.json

    try:
        borrower_id = int(data['borrower_id'])
        interest_month = data['interest_month']
        chit_id = int(data['chit_id'])
        chit_month = data['chit_month']
        amount = float(data['amount'])

        # Get interest view
        interest_view = db_manager.get_interest_month_view(borrower_id, interest_month)

        # Get chit view
        chit_view = db_manager.get_chit_month_view(borrower_id, chit_id, chit_month)

        # Calculate max allowed
        max_allowed = min(interest_view['interest_available'], chit_view['remaining_due'])

        # Validation checks
        errors = []

        if not db_manager.is_borrower_linked_to_chit(borrower_id, chit_id):
            errors.append('Borrower is not linked to this chit')

        if amount <= 0:
            errors.append('Amount must be positive')

        if amount > interest_view['interest_available']:
            errors.append(f'Insufficient interest available (₹{interest_view["interest_available"]:.2f})')

        if amount > chit_view['remaining_due']:
            errors.append(f'Amount exceeds remaining due (₹{chit_view["remaining_due"]:.2f})')

        if chit_view['remaining_due'] == 0:
            errors.append('Chit month is already fully paid')

        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors,
            'interest_view': interest_view,
            'chit_view': chit_view,
            'max_allowed': max_allowed
        })

    except Exception as e:
        return jsonify({'valid': False, 'errors': [str(e)]}), 400

if __name__ == '__main__':
    print("=" * 60)
    print("Lending Tracker App Starting...")
    print("=" * 60)
    print(f"Default PIN: 1234")
    print(f"Access the app at: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
