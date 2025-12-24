# Installation & Verification Checklist

Use this checklist to verify your Lending Tracker installation.

## Pre-Installation

- [ ] Python 3.8+ installed (`python --version` or `python3 --version`)
- [ ] pip installed (`pip --version`)
- [ ] Modern web browser available

## Installation

- [ ] Navigate to `lending-tracker` directory
- [ ] Run installation:
  - [ ] Mac/Linux: `./start.sh`
  - [ ] Windows: `start.bat`
  - [ ] OR Manual: `pip install -r requirements.txt && python app.py`

## Verification

### 1. Application Starts
- [ ] No Python errors in terminal
- [ ] See message: "Running on http://0.0.0.0:5000"
- [ ] Database initialized message appears

### 2. Web Interface
- [ ] Can access http://localhost:5000
- [ ] Login page displays correctly
- [ ] Can login with PIN: 1234
- [ ] Redirected to Loans page after login

### 3. Navigation
- [ ] Can click "Loans" tab
- [ ] Can click "Payments" tab
- [ ] Can click "Person History" tab
- [ ] Can click "Monthly Report" tab
- [ ] Can click "Logout"

### 4. Loans Functionality
- [ ] Can click "+ Add Loan" button
- [ ] Modal opens with form
- [ ] All form fields visible
- [ ] Can submit form with test data:
  - Name: Test Borrower
  - Principal: 10000
  - Rate: 2
  - Date: Today
- [ ] Loan appears in table
- [ ] Can click "View" button
- [ ] Loan details modal opens
- [ ] Can click "Close" button
- [ ] Close loan modal opens

### 5. Payments Functionality
- [ ] Can access Payments page
- [ ] Loan dropdown populated with active loans
- [ ] Can select a loan
- [ ] Interest due displays when month selected
- [ ] Can enter payment details
- [ ] Validation works (Interest + Principal = Total)
- [ ] Can submit payment
- [ ] Success message appears

### 6. Person History
- [ ] Can access Person History page
- [ ] Borrower dropdown populated
- [ ] Can select borrower
- [ ] History displays correctly
- [ ] Payment ledger shows all payments

### 7. Monthly Report
- [ ] Can access Monthly Report page
- [ ] Current month pre-selected
- [ ] Report generates without errors
- [ ] Shows categorized loans:
  - Full Interest Paid
  - Partial Interest Paid
  - No Interest Paid
- [ ] Totals displayed correctly

### 8. Data Export
- [ ] "Export CSV" button on Loans page
- [ ] Clicking downloads loans.csv
- [ ] "Export CSV" button on Payments page
- [ ] Clicking downloads payments.csv
- [ ] CSV files open correctly in Excel/Sheets

### 9. Database
- [ ] File exists: `database/lending.db`
- [ ] Can connect: `sqlite3 database/lending.db`
- [ ] Tables exist:
  ```sql
  .tables
  ```
  Should show: borrowers, loans, payments, users

### 10. Security
- [ ] Cannot access pages without login
- [ ] Login required for all routes
- [ ] Logout works correctly
- [ ] Session persists during use

## File Structure Verification

```bash
cd lending-tracker
ls -la
```

Should see:
- [ ] app.py
- [ ] requirements.txt
- [ ] README.md
- [ ] QUICKSTART.md
- [ ] START_HERE.txt
- [ ] start.sh / start.bat
- [ ] database/ directory
- [ ] templates/ directory
- [ ] static/ directory

## Test Data Verification

Create a complete test workflow:

1. **Add Test Loan**
   - [ ] Borrower: John Doe
   - [ ] Principal: 100,000
   - [ ] Rate: 2%
   - [ ] Date: Today

2. **Add Test Payment**
   - [ ] Loan: John Doe
   - [ ] Total: 2,000
   - [ ] Interest: 2,000
   - [ ] Principal: 0
   - [ ] Date: Today
   - [ ] Month: Current month

3. **Verify in Reports**
   - [ ] Person History shows payment
   - [ ] Monthly Report shows in "Full Paid"
   - [ ] Loan view shows payment history

4. **Clean Up Test Data** (Optional)
   - [ ] Can delete database/lending.db
   - [ ] Restart app creates fresh database

## Common Issues & Solutions

### "Python not found"
```bash
# Try python3 instead
python3 --version
python3 app.py
```

### "Module not found"
```bash
# Install dependencies
pip install -r requirements.txt
# OR
pip3 install -r requirements.txt
```

### "Address already in use"
```bash
# Kill process on port 5000
# Mac/Linux:
lsof -ti:5000 | xargs kill
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### "Cannot connect to database"
```bash
# Check file exists
ls -la database/lending.db
# If not, run app once to create
python app.py
```

### "Login not working"
```bash
# Verify default PIN is 1234
# Check browser console (F12) for errors
# Check terminal for Flask errors
```

## Performance Verification

- [ ] Loans page loads in < 1 second
- [ ] Payment form responds immediately
- [ ] Reports generate in < 2 seconds
- [ ] No JavaScript errors in console (F12)
- [ ] No Python errors in terminal

## Browser Compatibility

Test in at least one browser:
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Edge

## Final Checks

- [ ] All navigation links work
- [ ] All modals open and close
- [ ] All forms validate input
- [ ] All buttons perform actions
- [ ] All data persists after refresh
- [ ] Logout and login again works

## Documentation Review

- [ ] Read START_HERE.txt
- [ ] Skim QUICKSTART.md
- [ ] Check README.md for detailed info
- [ ] Bookmark SQL_REFERENCE.md for later

## Production Readiness

Before using for real data:
- [ ] Change default PIN from 1234
- [ ] Test backup and restore
- [ ] Plan regular backup schedule
- [ ] Understand interest calculation logic
- [ ] Review business rules in README

## Completion

If all checks pass:
- ✅ Installation successful!
- ✅ Application fully functional
- ✅ Ready for production use

If any checks fail:
1. Review error messages
2. Check QUICKSTART.md troubleshooting
3. Verify Python and dependencies
4. Check file permissions

---

**Installation Date**: _______________
**Verified By**: _______________
**Status**: [ ] Pass [ ] Fail
**Notes**: _______________________________________________
