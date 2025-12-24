// Load out-of-pocket payments on page load
document.addEventListener('DOMContentLoaded', function() {
    loadOutOfPocketPayments();
});

// Helper function to format month/year from date
function formatMonthYear(dateString) {
    const date = new Date(dateString);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${months[date.getMonth()]} ${date.getFullYear()}`;
}

// Load all out-of-pocket payments
async function loadOutOfPocketPayments() {
    try {
        const response = await fetch('/api/out-of-pocket-payments');
        const payments = await response.json();

        const tbody = document.getElementById('outOfPocketTableBody');
        tbody.innerHTML = '';

        if (payments.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" style="text-align: center;">No out-of-pocket payments found</td></tr>';
            return;
        }

        payments.forEach(payment => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${payment.borrower_name}</td>
                <td>${payment.chit_name}</td>
                <td>${formatMonthYear(payment.due_date)}</td>
                <td>${formatDate(payment.due_date)}</td>
                <td>${formatCurrency(payment.due_amount)}</td>
                <td>${formatCurrency(payment.out_of_pocket_amount)}</td>
                <td>${payment.paid_date ? formatDate(payment.paid_date) : '-'}</td>
                <td>${payment.payment_mode || '-'}</td>
                <td><span class="status-badge status-${payment.payment_status.toLowerCase()}">${payment.payment_status}</span></td>
                <td>${payment.notes || '-'}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading out-of-pocket payments:', error);
        showNotification('Error loading out-of-pocket payments', 'error');
    }
}
