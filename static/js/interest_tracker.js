document.addEventListener('DOMContentLoaded', function() {
    loadInterestData();
});

function loadInterestData() {
    const statusFilter = document.getElementById('statusFilter').value;
    const url = statusFilter === 'All'
        ? '/api/interest-tracker'
        : `/api/interest-tracker?status=${encodeURIComponent(statusFilter)}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            renderTable(data);
            updateSummary(data);
        })
        .catch(error => {
            console.error('Error loading interest data:', error);
            document.getElementById('interestTableBody').innerHTML =
                '<tr><td colspan="7" style="text-align: center; color: red;">Failed to load data</td></tr>';
        });
}

function renderTable(data) {
    const tbody = document.getElementById('interestTableBody');

    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">No records found</td></tr>';
        return;
    }

    tbody.innerHTML = data.map(row => {
        const statusClass = getStatusClass(row.status);
        return `
            <tr class="${statusClass}">
                <td>${row.borrower_name}</td>
                <td>${row.loan_id}</td>
                <td>${row.interest_month}</td>
                <td>${formatCurrency(row.interest_due)}</td>
                <td>${formatCurrency(row.interest_paid)}</td>
                <td>${formatCurrency(row.pending)}</td>
                <td>
                    <select class="status-select ${statusClass}"
                            onchange="updateStatus(${row.loan_id}, '${row.interest_month}', this.value)"
                            data-loan="${row.loan_id}" data-month="${row.interest_month}">
                        <option value="Paid" ${row.status === 'Paid' ? 'selected' : ''}>Paid</option>
                        <option value="Not Paid" ${row.status === 'Not Paid' ? 'selected' : ''}>Not Paid</option>
                        <option value="Ignore" ${row.status === 'Ignore' ? 'selected' : ''}>Ignore</option>
                        <option value="Closed" ${row.status === 'Closed' ? 'selected' : ''}>Closed</option>
                    </select>
                </td>
            </tr>
        `;
    }).join('');
}

function updateSummary(data) {
    let totalDue = 0, totalPaid = 0, totalPending = 0;
    data.forEach(row => {
        totalDue += row.interest_due;
        totalPaid += row.interest_paid;
        totalPending += row.pending;
    });

    document.getElementById('totalDue').textContent = formatCurrency(totalDue);
    document.getElementById('totalPaid').textContent = formatCurrency(totalPaid);
    document.getElementById('totalPending').textContent = formatCurrency(totalPending);
    document.getElementById('totalRecords').textContent = data.length;
}

function updateStatus(loanId, interestMonth, status) {
    fetch('/api/interest-status', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            loan_id: loanId,
            interest_month: interestMonth,
            status: status
        })
    })
    .then(response => response.json())
    .then(result => {
        if (!result.success) {
            alert('Failed to update status: ' + result.error);
        }
        // Update the select styling
        const select = document.querySelector(
            `select[data-loan="${loanId}"][data-month="${interestMonth}"]`
        );
        if (select) {
            select.className = 'status-select ' + getStatusClass(status);
            select.closest('tr').className = getStatusClass(status);
        }
    })
    .catch(error => {
        console.error('Error updating status:', error);
        alert('Failed to update status');
    });
}

function getStatusClass(status) {
    switch (status) {
        case 'Paid': return 'status-paid';
        case 'Not Paid': return 'status-not-paid';
        case 'Ignore': return 'status-ignore';
        case 'Closed': return 'status-closed';
        default: return '';
    }
}
