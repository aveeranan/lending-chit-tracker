# Lending Tracker

A local-only web application for tracking personal loans, interest payments, and payment history. Built with Flask and SQLite for complete privacy and local data storage.

## Features

### 1. Loans Management
- Track all loans with borrower details, principal amounts, interest rates
- Support for monthly interest-only loans
- Document tracking (type, path, received date)
- Loan status management (Active/Closed)
- Search and filter capabilities
- Detailed loan view with payment history

### 2. Payments
- Record interest and principal payments
- Automatic interest calculation for selected month
- Payment attribution to specific interest months
- Multiple payment modes (Cash, Bank Transfer, UPI, Cheque)
- Payment validation (Interest + Principal = Total)

### 3. Person History
- Complete payment ledger by borrower
- Month-wise transaction history
- Loan-wise summary and totals

### 4. Monthly Reports
- Categorized view: Full paid, Partial paid, No payment
- Active loans tracking by default
- Option to include closed loans
- Total interest and principal received
- Comprehensive monthly financial overview

### 5. Data Management
- CSV export for loans and payments
- Database backup and restore
- PIN-based authentication
- Fully local - no cloud dependencies

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Navigate to the project directory:**
   ```bash
   cd lending-tracker
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Access the application:**
   Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

5. **Login:**
   - Default PIN: `1234`
   - You can change this later through the database

## Usage Guide

### Adding a Loan

1. Go to the **Loans** page
2. Click **+ Add Loan**
3. Fill in the required fields:
   - Borrower name (required)
   - Phone (optional)
   - Principal given (required)
   - Given date (required)
   - Interest rate (monthly %, required)
   - Interest due day (1-28, default: 5)
4. Optionally add document details
5. Click **Add Loan**

### Recording a Payment

1. Go to the **Payments** page
2. Select the loan/borrower
3. Enter payment details:
   - Payment date
   - Interest month (YYYY-MM format)
   - Total amount received
   - Interest paid
   - Principal paid (must equal: Total - Interest)
4. Add payment mode and reference (optional)
5. Click **Add Payment**

**Tip:** The system will automatically calculate the interest due for the selected month to help you allocate the payment correctly.

### Editing a Loan

1. Go to the **Loans** page
2. Find the loan you want to edit
3. Click **Edit** button
4. Modify the fields:
   - Borrower details (name, phone)
   - Principal given/outstanding
   - Interest rate
   - Given date
   - Document details
   - Notes
5. Click **Update Loan**

**Important Notes:**
- Changing **Principal Given** or **Interest Rate** will affect all interest calculations
- **Outstanding Principal** should match: Principal Given - Total Principal Paid
- Changes take effect immediately
- Edit with caution as it affects historical calculations

### Closing a Loan

1. Go to the **Loans** page
2. Find the loan you want to close
3. Click **Close** button
4. Review outstanding amounts
5. Select close reason:
   - Fully Repaid
   - Settled
   - Written Off
   - Other
6. Confirm closure

**Note:** Loans can be closed even with pending amounts. Once closed, they won't accrue interest and won't appear in monthly reports by default.

### Viewing Person History

1. Go to **Person History** page
2. Select a borrower from the dropdown
3. View:
   - All loans for that borrower
   - Complete payment ledger
   - Totals for each loan

### Generating Monthly Reports

1. Go to **Monthly Report** page
2. Select the month (YYYY-MM format)
3. Optionally check "Include Closed Loans"
4. View categorized report:
   - Full Interest Paid
   - Partial Interest Paid
   - No Interest Paid
   - Summary totals

## Database Schema

### Borrowers Table
- `id`: Primary key
- `name`: Borrower name
- `phone`: Phone number (optional)

### Loans Table
- `id`: Primary key
- `borrower_id`: Foreign key to borrowers
- `principal_given`: Original loan amount
- `outstanding_principal`: Current outstanding amount
- `monthly_rate`: Interest rate (monthly %)
- `interest_due_day`: Day of month when interest is due (1-28)
- `given_date`: Date loan was given
- `status`: Active or Closed
- `closed_date`: Date when loan was closed
- `close_reason`: Reason for closure
- `document_received`: Boolean
- `document_type`: Type of document
- `document_path`: Local file path to document
- `document_received_date`: Date document was received
- `notes`: Additional notes

### Payments Table
- `id`: Primary key
- `loan_id`: Foreign key to loans
- `payment_date`: Date of payment
- `interest_month`: Month for which interest applies (YYYY-MM)
- `total_received`: Total amount received
- `interest_paid`: Amount allocated to interest
- `principal_paid`: Amount allocated to principal
- `payment_mode`: Mode of payment (Cash, Bank Transfer, etc.)
- `reference`: Reference number
- `notes`: Additional notes

## Business Logic

### Interest Calculation

Interest for any month is calculated as:
```
Interest = Opening Outstanding Principal × (Monthly Rate / 100)
```

Where **Opening Outstanding Principal** is the principal at the start of the month, calculated as:
```
Opening Principal = Principal Given - Sum of all principal payments made BEFORE this month
```

### Payment Attribution

- Each payment is attributed to a specific interest month (YYYY-MM)
- Interest paid is recorded separately from principal paid
- Principal payments immediately reduce the outstanding principal
- Future interest calculations use the reduced principal

### Closed Loans

- Closed loans do not accrue interest after the closed date
- They are excluded from monthly reports by default
- No new payments can be added (unless loan is reopened)
- All historical data is preserved

## Data Export & Backup

### Export to CSV

**Loans Export:**
- Go to Loans page
- Click "Export CSV"
- Downloads all loan data with borrower information

**Payments Export:**
- Go to Payments page
- Click "Export CSV"
- Downloads all payment records with borrower names

### Database Backup

The application stores all data in `database/lending.db`

**Manual Backup:**
1. Stop the application
2. Copy the file `database/lending.db` to a safe location
3. Restart the application

**Restore from Backup:**
1. Stop the application
2. Replace `database/lending.db` with your backup file
3. Restart the application

## Security

### PIN Protection

- The application uses PIN-based authentication
- Default PIN: `1234`
- PIN is hashed using Werkzeug security

**To Change PIN:**
```python
python -c "from database.db_manager import update_pin; update_pin('YOUR_NEW_PIN')"
```

### Local-Only Operation

- All data stored locally in SQLite database
- No external API calls or cloud dependencies
- Runs entirely on localhost
- Suitable for personal/family use

## File Structure

```
lending-tracker/
├── app.py                      # Flask application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── database/
│   ├── schema.sql             # Database schema
│   ├── db_manager.py          # Database operations
│   └── lending.db             # SQLite database (created on first run)
├── templates/
│   ├── base.html              # Base template
│   ├── login.html             # Login page
│   ├── loans.html             # Loans page
│   ├── payments.html          # Payments page
│   ├── person_history.html    # Person history page
│   └── monthly_report.html    # Monthly report page
└── static/
    ├── css/
    │   └── style.css          # Styles
    └── js/
        ├── main.js            # Common utilities
        ├── loans.js           # Loans page logic
        ├── payments.js        # Payments page logic
        ├── person_history.js  # Person history logic
        └── monthly_report.js  # Monthly report logic
```

## Troubleshooting

### Application won't start
- Ensure Python 3.8+ is installed: `python --version`
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check if port 5000 is available

### Database errors
- Delete `database/lending.db` and restart (creates fresh database)
- Restore from backup if available

### Can't login
- Default PIN is `1234`
- If you changed it and forgot, you can reset by deleting the database

### Interest calculation seems wrong
- Remember: Interest is calculated on the **opening principal** for each month
- Check that payments are attributed to the correct interest month
- Principal payments only affect future months, not the current month's interest

## Support

For issues or questions:
1. Check this README
2. Review the database schema
3. Check the browser console for JavaScript errors
4. Review Flask logs in the terminal

## License

This is a personal/private application. Modify as needed for your use case.

## Version

Version 1.0.0 - Initial Release
