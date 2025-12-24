// Set current month on page load
document.addEventListener('DOMContentLoaded', function() {
    const currentMonth = new Date().toISOString().slice(0, 7);
    document.getElementById('reportMonth').value = currentMonth;
    loadMonthlyReport();
});

function loadMonthlyReport() {
    const reportMonth = document.getElementById('reportMonth').value;
    const includeClosed = document.getElementById('includeClosed').checked;

    if (!reportMonth) {
        document.getElementById('reportContent').innerHTML = '<p class="info-message">Select a month to view the report.</p>';
        return;
    }

    fetch(`/api/monthly-report?month=${reportMonth}&include_closed=${includeClosed}`)
        .then(response => response.json())
        .then(report => {
            displayMonthlyReport(reportMonth, report);
        })
        .catch(error => {
            console.error('Error loading report:', error);
            showError('Failed to load report');
        });
}

function displayMonthlyReport(month, report) {
    const container = document.getElementById('reportContent');

    // Format month for display
    const monthDate = new Date(month + '-01');
    const monthName = monthDate.toLocaleDateString('en-IN', { year: 'numeric', month: 'long' });

    let html = `
    <div class="report-totals">
        <div class="total-item">
            <div class="total-label">Total Interest Received</div>
            <div class="total-value">${formatCurrency(report.totals.interest_received)}</div>
        </div>
        <div class="total-item">
            <div class="total-label">Total Principal Received</div>
            <div class="total-value">${formatCurrency(report.totals.principal_received)}</div>
        </div>
        <div class="total-item">
            <div class="total-label">Total Received</div>
            <div class="total-value">${formatCurrency(report.totals.total_received)}</div>
        </div>
        <div class="total-item">
            <div class="total-label">Pending Interest (This Month)</div>
            <div class="total-value" style="color: #ff9800;">${formatCurrency(report.totals.interest_pending_month || 0)}</div>
        </div>
        <div class="total-item">
            <div class="total-label">Total Pending Interest</div>
            <div class="total-value" style="color: #e74c3c;">${formatCurrency(report.totals.interest_pending || 0)}</div>
        </div>
    </div>
    `;

    // Full Interest Paid
    html += `
    <div class="report-section">
        <h2 style="color: #27ae60;">Full Interest Paid (${report.full_paid.length})</h2>
        ${renderReportTable(report.full_paid, true)}
    </div>
    `;

    // Partial Interest Paid
    html += `
    <div class="report-section">
        <h2 style="color: #f39c12;">Partial Interest Paid (${report.partial_paid.length})</h2>
        ${renderReportTable(report.partial_paid, false)}
    </div>
    `;

    // No Interest Paid
    html += `
    <div class="report-section">
        <h2 style="color: #e74c3c;">No Interest Paid (${report.not_paid.length})</h2>
        ${renderReportTable(report.not_paid, false)}
    </div>
    `;

    container.innerHTML = html;
}

function renderReportTable(loans, showReceived) {
    if (loans.length === 0) {
        return '<p style="color: #95a5a6;">None</p>';
    }

    let html = `
    <table class="data-table">
        <thead>
            <tr>
                <th>Borrower</th>
                <th>Outstanding Principal</th>
                <th>Rate</th>
                <th>Interest Due</th>
                <th>Interest Paid</th>
                <th>Pending (Month)</th>
                <th>Total Pending</th>
                ${showReceived ? '<th>Principal Paid</th><th>Total Received</th>' : ''}
            </tr>
        </thead>
        <tbody>
    `;

    loans.forEach(loan => {
        html += `
            <tr>
                <td>${loan.borrower_name}</td>
                <td>${formatCurrency(loan.outstanding_principal)}</td>
                <td>${loan.monthly_rate}%</td>
                <td>${formatCurrency(loan.interest_due)}</td>
                <td>${formatCurrency(loan.interest_paid)}</td>
                <td style="color: ${loan.interest_pending_month > 0 ? '#ff9800' : '#27ae60'};">${formatCurrency(loan.interest_pending_month || 0)}</td>
                <td style="color: ${loan.interest_pending > 0 ? '#e74c3c' : '#27ae60'};">${formatCurrency(loan.interest_pending || 0)}</td>
                ${showReceived ? `
                    <td>${formatCurrency(loan.principal_paid)}</td>
                    <td>${formatCurrency(loan.total_received)}</td>
                ` : ''}
            </tr>
        `;
    });

    html += `
        </tbody>
    </table>
    `;

    return html;
}
