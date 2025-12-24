// Load active loans on page load
document.addEventListener('DOMContentLoaded', function() {
    loadActiveLoans();

    // Set today as default date
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('payment_date').value = today;

    // Set current month as default
    const currentMonth = new Date().toISOString().slice(0, 7);
    document.getElementById('interest_month').value = currentMonth;

    // Check if loan_id is in URL
    const urlParams = new URLSearchParams(window.location.search);
    const loanId = urlParams.get('loan_id');
    if (loanId) {
        setTimeout(() => {
            document.getElementById('loan_id').value = loanId;
            updateInterestDue();
        }, 500);
    }
});

function loadActiveLoans() {
    fetch('/api/loans?status=Active')
        .then(response => response.json())
        .then(loans => {
            const select = document.getElementById('loan_id');
            select.innerHTML = '<option value="">Select loan...</option>';

            loans.forEach(loan => {
                const option = document.createElement('option');
                option.value = loan.id;
                option.textContent = `${loan.borrower_name} - ${formatCurrency(loan.outstanding_principal)} outstanding`;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading loans:', error);
            showError('Failed to load loans');
        });
}

function updateInterestDue() {
    const loanId = document.getElementById('loan_id').value;
    const interestMonth = document.getElementById('interest_month').value;

    if (!loanId || !interestMonth) {
        document.getElementById('interestDueDisplay').textContent = '-';
        return;
    }

    fetch(`/api/loans/${loanId}/interest-due?month=${interestMonth}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('interestDueDisplay').textContent = formatCurrency(data.interest_due);
        })
        .catch(error => {
            console.error('Error calculating interest:', error);
        });
}

function calculateSplit() {
    const total = parseFloat(document.getElementById('total_received').value) || 0;
    const interestDueText = document.getElementById('interestDueDisplay').textContent;

    // Extract numeric value from formatted currency
    const interestDue = parseFloat(interestDueText.replace(/[^0-9.-]+/g, '')) || 0;

    if (total > 0 && interestDue > 0) {
        if (total >= interestDue) {
            document.getElementById('interest_paid').value = interestDue.toFixed(2);
            document.getElementById('principal_paid').value = (total - interestDue).toFixed(2);
        } else {
            document.getElementById('interest_paid').value = total.toFixed(2);
            document.getElementById('principal_paid').value = '0.00';
        }
    }
}

function validateTotal() {
    const total = parseFloat(document.getElementById('total_received').value) || 0;
    const interest = parseFloat(document.getElementById('interest_paid').value) || 0;
    const principal = parseFloat(document.getElementById('principal_paid').value) || 0;

    const validationMsg = document.getElementById('validationMessage');

    if (Math.abs((interest + principal) - total) > 0.01) {
        validationMsg.textContent = 'Interest Paid + Principal Paid must equal Total Amount Received';
        validationMsg.style.display = 'block';
        return false;
    } else {
        validationMsg.style.display = 'none';
        return true;
    }
}

function submitPayment(event) {
    event.preventDefault();

    if (!validateTotal()) {
        return;
    }

    const formData = new FormData(event.target);
    const data = {
        loan_id: formData.get('loan_id'),
        payment_date: formData.get('payment_date'),
        interest_month: formData.get('interest_month'),
        total_received: formData.get('total_received'),
        interest_paid: formData.get('interest_paid'),
        principal_paid: formData.get('principal_paid'),
        payment_mode: formData.get('payment_mode'),
        reference: formData.get('reference'),
        notes: formData.get('notes')
    };

    fetch('/api/payments', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            const successMsg = document.getElementById('successMessage');
            successMsg.style.display = 'block';
            setTimeout(() => {
                window.location.reload();
            }, 500);
        } else {
            showError(result.error);
        }
    })
    .catch(error => {
        console.error('Error adding payment:', error);
        showError('Failed to add payment');
    });
}

function exportPayments() {
    window.location.href = '/api/export/payments';
}
