# Lending & Chit Tracker

A local-only web application for tracking personal loans, interest payments, chit funds, and payment history with advanced adjustment features. Built with Flask and SQLite for complete privacy and local data storage.

## Features

### 1. Loans Management
- Track all loans with borrower details, principal amounts, interest rates
- Support for monthly interest-only loans
- Document tracking (type, path, received date)
- Loan status management (Active/Closed)
- Search and filter capabilities
- Detailed loan view with payment history

### 2. Chit Management (Individual Chits)
- Track individual chit memberships with monthly schedules
- Support for variable monthly amounts
- Prized month and prize amount tracking
- Monthly payment status (Pending, Partial, Paid, Adjusted)
- Pending dues tracking with overdue indicators
- Edit chit details while protecting past/paid months
- Export chit data to CSV
- Summary dashboard showing active chits and pending dues

### 3. Chit Adjustment Against Loan Interest
- **Smart Adjustment System**: Use loan interest to pay chit dues
- **Dual Payment Tracking**:
  - Amount adjusted from interest (auto-calculated)
  - Out-of-pocket payment (manual entry)
- **Intelligent Calculation**:
  - Automatically calculates available interest for selected month
  - Shows breakdown: Interest Due, Already Paid, Available
  - Validates adjustment against remaining chit due
  - Handles partial adjustments when interest < chit amount
- **Complete Audit Trail**:
  - Creates payment entry for interest adjustment
  - Records out-of-pocket payments separately
  - Links adjustments to specific loan interest months
  - Detailed notes for each transaction

### 4. Payments
- Record interest and principal payments
- Automatic interest calculation for selected month
- Payment attribution to specific interest months
- Multiple payment modes (Cash, Bank Transfer, UPI, Cheque, Adjustment)
- Payment validation (Interest + Principal = Total)
- Success confirmations with detailed popups

### 5. Person History
- Complete payment ledger by borrower
- Month-wise transaction history
- Loan-wise summary and totals
- Includes both loan payments and chit adjustments

### 6. Monthly Reports
- **Categorized View**:
  - Full paid (with principal received)
  - Partial paid
  - No payment
- **Advanced Pending Interest Tracking**:
  - Pending Interest (This Month) - Only from partial/unpaid loans
  - Total Pending Interest - Cumulative from loan start date
- **Smart Loan Filtering**:
  - Considers loan start date (excludes future loans)
  - Active loans tracking by default
  - Option to include closed loans
- **Comprehensive Totals**:
  - Total interest and principal received
  - Monthly and cumulative pending amounts
  - Complete financial overview

### 7. Out-of-Pocket Payments
- **Dedicated Tracking**: Separate tab for cash chit payments
- **Clear Distinction**: Shows only out-of-pocket amounts (excluding interest adjustments)
- **Complete Details**:
  - Borrower and chit information
  - Payment dates and modes
  - Payment status
  - Transaction notes

### 8. Data Management
- CSV export for loans, payments, and chits
- Database backup and restore
- PIN-based authentication
- Fully local - no cloud dependencies
- Privacy toggle for amounts (hide/show)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Navigate to the project directory:**
   ```bash
   cd lending-chit-tracker
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

### Adding a Chit

1. Go to the **Chits** page
2. Click **+ Add Chit**
3. Fill in the required fields:
   - Borrower name (required, auto-complete from existing borrowers)
   - Chit name (required)
   - Total months (required)
   - Start date (required)
   - Monthly amounts (can vary each month)
   - Prized month (optional)
   - Prize amount (optional)
4. **Quick Fill Options**:
   - Fill all months with same amount
   - Fill from prized month onwards
5. Click **Add Chit**

### Adjusting Chit Payment Against Loan Interest

This powerful feature allows you to use loan interest to pay chit dues:

1. Go to **Chits** page → **Pending Chit Dues**
2. Find the chit installment you want to pay
3. Click **Adjust** button
4. **Select Loan and Interest Month**:
   - Choose the borrower's active loan
   - Select interest month (defaults to chit due month)
5. **Review Auto-Calculated Split**:
   - Amount from Interest: Auto-calculated based on available interest
   - Out of Pocket: Enter any additional amount you're paying
   - Total Payment: Shows combined amount
6. **View Detailed Breakdown**:
   - Interest Due for selected month
   - Already Paid
   - Available Interest
   - Remaining Chit Due
   - Amount to adjust from interest
   - Additional payment needed (if any)
7. Add notes and click **Submit Adjustment**

**Important Notes:**
- System validates you have enough available interest
- If available interest < chit due, shows partial payment warning
- Creates audit entries in both payments and chit schedule
- Prevents over-payment beyond remaining due amount
- Success popup shows complete breakdown before refresh

### Paying Chit Directly (Out-of-Pocket)

1. Go to **Chits** page → **Pending Chit Dues**
2. Find the chit installment
3. Click **Pay** button
4. **System automatically shows**:
   - Remaining amount to pay (if partial payment exists)
   - Already paid amount
   - Due amount
5. Enter payment details:
   - Paid amount (defaults to remaining, max = remaining)
   - Payment date
   - Payment mode
   - Notes (optional)
6. Click **Record Payment**

**Validation:**
- Cannot pay more than remaining amount
- Cannot pay zero or negative amounts
- Shows clear error messages if validation fails
- Success popup confirms payment before refresh

### Editing a Chit

1. Go to **Chits** page → **All Chits**
2. Click **View** on the chit you want to edit
3. Click **Edit Chit** button
4. **Edit Protection**:
   - Past months (before current month): Read-only
   - Paid/Adjusted months: Read-only (shown in green)
   - Future/Pending months: Editable
5. Modify editable fields:
   - Borrower name
   - Chit name
   - Start date
   - Future month amounts
   - Prized month, prize amount
   - Notes
6. Click **Update Chit**

### Recording a Loan Payment

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

### Viewing Person History

1. Go to **Person History** page
2. Select a borrower from the dropdown
3. View:
   - All loans for that borrower
   - Complete payment ledger (including chit adjustments)
   - Totals for each loan

### Generating Monthly Reports

1. Go to **Monthly Report** page
2. Select the month (YYYY-MM format)
3. Optionally check "Include Closed Loans"
4. View categorized report:
   - **Full Interest Paid** (shows principal paid and total received)
   - **Partial Interest Paid** (contributes to monthly pending)
   - **No Interest Paid** (contributes to monthly pending)
   - **Summary Banner**:
     - Total Interest Received
     - Total Principal Received
     - Total Received
     - Pending Interest (This Month) - Only from partial/unpaid
     - Total Pending Interest - Cumulative from loan start

### Viewing Out-of-Pocket Chit Payments

1. Go to **Out of Pocket** page
2. View all chit payments made from your pocket
3. **Displays**:
   - Borrower and chit details
   - Month and due date
   - Due amount vs out-of-pocket amount
   - Payment date and mode
   - Status and notes
4. **Note**: This excludes amounts adjusted from interest (those appear in Monthly Report and Payment History)

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

### Closing a Chit

1. Go to the **Chits** page
2. Find the chit you want to close
3. Click **Close** button
4. Confirm closure

**Note:** Closed chits are excluded from pending dues and can be filtered out from the main view.

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
- `payment_mode`: Mode of payment (Cash, Bank Transfer, UPI, Cheque, Adjustment)
- `reference`: Reference number
- `notes`: Additional notes

### Chits Table
- `id`: Primary key
- `borrower_id`: Foreign key to borrowers
- `borrower_name`: Borrower name (denormalized for easier queries)
- `chit_name`: Name of the chit
- `total_months`: Total number of months
- `start_date`: Chit start date
- `prized_month`: Month when prize was received (optional)
- `prize_amount`: Prize amount received (optional)
- `status`: Active or Closed
- `notes`: Additional notes
- `created_at`: Timestamp

### Chit Monthly Schedule Table
- `id`: Primary key
- `chit_id`: Foreign key to chits
- `month_number`: Month number (1, 2, 3...)
- `due_date`: Due date for this month
- `due_amount`: Amount due for this month
- `paid_amount`: Amount paid (cumulative for partial payments)
- `paid_date`: Date when payment was made
- `payment_mode`: Mode of payment
- `payment_status`: Pending, Partial, Paid, or Adjusted
- `notes`: Additional notes

### Chit Adjustments Table
- `id`: Primary key
- `chit_schedule_id`: Foreign key to chit_monthly_schedule
- `loan_id`: Foreign key to loans
- `interest_month`: Interest month being used (YYYY-MM)
- `adjusted_amount`: Amount adjusted from interest
- `adjustment_date`: Date of adjustment
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

### Chit Adjustment Logic

When adjusting a chit payment against loan interest:

1. **Calculate Available Interest**:
   ```
   Interest Due = Opening Principal × (Monthly Rate / 100)
   Available Interest = Interest Due - Already Paid for Month
   ```

2. **Determine Adjustment Amount**:
   ```
   Adjustable Amount = MIN(Available Interest, Remaining Chit Due)
   ```

3. **Create Dual Entries**:
   - **Chit Adjustment Record**: Links chit schedule to loan interest month
   - **Payment Entry**: Records as payment mode "Adjustment"
   - **Chit Schedule Update**: Updates paid_amount and status

4. **Handle Partial Adjustments**:
   - If Available Interest < Remaining Chit Due:
     - Adjusts maximum possible from interest
     - Marks chit as "Partial"
     - Shows remaining amount to be paid
   - If Available Interest ≥ Remaining Chit Due:
     - Fully pays the chit
     - Marks as "Adjusted"

5. **Out-of-Pocket Component**:
   - Can be added to adjustment to fully pay chit
   - Recorded as regular payment on chit schedule
   - Total = Interest Adjustment + Out-of-Pocket

### Pending Interest Calculation

**Pending Interest (This Month)**:
- Only includes loans with partial or no payment for selected month
- Calculated as: Interest Due - Interest Paid (for that month only)
- Excludes fully paid loans from total

**Total Pending Interest**:
- Cumulative from loan start date to selected month
- Includes all unpaid interest across all months
- Formula:
  ```
  Total Pending = Σ(Interest Due per Month) - Σ(Interest Paid per Month)
  From loan start date to report month
  ```

### Loan Start Date Filtering

- Monthly reports only include loans that started on or before the report month
- Loans starting after the report month are excluded entirely
- Prevents future loans from affecting historical reports

### Closed Loans

- Closed loans do not accrue interest after the closed date
- They are excluded from monthly reports by default
- No new payments can be added (unless loan is reopened)
- All historical data is preserved

### Closed Chits

- Closed chits don't appear in pending dues
- Can be filtered out from main chit list
- All payment history preserved
- Monthly schedule remains accessible

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

**Chits Export:**
- Go to Chits page
- Click "Export CSV"
- Downloads all chit data with schedule details

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

### Privacy Features

- **Amount Hiding**: Toggle visibility of chit amounts with 👁️/🔒 button
- **Local Storage**: Preference saved in browser localStorage
- **Local-Only Operation**: All data stored locally in SQLite database
- No external API calls or cloud dependencies
- Runs entirely on localhost
- Suitable for personal/family use

## File Structure

```
lending-chit-adjustment/
├── app.py                      # Flask application
├── chit_api_endpoints.py       # Chit API routes
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── database/
│   ├── schema.sql             # Database schema
│   ├── db_manager.py          # Database operations (loans + chits)
│   ├── chit_logic.py          # Chit business logic
│   └── lending.db             # SQLite database (created on first run)
├── templates/
│   ├── base.html              # Base template with navigation
│   ├── login.html             # Login page
│   ├── loans.html             # Loans page
│   ├── payments.html          # Payments page
│   ├── chits.html             # Chits page with adjustment modals
│   ├── out_of_pocket.html     # Out-of-pocket payments page
│   ├── person_history.html    # Person history page
│   └── monthly_report.html    # Monthly report page
└── static/
    ├── css/
    │   └── style.css          # Styles
    └── js/
        ├── main.js            # Common utilities
        ├── loans.js           # Loans page logic
        ├── payments.js        # Payments page logic
        ├── chits.js           # Chits page logic with adjustment
        ├── out_of_pocket.js   # Out-of-pocket payments logic
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

### Chit adjustment not working
- Ensure the borrower has an active loan
- Check that there's available interest for the selected month
- Verify the interest month hasn't been fully paid already
- Review the detailed breakdown shown in the adjustment modal

### Pending Interest (This Month) seems incorrect
- This only includes partial and unpaid loans for the selected month
- Fully paid loans are excluded from this total
- Loans that haven't started yet are excluded
- Check individual loan details in the table below

### Can't pay more than remaining amount on partial chit
- This is intentional - prevents overpayment
- System shows remaining amount and already paid amount
- Maximum payment allowed = Remaining amount only
- If you need to modify, edit the chit schedule directly

## Database Access from Terminal

You can directly access and query the SQLite database from the terminal using the `sqlite3` command.

### Opening the Database

**Interactive mode:**
```bash
sqlite3 /Users/asveeranan/git/lending-chit-tracker/database/lending.db
```

**Run a single query:**
```bash
sqlite3 /Users/asveeranan/git/lending-chit-tracker/database/lending.db "SELECT * FROM borrowers;"
```

### Useful SQLite Commands

Once inside the sqlite3 prompt, you can use these commands:

```sql
.tables                    -- List all tables
.schema payments           -- Show table structure
.headers on                -- Show column headers in results
.mode column               -- Display results in column format
.exit                      -- Exit sqlite3
```

### Common Queries

#### View All Borrowers
```sql
SELECT * FROM borrowers;
```

#### View All Loans for a Borrower
```sql
SELECT * FROM loans WHERE borrower_id = (SELECT id FROM borrowers WHERE name = 'BorrowerName');
```

#### View Recent Payments for a Borrower
```sql
SELECT p.id, p.payment_date, p.total_received, p.interest_paid, p.principal_paid, b.name
FROM payments p
JOIN loans l ON p.loan_id = l.id
JOIN borrowers b ON l.borrower_id = b.id
WHERE b.name = 'BorrowerName'
ORDER BY p.payment_date DESC
LIMIT 10;
```

#### View Recent Chit Payments
```sql
SELECT cms.id, c.chit_name, b.name, cms.due_date, cms.due_amount, cms.paid_amount, cms.payment_status
FROM chit_monthly_schedule cms
JOIN chits c ON cms.chit_id = c.id
JOIN borrowers b ON c.borrower_id = b.id
WHERE cms.payment_status != 'Pending'
ORDER BY cms.paid_date DESC
LIMIT 10;
```

#### View Chit Adjustments
```sql
SELECT ca.id, ca.adjustment_date, c.chit_name, b.name, ca.interest_month, ca.adjusted_amount, ca.notes
FROM chit_adjustments ca
JOIN chit_monthly_schedule cms ON ca.chit_schedule_id = cms.id
JOIN chits c ON cms.chit_id = c.id
JOIN borrowers b ON c.borrower_id = b.id
ORDER BY ca.adjustment_date DESC
LIMIT 10;
```

#### View Direct Chit Payments (Out-of-Pocket)
```sql
SELECT dcp.id, dcp.payment_date, c.chit_name, b.name, cms.due_date, dcp.paid_amount, dcp.payment_mode
FROM direct_chit_payments dcp
JOIN chit_monthly_schedule cms ON dcp.chit_schedule_id = cms.id
JOIN chits c ON cms.chit_id = c.id
JOIN borrowers b ON c.borrower_id = b.id
ORDER BY dcp.payment_date DESC
LIMIT 10;
```

### Deleting Records

**IMPORTANT**: Always backup your database before deleting records. Deletions are permanent and cannot be undone.

#### Delete a Loan Repayment Entry

First, find the payment ID you want to delete:
```sql
SELECT p.id, p.payment_date, p.total_received, p.interest_paid, p.principal_paid, b.name
FROM payments p
JOIN loans l ON p.loan_id = l.id
JOIN borrowers b ON l.borrower_id = b.id
WHERE b.name = 'BorrowerName'
ORDER BY p.payment_date DESC;
```

Then delete by ID:
```sql
DELETE FROM payments WHERE id = [payment_id];
```

Example:
```sql
DELETE FROM payments WHERE id = 31;
```

#### Delete a Chit Adjustment Entry

First, find the adjustment ID:
```sql
SELECT ca.id, ca.adjustment_date, c.chit_name, b.name, ca.interest_month, ca.adjusted_amount
FROM chit_adjustments ca
JOIN chit_monthly_schedule cms ON ca.chit_schedule_id = cms.id
JOIN chits c ON cms.chit_id = c.id
JOIN borrowers b ON c.borrower_id = b.id
WHERE b.name = 'BorrowerName'
ORDER BY ca.adjustment_date DESC;
```

Then delete by ID:
```sql
DELETE FROM chit_adjustments WHERE id = [adjustment_id];
```

**Note**: Deleting a chit adjustment does NOT automatically remove the corresponding payment entry or update the chit schedule. You may need to:
1. Delete the related payment entry (if it was created as "Adjustment" mode)
2. Update the chit_monthly_schedule to reduce paid_amount and adjust payment_status

#### Delete an Out-of-Pocket Chit Payment

First, find the payment ID:
```sql
SELECT dcp.id, dcp.payment_date, c.chit_name, b.name, dcp.paid_amount, dcp.payment_mode
FROM direct_chit_payments dcp
JOIN chit_monthly_schedule cms ON dcp.chit_schedule_id = cms.id
JOIN chits c ON cms.chit_id = c.id
JOIN borrowers b ON c.borrower_id = b.id
WHERE b.name = 'BorrowerName'
ORDER BY dcp.payment_date DESC;
```

Then delete by ID:
```sql
DELETE FROM direct_chit_payments WHERE id = [payment_id];
```

**Note**: Deleting from direct_chit_payments does NOT automatically update the chit_monthly_schedule. You may need to manually update the paid_amount and payment_status in the chit_monthly_schedule table.

#### Delete Multiple Records (Use with Caution)

Delete all payments for a specific date:
```sql
DELETE FROM payments WHERE payment_date = '2026-01-18';
```

Delete all adjustments for a specific month:
```sql
DELETE FROM chit_adjustments WHERE interest_month = '2026-01';
```

### Database Backup Before Deletion

Always create a backup before deleting records:

```bash
# Create a backup with timestamp
cp /Users/asveeranan/git/lending-chit-tracker/database/lending.db \
   /Users/asveeranan/git/lending-chit-tracker/database/lending_backup_$(date +%Y%m%d_%H%M%S).db
```

## Support

For issues or questions:
1. Check this README
2. Review the database schema
3. Check the browser console for JavaScript errors
4. Review Flask logs in the terminal
5. Check SQL_REFERENCE.md for direct database queries
6. Use terminal database access for direct queries and corrections

## License

This is a personal/private application. Modify as needed for your use case.

## Version

Version 2.0.0 - Chit Management with Interest Adjustment

**Major Features:**
- Individual chit tracking with monthly schedules
- Chit adjustment against loan interest
- Dual payment tracking (interest adjustment vs out-of-pocket)
- Enhanced monthly reports with granular pending interest
- Loan start date filtering
- Privacy toggles and improved UX
