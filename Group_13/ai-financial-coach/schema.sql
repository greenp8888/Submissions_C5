-- =============================================================================
-- Wealth Management Application - Database Schema (PostgreSQL)
-- =============================================================================

-- 1. Users Table
-- Rationale: Central table for all user accounts. 
-- Email is unique to prevent duplicate registrations.
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- 2. Expense Categories
-- Rationale: Lookup table for categorizing expenses (e.g., Food, Rent, Travel).
CREATE TABLE ExpenseCategories (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL
);

-- 3. Salary History
-- Rationale: Tracks salary changes over time. 
-- ON DELETE CASCADE: If a user is deleted, their salary history is no longer relevant.
CREATE TABLE SalaryHistory (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    monthly_amount NUMERIC(15, 2) NOT NULL CHECK (monthly_amount >= 0),
    employer_name VARCHAR(255) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE, -- NULL means current salary
    CONSTRAINT valid_date_range CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

-- 4. Other Incomes
-- Rationale: Captures non-salary income (Dividends, Rent, Freelance).
CREATE TABLE OtherIncomes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    income_source VARCHAR(255) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL CHECK (amount >= 0),
    date_received DATE NOT NULL,
    is_taxable BOOLEAN DEFAULT TRUE
);

-- 5. Expenses
-- Rationale: Detailed transaction log.
-- ON DELETE RESTRICT for category: Prevent deleting a category if it has associated expenses.
CREATE TABLE Expenses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES ExpenseCategories(id) ON DELETE RESTRICT,
    amount NUMERIC(15, 2) NOT NULL CHECK (amount > 0),
    transaction_date DATE NOT NULL,
    description VARCHAR(500)
);

-- 6. Securities
-- Rationale: Master list of tradable assets (Stocks, Bonds, ETFs).
CREATE TABLE Securities (
    ticker VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    asset_class VARCHAR(50) NOT NULL -- e.g., Equity, Debt, Gold
);

-- 7. Trades
-- Rationale: Records buy/sell activities.
CREATE TABLE Trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    ticker VARCHAR(20) NOT NULL REFERENCES Securities(ticker) ON DELETE RESTRICT,
    trade_type VARCHAR(4) NOT NULL CHECK (trade_type IN ('BUY', 'SELL')),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price_per_unit NUMERIC(15, 4) NOT NULL CHECK (price_per_unit > 0),
    execution_date DATE NOT NULL,
    brokerage_fees NUMERIC(10, 2) DEFAULT 0 CHECK (brokerage_fees >= 0)
);

-- 8. Tax Lots
-- Rationale: Tracks specific purchase units for capital gains calculation (FIFO/LIFO).
CREATE TABLE TaxLots (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER NOT NULL REFERENCES Trades(id) ON DELETE CASCADE,
    remaining_quantity INTEGER NOT NULL CHECK (remaining_quantity >= 0),
    buy_price NUMERIC(15, 4) NOT NULL CHECK (buy_price > 0),
    purchase_date DATE NOT NULL
);

-- 9. Fixed Investments
-- Rationale: Traditional assets like FDs, PPF.
CREATE TABLE FixedInvestments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    investment_type VARCHAR(50) NOT NULL, -- FD, PPF, NSC
    principal_amount NUMERIC(15, 2) NOT NULL CHECK (principal_amount > 0),
    interest_rate NUMERIC(5, 2) NOT NULL CHECK (interest_rate >= 0),
    start_date DATE NOT NULL,
    maturity_date DATE,
    tax_exemption_category VARCHAR(50), -- e.g., 80C
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'MATURED', 'CLOSED'))
);

-- 10. Loans
-- Rationale: Tracks liabilities.
CREATE TABLE Loans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    loan_type VARCHAR(50) NOT NULL, -- Home, Car, Personal
    principal_amount NUMERIC(15, 2) NOT NULL CHECK (principal_amount > 0),
    interest_rate NUMERIC(5, 2) NOT NULL CHECK (interest_rate >= 0),
    start_date DATE NOT NULL,
    end_date DATE,
    monthly_emi NUMERIC(15, 2) CHECK (monthly_emi >= 0)
);

-- 11. Loan Payments
-- Rationale: Tracks repayment schedule and principal/interest split.
CREATE TABLE LoanPayments (
    id SERIAL PRIMARY KEY,
    loan_id INTEGER NOT NULL REFERENCES Loans(id) ON DELETE CASCADE,
    payment_date DATE NOT NULL,
    amount_paid NUMERIC(15, 2) NOT NULL CHECK (amount_paid > 0),
    principal_component NUMERIC(15, 2) CHECK (principal_component >= 0),
    interest_component NUMERIC(15, 2) CHECK (interest_component >= 0)
);

-- 12. Financial Years
-- Rationale: Standardizes tax periods.
CREATE TABLE FinancialYears (
    id SERIAL PRIMARY KEY,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    CONSTRAINT valid_fy_range CHECK (end_date > start_date)
);

-- 13. Monthly Financial Summaries
-- Rationale: Denormalized table for fast dashboard rendering.
CREATE TABLE MonthlyFinancialSummaries (
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    year_month VARCHAR(7) NOT NULL, -- YYYY-MM
    total_salary NUMERIC(15, 2) DEFAULT 0,
    total_other_income NUMERIC(15, 2) DEFAULT 0,
    total_expenses NUMERIC(15, 2) DEFAULT 0,
    net_savings NUMERIC(15, 2) DEFAULT 0,
    PRIMARY KEY (user_id, year_month)
);

-- 14. Tax Obligations
-- Rationale: Calculated tax liability per FY.
-- ON DELETE RESTRICT: Keep tax records even if FY is deleted (though FYs are rarely deleted).
CREATE TABLE TaxObligations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    financial_year_id INTEGER NOT NULL REFERENCES FinancialYears(id) ON DELETE RESTRICT,
    tax_category VARCHAR(50) NOT NULL, -- Income Tax, Capital Gains
    calculated_liability NUMERIC(15, 2) DEFAULT 0 CHECK (calculated_liability >= 0)
);

-- 15. Tax Payments
-- Rationale: Records actual payments made to tax authorities.
CREATE TABLE TaxPayments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    financial_year_id INTEGER NOT NULL REFERENCES FinancialYears(id) ON DELETE RESTRICT,
    amount_paid NUMERIC(15, 2) NOT NULL CHECK (amount_paid > 0),
    payment_date DATE NOT NULL,
    payment_type VARCHAR(50) -- Advance Tax, Self-Assessment
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Index for frequent user-based lookups
CREATE INDEX idx_expenses_user_date ON Expenses(user_id, transaction_date);
CREATE INDEX idx_trades_user_ticker ON Trades(user_id, ticker);
CREATE INDEX idx_other_income_user_date ON OtherIncomes(user_id, date_received);

-- Index for foreign keys to optimize joins
CREATE INDEX idx_expenses_category ON Expenses(category_id);
CREATE INDEX idx_loan_payments_loan ON LoanPayments(loan_id);
CREATE INDEX idx_tax_lots_trade ON TaxLots(trade_id);

-- Index for tax reporting
CREATE INDEX idx_tax_obligations_user_fy ON TaxObligations(user_id, financial_year_id);
CREATE INDEX idx_tax_payments_user_fy ON TaxPayments(user_id, financial_year_id);

-- Index for dashboard summaries
CREATE INDEX idx_monthly_summaries_user ON MonthlyFinancialSummaries(user_id);
