"""
NEW CHIT API ENDPOINTS
Replace the old chit endpoints in app.py with these
"""

# Add these routes to app.py

# ============================================================================
# CHIT GROUP MANAGEMENT
# ============================================================================

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


# ============================================================================
# BORROWER-CHIT LINKS
# ============================================================================

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


# ============================================================================
# ADJUSTMENTS (Interest → Chit)
# ============================================================================

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


# ============================================================================
# DIRECT CHIT PAYMENTS
# ============================================================================

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


# ============================================================================
# CALCULATIONS & VIEWS
# ============================================================================

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


# ============================================================================
# VALIDATION HELPERS (for UI)
# ============================================================================

@app.route('/api/validate-adjustment', methods=['POST'])
@login_required
def api_validate_adjustment():
    """
    Validate an adjustment before creating it.
    Returns validation result and calculations.
    """
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
