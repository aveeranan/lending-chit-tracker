// Load borrowers on page load
document.addEventListener('DOMContentLoaded', function() {
    loadBorrowers();
    // Load all recent payments by default
    loadRecentPayments();
});

function loadBorrowers() {
    fetch('/api/borrowers')
        .then(response => response.json())
        .then(borrowers => {
            const select = document.getElementById('borrowerSelect');
            select.innerHTML = '<option value="all">All Borrowers</option>';

            borrowers.forEach(name => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading borrowers:', error);
            showError('Failed to load borrowers');
        });
}

function loadPersonHistory() {
    const borrowerName = document.getElementById('borrowerSelect').value;

    if (!borrowerName || borrowerName === 'all') {
        loadRecentPayments();
        return;
    }

    fetch(`/api/person-history/${encodeURIComponent(borrowerName)}`)
        .then(response => response.json())
        .then(history => {
            displayPersonHistory(borrowerName, history);
        })
        .catch(error => {
            console.error('Error loading history:', error);
            showError('Failed to load history');
        });
}

function loadRecentPayments() {
    fetch('/api/recent-payments?months=3')
        .then(response => response.json())
        .then(paymentsByMonth => {
            displayRecentPayments(paymentsByMonth);
        })
        .catch(error => {
            console.error('Error loading recent payments:', error);
            showError('Failed to load recent payments');
        });
}

function displayRecentPayments(paymentsByMonth) {
    const container = document.getElementById('historyContent');

    if (Object.keys(paymentsByMonth).length === 0) {
        container.innerHTML = '<p class="info-message">No payments found in the last 3 months.</p>';
        return;
    }

    let html = '<div class="report-section"><h2>All Borrowers - Last 3 Months</h2>';

    // Sort months in descending order
    const sortedMonths = Object.keys(paymentsByMonth).sort().reverse();

    sortedMonths.forEach(month => {
        const payments = paymentsByMonth[month];

        // Format month for display
        const monthDate = new Date(month + '-01');
        const monthName = monthDate.toLocaleDateString('en-IN', { year: 'numeric', month: 'long' });

        html += `
        <div class="history-section">
            <h3>${monthName}</h3>
            <table class="ledger-table">
                <thead>
                    <tr>
                        <th>Borrower</th>
                        <th>Payment Date</th>
                        <th>Total Received</th>
                        <th>Interest Paid</th>
                        <th>Principal Paid</th>
                        <th>Mode</th>
                        <th>Notes</th>
                    </tr>
                </thead>
                <tbody>
        `;

        payments.forEach(payment => {
            html += `
                <tr>
                    <td><strong>${payment.borrower_name}</strong></td>
                    <td>${formatDate(payment.payment_date)}</td>
                    <td>${formatCurrency(payment.total_received)}</td>
                    <td>${formatCurrency(payment.interest_paid)}</td>
                    <td>${formatCurrency(payment.principal_paid)}</td>
                    <td>${payment.payment_mode || '-'}</td>
                    <td>${payment.notes || '-'}</td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
        `;

        // Calculate monthly totals
        const monthlyTotal = payments.reduce((sum, p) => sum + p.total_received, 0);
        const monthlyInterest = payments.reduce((sum, p) => sum + p.interest_paid, 0);
        const monthlyPrincipal = payments.reduce((sum, p) => sum + p.principal_paid, 0);

        html += `
            <div style="margin-top: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 4px;">
                <strong>Monthly Totals:</strong>
                Total Received: ${formatCurrency(monthlyTotal)} |
                Interest: ${formatCurrency(monthlyInterest)} |
                Principal: ${formatCurrency(monthlyPrincipal)}
            </div>
        </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

function displayPersonHistory(borrowerName, history) {
    const container = document.getElementById('historyContent');

    if (history.length === 0) {
        container.innerHTML = '<p class="info-message">No loans found for this borrower.</p>';
        return;
    }

    let html = `<div class="report-section">
        <h2>${borrowerName} - Complete History</h2>
    `;

    history.forEach(({ loan, payments }) => {
        html += `
        <div class="history-section">
            <h3>Loan #${loan.id} - ${formatDate(loan.given_date)} (${loan.status})</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">Principal Given</div>
                    <div class="detail-value">${formatCurrency(loan.principal_given)}</div>
                </div>
            </div>
        `;

        if (payments.length > 0) {
            html += `
            <table class="ledger-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Interest Month</th>
                        <th>Total Received</th>
                        <th>Interest Paid</th>
                        <th>Principal Paid</th>
                        <th>Mode</th>
                        <th>Notes</th>
                    </tr>
                </thead>
                <tbody>
            `;

            payments.forEach(payment => {
                html += `
                    <tr>
                        <td>${formatDate(payment.payment_date)}</td>
                        <td>${payment.interest_month}</td>
                        <td>${formatCurrency(payment.total_received)}</td>
                        <td>${formatCurrency(payment.interest_paid)}</td>
                        <td>${formatCurrency(payment.principal_paid)}</td>
                        <td>${payment.payment_mode || '-'}</td>
                        <td>${payment.notes || '-'}</td>
                    </tr>
                `;
            });

            html += `
                </tbody>
            </table>
            `;

            // Calculate totals
            const totalReceived = payments.reduce((sum, p) => sum + p.total_received, 0);
            const totalInterest = payments.reduce((sum, p) => sum + p.interest_paid, 0);
            const totalPrincipal = payments.reduce((sum, p) => sum + p.principal_paid, 0);

            html += `
            <div style="margin-top: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 4px;">
                <strong>Totals:</strong>
                Total Received: ${formatCurrency(totalReceived)} |
                Interest: ${formatCurrency(totalInterest)} |
                Principal: ${formatCurrency(totalPrincipal)}
            </div>
            `;
        } else {
            html += '<p style="color: #95a5a6; margin-top: 1rem;">No payments recorded for this loan.</p>';
        }

        html += `</div>`;
    });

    html += `</div>`;
    container.innerHTML = html;
}
