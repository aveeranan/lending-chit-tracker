# Changelog

All notable changes to the Lending Tracker application.

## [1.3.0] - 2024-12-22

### Added
- **Enhanced Person History Page**: Major improvements to payment history viewing:
  - "All Borrowers" is now the default selection
  - Automatically shows last 3 months of payments on page load
  - Payments are segmented by month with clear monthly headers
  - Each month section shows all payments with borrower names
  - Monthly totals displayed for each month segment
  - Payments sorted by month (newest first) then by borrower
  - Can still select individual borrowers for complete history

### Changed
- Person History dropdown now starts with "All Borrowers" option
- Default view changed from empty state to showing recent activity
- Improved user experience with immediate visibility of recent payments
- Better organization of payment data by month

### Technical Details
- New API endpoint: `GET /api/recent-payments?months=N`
- New database function: `get_recent_payments_all(months=3)`
- Completely rewritten `person_history.js` with new display functions
- Added `loadRecentPayments()` and `displayRecentPayments()` functions
- Maintains backward compatibility with individual borrower history view

---

## [1.2.0] - 2024-12-22

### Added
- **Loans Summary Banner**: New summary banner at the top of the Loans page showing:
  - Total number of active loans
  - Total principal given (all active loans)
  - Total outstanding principal
  - Total pending interest across all loans
  - Auto-updates when loans are added, edited, or closed

- **Monthly Report Pending Interest**: Enhanced monthly report to show:
  - Pending interest column for each loan in the report
  - Total pending interest in the summary banner
  - Color-coded pending amounts (red for pending, green for zero)
  - Better visibility of outstanding payments

### Changed
- Monthly report now shows 4 totals instead of 3
- Loan statistics are now more prominent and visible
- Summary banner uses gradient styling matching the app theme

### Technical Details
- New API endpoint: `GET /api/loans/summary`
- New database function: `get_loans_summary()`
- Enhanced `get_monthly_report()` to calculate pending interest
- Updated CSS with `.loans-summary-banner` and `.summary-item` styles
- Modified `monthly_report.js` to display pending interest
- Auto-refresh summary on loan operations

---

## [1.1.0] - 2024-12-22

### Added
- **Loan Editing Feature**: Users can now edit existing loans
  - New "Edit" button in the Loans table
  - Edit modal with all loan fields pre-populated
  - Ability to update:
    - Borrower name and phone
    - Principal given and outstanding principal
    - Interest rate (with warning about calculation effects)
    - Given date
    - Interest due day
    - Document details
    - Notes
  - Real-time warnings for critical fields that affect calculations
  - API endpoint: `PUT /api/loans/<id>`
  - Database function: `update_loan()`

### Changed
- Updated loans table to include "Edit" button between "View" and "Add Payment"
- Modified `loans.js` to handle edit functionality
- Enhanced modal closing logic to include edit modal
- Updated README.md with "Editing a Loan" section

### Technical Details
- New API route: `/api/loans/<int:loan_id>` with PUT method
- New database function: `update_loan()` in `db_manager.py`
- New modal: `editLoanModal` in `loans.html`
- New JavaScript functions:
  - `editLoan(loanId)` - Loads and displays loan in edit form
  - `closeEditLoanModal()` - Closes the edit modal
  - `submitEditLoan(event)` - Submits edited loan data

### Important Notes
- Editing principal or interest rate affects all interest calculations
- Outstanding principal should be manually verified after edits
- Changes take effect immediately
- No audit trail for edits (consider adding in future versions)

---

## [1.0.0] - 2024-12-22

### Initial Release
- Complete lending tracker application
- Loan management (Add, View, Close)
- Payment recording with validation
- Person history tracking
- Monthly reports
- CSV export functionality
- Database backup/restore
- PIN authentication
- Local-only operation with SQLite
- Comprehensive documentation

### Features
- Monthly interest-only loan support
- Interest calculation based on opening principal
- Payment attribution to specific months
- Automatic principal reduction
- Pending interest calculation
- Closed loan handling

### Documentation
- README.md - Complete user guide
- QUICKSTART.md - Quick start guide
- SQL_REFERENCE.md - SQL query reference
- PROJECT_SUMMARY.md - Technical overview
- START_HERE.txt - Getting started
- INSTALLATION_CHECKLIST.md - Verification guide
