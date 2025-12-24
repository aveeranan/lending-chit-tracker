// Chits Management JavaScript

let currentChit = null;
let currentScheduleItem = null;

// Helper function to format month/year from date
function formatMonthYear(dateString) {
    const date = new Date(dateString);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${months[date.getMonth()]} ${date.getFullYear()}`;
}

// Load chits on page load
document.addEventListener('DOMContentLoaded', function() {
    loadChits();
    loadChitsSummary();
    loadPendingDues();
    loadBorrowers();

    // Set default start date to today
    document.getElementById('startDate').valueAsDate = new Date();
    document.getElementById('paidDate').valueAsDate = new Date();

    // Generate initial 20 monthly inputs
    generateMonthlyInputs();

    // Load toggle state from localStorage
    const hideChitAmounts = localStorage.getItem('hideChitAmounts') === 'true';
    if (hideChitAmounts) {
        toggleChitAmounts();
    }
});

// Load all chits
async function loadChits() {
    const status = document.getElementById('statusFilter').value;
    const url = status ? `/api/chits?status=${status}` : '/api/chits';

    try {
        const response = await fetch(url);
        const chits = await response.json();

        const tbody = document.getElementById('chitsTableBody');
        tbody.innerHTML = '';

        if (chits.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">No chits found</td></tr>';
            return;
        }

        chits.forEach(chit => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${chit.borrower_name}</td>
                <td>${chit.chit_name}</td>
                <td>${formatDate(chit.start_date)}</td>
                <td>${chit.total_months}</td>
                <td>${chit.prized_month || 'N/A'}</td>
                <td>${chit.prize_amount ? formatCurrency(chit.prize_amount) : 'N/A'}</td>
                <td><span class="status-badge status-${chit.status.toLowerCase()}">${chit.status}</span></td>
                <td>
                    <button onclick="viewChitDetails(${chit.id})" class="btn btn-sm">View</button>
                    ${chit.status === 'Active' ?
                        `<button onclick="closeChit(${chit.id})" class="btn btn-sm btn-danger">Close</button>` :
                        ''}
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading chits:', error);
        showNotification('Error loading chits', 'error');
    }
}

// Load pending dues
async function loadPendingDues() {
    try {
        const response = await fetch('/api/pending-chit-dues');
        const dues = await response.json();

        const tbody = document.getElementById('pendingDuesTableBody');
        tbody.innerHTML = '';

        if (dues.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">No pending dues</td></tr>';
            return;
        }

        dues.forEach(due => {
            const row = document.createElement('tr');
            const isOverdue = new Date(due.due_date) < new Date();
            row.className = isOverdue ? 'overdue' : '';

            // For Partial status, show only Pay button. For Pending, show both Pay and Adjust
            // IMPORTANT: Pass remaining amount, not due_amount, and also pass paid_amount
            const actionButtons = due.payment_status === 'Partial'
                ? `<button onclick="showPayChitModalWithRemaining(${due.id}, '${due.borrower_name}', '${due.chit_name}', '${formatMonthYear(due.due_date)}', ${due.due_amount}, ${due.paid_amount || 0})" class="btn btn-sm btn-primary">Pay</button>`
                : `<button onclick="showPayChitModalWithRemaining(${due.id}, '${due.borrower_name}', '${due.chit_name}', '${formatMonthYear(due.due_date)}', ${due.due_amount}, ${due.paid_amount || 0})" class="btn btn-sm btn-primary">Pay</button>
                   <button onclick="showAdjustBalanceModal(${due.id}, '${due.borrower_name}', '${due.chit_name}', '${formatMonthYear(due.due_date)}', ${due.due_amount}, ${due.borrower_id}, '${due.due_date}')" class="btn btn-sm">Adjust</button>`;

            row.innerHTML = `
                <td>${due.borrower_name}</td>
                <td>${due.chit_name}</td>
                <td>${formatMonthYear(due.due_date)}</td>
                <td>${formatDate(due.due_date)} ${isOverdue ? '<span style="color: red;">(Overdue)</span>' : ''}</td>
                <td>${formatCurrency(due.remaining)} ${due.payment_status === 'Partial' ? '<span style="color: orange; font-size: 0.85em;">(Partial)</span>' : ''}</td>
                <td>
                    ${actionButtons}
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading pending dues:', error);
        showNotification('Error loading pending dues', 'error');
    }
}

// Load borrowers for autocomplete
async function loadBorrowers() {
    try {
        const response = await fetch('/api/borrowers');
        const borrowers = await response.json();

        const datalist = document.getElementById('borrowersList');
        datalist.innerHTML = '';

        borrowers.forEach(borrower => {
            const option = document.createElement('option');
            option.value = borrower;
            datalist.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading borrowers:', error);
    }
}

// Load chits summary
async function loadChitsSummary() {
    try {
        const [chitsResponse, duesResponse] = await Promise.all([
            fetch('/api/chits'),
            fetch('/api/pending-chit-dues')
        ]);

        const allChits = await chitsResponse.json();
        const pendingDues = await duesResponse.json();

        const activeChits = allChits.filter(c => c.status === 'Active').length;

        // Calculate current month dues
        const today = new Date();
        const currentMonth = today.toISOString().substring(0, 7);
        const currentMonthDues = pendingDues.filter(d => d.due_date.substring(0, 7) === currentMonth);
        const currentMonthTotal = currentMonthDues.reduce((sum, d) => sum + d.due_amount, 0);

        // Calculate total pending dues
        const totalPending = pendingDues.reduce((sum, d) => sum + d.due_amount, 0);

        // Calculate total paid (sum all paid_amount from all chits' schedules)
        let totalPaid = 0;
        for (const chit of allChits) {
            const chitDetails = await fetch(`/api/chits/${chit.id}`).then(r => r.json());
            if (chitDetails.schedule) {
                totalPaid += chitDetails.schedule.reduce((sum, s) => sum + (s.paid_amount || 0), 0);
            }
        }

        document.getElementById('summaryActiveChits').textContent = activeChits;
        document.getElementById('summaryCurrentMonthDues').textContent = formatCurrency(currentMonthTotal);
        document.getElementById('summaryTotalPendingDues').textContent = formatCurrency(totalPending);
        document.getElementById('summaryTotalPaid').textContent = formatCurrency(totalPaid);
    } catch (error) {
        console.error('Error loading chits summary:', error);
    }
}

// Export chits to CSV
async function exportChits() {
    try {
        const response = await fetch('/api/chits');
        const chits = await response.json();

        if (chits.length === 0) {
            showNotification('No chits to export', 'error');
            return;
        }

        // Create CSV content
        const headers = ['Borrower', 'Chit Name', 'Start Date', 'Total Months', 'Prized Month', 'Prize Amount', 'Status', 'Notes'];
        const csvContent = [
            headers.join(','),
            ...chits.map(chit => [
                `"${chit.borrower_name}"`,
                `"${chit.chit_name}"`,
                chit.start_date,
                chit.total_months,
                chit.prized_month || '',
                chit.prize_amount || '',
                chit.status,
                `"${(chit.notes || '').replace(/"/g, '""')}"`
            ].join(','))
        ].join('\n');

        // Download file
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chits_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        showNotification('Chits exported successfully', 'success');
    } catch (error) {
        console.error('Error exporting chits:', error);
        showNotification('Error exporting chits', 'error');
    }
}

// Toggle chit amounts visibility
function toggleChitAmounts() {
    const values = document.querySelectorAll('#chitsSummaryBanner .summary-value');
    const icon = document.getElementById('toggleChitIcon');
    const text = document.getElementById('toggleChitText');

    const isHidden = values[0].classList.contains('hidden-amount');

    values.forEach(value => {
        value.classList.toggle('hidden-amount');
    });

    if (isHidden) {
        icon.textContent = '👁️';
        text.textContent = 'Hide Amounts';
        localStorage.setItem('hideChitAmounts', 'false');
    } else {
        icon.textContent = '🔒';
        text.textContent = 'Show Amounts';
        localStorage.setItem('hideChitAmounts', 'true');
    }
}

// Generate monthly amount input fields
function generateMonthlyInputs() {
    const totalMonths = parseInt(document.getElementById('totalMonths').value) || 20;
    const container = document.getElementById('monthlyAmountsContainer');
    container.innerHTML = '';

    for (let i = 1; i <= totalMonths; i++) {
        const div = document.createElement('div');
        div.innerHTML = `
            <label style="font-size: 0.9em;">Month ${i}</label>
            <input type="number" id="month_${i}" step="0.01" required placeholder="0.00" style="width: 100%;">
        `;
        container.appendChild(div);
    }
}

// Fill all months with same amount
function fillAllMonths() {
    const amount = document.getElementById('quickFillAmount').value;
    if (!amount) {
        showNotification('Please enter an amount first', 'error');
        return;
    }

    const totalMonths = parseInt(document.getElementById('totalMonths').value) || 20;
    for (let i = 1; i <= totalMonths; i++) {
        document.getElementById(`month_${i}`).value = amount;
    }
    showNotification('All months filled', 'success');
}

// Fill from prized month onwards
function fillRemainingMonths() {
    const amount = document.getElementById('quickFillAmount').value;
    const prizedMonth = parseInt(document.getElementById('prizedMonth').value);

    if (!amount) {
        showNotification('Please enter an amount first', 'error');
        return;
    }

    if (!prizedMonth) {
        showNotification('Please enter prized month first', 'error');
        return;
    }

    const totalMonths = parseInt(document.getElementById('totalMonths').value) || 20;
    for (let i = prizedMonth; i <= totalMonths; i++) {
        document.getElementById(`month_${i}`).value = amount;
    }
    showNotification(`Filled from month ${prizedMonth} onwards`, 'success');
}

// Show add chit modal
function showAddChitModal() {
    document.getElementById('addChitModal').style.display = 'block';
    document.getElementById('addChitForm').reset();
    document.getElementById('startDate').valueAsDate = new Date();
    generateMonthlyInputs();
}

// Close add chit modal
function closeAddChitModal() {
    document.getElementById('addChitModal').style.display = 'none';
    document.getElementById('addChitForm').reset();
}

// Submit chit
async function submitChit(event) {
    event.preventDefault();

    const totalMonths = parseInt(document.getElementById('totalMonths').value) || 20;
    const monthlyAmounts = [];

    // Collect monthly amounts
    for (let i = 1; i <= totalMonths; i++) {
        const amount = parseFloat(document.getElementById(`month_${i}`).value);
        monthlyAmounts.push(amount);
    }

    const data = {
        borrower_name: document.getElementById('borrowerName').value,
        chit_name: document.getElementById('chitName').value,
        total_months: totalMonths,
        start_date: document.getElementById('startDate').value,
        monthly_amounts: monthlyAmounts,
        prized_month: document.getElementById('prizedMonth').value || null,
        prize_amount: document.getElementById('prizeAmount').value || null,
        notes: document.getElementById('notes').value || ''
    };

    try {
        const response = await fetch('/api/chits', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            closeAddChitModal();
            showNotification('Chit created successfully', 'success');
            setTimeout(() => window.location.reload(), 500);
        } else {
            showNotification(result.error || 'Error creating chit', 'error');
        }
    } catch (error) {
        console.error('Error creating chit:', error);
        showNotification('Error creating chit', 'error');
    }
}

// View chit details
async function viewChitDetails(chitId) {
    try {
        const response = await fetch(`/api/chits/${chitId}`);
        const chit = await response.json();

        currentChit = chit;

        let scheduleHtml = '<table style="width: 100%; margin-top: 20px;"><thead><tr>' +
            '<th>Month</th><th>Due Date</th><th>Due Amount</th><th>Status</th>' +
            '<th>Paid Amount</th><th>Paid Date</th><th>Actions</th></tr></thead><tbody>';

        chit.schedule.forEach(item => {
            // Determine action buttons based on payment status
            let actionButtons = '-';
            if (item.payment_status === 'Pending') {
                actionButtons = `<button onclick="showPayChitModalWithRemaining(${item.id}, '${chit.borrower_name}', '${chit.chit_name}', '${formatMonthYear(item.due_date)}', ${item.due_amount}, ${item.paid_amount || 0})" class="btn btn-sm btn-primary">Pay</button>
                                 <button onclick="showAdjustBalanceModal(${item.id}, '${chit.borrower_name}', '${chit.chit_name}', '${formatMonthYear(item.due_date)}', ${item.due_amount}, ${chit.borrower_id}, '${item.due_date}')" class="btn btn-sm">Adjust</button>`;
            } else if (item.payment_status === 'Partial') {
                actionButtons = `<button onclick="showPayChitModalWithRemaining(${item.id}, '${chit.borrower_name}', '${chit.chit_name}', '${formatMonthYear(item.due_date)}', ${item.due_amount}, ${item.paid_amount || 0})" class="btn btn-sm btn-primary">Pay</button>`;
            }

            scheduleHtml += `<tr>
                <td>${formatMonthYear(item.due_date)}</td>
                <td>${formatDate(item.due_date)}</td>
                <td>${formatCurrency(item.due_amount)}</td>
                <td><span class="status-badge status-${item.payment_status.toLowerCase()}">${item.payment_status}</span></td>
                <td>${item.paid_amount ? formatCurrency(item.paid_amount) : '-'}</td>
                <td>${item.paid_date ? formatDate(item.paid_date) : '-'}</td>
                <td>
                    ${actionButtons}
                </td>
            </tr>`;
        });

        scheduleHtml += '</tbody></table>';

        const content = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3 style="margin: 0;">${chit.chit_name}</h3>
                ${chit.status === 'Active' ?
                    `<button onclick="editChit(${chit.id})" class="btn btn-secondary">Edit Chit</button>` :
                    ''}
            </div>
            <table style="width: 100%; margin-bottom: 20px; background: #f9f9f9;">
                <tr>
                    <td style="padding: 10px; width: 50%;"><strong>Borrower:</strong></td>
                    <td style="padding: 10px;">${chit.borrower_name}</td>
                </tr>
                <tr>
                    <td style="padding: 10px;"><strong>Start Date:</strong></td>
                    <td style="padding: 10px;">${formatDate(chit.start_date)}</td>
                </tr>
                <tr>
                    <td style="padding: 10px;"><strong>Total Months:</strong></td>
                    <td style="padding: 10px;">${chit.total_months}</td>
                </tr>
                <tr>
                    <td style="padding: 10px;"><strong>Prized Month:</strong></td>
                    <td style="padding: 10px;">${chit.prized_month || 'N/A'}</td>
                </tr>
                <tr>
                    <td style="padding: 10px;"><strong>Prize Amount:</strong></td>
                    <td style="padding: 10px;">${chit.prize_amount ? formatCurrency(chit.prize_amount) : 'N/A'}</td>
                </tr>
                <tr>
                    <td style="padding: 10px;"><strong>Status:</strong></td>
                    <td style="padding: 10px;"><span class="status-badge status-${chit.status.toLowerCase()}">${chit.status}</span></td>
                </tr>
                ${chit.notes ? `<tr>
                    <td style="padding: 10px;"><strong>Notes:</strong></td>
                    <td style="padding: 10px;">${chit.notes}</td>
                </tr>` : ''}
            </table>
            <h3>Monthly Schedule</h3>
            ${scheduleHtml}
        `;

        // Update modal title
        document.getElementById('viewChitTitle').textContent = chit.chit_name;
        document.getElementById('chitDetailsContent').innerHTML = content;
        document.getElementById('viewChitModal').style.display = 'block';
    } catch (error) {
        console.error('Error loading chit details:', error);
        showNotification('Error loading chit details', 'error');
    }
}

// Close view chit modal
function closeViewChitModal() {
    document.getElementById('viewChitModal').style.display = 'none';
}

// Edit chit
async function editChit(chitId) {
    try {
        const response = await fetch(`/api/chits/${chitId}`);
        const chit = await response.json();

        // Store current chit for reference
        currentChit = chit;

        // Populate form fields
        document.getElementById('editChitId').value = chit.id;
        document.getElementById('editBorrowerName').value = chit.borrower_name;
        document.getElementById('editChitName').value = chit.chit_name;
        document.getElementById('editTotalMonths').value = chit.total_months;
        document.getElementById('editStartDate').value = chit.start_date;
        document.getElementById('editPrizedMonth').value = chit.prized_month || '';
        document.getElementById('editPrizeAmount').value = chit.prize_amount || '';
        document.getElementById('editNotes').value = chit.notes || '';

        // Generate monthly amount inputs with current values
        const container = document.getElementById('editMonthlyAmountsContainer');
        container.innerHTML = '';

        // Get current month for comparison
        const today = new Date();
        const currentMonth = today.toISOString().substring(0, 7);

        chit.schedule.forEach((item, index) => {
            const monthNum = item.month_number;
            const itemMonth = item.due_date.substring(0, 7);
            const isPast = itemMonth < currentMonth;
            const isPaidOrAdjusted = item.payment_status !== 'Pending';
            const isEditable = !isPast && !isPaidOrAdjusted;

            const div = document.createElement('div');
            div.innerHTML = `
                <label style="font-size: 0.9em; ${!isEditable ? 'color: #999;' : ''}">
                    Month ${monthNum}
                    ${isPaidOrAdjusted ? ` <span style="color: green; font-size: 0.8em;">(${item.payment_status})</span>` : ''}
                    ${isPast && !isPaidOrAdjusted ? ' <span style="color: #666; font-size: 0.8em;">(Past)</span>' : ''}
                </label>
                <input type="number"
                       id="edit_month_${monthNum}"
                       step="0.01"
                       required
                       value="${item.due_amount}"
                       ${!isEditable ? 'readonly style="background: #f0f0f0; color: #999;"' : 'style="width: 100%;"'}
                       placeholder="0.00">
            `;
            container.appendChild(div);
        });

        // Close view modal if open and show edit modal
        closeViewChitModal();
        document.getElementById('editChitModal').style.display = 'block';
    } catch (error) {
        console.error('Error loading chit for edit:', error);
        showNotification('Error loading chit details', 'error');
    }
}

// Close edit chit modal
function closeEditChitModal() {
    document.getElementById('editChitModal').style.display = 'none';
    document.getElementById('editChitForm').reset();
}

// Fill future months in edit mode
function fillFutureMonths() {
    const amount = document.getElementById('editQuickFillAmount').value;
    if (!amount) {
        showNotification('Please enter an amount first', 'error');
        return;
    }

    const totalMonths = parseInt(document.getElementById('editTotalMonths').value) || 20;
    let filled = 0;

    for (let i = 1; i <= totalMonths; i++) {
        const input = document.getElementById(`edit_month_${i}`);
        if (input && !input.hasAttribute('readonly')) {
            input.value = amount;
            filled++;
        }
    }

    showNotification(`Filled ${filled} editable month(s)`, 'success');
}

// Submit edit chit
async function submitEditChit(event) {
    event.preventDefault();

    const chitId = parseInt(document.getElementById('editChitId').value);
    const totalMonths = parseInt(document.getElementById('editTotalMonths').value);

    // Collect monthly amounts
    const monthlyAmounts = [];
    for (let i = 1; i <= totalMonths; i++) {
        const amount = parseFloat(document.getElementById(`edit_month_${i}`).value);
        monthlyAmounts.push(amount);
    }

    const data = {
        chit_id: chitId,
        borrower_name: document.getElementById('editBorrowerName').value,
        chit_name: document.getElementById('editChitName').value,
        start_date: document.getElementById('editStartDate').value,
        monthly_amounts: monthlyAmounts,
        prized_month: document.getElementById('editPrizedMonth').value || null,
        prize_amount: document.getElementById('editPrizeAmount').value || null,
        notes: document.getElementById('editNotes').value || ''
    };

    try {
        const response = await fetch(`/api/chits/${chitId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            closeEditChitModal();
            showNotification('Chit updated successfully', 'success');
            setTimeout(() => window.location.reload(), 500);
        } else {
            showNotification(result.error || 'Error updating chit', 'error');
        }
    } catch (error) {
        console.error('Error updating chit:', error);
        showNotification('Error updating chit', 'error');
    }
}

// Global variable to store max payment allowed
let maxPaymentAllowed = 0;

// Show pay chit modal with remaining amount (simplified version that takes paid_amount directly)
function showPayChitModalWithRemaining(scheduleId, borrowerName, chitName, monthDisplay, dueAmount, paidAmount) {
    // Close view modal if open
    closeViewChitModal();

    const currentPaid = paidAmount || 0;
    const remaining = dueAmount - currentPaid;
    maxPaymentAllowed = remaining;

    document.getElementById('payScheduleId').value = scheduleId;
    const paidAmountInput = document.getElementById('paidAmount');
    paidAmountInput.value = remaining > 0 ? remaining.toFixed(2) : 0;
    paidAmountInput.max = remaining > 0 ? remaining.toFixed(2) : 0;
    document.getElementById('paidDate').valueAsDate = new Date();

    document.getElementById('paymentDetails').innerHTML = `
        <p><strong>Borrower:</strong> ${borrowerName}</p>
        <p><strong>Chit:</strong> ${chitName}</p>
        <p><strong>Month:</strong> ${monthDisplay}</p>
        <p><strong>Due Amount:</strong> ${formatCurrency(dueAmount)}</p>
        ${currentPaid > 0 ? `<p><strong>Already Paid:</strong> <span style="color: green;">${formatCurrency(currentPaid)}</span></p>` : ''}
        ${currentPaid > 0 ? `<p><strong>Remaining:</strong> <span style="color: #e74c3c; font-weight: bold;">${formatCurrency(remaining)}</span></p>` : ''}
        ${currentPaid > 0 ? `<p style="color: #ff9800; font-size: 0.9em; margin-top: 10px;"><strong>⚠️ Note:</strong> You can only pay up to ₹${remaining.toFixed(2)} (the remaining amount)</p>` : ''}
    `;

    document.getElementById('payChitModal').style.display = 'block';
}

// Legacy function - kept for backward compatibility (now redirects to new function with API fetch)
async function showPayChitModal(scheduleId, borrowerName, chitName, monthDisplay, dueAmount) {
    // Close view modal if open
    closeViewChitModal();

    // Fetch current schedule details to show already paid amount
    try {
        const scheduleResponse = await fetch(`/api/chits/${currentChit ? currentChit.id : 0}`);
        const chitData = await scheduleResponse.json();

        let currentPaid = 0;
        if (chitData && chitData.schedule) {
            const scheduleItem = chitData.schedule.find(s => s.id === scheduleId);
            if (scheduleItem) {
                currentPaid = scheduleItem.paid_amount || 0;
            }
        }

        // Call the new function with the fetched paid amount
        showPayChitModalWithRemaining(scheduleId, borrowerName, chitName, monthDisplay, dueAmount, currentPaid);
    } catch (error) {
        console.error('Error fetching schedule details:', error);
        // Fallback: call with 0 paid amount
        showPayChitModalWithRemaining(scheduleId, borrowerName, chitName, monthDisplay, dueAmount, 0);
    }
}

// Close pay chit modal
function closePayChitModal() {
    document.getElementById('payChitModal').style.display = 'none';
    document.getElementById('payChitForm').reset();
}

// Submit chit payment
async function submitChitPayment(event) {
    event.preventDefault();

    const paidAmount = parseFloat(document.getElementById('paidAmount').value);

    // Validate payment amount
    if (paidAmount <= 0) {
        alert('❌ Invalid Amount\n\nPayment amount must be greater than zero.');
        return;
    }

    if (paidAmount > maxPaymentAllowed) {
        alert(`❌ Amount Exceeds Remaining Due\n\nYou can only pay up to ₹${maxPaymentAllowed.toFixed(2)} (the remaining amount).\n\nEntered amount: ₹${paidAmount.toFixed(2)}`);
        return;
    }

    const data = {
        schedule_id: parseInt(document.getElementById('payScheduleId').value),
        paid_amount: paidAmount,
        paid_date: document.getElementById('paidDate').value,
        payment_mode: document.getElementById('paymentMode').value,
        notes: document.getElementById('payNotes').value
    };

    try {
        const response = await fetch(`/api/chit-schedule/${data.schedule_id}/pay`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            closePayChitModal();
            alert('✅ Payment Recorded Successfully\n\nPayment of ₹' + paidAmount.toFixed(2) + ' has been recorded.');
            showNotification('Payment recorded successfully', 'success');
            setTimeout(() => window.location.reload(), 500);
        } else {
            alert('❌ Payment Failed\n\n' + (result.error || 'Error recording payment'));
            showNotification(result.error || 'Error recording payment', 'error');
        }
    } catch (error) {
        console.error('Error recording payment:', error);
        showNotification('Error recording payment', 'error');
    }
}

// Global variables to store adjustment context
let currentAdjustmentContext = {
    scheduleId: null,
    borrowerName: null,
    chitName: null,
    monthDisplay: null,
    dueAmount: 0,
    borrowerId: null,
    dueDate: null,
    currentPaid: 0,
    remaining: 0
};

// Show adjust balance modal
async function showAdjustBalanceModal(scheduleId, borrowerName, chitName, monthDisplay, dueAmount, borrowerId, dueDate) {
    // Close view modal if open
    closeViewChitModal();

    // Store context
    currentAdjustmentContext = {
        scheduleId,
        borrowerName,
        chitName,
        monthDisplay,
        dueAmount,
        borrowerId,
        dueDate,
        currentPaid: 0,
        remaining: dueAmount
    };

    // Fetch current schedule details to show already paid amount
    try {
        const scheduleResponse = await fetch(`/api/chits/${currentChit ? currentChit.id : 0}`);
        const chitData = await scheduleResponse.json();

        if (chitData && chitData.schedule) {
            const scheduleItem = chitData.schedule.find(s => s.id === scheduleId);
            if (scheduleItem) {
                currentAdjustmentContext.currentPaid = scheduleItem.paid_amount || 0;
            }
        }
    } catch (error) {
        console.error('Error fetching schedule details:', error);
    }

    currentAdjustmentContext.remaining = dueAmount - currentAdjustmentContext.currentPaid;

    document.getElementById('adjustScheduleId').value = scheduleId;
    document.getElementById('adjustedAmountFromInterest').value = '';
    document.getElementById('outOfPocketAmount').value = '0';
    document.getElementById('totalPaymentDisplay').textContent = '₹0.00';
    document.getElementById('interestAvailableDisplay').style.display = 'none';

    document.getElementById('adjustmentDetails').innerHTML = `
        <p><strong>Borrower:</strong> ${borrowerName}</p>
        <p><strong>Chit:</strong> ${chitName}</p>
        <p><strong>Month:</strong> ${monthDisplay}</p>
        <p><strong>Due Amount:</strong> ${formatCurrency(dueAmount)}</p>
        ${currentAdjustmentContext.currentPaid > 0 ? `<p><strong>Already Paid/Adjusted:</strong> <span style="color: green;">${formatCurrency(currentAdjustmentContext.currentPaid)}</span></p>` : ''}
        ${currentAdjustmentContext.currentPaid > 0 ? `<p><strong>Remaining:</strong> <span style="color: #e74c3c; font-weight: bold;">${formatCurrency(currentAdjustmentContext.remaining)}</span></p>` : ''}
    `;

    // Load active loans for this borrower
    try {
        const response = await fetch(`/api/loans?status=Active&search=${encodeURIComponent(borrowerName)}`);
        const loans = await response.json();

        const select = document.getElementById('adjustLoanId');
        select.innerHTML = '<option value="">Select Loan</option>';

        loans.forEach(loan => {
            const option = document.createElement('option');
            option.value = loan.id;
            option.textContent = `Loan #${loan.id} - Principal: ${formatCurrency(loan.principal_given)} - Rate: ${loan.monthly_rate}%`;
            select.appendChild(option);
        });

        if (loans.length === 0) {
            showNotification('No active loans found for this borrower', 'error');
            return;
        }

        // Set interest month to the chit due date's month (YYYY-MM format)
        const chitDueMonth = dueDate.substring(0, 7); // Extract YYYY-MM from YYYY-MM-DD
        document.getElementById('adjustInterestMonth').value = chitDueMonth;

        document.getElementById('adjustBalanceModal').style.display = 'block';
    } catch (error) {
        console.error('Error loading loans:', error);
        showNotification('Error loading loans for borrower', 'error');
    }
}

// Calculate adjustment split when loan/month changes
async function calculateAdjustmentSplit() {
    const loanId = document.getElementById('adjustLoanId').value;
    const interestMonth = document.getElementById('adjustInterestMonth').value;

    if (!loanId || !interestMonth) {
        document.getElementById('adjustedAmountFromInterest').value = '';
        document.getElementById('interestAvailableDisplay').style.display = 'none';
        updateTotalAdjustment();
        return;
    }

    try {
        // Fetch interest due for the selected month
        const response = await fetch(`/api/loans/${loanId}/interest-due?month=${interestMonth}`);
        const data = await response.json();
        const interestDue = data.interest_due;

        // Fetch payments to calculate already paid interest
        const paymentsResponse = await fetch(`/api/payments/${loanId}`);
        const payments = await paymentsResponse.json();

        // Calculate already paid interest for this month
        const alreadyPaid = payments
            .filter(p => p.interest_month === interestMonth)
            .reduce((sum, p) => sum + (p.interest_paid || 0), 0);

        const availableInterest = interestDue - alreadyPaid;

        // Calculate how much can be adjusted from interest
        const remainingChitDue = currentAdjustmentContext.remaining;
        const adjustableFromInterest = Math.min(availableInterest, remainingChitDue);

        // Update the read-only field
        document.getElementById('adjustedAmountFromInterest').value = adjustableFromInterest > 0 ? adjustableFromInterest.toFixed(2) : '0.00';

        // Show interest available information
        const displayDiv = document.getElementById('interestAvailableDisplay');
        displayDiv.style.display = 'block';
        displayDiv.innerHTML = `
            <p style="margin: 5px 0;"><strong>Interest Due for ${interestMonth}:</strong> ${formatCurrency(interestDue)}</p>
            <p style="margin: 5px 0;"><strong>Already Paid:</strong> ${formatCurrency(alreadyPaid)}</p>
            <p style="margin: 5px 0;"><strong>Available Interest:</strong> <span style="color: #2ecc71; font-weight: bold;">${formatCurrency(availableInterest)}</span></p>
            <p style="margin: 5px 0;"><strong>Remaining Chit Due:</strong> <span style="color: #e74c3c; font-weight: bold;">${formatCurrency(remainingChitDue)}</span></p>
            <hr style="margin: 10px 0;">
            <p style="margin: 5px 0;"><strong>Will Adjust from Interest:</strong> <span style="color: #3498db; font-weight: bold;">${formatCurrency(adjustableFromInterest)}</span></p>
            ${adjustableFromInterest < remainingChitDue ? `<p style="margin: 5px 0; color: #e67e22;"><strong>⚠️ Additional Payment Needed:</strong> ${formatCurrency(remainingChitDue - adjustableFromInterest)}</p>` : ''}
        `;

        updateTotalAdjustment();
    } catch (error) {
        console.error('Error calculating adjustment split:', error);
        showNotification('Error calculating interest available', 'error');
    }
}

// Update total adjustment display
function updateTotalAdjustment() {
    const fromInterest = parseFloat(document.getElementById('adjustedAmountFromInterest').value) || 0;
    const outOfPocket = parseFloat(document.getElementById('outOfPocketAmount').value) || 0;
    const total = fromInterest + outOfPocket;

    document.getElementById('totalPaymentDisplay').textContent = formatCurrency(total);

    // Update validation message if total exceeds remaining
    const remaining = currentAdjustmentContext.remaining;
    if (total > remaining) {
        showNotification(`Total payment (${formatCurrency(total)}) exceeds remaining due (${formatCurrency(remaining)})`, 'error');
    }
}

// Close adjust balance modal
function closeAdjustBalanceModal() {
    document.getElementById('adjustBalanceModal').style.display = 'none';
    document.getElementById('adjustBalanceForm').reset();
}

// Submit adjustment
async function submitAdjustment(event) {
    event.preventDefault();

    const adjustedFromInterest = parseFloat(document.getElementById('adjustedAmountFromInterest').value) || 0;
    const outOfPocket = parseFloat(document.getElementById('outOfPocketAmount').value) || 0;
    const totalPayment = adjustedFromInterest + outOfPocket;

    // Validation
    if (totalPayment <= 0) {
        alert('❌ Invalid Payment\n\nTotal payment must be greater than zero.');
        return;
    }

    if (totalPayment > currentAdjustmentContext.remaining) {
        alert(`❌ Payment Exceeds Due Amount\n\nTotal payment (${formatCurrency(totalPayment)}) exceeds remaining due (${formatCurrency(currentAdjustmentContext.remaining)})`);
        return;
    }

    // Build summary message
    let summaryMsg = '📝 Payment Summary\n\n';
    summaryMsg += `Chit: ${currentAdjustmentContext.chitName}\n`;
    summaryMsg += `Month: ${currentAdjustmentContext.monthDisplay}\n`;
    summaryMsg += `Total Due: ${formatCurrency(currentAdjustmentContext.remaining)}\n\n`;
    summaryMsg += `--- Payment Breakdown ---\n`;
    if (adjustedFromInterest > 0) {
        summaryMsg += `From Interest: ${formatCurrency(adjustedFromInterest)}\n`;
    }
    if (outOfPocket > 0) {
        summaryMsg += `Out of Pocket: ${formatCurrency(outOfPocket)}\n`;
    }
    summaryMsg += `\nTotal Payment: ${formatCurrency(totalPayment)}\n`;
    summaryMsg += `Remaining After: ${formatCurrency(currentAdjustmentContext.remaining - totalPayment)}\n\n`;
    summaryMsg += 'Proceed with this payment?';

    if (!confirm(summaryMsg)) {
        return;
    }

    try {
        // If there's interest adjustment, create it
        if (adjustedFromInterest > 0) {
            const adjustmentData = {
                schedule_id: parseInt(document.getElementById('adjustScheduleId').value),
                loan_id: parseInt(document.getElementById('adjustLoanId').value),
                interest_month: document.getElementById('adjustInterestMonth').value,
                adjusted_amount: adjustedFromInterest,
                notes: document.getElementById('adjustNotes').value || 'Interest adjustment'
            };

            const adjustmentResponse = await fetch('/api/chit-adjustments', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(adjustmentData)
            });

            const adjustmentResult = await adjustmentResponse.json();

            if (!adjustmentResult.success) {
                throw new Error(adjustmentResult.error || 'Failed to create interest adjustment');
            }
        }

        // If there's out-of-pocket payment, record it
        if (outOfPocket > 0) {
            const scheduleId = parseInt(document.getElementById('adjustScheduleId').value);
            const paymentData = {
                schedule_id: scheduleId,
                paid_amount: outOfPocket,
                paid_date: new Date().toISOString().split('T')[0],
                payment_mode: 'Cash',
                notes: document.getElementById('adjustNotes').value || 'Out of pocket payment'
            };

            const paymentResponse = await fetch(`/api/chit-schedule/${scheduleId}/pay`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(paymentData)
            });

            const paymentResult = await paymentResponse.json();

            if (!paymentResult.success) {
                throw new Error(paymentResult.error || 'Failed to record out-of-pocket payment');
            }
        }

        closeAdjustBalanceModal();

        // Show success message
        let successMsg = '✅ Payment Recorded Successfully\n\n';
        if (adjustedFromInterest > 0) {
            successMsg += `Interest Adjusted: ${formatCurrency(adjustedFromInterest)}\n`;
        }
        if (outOfPocket > 0) {
            successMsg += `Out of Pocket Paid: ${formatCurrency(outOfPocket)}\n`;
        }
        successMsg += `\nTotal Payment: ${formatCurrency(totalPayment)}`;

        alert(successMsg);
        showNotification('Payment recorded successfully', 'success');
        setTimeout(() => window.location.reload(), 500);

    } catch (error) {
        console.error('Error creating payment:', error);
        alert('❌ Payment Failed\n\n' + error.message);
        showNotification('Error recording payment', 'error');
    }
}

// Close chit
async function closeChit(chitId) {
    if (!confirm('Are you sure you want to close this chit? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/api/chits/${chitId}/close`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            showNotification('Chit closed successfully', 'success');
            setTimeout(() => window.location.reload(), 500);
        } else {
            showNotification(result.error || 'Error closing chit', 'error');
        }
    } catch (error) {
        console.error('Error closing chit:', error);
        showNotification('Error closing chit', 'error');
    }
}

// Close modals when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}
