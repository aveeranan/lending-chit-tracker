# Quick Start Guide

## 5-Minute Setup

### Option 1: Using the Start Script (Recommended)

**Mac/Linux:**
```bash
cd lending-tracker
./start.sh
```

**Windows:**
```cmd
cd lending-tracker
start.bat
```

### Option 2: Manual Setup

1. **Install dependencies:**
   ```bash
   cd lending-tracker
   pip install -r requirements.txt
   ```

2. **Start the application:**
   ```bash
   python app.py
   ```

3. **Open browser:**
   - Navigate to: http://localhost:5000
   - Login with PIN: `1234`

## First Steps After Login

### 1. Add Your First Loan (2 minutes)

1. Click **Loans** in the navigation
2. Click **+ Add Loan** button
3. Fill in:
   - Borrower Name: "John Doe"
   - Principal Given: 100000
   - Given Date: (today's date)
   - Monthly Rate: 2 (for 2% per month)
4. Click **Add Loan**

### 2. Record a Payment (1 minute)

1. Click **Payments** in the navigation
2. Select the loan you just created
3. The system shows the interest due
4. Enter:
   - Total Amount Received: 2000
   - Interest Paid: 2000 (full interest)
   - Principal Paid: 0
5. Click **Add Payment**

### 3. View Reports (1 minute)

**Person History:**
- Click **Person History**
- Select "John Doe"
- View complete payment ledger

**Monthly Report:**
- Click **Monthly Report**
- Current month is pre-selected
- See who paid and who didn't

## Common Workflows

### Adding a Loan with Document

```
Loans → + Add Loan
├── Fill borrower details
├── Check "Document Received"
├── Enter document type (e.g., "Promissory Note")
├── Enter local file path (e.g., "/Users/me/documents/john_doe_loan.pdf")
└── Add Loan
```

### Recording Partial Payment

```
Payments → Select Loan
├── Total Received: 1500
├── Interest Paid: 1500 (partial)
├── Principal Paid: 0
└── Add Payment
```

### Recording Full Payment (Interest + Principal)

```
Payments → Select Loan
├── Total Received: 5000
├── Interest Paid: 2000 (full interest)
├── Principal Paid: 3000
└── Add Payment
```

### Closing a Loan

```
Loans → Find Loan → Close
├── Review outstanding amounts
├── Select reason: "Fully Repaid"
└── Confirm
```

## Key Concepts

### Interest Calculation
- Interest = Opening Principal × (Rate/100)
- Calculated monthly based on opening balance
- Example: ₹100,000 @ 2% = ₹2,000/month

### Payment Attribution
- Each payment goes to a specific month
- Interest is paid first, then principal
- Principal payments reduce future interest

### Loan Status
- **Active**: Accrues interest, appears in reports
- **Closed**: No interest, hidden from reports (unless toggled)

## Tips

1. **Export Data Regularly**
   - Loans page → Export CSV
   - Payments page → Export CSV
   - Keep backups of database file

2. **Track Documents**
   - Use local file paths for loan documents
   - Keep documents organized by borrower

3. **Monthly Reports**
   - Review at start of each month
   - Follow up with borrowers who haven't paid

4. **Change PIN**
   ```python
   python -c "from database.db_manager import update_pin; update_pin('YOUR_PIN')"
   ```

## Troubleshooting

**Can't start the app?**
- Ensure Python 3.8+ installed: `python --version`
- Install dependencies: `pip install -r requirements.txt`

**Login not working?**
- Default PIN is `1234`
- Check browser console (F12) for errors

**Interest calculation wrong?**
- Remember: Interest uses OPENING principal
- Check payment attribution to correct month

**Need to reset everything?**
- Delete `database/lending.db`
- Restart app (fresh database created)

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Add all your existing loans
3. Record historical payments if needed
4. Set up a backup schedule
5. Customize PIN for security

## Support

Check the [README.md](README.md) for:
- Detailed feature documentation
- Database schema
- Business logic explanations
- Advanced usage scenarios
