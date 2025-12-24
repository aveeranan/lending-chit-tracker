# SQL Reference Guide

This guide provides useful SQL queries for advanced users who want to directly query the database for custom reports or analysis.

## Connecting to Database

```bash
# From the lending-tracker directory
sqlite3 database/lending.db
```

## Useful Queries

### 1. All Active Loans with Borrower Details

```sql
SELECT
    b.name as borrower,
    b.phone,
    l.principal_given,
    l.outstanding_principal,
    l.monthly_rate,
    l.given_date,
    l.interest_due_day
FROM loans l
JOIN borrowers b ON l.borrower_id = b.id
WHERE l.status = 'Active'
ORDER BY b.name;
```

### 2. Total Outstanding Principal

```sql
SELECT
    SUM(outstanding_principal) as total_outstanding,
    COUNT(*) as active_loans
FROM loans
WHERE status = 'Active';
```

### 3. Payment History for a Borrower

```sql
SELECT
    b.name as borrower,
    p.payment_date,
    p.interest_month,
    p.total_received,
    p.interest_paid,
    p.principal_paid,
    p.payment_mode
FROM payments p
JOIN loans l ON p.loan_id = l.id
JOIN borrowers b ON l.borrower_id = b.id
WHERE b.name = 'John Doe'
ORDER BY p.payment_date DESC;
```

### 4. Monthly Interest Collection Summary

```sql
SELECT
    p.interest_month,
    COUNT(DISTINCT p.loan_id) as loans_paid,
    SUM(p.interest_paid) as total_interest,
    SUM(p.principal_paid) as total_principal,
    SUM(p.total_received) as total_collected
FROM payments p
GROUP BY p.interest_month
ORDER BY p.interest_month DESC;
```

### 5. Borrowers Who Haven't Paid This Month

```sql
-- Replace '2024-01' with current month
SELECT
    b.name as borrower,
    l.outstanding_principal,
    l.monthly_rate,
    (l.outstanding_principal * l.monthly_rate / 100) as interest_due
FROM loans l
JOIN borrowers b ON l.borrower_id = b.id
WHERE l.status = 'Active'
  AND l.id NOT IN (
      SELECT loan_id
      FROM payments
      WHERE interest_month = '2024-01'
  );
```

### 6. Top Borrowers by Outstanding Amount

```sql
SELECT
    b.name as borrower,
    SUM(l.outstanding_principal) as total_outstanding,
    COUNT(l.id) as number_of_loans
FROM loans l
JOIN borrowers b ON l.borrower_id = b.id
WHERE l.status = 'Active'
GROUP BY b.name
ORDER BY total_outstanding DESC
LIMIT 10;
```

### 7. Payment Compliance Rate

```sql
-- Percentage of on-time payments (interest month matches payment month)
SELECT
    COUNT(CASE
        WHEN strftime('%Y-%m', payment_date) = interest_month
        THEN 1
    END) * 100.0 / COUNT(*) as on_time_percentage
FROM payments;
```

### 8. Total Interest Earned Per Borrower

```sql
SELECT
    b.name as borrower,
    SUM(p.interest_paid) as total_interest_earned,
    COUNT(DISTINCT p.interest_month) as months_paid
FROM payments p
JOIN loans l ON p.loan_id = l.id
JOIN borrowers b ON l.borrower_id = b.id
GROUP BY b.name
ORDER BY total_interest_earned DESC;
```

### 9. Loan Performance Analysis

```sql
SELECT
    l.id as loan_id,
    b.name as borrower,
    l.principal_given,
    l.outstanding_principal,
    l.principal_given - l.outstanding_principal as principal_recovered,
    COALESCE(SUM(p.interest_paid), 0) as total_interest_received,
    CASE
        WHEN l.status = 'Closed' THEN 'Closed'
        WHEN l.outstanding_principal = l.principal_given THEN 'No Payments'
        ELSE 'Active'
    END as loan_status
FROM loans l
JOIN borrowers b ON l.borrower_id = b.id
LEFT JOIN payments p ON l.id = p.loan_id
GROUP BY l.id, b.name, l.principal_given, l.outstanding_principal, l.status
ORDER BY b.name;
```

### 10. Monthly Expected vs Actual Interest

```sql
-- For a specific month
WITH expected AS (
    SELECT
        l.id as loan_id,
        b.name as borrower,
        l.outstanding_principal * l.monthly_rate / 100 as expected_interest
    FROM loans l
    JOIN borrowers b ON l.borrower_id = b.id
    WHERE l.status = 'Active'
),
actual AS (
    SELECT
        loan_id,
        SUM(interest_paid) as actual_interest
    FROM payments
    WHERE interest_month = '2024-01'  -- Change this
    GROUP BY loan_id
)
SELECT
    e.borrower,
    ROUND(e.expected_interest, 2) as expected,
    ROUND(COALESCE(a.actual_interest, 0), 2) as actual,
    ROUND(e.expected_interest - COALESCE(a.actual_interest, 0), 2) as shortfall
FROM expected e
LEFT JOIN actual a ON e.loan_id = a.loan_id
ORDER BY shortfall DESC;
```

### 11. Closed Loans Analysis

```sql
SELECT
    b.name as borrower,
    l.principal_given,
    l.outstanding_principal,
    l.given_date,
    l.closed_date,
    l.close_reason,
    julianday(l.closed_date) - julianday(l.given_date) as days_active,
    COALESCE(SUM(p.interest_paid), 0) as total_interest_earned
FROM loans l
JOIN borrowers b ON l.borrower_id = b.id
LEFT JOIN payments p ON l.id = p.loan_id
WHERE l.status = 'Closed'
GROUP BY l.id
ORDER BY l.closed_date DESC;
```

### 12. Payment Methods Analysis

```sql
SELECT
    payment_mode,
    COUNT(*) as transaction_count,
    SUM(total_received) as total_amount,
    AVG(total_received) as avg_amount
FROM payments
WHERE payment_mode IS NOT NULL AND payment_mode != ''
GROUP BY payment_mode
ORDER BY total_amount DESC;
```

## Custom Reports

### Generate CSV from SQL Query

```bash
sqlite3 -header -csv database/lending.db "YOUR_QUERY_HERE" > output.csv
```

Example:
```bash
sqlite3 -header -csv database/lending.db \
  "SELECT * FROM payments WHERE interest_month = '2024-01'" \
  > jan_2024_payments.csv
```

### Backup Specific Tables

```bash
# Backup loans table
sqlite3 database/lending.db ".dump loans" > loans_backup.sql

# Backup payments table
sqlite3 database/lending.db ".dump payments" > payments_backup.sql
```

## Database Maintenance

### Check Database Integrity

```sql
PRAGMA integrity_check;
```

### Optimize Database

```sql
VACUUM;
```

### View Table Structure

```sql
.schema loans
.schema payments
.schema borrowers
```

### Database Statistics

```sql
SELECT
    'Total Borrowers' as metric,
    COUNT(*) as value
FROM borrowers
UNION ALL
SELECT
    'Total Loans',
    COUNT(*)
FROM loans
UNION ALL
SELECT
    'Active Loans',
    COUNT(*)
FROM loans
WHERE status = 'Active'
UNION ALL
SELECT
    'Total Payments',
    COUNT(*)
FROM payments
UNION ALL
SELECT
    'Total Principal Given',
    SUM(principal_given)
FROM loans
UNION ALL
SELECT
    'Total Outstanding',
    SUM(outstanding_principal)
FROM loans
WHERE status = 'Active'
UNION ALL
SELECT
    'Total Interest Collected',
    SUM(interest_paid)
FROM payments;
```

## Tips

1. **Always backup before running UPDATE or DELETE queries**
   ```bash
   cp database/lending.db database/lending.db.backup
   ```

2. **Use transactions for multiple updates**
   ```sql
   BEGIN TRANSACTION;
   -- Your queries here
   COMMIT;
   -- Or ROLLBACK if something goes wrong
   ```

3. **Export results to file**
   ```sql
   .output results.txt
   -- Your query
   .output stdout
   ```

4. **Pretty print results**
   ```sql
   .mode column
   .headers on
   -- Your query
   ```

## Warning

Direct database manipulation bypasses application logic. Use with caution:
- Interest calculations are done by the application
- Deleting records may break referential integrity
- Always backup before modifying data
- Consider using the web interface for routine operations
