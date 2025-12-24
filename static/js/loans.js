let selectedLoanId = null;
let selectedInterestMonth = null;

// Load loans on page load
document.addEventListener('DOMContentLoaded', function() {
    loadLoans();
    loadLoansSummary();

    // Toggle document fields for Add form
    document.getElementById('document_received').addEventListener('change', function() {
        document.getElementById('documentFields').style.display = this.checked ? 'block' : 'none';
    });

    // Toggle document fields for Edit form
    document.getElementById('edit_document_received').addEventListener('change', function() {
        document.getElementById('editDocumentFields').style.display = this.checked ? 'block' : 'none';
    });

    // Set today as default date
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('given_date').value = today;

    // Load toggle state from localStorage
    const hideLoanAmounts = localStorage.getItem('hideLoanAmounts') === 'true';
    if (hideLoanAmounts) {
        toggleLoanAmounts();
    }
});

function loadLoansSummary() {
    fetch('/api/loans/summary')
        .then(response => response.json())
        .then(summary => {
            document.getElementById('summaryTotalLoans').textContent = summary.total_loans || 0;
            document.getElementById('summaryPrincipalGiven').textContent = formatCurrency(summary.total_principal_given || 0);
            document.getElementById('summaryOutstanding').textContent = formatCurrency(summary.total_outstanding || 0);
            document.getElementById('summaryPendingInterest').textContent = formatCurrency(summary.total_pending_interest || 0);
        })
        .catch(error => {
            console.error('Error loading summary:', error);
        });
}

function loadLoans() {
    const status = document.getElementById('statusFilter').value;
    const search = document.getElementById('searchFilter').value;

    let url = '/api/loans?';
    if (status) url += `status=${status}&`;
    if (search) url += `search=${search}&`;

    fetch(url)
        .then(response => response.json())
        .then(loans => {
            displayLoans(loans);
        })
        .catch(error => {
            console.error('Error loading loans:', error);
            showError('Failed to load loans');
        });
}

function displayLoans(loans) {
    const tbody = document.getElementById('loansTableBody');

    if (loans.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No loans found</td></tr>';
        return;
    }

    // Get current month for interest due calculation
    const currentMonth = new Date().toISOString().slice(0, 7);
    selectedInterestMonth = currentMonth;

    tbody.innerHTML = loans.map(loan => `
        <tr>
            <td>${loan.borrower_name}</td>
            <td>${loan.borrower_phone || '-'}</td>
            <td>${formatCurrency(loan.principal_given)}</td>
            <td>${formatCurrency(loan.outstanding_principal)}</td>
            <td>${loan.monthly_rate}%</td>
            <td id="interest-${loan.id}">-</td>
            <td><span class="status-badge status-${loan.status.toLowerCase()}">${loan.status}</span></td>
            <td>
                <button class="btn btn-sm btn-secondary" onclick="viewLoan(${loan.id})">View</button>
                <button class="btn btn-sm btn-success" onclick="editLoan(${loan.id})">Edit</button>
                <button class="btn btn-sm btn-primary" onclick="addPaymentForLoan(${loan.id})">Add Payment</button>
                ${loan.status === 'Active' ? `<button class="btn btn-sm btn-danger" onclick="showCloseLoan(${loan.id})">Close</button>` : ''}
            </td>
        </tr>
    `).join('');

    // Calculate interest due for each loan
    loans.forEach(loan => {
        if (loan.status === 'Active') {
            calculateInterestDue(loan.id, currentMonth);
        }
    });
}

function calculateInterestDue(loanId, month) {
    fetch(`/api/loans/${loanId}/interest-due?month=${month}`)
        .then(response => response.json())
        .then(data => {
            const cell = document.getElementById(`interest-${loanId}`);
            if (cell) {
                cell.textContent = formatCurrency(data.interest_due);
            }
        });
}

function showAddLoanModal() {
    document.getElementById('addLoanModal').style.display = 'block';
}

function closeAddLoanModal() {
    document.getElementById('addLoanModal').style.display = 'none';
    document.getElementById('addLoanForm').reset();
    document.getElementById('documentFields').style.display = 'none';
}

function submitLoan(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const data = {
        borrower_name: formData.get('borrower_name'),
        phone: formData.get('phone'),
        principal_given: formData.get('principal_given'),
        given_date: formData.get('given_date'),
        monthly_rate: formData.get('monthly_rate'),
        interest_due_day: formData.get('interest_due_day'),
        document_received: document.getElementById('document_received').checked,
        document_type: formData.get('document_type'),
        document_path: formData.get('document_path'),
        document_received_date: formData.get('document_received_date'),
        notes: formData.get('notes')
    };

    fetch('/api/loans', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showSuccess('Loan added successfully!');
            closeAddLoanModal();
            setTimeout(() => window.location.reload(), 500);
        } else {
            showError(result.error);
        }
    })
    .catch(error => {
        console.error('Error adding loan:', error);
        showError('Failed to add loan');
    });
}

function viewLoan(loanId) {
    fetch(`/api/loans/${loanId}`)
        .then(response => response.json())
        .then(loan => {
            displayLoanDetails(loan);

            // Load payments
            fetch(`/api/payments/${loanId}`)
                .then(response => response.json())
                .then(payments => {
                    displayPaymentHistory(payments);
                });
        })
        .catch(error => {
            console.error('Error loading loan:', error);
            showError('Failed to load loan details');
        });

    document.getElementById('viewLoanModal').style.display = 'block';
}

function displayLoanDetails(loan) {
    const content = `
        <div class="loan-details">
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">Borrower</div>
                    <div class="detail-value">${loan.borrower_name}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Phone</div>
                    <div class="detail-value">${loan.borrower_phone || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Principal Given</div>
                    <div class="detail-value">${formatCurrency(loan.principal_given)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Outstanding Principal</div>
                    <div class="detail-value">${formatCurrency(loan.outstanding_principal)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Monthly Rate</div>
                    <div class="detail-value">${loan.monthly_rate}%</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Interest Due Day</div>
                    <div class="detail-value">${loan.interest_due_day}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Given Date</div>
                    <div class="detail-value">${formatDate(loan.given_date)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Status</div>
                    <div class="detail-value"><span class="status-badge status-${loan.status.toLowerCase()}">${loan.status}</span></div>
                </div>
                ${loan.closed_date ? `
                <div class="detail-item">
                    <div class="detail-label">Closed Date</div>
                    <div class="detail-value">${formatDate(loan.closed_date)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Close Reason</div>
                    <div class="detail-value">${loan.close_reason || '-'}</div>
                </div>
                ` : ''}
                <div class="detail-item">
                    <div class="detail-label">Pending Interest</div>
                    <div class="detail-value" style="color: #e74c3c;">${formatCurrency(loan.pending_interest || 0)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Document Received</div>
                    <div class="detail-value">${loan.document_received ? 'Yes' : 'No'}</div>
                </div>
                ${loan.document_received ? `
                <div class="detail-item">
                    <div class="detail-label">Document Type</div>
                    <div class="detail-value">${loan.document_type || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Document Path</div>
                    <div class="detail-value">${loan.document_path || '-'}</div>
                </div>
                ` : ''}
            </div>
            ${loan.notes ? `
            <div class="detail-item" style="margin-top: 1rem;">
                <div class="detail-label">Notes</div>
                <div class="detail-value">${loan.notes}</div>
            </div>
            ` : ''}
            <div class="payment-history">
                <h3>Payment History</h3>
                <div id="paymentHistoryContent">Loading...</div>
            </div>
        </div>
    `;

    document.getElementById('viewLoanContent').innerHTML = content;
}

function displayPaymentHistory(payments) {
    const container = document.getElementById('paymentHistoryContent');

    if (payments.length === 0) {
        container.innerHTML = '<p class="info-message">No payments recorded yet.</p>';
        return;
    }

    container.innerHTML = payments.map(payment => `
        <div class="payment-item">
            <div class="payment-header">
                <div class="payment-date">${formatDate(payment.payment_date)} - ${payment.interest_month}</div>
                <div class="payment-amount">${formatCurrency(payment.total_received)}</div>
            </div>
            <div class="payment-details">
                <div>Interest: ${formatCurrency(payment.interest_paid)}</div>
                <div>Principal: ${formatCurrency(payment.principal_paid)}</div>
                ${payment.payment_mode ? `<div>Mode: ${payment.payment_mode}</div>` : ''}
                ${payment.reference ? `<div>Ref: ${payment.reference}</div>` : ''}
            </div>
            ${payment.notes ? `<div style="margin-top: 0.5rem; font-size: 0.9rem;">${payment.notes}</div>` : ''}
        </div>
    `).join('');
}

function closeViewLoanModal() {
    document.getElementById('viewLoanModal').style.display = 'none';
}

function showCloseLoan(loanId) {
    selectedLoanId = loanId;

    fetch(`/api/loans/${loanId}`)
        .then(response => response.json())
        .then(loan => {
            const info = `
                <div style="padding: 1.5rem;">
                    <p><strong>Borrower:</strong> ${loan.borrower_name}</p>
                    <p><strong>Outstanding Principal:</strong> ${formatCurrency(loan.outstanding_principal)}</p>
                    <p><strong>Pending Interest:</strong> ${formatCurrency(loan.pending_interest || 0)}</p>
                </div>
            `;
            document.getElementById('closeLoanInfo').innerHTML = info;
            document.getElementById('closeLoanModal').style.display = 'block';
        });
}

function closeCloseLoanModal() {
    document.getElementById('closeLoanModal').style.display = 'none';
    selectedLoanId = null;
}

function submitCloseLoan(event) {
    event.preventDefault();

    const closeReason = document.getElementById('close_reason').value;

    fetch(`/api/loans/${selectedLoanId}/close`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ close_reason: closeReason })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showSuccess('Loan closed successfully!');
            closeCloseLoanModal();
            setTimeout(() => window.location.reload(), 500);
        } else {
            showError(result.error);
        }
    })
    .catch(error => {
        console.error('Error closing loan:', error);
        showError('Failed to close loan');
    });
}

function editLoan(loanId) {
    fetch(`/api/loans/${loanId}`)
        .then(response => response.json())
        .then(loan => {
            // Populate the edit form
            document.getElementById('edit_loan_id').value = loan.id;
            document.getElementById('edit_borrower_name').value = loan.borrower_name;
            document.getElementById('edit_phone').value = loan.borrower_phone || '';
            document.getElementById('edit_principal_given').value = loan.principal_given;
            document.getElementById('edit_outstanding_principal').value = loan.outstanding_principal;
            document.getElementById('edit_given_date').value = loan.given_date;
            document.getElementById('edit_monthly_rate').value = loan.monthly_rate;
            document.getElementById('edit_interest_due_day').value = loan.interest_due_day;
            document.getElementById('edit_document_received').checked = loan.document_received;
            document.getElementById('edit_document_type').value = loan.document_type || '';
            document.getElementById('edit_document_path').value = loan.document_path || '';
            document.getElementById('edit_document_received_date').value = loan.document_received_date || '';
            document.getElementById('edit_notes').value = loan.notes || '';

            // Show/hide document fields
            document.getElementById('editDocumentFields').style.display = loan.document_received ? 'block' : 'none';

            // Show modal
            document.getElementById('editLoanModal').style.display = 'block';
        })
        .catch(error => {
            console.error('Error loading loan:', error);
            showError('Failed to load loan details');
        });
}

function closeEditLoanModal() {
    document.getElementById('editLoanModal').style.display = 'none';
}

function submitEditLoan(event) {
    event.preventDefault();

    const loanId = document.getElementById('edit_loan_id').value;
    const formData = new FormData(event.target);
    const data = {
        borrower_name: formData.get('edit_borrower_name'),
        phone: formData.get('edit_phone'),
        principal_given: formData.get('edit_principal_given'),
        outstanding_principal: formData.get('edit_outstanding_principal'),
        given_date: formData.get('edit_given_date'),
        monthly_rate: formData.get('edit_monthly_rate'),
        interest_due_day: formData.get('edit_interest_due_day'),
        document_received: document.getElementById('edit_document_received').checked,
        document_type: formData.get('edit_document_type'),
        document_path: formData.get('edit_document_path'),
        document_received_date: formData.get('edit_document_received_date'),
        notes: formData.get('edit_notes')
    };

    fetch(`/api/loans/${loanId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showSuccess('Loan updated successfully!');
            closeEditLoanModal();
            setTimeout(() => window.location.reload(), 500);
        } else {
            showError(result.error);
        }
    })
    .catch(error => {
        console.error('Error updating loan:', error);
        showError('Failed to update loan');
    });
}

function addPaymentForLoan(loanId) {
    window.location.href = `/payments?loan_id=${loanId}`;
}

function exportLoans() {
    window.location.href = '/api/export/loans';
}

// Toggle loan amounts visibility
function toggleLoanAmounts() {
    const values = document.querySelectorAll('#loansSummaryBanner .summary-value');
    const icon = document.getElementById('toggleLoanIcon');
    const text = document.getElementById('toggleLoanText');

    const isHidden = values[0].classList.contains('hidden-amount');

    values.forEach(value => {
        value.classList.toggle('hidden-amount');
    });

    if (isHidden) {
        icon.textContent = '👁️';
        text.textContent = 'Hide Amounts';
        localStorage.setItem('hideLoanAmounts', 'false');
    } else {
        icon.textContent = '🔒';
        text.textContent = 'Show Amounts';
        localStorage.setItem('hideLoanAmounts', 'true');
    }
}

// Close modals when clicking outside
window.onclick = function(event) {
    const addModal = document.getElementById('addLoanModal');
    const closeModal = document.getElementById('closeLoanModal');
    const viewModal = document.getElementById('viewLoanModal');
    const editModal = document.getElementById('editLoanModal');

    if (event.target === addModal) {
        closeAddLoanModal();
    }
    if (event.target === closeModal) {
        closeCloseLoanModal();
    }
    if (event.target === viewModal) {
        closeViewLoanModal();
    }
    if (event.target === editModal) {
        closeEditLoanModal();
    }
}
