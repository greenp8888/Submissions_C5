import express from 'express';
import { createServer as createViteServer } from 'vite';
import Database from 'better-sqlite3';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import dotenv from 'dotenv';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const db = new Database('finance.db');
db.pragma('foreign_keys = OFF');
const JWT_SECRET = process.env.JWT_SECRET || 'super-secret-key';
const normalizeEmail = (email: string) => email.trim().toLowerCase();

// Initialize SQL Schema based on User's Mermaid Diagram
db.exec(`
  CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    name TEXT,
    onboarding_completed INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
`);

// Migration: Ensure all necessary columns exist in the Users table
const getColumns = (tableName: string) => {
  try {
    const info = db.pragma(`table_info(${tableName})`) as any[];
    return info.map(col => col.name);
  } catch (e) {
    return [];
  }
};

let userColumns = getColumns('Users');

// Handle primary key rename if it was 'id' before
if (userColumns.includes('id') && !userColumns.includes('user_id')) {
  try {
    db.exec('ALTER TABLE Users RENAME COLUMN id TO user_id');
    console.log('Renamed id to user_id in Users table');
    userColumns = getColumns('Users');
  } catch (err) {
    console.error('Failed to rename id to user_id:', err);
  }
}

// Ensure other tables have user_id if they were created with id before
const tablesToMigrate = ['SalaryHistory', 'OtherIncomes', 'Expenses', 'FixedInvestments', 'Loans', 'MonthlyFinancialSummaries', 'TaxObligations', 'TaxPayments', 'Trades'];
tablesToMigrate.forEach(tableName => {
  const cols = getColumns(tableName);
  if (cols.length > 0 && !cols.includes('user_id')) {
    try {
      db.exec(`ALTER TABLE ${tableName} ADD COLUMN user_id INTEGER REFERENCES Users(user_id) ON DELETE CASCADE`);
      console.log(`Added user_id to ${tableName}`);
    } catch (e) {
      console.error(`Failed to add user_id to ${tableName}:`, e);
    }
  }
});

// Migration for Expenses table: Ensure category_id exists
const expenseCols = getColumns('Expenses');
if (expenseCols.length > 0 && !expenseCols.includes('category_id')) {
  try {
    db.exec('ALTER TABLE Expenses ADD COLUMN category_id INTEGER REFERENCES ExpenseCategories(id) ON DELETE SET NULL');
    console.log('Added category_id to Expenses table');
  } catch (e) {
    console.error('Failed to add category_id to Expenses table:', e);
  }
}

const requiredColumns = [
  { name: 'password', type: 'TEXT' },
  { name: 'name', type: 'TEXT' },
  { name: 'onboarding_completed', type: 'INTEGER DEFAULT 0' }
];

for (const col of requiredColumns) {
  if (!userColumns.includes(col.name)) {
    try {
      db.exec(`ALTER TABLE Users ADD COLUMN ${col.name} ${col.type}`);
      console.log(`Added ${col.name} column to Users table`);
    } catch (err) {
      console.error(`Failed to add ${col.name} column:`, err);
    }
  }
}

db.exec(`
  CREATE TABLE IF NOT EXISTS ExpenseCategories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT UNIQUE NOT NULL
  );

  CREATE TABLE IF NOT EXISTS SalaryHistory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    monthly_amount REAL NOT NULL,
    employer_name TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    gross_monthly REAL,
    basic_salary REAL,
    hra REAL,
    special_allowance REAL,
    lta REAL,
    tax_deduction REAL,
    pf_deduction REAL,
    nps_deduction REAL,
    professional_tax REAL,
    other_deductions REAL
  );

  CREATE TABLE IF NOT EXISTS OtherIncomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    income_source TEXT NOT NULL,
    amount REAL NOT NULL,
    date_received TEXT NOT NULL,
    is_taxable INTEGER DEFAULT 1
  );

  CREATE TABLE IF NOT EXISTS Expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES ExpenseCategories(id) ON DELETE SET NULL,
    amount REAL NOT NULL,
    transaction_date TEXT NOT NULL,
    description TEXT
  );

  CREATE TABLE IF NOT EXISTS Securities (
    ticker TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    asset_class TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS Trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    ticker TEXT NOT NULL REFERENCES Securities(ticker) ON DELETE RESTRICT,
    trade_type TEXT NOT NULL CHECK (trade_type IN ('BUY', 'SELL')),
    quantity INTEGER NOT NULL,
    price_per_unit REAL NOT NULL,
    execution_date TEXT NOT NULL,
    brokerage_fees REAL DEFAULT 0,
    buy_date TEXT,
    sell_date TEXT,
    realized_gain REAL DEFAULT 0,
    holding_type TEXT
  );

  CREATE TABLE IF NOT EXISTS TaxLots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id INTEGER NOT NULL REFERENCES Trades(id) ON DELETE CASCADE,
    remaining_quantity INTEGER NOT NULL,
    buy_price REAL NOT NULL,
    purchase_date TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS FixedInvestments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    investment_type TEXT NOT NULL,
    asset_category TEXT,
    commodity_type TEXT,
    principal_amount REAL NOT NULL,
    interest_rate REAL NOT NULL,
    quantity_units REAL,
    buy_price_per_unit REAL,
    start_date TEXT NOT NULL,
    purchase_date TEXT,
    maturity_date TEXT,
    tenure_months INTEGER,
    maturity_amount REAL,
    tax_exemption_category TEXT,
    status TEXT DEFAULT 'ACTIVE'
  );

  CREATE TABLE IF NOT EXISTS Goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    goal_name TEXT NOT NULL,
    goal_type TEXT NOT NULL,
    target_amount REAL NOT NULL,
    current_amount REAL DEFAULT 0,
    target_date TEXT,
    monthly_contribution REAL DEFAULT 0,
    notes TEXT
  );

  CREATE TABLE IF NOT EXISTS Loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    loan_type TEXT NOT NULL,
    principal_amount REAL NOT NULL,
    interest_rate REAL NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    tenure_months INTEGER,
    monthly_emi REAL
  );

  CREATE TABLE IF NOT EXISTS LoanPayments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER NOT NULL REFERENCES Loans(id) ON DELETE CASCADE,
    payment_date TEXT NOT NULL,
    amount_paid REAL NOT NULL,
    principal_component REAL,
    interest_component REAL
  );

  CREATE TABLE IF NOT EXISTS FinancialYears (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS MonthlyFinancialSummaries (
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    year_month TEXT NOT NULL,
    total_salary REAL DEFAULT 0,
    total_other_income REAL DEFAULT 0,
    total_expenses REAL DEFAULT 0,
    net_savings REAL DEFAULT 0,
    PRIMARY KEY (user_id, year_month)
  );

  CREATE TABLE IF NOT EXISTS TaxObligations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    financial_year_id INTEGER NOT NULL REFERENCES FinancialYears(id),
    tax_category TEXT NOT NULL,
    calculated_liability REAL DEFAULT 0
  );

  CREATE TABLE IF NOT EXISTS TaxPayments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    financial_year_id INTEGER NOT NULL REFERENCES FinancialYears(id),
    amount_paid REAL NOT NULL,
    payment_date TEXT NOT NULL,
    payment_type TEXT
  );

  CREATE TABLE IF NOT EXISTS TaxBenefitEntries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    benefit_category TEXT NOT NULL,
    amount REAL NOT NULL,
    contribution_date TEXT NOT NULL,
    description TEXT,
    entry_type TEXT DEFAULT 'investment'
  );

  CREATE TABLE IF NOT EXISTS HealthScores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    fy_id TEXT NOT NULL,
    fy_label TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    overall REAL DEFAULT 0,
    savings_rate_score REAL DEFAULT 0,
    debt_score REAL DEFAULT 0,
    investment_coverage_score REAL DEFAULT 0,
    emergency_fund_score REAL DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, fy_id)
  );
`);

const ensureColumns = (tableName: string, columns: Array<{ name: string; type: string }>) => {
  const existingColumns = getColumns(tableName);
  columns.forEach((column) => {
    if (!existingColumns.includes(column.name)) {
      try {
        db.exec(`ALTER TABLE ${tableName} ADD COLUMN ${column.name} ${column.type}`);
        console.log(`Added ${column.name} to ${tableName}`);
      } catch (err) {
        console.error(`Failed to add ${column.name} to ${tableName}:`, err);
      }
    }
  });
};

const clampScore = (value: number) => Math.max(0, Math.min(100, value));

const getFinancialYearRanges = () => {
  const now = new Date();
  const currentEndYear = now.getMonth() >= 3 ? now.getFullYear() + 1 : now.getFullYear();
  return Array.from({ length: 3 }, (_, index) => {
    const endYear = currentEndYear - index;
    const start = new Date(endYear - 1, 3, 1);
    const end = new Date(endYear, 2, 31, 23, 59, 59, 999);
    return {
      fy_id: `${endYear - 1}-${endYear}`,
      fy_label: `FY ${String(endYear - 1).slice(-2)}-${String(endYear).slice(-2)}`,
      start,
      end,
    };
  });
};

const isDateInRange = (dateLike: unknown, start: Date, end: Date) => {
  const date = new Date(String(dateLike));
  if (Number.isNaN(date.getTime())) return false;
  return date >= start && date <= end;
};

const getInclusiveMonthCount = (start: Date, end: Date) => {
  if (start > end) return 0;
  return (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth()) + 1;
};

const inferInvestmentTaxCategory = (investment: any) => {
  if (investment.tax_exemption_category) return investment.tax_exemption_category;
  const type = String(investment.investment_type || '').toLowerCase();
  if (type.includes('ppf') || type.includes('epf') || type.includes('elss') || type.includes('nsc') || type.includes('tax saver')) {
    return '80C';
  }
  if (type.includes('nps')) return '80CCD(1B)';
  if (type.includes('insurance') || type.includes('medical')) return '80D';
  return '';
};

const isInsuranceLikeGoal = (goal: any) => {
  const label = `${goal.goal_type || ''} ${goal.goal_name || ''}`.toLowerCase();
  return label.includes('emergency');
};

ensureColumns('SalaryHistory', [
  { name: 'gross_monthly', type: 'REAL' },
  { name: 'basic_salary', type: 'REAL' },
  { name: 'hra', type: 'REAL' },
  { name: 'special_allowance', type: 'REAL' },
  { name: 'lta', type: 'REAL' },
  { name: 'tax_deduction', type: 'REAL' },
  { name: 'pf_deduction', type: 'REAL' },
  { name: 'nps_deduction', type: 'REAL' },
  { name: 'professional_tax', type: 'REAL' },
  { name: 'other_deductions', type: 'REAL' },
]);

ensureColumns('Trades', [
  { name: 'buy_date', type: 'TEXT' },
  { name: 'sell_date', type: 'TEXT' },
  { name: 'realized_gain', type: 'REAL DEFAULT 0' },
  { name: 'holding_type', type: 'TEXT' },
]);

ensureColumns('FixedInvestments', [
  { name: 'asset_category', type: 'TEXT' },
  { name: 'commodity_type', type: 'TEXT' },
  { name: 'tenure_months', type: 'INTEGER' },
  { name: 'maturity_amount', type: 'REAL' },
  { name: 'quantity_units', type: 'REAL' },
  { name: 'buy_price_per_unit', type: 'REAL' },
  { name: 'purchase_date', type: 'TEXT' },
]);

ensureColumns('Loans', [
  { name: 'tenure_months', type: 'INTEGER' },
]);

db.pragma('foreign_keys = ON');

// Seed Categories
const seedCategories = ['Food', 'Rent', 'Utilities', 'Shopping', 'Travel', 'Entertainment', 'Health', 'Other'];
const insertCategory = db.prepare('INSERT OR IGNORE INTO ExpenseCategories (category_name) VALUES (?)');
seedCategories.forEach(cat => insertCategory.run(cat));

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(cors());
  app.use(express.json());

  const buildUpdateStatement = (body: Record<string, any>) => {
    const fields = Object.keys(body).filter((key) => body[key] !== undefined);
    return {
      fields,
      values: fields.map((field) => body[field]),
      setClause: fields.map((field) => `${field} = ?`).join(', '),
    };
  };

  const recalculateHealthScoresForUser = (userId: number) => {
    const salaryRows = db.prepare('SELECT * FROM SalaryHistory WHERE user_id = ? ORDER BY date(effective_from) ASC, id ASC').all(userId) as any[];
    const incomeRows = db.prepare('SELECT * FROM OtherIncomes WHERE user_id = ?').all(userId) as any[];
    const expenseRows = db.prepare('SELECT * FROM Expenses WHERE user_id = ?').all(userId) as any[];
    const investmentRows = db.prepare('SELECT * FROM FixedInvestments WHERE user_id = ?').all(userId) as any[];
    const loanRows = db.prepare('SELECT * FROM Loans WHERE user_id = ?').all(userId) as any[];
    const tradeRows = db.prepare('SELECT * FROM Trades WHERE user_id = ?').all(userId) as any[];
    const goalRows = db.prepare('SELECT * FROM Goals WHERE user_id = ?').all(userId) as any[];

    const salaryRanges = salaryRows.map((salary, index) => {
      const start = salary.effective_from ? new Date(salary.effective_from) : null;
      const end = salary.effective_to ? new Date(salary.effective_to) : null;
      const nextSalary = salaryRows[index + 1];
      const inferredEnd = end || (nextSalary?.effective_from ? new Date(new Date(nextSalary.effective_from).getFullYear(), new Date(nextSalary.effective_from).getMonth(), 0) : null);
      return {
        ...salary,
        start,
        end: inferredEnd,
        monthly_amount: Number(salary.monthly_amount) || 0,
      };
    }).filter((salary) => salary.start && !Number.isNaN(salary.start.getTime()));

    const upsert = db.prepare(`
      INSERT INTO HealthScores (
        user_id, fy_id, fy_label, start_date, end_date,
        overall, savings_rate_score, debt_score, investment_coverage_score, emergency_fund_score, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
      ON CONFLICT(user_id, fy_id) DO UPDATE SET
        fy_label = excluded.fy_label,
        start_date = excluded.start_date,
        end_date = excluded.end_date,
        overall = excluded.overall,
        savings_rate_score = excluded.savings_rate_score,
        debt_score = excluded.debt_score,
        investment_coverage_score = excluded.investment_coverage_score,
        emergency_fund_score = excluded.emergency_fund_score,
        updated_at = CURRENT_TIMESTAMP
    `);

    getFinancialYearRanges().forEach((fy) => {
      const fyVisibleEnd = fy.end < new Date() ? fy.end : new Date();
      const fyMonthCount = Math.max(1, getInclusiveMonthCount(fy.start, fyVisibleEnd));

      const annualSalary = salaryRanges.reduce((sum, salary) => {
        const effectiveStart = new Date(Math.max(salary.start.getTime(), fy.start.getTime()));
        const effectiveEnd = new Date(Math.min((salary.end || fy.end).getTime(), fy.end.getTime()));
        if (effectiveStart > effectiveEnd) return sum;
        return sum + salary.monthly_amount * getInclusiveMonthCount(effectiveStart, effectiveEnd);
      }, 0);

      const otherIncome = incomeRows.reduce((sum, income) => {
        if (!isDateInRange(income.date_received, fy.start, fy.end)) return sum;
        return sum + (Number(income.amount) || 0);
      }, 0);

      const realizedGains = tradeRows.reduce((sum, trade) => {
        const tradeDate = trade.sell_date || trade.execution_date || trade.buy_date;
        if (!isDateInRange(tradeDate, fy.start, fy.end)) return sum;
        return sum + (Number(trade.realized_gain) || 0);
      }, 0);

      const annualIncome = annualSalary + otherIncome + realizedGains;

      const annualExpenses = expenseRows.reduce((sum, expense) => {
        if (!isDateInRange(expense.transaction_date, fy.start, fy.end)) return sum;
        return sum + (Number(expense.amount) || 0);
      }, 0);

      const monthlyIncome = annualIncome / fyMonthCount;
      const monthlyExpenses = annualExpenses / fyMonthCount;
      const totalMonthlyEmi = loanRows
        .filter((loan) => {
          if (!loan.end_date) return true;
          const endDate = new Date(loan.end_date);
          return Number.isNaN(endDate.getTime()) || endDate >= new Date();
        })
        .reduce((sum, loan) => sum + (Number(loan.monthly_emi) || 0), 0);

      const portfolioInvestments = investmentRows.filter((investment) => {
        const type = String(investment.investment_type || '').toLowerCase();
        return !(type.includes('insurance') || type.includes('medical'));
      });
      const investedAssets =
        portfolioInvestments.reduce((sum, investment) => sum + ((Number(investment.principal_amount) || 0) || ((Number(investment.quantity_units) || 0) * (Number(investment.buy_price_per_unit) || 0))), 0) +
        tradeRows.reduce((sum, trade) => sum + (Number(trade.quantity) || 0) * (Number(trade.price_per_unit) || 0), 0);

      const emergencyFundCurrent = goalRows
        .filter((goal) => isInsuranceLikeGoal(goal))
        .reduce((sum, goal) => sum + (Number(goal.current_amount) || 0), 0);
      const emergencyFundTarget = monthlyExpenses * 6;

      const savingsRateScore = clampScore(annualIncome > 0 ? ((Math.max(0, annualIncome - annualExpenses) / annualIncome) * 100) : 0);
      const dtiRatioPercent = monthlyIncome > 0 ? (totalMonthlyEmi / monthlyIncome) * 100 : 0;
      const debtScore = clampScore(100 - dtiRatioPercent * 2);
      const investmentCoverageScore = clampScore(annualIncome > 0 ? ((investedAssets / annualIncome) * 10) : 0);
      const emergencyFundScore = clampScore(emergencyFundTarget > 0 ? ((emergencyFundCurrent / emergencyFundTarget) * 100) : 0);
      const overall = (savingsRateScore + debtScore + investmentCoverageScore + emergencyFundScore) / 4;

      upsert.run(
        userId,
        fy.fy_id,
        fy.fy_label,
        fy.start.toISOString().split('T')[0],
        fy.end.toISOString().split('T')[0],
        overall,
        savingsRateScore,
        debtScore,
        investmentCoverageScore,
        emergencyFundScore,
      );
    });
  };

  // Middleware: Auth
  const authenticateToken = (req: any, res: any, next: any) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    if (!token) return res.sendStatus(401);

    jwt.verify(token, JWT_SECRET, (err: any, user: any) => {
      if (err) return res.sendStatus(403);
      req.user = user;
      next();
    });
  };

  // Auth Routes
  app.post('/api/auth/register', async (req, res) => {
    const { email, password, name } = req.body;
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }
    try {
      const normalizedEmail = normalizeEmail(email);
      const hashedPassword = await bcrypt.hash(password, 10);
      const result = db.prepare('INSERT INTO Users (email, password, name) VALUES (?, ?, ?)')
        .run(normalizedEmail, hashedPassword, name);
      
      const token = jwt.sign({ user_id: result.lastInsertRowid, email: normalizedEmail }, JWT_SECRET);
      res.json({ token, user: { user_id: result.lastInsertRowid, email: normalizedEmail, name } });
    } catch (err: any) {
      if (err.message.includes('UNIQUE constraint failed')) {
        return res.status(400).json({ error: 'Email already in use' });
      }
      console.error('Registration error:', err);
      res.status(500).json({ error: 'Registration failed' });
    }
  });

  app.post('/api/auth/login', async (req, res) => {
    const { email, password } = req.body;
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }
    try {
      const normalizedEmail = normalizeEmail(email);
      const user = db.prepare('SELECT * FROM Users WHERE email = ?').get(normalizedEmail) as any;
      if (!user || !user.password || !(await bcrypt.compare(password, user.password))) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }
      const token = jwt.sign({ user_id: user.user_id, email: normalizedEmail }, JWT_SECRET);
      res.json({ token, user: { user_id: user.user_id, email: normalizedEmail, name: user.name, onboarding_completed: user.onboarding_completed } });
    } catch (err: any) {
      console.error('Login error:', err);
      res.status(500).json({ error: 'Login failed' });
    }
  });

  app.post('/api/auth/reset-password', async (req, res) => {
    const { email, password } = req.body;
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and new password are required' });
    }
    try {
      const normalizedEmail = normalizeEmail(email);
      const user = db.prepare('SELECT user_id FROM Users WHERE email = ?').get(normalizedEmail) as any;
      if (!user) {
        return res.status(404).json({ error: 'No account found for this email' });
      }
      const hashedPassword = await bcrypt.hash(password, 10);
      db.prepare('UPDATE Users SET password = ? WHERE email = ?').run(hashedPassword, normalizedEmail);
      res.json({ success: true });
    } catch (err: any) {
      console.error('Reset password error:', err);
      res.status(500).json({ error: 'Password reset failed' });
    }
  });

  // User Profile
  app.get('/api/profile', authenticateToken, (req: any, res) => {
    const user = db.prepare('SELECT user_id, email, name, onboarding_completed FROM Users WHERE user_id = ?').get(req.user.user_id);
    res.json(user);
  });

  app.patch('/api/profile', authenticateToken, (req: any, res) => {
    const fields = Object.keys(req.body);
    if (fields.length === 0) {
      return res.status(400).json({ error: 'No fields to update' });
    }
    const values = Object.values(req.body);
    const setClause = fields.map(f => `${f} = ?`).join(', ');
    try {
      db.prepare(`UPDATE Users SET ${setClause} WHERE user_id = ?`)
        .run(...values, req.user.user_id);
      res.json({ success: true });
    } catch (err: any) {
      console.error('Profile update error:', err);
      res.status(500).json({ error: 'Failed to update profile' });
    }
  });

  app.get('/api/health-scores', authenticateToken, (req: any, res) => {
    const rows = db.prepare(`
      SELECT *
      FROM HealthScores
      WHERE user_id = ?
      ORDER BY start_date DESC
    `).all(req.user.user_id);
    res.json(rows);
  });

  // Salary History
  app.get('/api/salary/history', authenticateToken, (req: any, res) => {
    const salaries = db.prepare(`
      SELECT *
      FROM SalaryHistory
      WHERE user_id = ?
      ORDER BY date(effective_from) DESC, id DESC
    `).all(req.user.user_id);

    res.json(salaries);
  });

  app.get('/api/salary/latest', authenticateToken, (req: any, res) => {
    const salary = db.prepare(`
      SELECT *
      FROM SalaryHistory
      WHERE user_id = ?
      ORDER BY date(effective_from) DESC, id DESC
      LIMIT 1
    `).get(req.user.user_id);

    res.json(salary || null);
  });

  app.post('/api/salary', authenticateToken, (req: any, res) => {
    const {
      monthly_amount,
      employer_name,
      effective_from,
      effective_to,
      gross_monthly,
      basic_salary,
      hra,
      special_allowance,
      lta,
      tax_deduction,
      pf_deduction,
      nps_deduction,
      professional_tax,
      other_deductions,
    } = req.body;

    db.prepare(`
      INSERT INTO SalaryHistory (
        user_id,
        monthly_amount,
        employer_name,
        effective_from,
        effective_to,
        gross_monthly,
        basic_salary,
        hra,
        special_allowance,
        lta,
        tax_deduction,
        pf_deduction,
        nps_deduction,
        professional_tax,
        other_deductions
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      req.user.user_id,
      monthly_amount,
      employer_name,
      effective_from,
      effective_to || null,
      gross_monthly || null,
      basic_salary || null,
      hra || null,
      special_allowance || null,
      lta || null,
      tax_deduction || null,
      pf_deduction || null,
      nps_deduction || null,
      professional_tax || null,
      other_deductions || null
    );
    recalculateHealthScoresForUser(req.user.user_id);
    res.json({ success: true });
  });

  app.patch('/api/salary/:id', authenticateToken, (req: any, res) => {
    const { fields, values, setClause } = buildUpdateStatement(req.body);
    if (fields.length === 0) {
      return res.status(400).json({ error: 'No fields to update' });
    }
    db.prepare(`UPDATE SalaryHistory SET ${setClause} WHERE id = ? AND user_id = ?`)
      .run(...values, req.params.id, req.user.user_id);
    recalculateHealthScoresForUser(req.user.user_id);
    res.json({ success: true });
  });

  // Other Incomes
  app.get('/api/incomes', authenticateToken, (req: any, res) => {
    const incomes = db.prepare('SELECT * FROM OtherIncomes WHERE user_id = ?').all(req.user.user_id);
    res.json(incomes);
  });

  app.post('/api/incomes', authenticateToken, (req: any, res) => {
    const { income_source, amount, date_received, is_taxable } = req.body;
    db.prepare('INSERT INTO OtherIncomes (user_id, income_source, amount, date_received, is_taxable) VALUES (?, ?, ?, ?, ?)')
      .run(req.user.user_id, income_source, amount, date_received, is_taxable ? 1 : 0);
    recalculateHealthScoresForUser(req.user.user_id);
    res.json({ success: true });
  });

  // Expenses
  app.get('/api/expenses', authenticateToken, (req: any, res) => {
    const expenses = db.prepare(`
      SELECT e.*, c.category_name 
      FROM Expenses e 
      LEFT JOIN ExpenseCategories c ON e.category_id = c.id 
      WHERE e.user_id = ?
    `).all(req.user.user_id);
    res.json(expenses);
  });

  app.post('/api/expenses', authenticateToken, (req: any, res) => {
    const { amount, transaction_date, description, category_name } = req.body;
    let category = db.prepare('SELECT id FROM ExpenseCategories WHERE category_name = ?').get(category_name) as any;
    if (!category) {
      const result = db.prepare('INSERT INTO ExpenseCategories (category_name) VALUES (?)').run(category_name);
      category = { id: result.lastInsertRowid };
    }
    db.prepare('INSERT INTO Expenses (user_id, category_id, amount, transaction_date, description) VALUES (?, ?, ?, ?, ?)')
      .run(req.user.user_id, category.id, amount, transaction_date, description);
    recalculateHealthScoresForUser(req.user.user_id);
    res.json({ success: true });
  });

  app.patch('/api/expenses/:id', authenticateToken, (req: any, res) => {
    const payload = { ...req.body };
    if (payload.category_name !== undefined) {
      let category = db.prepare('SELECT id FROM ExpenseCategories WHERE category_name = ?').get(payload.category_name) as any;
      if (!category) {
        const result = db.prepare('INSERT INTO ExpenseCategories (category_name) VALUES (?)').run(payload.category_name);
        category = { id: result.lastInsertRowid };
      }
      payload.category_id = category.id;
      delete payload.category_name;
    }

    const { fields, values, setClause } = buildUpdateStatement(payload);
    if (fields.length === 0) {
      return res.status(400).json({ error: 'No fields to update' });
    }
    db.prepare(`UPDATE Expenses SET ${setClause} WHERE id = ? AND user_id = ?`)
      .run(...values, req.params.id, req.user.user_id);
    recalculateHealthScoresForUser(req.user.user_id);
    res.json({ success: true });
  });

  // Investments
  app.get('/api/investments', authenticateToken, (req: any, res) => {
    const investments = db.prepare('SELECT * FROM FixedInvestments WHERE user_id = ?').all(req.user.user_id);
    res.json(investments);
  });

  app.post('/api/investments', authenticateToken, (req: any, res) => {
    const {
      investment_type,
      asset_category,
      commodity_type,
      principal_amount,
      interest_rate,
      quantity_units,
      buy_price_per_unit,
      start_date,
      purchase_date,
      maturity_date,
      tenure_months,
      maturity_amount,
      tax_exemption_category
    } = req.body;
    db.prepare(`
      INSERT INTO FixedInvestments (
        user_id,
        investment_type,
        asset_category,
        commodity_type,
        principal_amount,
        interest_rate,
        quantity_units,
        buy_price_per_unit,
        start_date,
        purchase_date,
        maturity_date,
        tenure_months,
        maturity_amount,
        tax_exemption_category
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `)
      .run(
        req.user.user_id,
        investment_type,
        asset_category || null,
        commodity_type || null,
        principal_amount,
        interest_rate,
        quantity_units || null,
        buy_price_per_unit || null,
        start_date,
        purchase_date || null,
        maturity_date,
        tenure_months || null,
        maturity_amount || null,
        tax_exemption_category || null
      );
    recalculateHealthScoresForUser(req.user.user_id);
    res.json({ success: true });
  });

  app.patch('/api/investments/:id', authenticateToken, (req: any, res) => {
    const { fields, values, setClause } = buildUpdateStatement(req.body);
    if (fields.length === 0) {
      return res.status(400).json({ error: 'No fields to update' });
    }
    db.prepare(`UPDATE FixedInvestments SET ${setClause} WHERE id = ? AND user_id = ?`)
      .run(...values, req.params.id, req.user.user_id);
    recalculateHealthScoresForUser(req.user.user_id);
    res.json({ success: true });
  });

  app.get('/api/goals', authenticateToken, (req: any, res) => {
    const goals = db.prepare(`
      SELECT *
      FROM Goals
      WHERE user_id = ?
      ORDER BY date(target_date) ASC, id DESC
    `).all(req.user.user_id);
    res.json(goals);
  });

  app.post('/api/goals', authenticateToken, (req: any, res) => {
    const {
      goal_name,
      goal_type,
      target_amount,
      current_amount,
      target_date,
      monthly_contribution,
      notes,
    } = req.body;
    db.prepare(`
      INSERT INTO Goals (
        user_id,
        goal_name,
        goal_type,
        target_amount,
        current_amount,
        target_date,
        monthly_contribution,
        notes
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      req.user.user_id,
      goal_name,
      goal_type,
      target_amount,
      current_amount || 0,
      target_date || null,
      monthly_contribution || 0,
      notes || null
    );
    recalculateHealthScoresForUser(req.user.user_id);
    res.json({ success: true });
  });

  app.patch('/api/goals/:id', authenticateToken, (req: any, res) => {
    const { fields, values, setClause } = buildUpdateStatement(req.body);
    if (fields.length === 0) {
      return res.status(400).json({ error: 'No fields to update' });
    }
    db.prepare(`UPDATE Goals SET ${setClause} WHERE id = ? AND user_id = ?`)
      .run(...values, req.params.id, req.user.user_id);
    recalculateHealthScoresForUser(req.user.user_id);
    res.json({ success: true });
  });

  // Tax benefits
  app.get('/api/tax-benefits', authenticateToken, (req: any, res) => {
    const entries = db.prepare(`
      SELECT *
      FROM TaxBenefitEntries
      WHERE user_id = ?
      ORDER BY date(contribution_date) DESC, id DESC
    `).all(req.user.user_id);
    res.json(entries);
  });

  app.post('/api/tax-benefits', authenticateToken, (req: any, res) => {
    const { benefit_category, amount, contribution_date, description, entry_type } = req.body;
    db.prepare(`
      INSERT INTO TaxBenefitEntries (
        user_id,
        benefit_category,
        amount,
        contribution_date,
        description,
        entry_type
      ) VALUES (?, ?, ?, ?, ?, ?)
    `).run(
      req.user.user_id,
      benefit_category,
      amount,
      contribution_date,
      description || null,
      entry_type || 'investment'
    );
    recalculateHealthScoresForUser(req.user.user_id);
    res.json({ success: true });
  });

  app.patch('/api/tax-benefits/:id', authenticateToken, (req: any, res) => {
    const { fields, values, setClause } = buildUpdateStatement(req.body);
    if (fields.length === 0) {
      return res.status(400).json({ error: 'No fields to update' });
    }
    db.prepare(`UPDATE TaxBenefitEntries SET ${setClause} WHERE id = ? AND user_id = ?`)
      .run(...values, req.params.id, req.user.user_id);
    recalculateHealthScoresForUser(req.user.user_id);
    res.json({ success: true });
  });

  // Loans
  app.get('/api/loans', authenticateToken, (req: any, res) => {
    const loans = db.prepare('SELECT * FROM Loans WHERE user_id = ? ORDER BY date(start_date) DESC, id DESC').all(req.user.user_id);
    res.json(loans);
  });

  app.post('/api/loans', authenticateToken, (req: any, res) => {
    const { loan_type, principal_amount, interest_rate, start_date, end_date, tenure_months, monthly_emi } = req.body;
    db.prepare(`
      INSERT INTO Loans (
        user_id,
        loan_type,
        principal_amount,
        interest_rate,
        start_date,
        end_date,
        tenure_months,
        monthly_emi
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      req.user.user_id,
      loan_type,
      principal_amount,
      interest_rate,
      start_date,
      end_date || null,
      tenure_months || null,
      monthly_emi || null
    );
    recalculateHealthScoresForUser(req.user.user_id);
    res.json({ success: true });
  });

  app.patch('/api/loans/:id', authenticateToken, (req: any, res) => {
    const { fields, values, setClause } = buildUpdateStatement(req.body);
    if (fields.length === 0) {
      return res.status(400).json({ error: 'No fields to update' });
    }
    db.prepare(`UPDATE Loans SET ${setClause} WHERE id = ? AND user_id = ?`)
      .run(...values, req.params.id, req.user.user_id);
    recalculateHealthScoresForUser(req.user.user_id);
    res.json({ success: true });
  });

  // Trades
  app.get('/api/trades', authenticateToken, (req: any, res) => {
    const trades = db.prepare('SELECT * FROM Trades WHERE user_id = ?').all(req.user.user_id);
    res.json(trades);
  });

  app.post('/api/trades', authenticateToken, (req: any, res) => {
    const {
      ticker,
      trade_type,
      quantity,
      price_per_unit,
      execution_date,
      brokerage_fees,
      ticker_name,
      asset_class,
      buy_date,
      sell_date,
      realized_gain,
      holding_type,
    } = req.body;
    const resolvedExecutionDate = execution_date || sell_date || buy_date;
    if (!ticker || !trade_type || !quantity || !price_per_unit || !resolvedExecutionDate) {
      return res.status(400).json({ error: 'ticker, trade_type, quantity, price_per_unit, and an execution date are required' });
    }
    // Ensure security exists
    db.prepare('INSERT OR IGNORE INTO Securities (ticker, name, asset_class) VALUES (?, ?, ?)')
      .run(ticker, ticker_name || ticker, asset_class || 'Equity');
    
    db.prepare(`
      INSERT INTO Trades (
        user_id,
        ticker,
        trade_type,
        quantity,
        price_per_unit,
        execution_date,
        brokerage_fees,
        buy_date,
        sell_date,
        realized_gain,
        holding_type
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      req.user.user_id,
      ticker,
      trade_type,
      quantity,
      price_per_unit,
      resolvedExecutionDate,
      brokerage_fees || 0,
      buy_date || null,
      sell_date || null,
      realized_gain || 0,
      holding_type || null
    );
    recalculateHealthScoresForUser(req.user.user_id);
    res.json({ success: true });
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
