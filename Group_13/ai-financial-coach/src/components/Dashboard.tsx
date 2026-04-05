import React, { useEffect, useMemo, useState } from 'react';
import {
  Area,
  AreaChart,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Bell, Clock3, Info, Loader2, Trash2, Upload } from 'lucide-react';
import { motion } from 'motion/react';
import { useFirebase } from './FirebaseProvider';
import AIChat from './AIChat';
import { apiClient } from '../lib/api';
import { parseExpenses } from '../lib/agents/expenseParser';
import { parseEquityPL } from '../lib/agents/equityParser';
import { buildTradePayloadFromParsedTrade } from '../lib/tradeImport';
import { buildPortfolioSnapshot } from '../lib/portfolioSnapshot';

const currencyFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
});

const compactFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  notation: 'compact',
  maximumFractionDigits: 1,
});

const monthFormatter = new Intl.DateTimeFormat('en-IN', { month: 'short' });
const ASSET_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
const EXPENSE_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
const SECTION_80C_LIMIT = 150000;
const SECTION_80D_LIMIT = 25000;

type DashboardPage = 'overview' | 'salary' | 'investments' | 'goals' | 'tax' | 'loans' | 'expenses';
const PAGE_SIZE = 5;

const toNumber = (value: unknown) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
};

const getMonthKey = (value: unknown) => {
  const date = new Date(String(value));
  if (Number.isNaN(date.getTime())) return '';
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
};

const getInitials = (name?: string | null, email?: string | null) => {
  const seed = name?.trim() || email?.trim() || 'U';
  return seed
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || '')
    .join('');
};

const inferTaxCategoryFromInvestment = (investment: any) => {
  const explicitCategory = investment.tax_exemption_category;
  if (explicitCategory) return explicitCategory;

  const type = String(investment.investment_type || '').toLowerCase();
  if (type.includes('ppf') || type.includes('epf') || type.includes('elss') || type.includes('nsc') || type.includes('tax saver')) {
    return '80C';
  }
  if (type.includes('nps')) return '80CCD(1B)';
  if (type.includes('insurance') || type.includes('medical')) return '80D';
  return '';
};

const getInvestmentContributionDate = (investment: any) => {
  return investment.purchase_date || investment.start_date || investment.maturity_date || '';
};

const getTaxBracketLabel = (taxableIncome: number) => {
  const income = Math.max(0, taxableIncome);
  if (income <= 400000) return 'Nil';
  if (income <= 800000) return '5%';
  if (income <= 1200000) return '10%';
  if (income <= 1600000) return '15%';
  if (income <= 2000000) return '20%';
  if (income <= 2400000) return '25%';
  return '30%';
};

const isInsuranceType = (type?: string) => {
  const value = String(type || '').toLowerCase();
  return value.includes('insurance') || value.includes('medical');
};

const isEmergencyFundGoal = (goal: any) => {
  const label = `${goal?.goal_type || ''} ${goal?.goal_name || ''}`.toLowerCase();
  return label.includes('emergency');
};

const calculateGoalProgress = (currentAmount: number, targetAmount: number) => {
  if (!targetAmount) return 0;
  return Math.max(0, Math.min(100, (currentAmount / targetAmount) * 100));
};

const clampScore = (value: number) => Math.max(0, Math.min(100, value));

const INVESTMENT_FILTERS = ['debt', 'equity', 'mutual_fund', 'etf', 'commodity'] as const;
type InvestmentFilter = typeof INVESTMENT_FILTERS[number];

const getInvestmentFilter = (investment: any): InvestmentFilter => {
  const type = String(investment.investment_type || '').toLowerCase();
  const assetCategory = String(investment.asset_category || '').toLowerCase();
  if (type.includes('commodity') || assetCategory.includes('commodity') || type.includes('gold') || type.includes('silver')) {
    return 'commodity';
  }
  if (type.includes('mutual')) return 'mutual_fund';
  if (type.includes('etf')) return 'etf';
  if (type.includes('equity') || type.includes('stock') || type.includes('share')) return 'equity';
  return 'debt';
};

const getInvestmentFilterLabel = (filter: InvestmentFilter) => {
  switch (filter) {
    case 'debt':
      return 'Debt';
    case 'equity':
      return 'Equity';
    case 'mutual_fund':
      return 'Mutual Fund';
    case 'etf':
      return 'ETFs';
    case 'commodity':
      return 'Commodity';
  }
};

const getTradeAssetClass = (trade: any) => {
  const explicit = String(trade.asset_class || '').trim();
  if (explicit) return explicit;

  const symbol = String(trade.ticker_name || trade.ticker || trade.symbol || '').toLowerCase();
  if (
    symbol.includes('etf') ||
    symbol.includes('bees') ||
    symbol.includes('niftybees') ||
    symbol.includes('goldbees') ||
    symbol.includes('juniorbees')
  ) {
    return 'ETF';
  }
  if (
    symbol.includes('fund') ||
    symbol.includes('mf') ||
    symbol.includes('growth') ||
    symbol.includes('direct') ||
    symbol.includes('regular')
  ) {
    return 'Mutual Fund';
  }
  return 'Equity';
};

const getTradeFilter = (trade: any): InvestmentFilter => {
  const assetClass = getTradeAssetClass(trade).toLowerCase();
  if (assetClass.includes('mutual')) return 'mutual_fund';
  if (assetClass.includes('etf')) return 'etf';
  return 'equity';
};

const getNormalizedTradeType = (trade: any) => {
  const explicit = String(trade.trade_type || '').toUpperCase();
  if (explicit === 'BUY' || explicit === 'SELL') return explicit;
  return trade.sell_date ? 'SELL' : 'BUY';
};

const getTradeSnapshots = (trades: any[]) => {
  const grouped = new Map<string, any>();

  trades.forEach((trade) => {
    const key = String(trade.ticker || trade.symbol || trade.ticker_name || 'Unknown');
    const quantity = toNumber(trade.quantity);
    const price = toNumber(trade.price_per_unit);
    const currentPrice = toNumber(trade.current_price);
    const uploadedUnrealizedGain = toNumber(trade.unrealized_gain);
    const realizedGain = toNumber(trade.realized_gain);
    const type = getNormalizedTradeType(trade);
    const executionDate = trade.execution_date || trade.sell_date || trade.buy_date || '';
    const executionTs = new Date(String(executionDate)).getTime();
    const current = grouped.get(key) || {
      key,
      name: trade.ticker_name || trade.ticker || trade.symbol || key,
      assetClass: getTradeAssetClass(trade),
      boughtQty: 0,
      soldQty: 0,
      buyCost: 0,
      realizedGain: 0,
      latestPrice: 0,
      latestTs: Number.NEGATIVE_INFINITY,
      currentPrice: 0,
      currentPriceTs: Number.NEGATIVE_INFINITY,
      uploadedUnrealizedGain: 0,
      tradeCount: 0,
    };

    if (type === 'BUY') {
      current.boughtQty += quantity;
      current.buyCost += quantity * price;
    } else {
      current.soldQty += quantity;
      current.realizedGain += realizedGain;
    }

    if (Number.isFinite(executionTs) ? executionTs >= current.latestTs : current.tradeCount === 0) {
      current.latestTs = Number.isFinite(executionTs) ? executionTs : current.latestTs;
      current.latestPrice = price;
    }

    if (type === 'BUY' && currentPrice > 0 && (Number.isFinite(executionTs) ? executionTs >= current.currentPriceTs : current.tradeCount === 0)) {
      current.currentPrice = currentPrice;
      current.currentPriceTs = Number.isFinite(executionTs) ? executionTs : current.currentPriceTs;
    }

    if (type === 'BUY' && uploadedUnrealizedGain !== 0) {
      current.uploadedUnrealizedGain = uploadedUnrealizedGain;
    }

    current.tradeCount += 1;
    grouped.set(key, current);
  });

  const active = Array.from(grouped.values())
    .map((item) => {
      const openQuantity = Math.max(0, item.boughtQty - item.soldQty);
      const averageBuyPrice = item.boughtQty > 0 ? item.buyCost / item.boughtQty : 0;
      const costBasis = openQuantity * averageBuyPrice;
      const marketPrice = item.currentPrice || item.latestPrice;
      const currentValue = marketPrice > 0
        ? openQuantity * marketPrice
        : (item.uploadedUnrealizedGain !== 0 ? costBasis + item.uploadedUnrealizedGain : costBasis);
      return {
        id: `trade-active-${item.key}`,
        name: item.name,
        assetClass: item.assetClass,
        openQuantity,
        averageBuyPrice,
        currentPrice: openQuantity > 0 ? currentValue / openQuantity : marketPrice,
        currentValue,
        unrealizedGain: item.uploadedUnrealizedGain !== 0 ? item.uploadedUnrealizedGain : currentValue - costBasis,
        tradeCount: item.tradeCount,
      };
    })
    .filter((item) => item.openQuantity > 0);

  const past = Array.from(grouped.values())
    .map((item) => {
      const openQuantity = Math.max(0, item.boughtQty - item.soldQty);
      return {
        id: `trade-past-${item.key}`,
        name: item.name,
        assetClass: item.assetClass,
        soldQuantity: item.soldQty,
        realizedGain: item.realizedGain,
        tradeCount: item.tradeCount,
        openQuantity,
      };
    })
    .filter((item) => item.soldQuantity > 0 && item.openQuantity <= 0)
    .map(({ openQuantity, ...item }) => item);

  return { active, past };
};

const addMonthsToDate = (dateString: string, months: number) => {
  if (!dateString || !months) return '';
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) return '';
  const result = new Date(date);
  result.setMonth(result.getMonth() + months);
  return result.toISOString().split('T')[0];
};

const calculateFdMaturityAmount = (principal: number, annualRate: number, tenureMonths: number) => {
  if (!principal || !annualRate || !tenureMonths) return 0;
  const monthlyRate = annualRate / 12 / 100;
  return principal * Math.pow(1 + monthlyRate, tenureMonths);
};

const calculateLoanEmi = (principal: number, annualRate: number, tenureMonths: number) => {
  if (!principal || !tenureMonths) return 0;
  const monthlyRate = annualRate / 12 / 100;
  if (monthlyRate === 0) return principal / tenureMonths;
  const factor = Math.pow(1 + monthlyRate, tenureMonths);
  return (principal * monthlyRate * factor) / (factor - 1);
};

const calculatePendingLoanBalance = (
  principal: number,
  annualRate: number,
  tenureMonths: number,
  startDate?: string
) => {
  if (!principal) return 0;
  if (!tenureMonths || !startDate) return principal;

  const start = new Date(startDate);
  if (Number.isNaN(start.getTime())) return principal;

  const now = new Date();
  const elapsedMonths = Math.max(
    0,
    Math.min(
      tenureMonths,
      (now.getFullYear() - start.getFullYear()) * 12 + (now.getMonth() - start.getMonth())
    )
  );

  const monthlyRate = annualRate / 12 / 100;
  if (monthlyRate === 0) {
    return Math.max(0, principal * (1 - elapsedMonths / tenureMonths));
  }

  const emi = calculateLoanEmi(principal, annualRate, tenureMonths);
  const remainingFactor = Math.pow(1 + monthlyRate, tenureMonths - elapsedMonths);
  return Math.max(0, (emi * (remainingFactor - 1)) / monthlyRate / remainingFactor);
};

const getFinancialYearRange = (endYear: number) => {
  const start = new Date(endYear - 1, 3, 1);
  const end = new Date(endYear, 2, 31, 23, 59, 59, 999);
  return { start, end };
};

const getFinancialYearOptions = () => {
  const now = new Date();
  const currentEndYear = now.getMonth() >= 3 ? now.getFullYear() + 1 : now.getFullYear();
  return Array.from({ length: 3 }, (_, index) => {
    const endYear = currentEndYear - index;
    return {
      id: `${endYear - 1}-${endYear}`,
      label: `FY ${String(endYear - 1).slice(-2)}-${String(endYear).slice(-2)}`,
      ...getFinancialYearRange(endYear),
    };
  });
};

const isWithinRange = (dateLike: unknown, start: Date, end: Date) => {
  const date = new Date(String(dateLike));
  if (Number.isNaN(date.getTime())) return false;
  return date >= start && date <= end;
};

const getInclusiveMonthCount = (start: Date, end: Date) => {
  if (start > end) return 0;
  return (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth()) + 1;
};

const getRollingSixMonthExpenseTotal = (expenses: any[]) => {
  const now = new Date();
  const rangeStart = new Date(now.getFullYear(), now.getMonth() - 5, 1);
  const rangeEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59, 999);

  return expenses.reduce((sum, expense) => {
    if (!isWithinRange(expense.transaction_date, rangeStart, rangeEnd)) return sum;
    return sum + toNumber(expense.amount);
  }, 0);
};

const getRollingSixMonthSalaryTotal = (salaryRanges: any[]) => {
  const now = new Date();

  return Array.from({ length: 6 }, (_, index) => {
    const monthDate = new Date(now.getFullYear(), now.getMonth() - (5 - index), 1);
    const monthStart = new Date(monthDate.getFullYear(), monthDate.getMonth(), 1);
    const monthEnd = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0, 23, 59, 59, 999);

    return salaryRanges.reduce((sum, salary) => {
      const salaryStart = salary.start;
      const salaryEnd = salary.rangeEnd || monthEnd;
      if (!salaryStart || salaryStart > monthEnd || salaryEnd < monthStart) return sum;
      return sum + toNumber(salary.monthly_amount);
    }, 0);
  }).reduce((sum, value) => sum + value, 0);
};

const getOptimizationStatus = (value: number, limit?: number) => {
  if (!limit) return value > 0 ? 'claimed' : 'pending';
  if (value >= limit) return 'complete';
  if (value > 0) return 'partial';
  return 'pending';
};

const estimateTaxByNewRegime = (taxableIncome: number) => {
  const income = Math.max(0, taxableIncome);
  if (income <= 400000) return 0;

  const slabs = [
    { limit: 400000, rate: 0 },
    { limit: 800000, rate: 0.05 },
    { limit: 1200000, rate: 0.1 },
    { limit: 1600000, rate: 0.15 },
    { limit: 2000000, rate: 0.2 },
    { limit: 2400000, rate: 0.25 },
    { limit: Number.POSITIVE_INFINITY, rate: 0.3 },
  ];

  let previousLimit = 0;
  let tax = 0;
  slabs.forEach((slab) => {
    if (income <= previousLimit) return;
    const taxablePortion = Math.min(income, slab.limit) - previousLimit;
    if (taxablePortion > 0) {
      tax += taxablePortion * slab.rate;
    }
    previousLimit = slab.limit;
  });

  return tax * 1.04;
};

export default function Dashboard() {
  const {
    userProfile,
    salaryHistory,
    otherIncomes,
    investments,
    goals,
    taxBenefits,
    loans,
    equityTrades,
    expenses,
    logout,
    refreshProfile,
  } = useFirebase();
  const [page, setPage] = useState<DashboardPage>('overview');
  const financialYears = useMemo(() => getFinancialYearOptions(), []);
  const [selectedFyId, setSelectedFyId] = useState(financialYears[0]?.id || '');
  const [activeHealthInfo, setActiveHealthInfo] = useState<'savings' | 'debt' | 'investments' | 'emergency' | null>(null);
  const [taxBenefitDraft, setTaxBenefitDraft] = useState<{
    benefitCategory: string;
    entryType: string;
    description: string;
  } | null>(null);

  const data = useMemo(() => {
    if (!userProfile) return null;
    const selectedFy = financialYears.find((fy) => fy.id === selectedFyId) || financialYears[0];
    const fyStart = selectedFy.start;
    const fyEnd = selectedFy.end;
    const today = new Date();
    const fyVisibleEnd = fyEnd < today ? fyEnd : today;
    const fyMonthCount = Math.max(1, getInclusiveMonthCount(fyStart, fyVisibleEnd));

    const currentMonthKey = getMonthKey(new Date());
    const salaryPeriods = salaryHistory
      .map((salary) => {
        const start = salary.effective_from ? new Date(salary.effective_from) : null;
        const end = salary.effective_to ? new Date(salary.effective_to) : null;
        return {
          ...salary,
          monthly_amount: toNumber(salary.monthly_amount),
          start,
          end,
        };
      })
      .filter((salary) => salary.start && !Number.isNaN(salary.start.getTime()))
      .sort((a, b) => a.start!.getTime() - b.start!.getTime());

    const salaryRanges = salaryPeriods.map((salary, index) => {
      const nextSalary = salaryPeriods[index + 1];
      const naturalEnd =
        salary.end || (nextSalary?.start ? new Date(nextSalary.start.getFullYear(), nextSalary.start.getMonth(), 0) : null);
      return {
        ...salary,
        rangeEnd: naturalEnd,
      };
    });

    const countMonthsInRange = (salaryStart: Date, salaryEnd: Date | null) => {
      const effectiveStart = new Date(Math.max(salaryStart.getTime(), fyStart.getTime()));
      const effectiveEnd = new Date(Math.min((salaryEnd || fyEnd).getTime(), fyEnd.getTime()));
      if (effectiveStart > effectiveEnd) return 0;
      return getInclusiveMonthCount(effectiveStart, effectiveEnd);
    };

    const currentYearSalary = salaryRanges.reduce((sum, salary) => {
      const months = countMonthsInRange(salary.start!, salary.rangeEnd);
      return sum + salary.monthly_amount * months;
    }, 0);
    const trackedSalaryMonths = salaryRanges.reduce((sum, salary) => {
      return sum + countMonthsInRange(salary.start!, salary.rangeEnd);
    }, 0);

    const totalSalaryComponentForFy = (field: string) =>
      salaryRanges.reduce((sum, salary) => {
        const months = countMonthsInRange(salary.start!, salary.rangeEnd);
        return sum + toNumber(salary[field]) * months;
      }, 0);

    const currentMonthOtherIncome = otherIncomes.reduce((sum, income) => {
      return getMonthKey(income.date_received) === currentMonthKey ? sum + toNumber(income.amount) : sum;
    }, 0);

    const currentYearOtherIncome = otherIncomes.reduce((sum, income) => {
      if (!isWithinRange(income.date_received, fyStart, fyEnd)) return sum;
      return sum + toNumber(income.amount);
    }, 0);

    const currentMonthExpenses = expenses.reduce((sum, expense) => {
      return getMonthKey(expense.transaction_date) === currentMonthKey ? sum + toNumber(expense.amount) : sum;
    }, 0);

    const currentMonthTradeGain = equityTrades.reduce((sum, trade) => {
      const tradeDate = trade.sell_date || trade.execution_date || trade.buy_date;
      return getMonthKey(tradeDate) === currentMonthKey ? sum + toNumber(trade.realized_gain) : sum;
    }, 0);

    const currentYearTradeGain = equityTrades.reduce((sum, trade) => {
      const tradeDate = trade.sell_date || trade.execution_date || trade.buy_date;
      if (!isWithinRange(tradeDate, fyStart, fyEnd)) return sum;
      return sum + toNumber(trade.realized_gain);
    }, 0);

    const currentYearIncome = currentYearSalary + currentYearOtherIncome + currentYearTradeGain;
    const currentYearExpenses = expenses.reduce((sum, expense) => {
      if (!isWithinRange(expense.transaction_date, fyStart, fyEnd)) return sum;
      return sum + toNumber(expense.amount);
    }, 0);
    const fyAverageMonthlySalary = trackedSalaryMonths > 0 ? currentYearSalary / trackedSalaryMonths : 0;
    const fyAverageMonthlyIncome = currentYearIncome / fyMonthCount;
    const fyAverageMonthlyExpenses = currentYearExpenses / fyMonthCount;
    const fyAverageMonthlySavings = (currentYearIncome - currentYearExpenses) / fyMonthCount;
    const rollingSixMonthExpenseTotal = getRollingSixMonthExpenseTotal(expenses);
    const rollingSixMonthAverageExpense = rollingSixMonthExpenseTotal / 6;
    const rollingSixMonthSalaryTotal = getRollingSixMonthSalaryTotal(salaryRanges);
    const rollingSixMonthAverageSalary = rollingSixMonthSalaryTotal / 6;

    const portfolioInvestments = investments.filter((investment) => !isInsuranceType(investment.investment_type));
    const marketInvestments = portfolioInvestments.filter((investment) => {
      const filter = getInvestmentFilter(investment);
      return filter === 'equity' || filter === 'mutual_fund' || filter === 'etf';
    });
    const tradeSnapshots = getTradeSnapshots(equityTrades);

    const fixedHoldings = portfolioInvestments.map((investment) => ({
      id: `fixed-${investment.id}`,
      name: investment.instrument_name || investment.commodity_type || investment.investment_type || 'Investment',
      kind: 'fixed',
      trackedValue: toNumber(investment.principal_amount) || toNumber(investment.quantity_units) * toNumber(investment.buy_price_per_unit),
      rate: toNumber(investment.interest_rate),
      maturityAmount: toNumber(investment.maturity_amount),
      realizedGain: 0,
      sortMetric: toNumber(investment.principal_amount),
    }));

    const activeTradeHoldings = tradeSnapshots.active.map((holding) => ({
      id: holding.id,
      name: holding.name,
      kind: 'equity',
      trackedValue: holding.currentValue,
      rate: 0,
      maturityAmount: 0,
      unrealizedGain: holding.unrealizedGain,
      trades: holding.tradeCount,
      openQuantity: holding.openQuantity,
      currentPrice: holding.currentPrice,
      averageBuyPrice: holding.averageBuyPrice,
      sortMetric: holding.currentValue || holding.unrealizedGain,
      assetClass: holding.assetClass,
    }));

    const pastTradeHoldings = tradeSnapshots.past.map((holding) => ({
      ...holding,
      sortMetric: Math.abs(holding.realizedGain),
    }));

    const activeManualMarketHoldings = marketInvestments.map((investment) => {
      const costBasis =
        toNumber(investment.quantity_units) > 0 && toNumber(investment.buy_price_per_unit) > 0
          ? toNumber(investment.quantity_units) * toNumber(investment.buy_price_per_unit)
          : toNumber(investment.principal_amount);
      const currentValue = toNumber(investment.principal_amount) || costBasis;
      return {
        id: `manual-market-${investment.id}`,
        name: investment.instrument_name || investment.commodity_type || investment.investment_type || 'Holding',
        kind: 'manual_market',
        trackedValue: currentValue,
        unrealizedGain: currentValue - costBasis,
        assetClass: getInvestmentFilterLabel(getInvestmentFilter(investment)),
        openQuantity: toNumber(investment.quantity_units),
        averageBuyPrice: toNumber(investment.buy_price_per_unit),
        currentPrice: toNumber(investment.quantity_units) > 0 ? currentValue / Math.max(1, toNumber(investment.quantity_units)) : 0,
        sortMetric: currentValue,
      };
    });

    const fixedDepositTotal = portfolioInvestments
      .filter((investment) => getInvestmentFilter(investment) === 'debt')
      .reduce((sum, investment) => sum + (toNumber(investment.principal_amount) || toNumber(investment.quantity_units) * toNumber(investment.buy_price_per_unit)), 0);
    const commodityTotal = portfolioInvestments
      .filter((investment) => getInvestmentFilter(investment) === 'commodity')
      .reduce((sum, investment) => sum + (toNumber(investment.principal_amount) || toNumber(investment.quantity_units) * toNumber(investment.buy_price_per_unit)), 0);
    const equityTotal = [...activeManualMarketHoldings, ...activeTradeHoldings].reduce((sum, item) => sum + toNumber(item.trackedValue), 0);

    const allHoldings = [...fixedHoldings, ...activeTradeHoldings];
    const totalInvestments = fixedHoldings.reduce((sum, item) => sum + item.trackedValue, 0);
    const totalPortfolioTrackedValue = allHoldings.reduce((sum, item) => sum + item.trackedValue, 0);
    const totalActiveUnrealizedGain = [...activeManualMarketHoldings, ...activeTradeHoldings].reduce((sum, item) => sum + toNumber(item.unrealizedGain), 0);
    const totalRealizedGain = pastTradeHoldings.reduce((sum, item) => sum + toNumber(item.realizedGain), 0);
    const dashboardPortfolioHoldings =
      [...activeManualMarketHoldings, ...activeTradeHoldings].length > 0
        ? [...activeManualMarketHoldings, ...activeTradeHoldings].sort((a, b) => b.sortMetric - a.sortMetric).slice(0, 2)
        : [...fixedHoldings].sort((a, b) => b.sortMetric - a.sortMetric).slice(0, 2);

    const activeLoanBreakdown = loans.filter((loan) => {
      if (!loan.end_date) return true;
      const endDate = new Date(loan.end_date);
      return Number.isNaN(endDate.getTime()) || endDate >= new Date();
    }).map((loan) => {
      const principal = toNumber(loan.principal_amount);
      const interest = toNumber(loan.interest_rate);
      const tenure = toNumber(loan.tenure_months);
      const pendingAmount = calculatePendingLoanBalance(principal, interest, tenure, loan.start_date);
      const totalInterestAmount = Math.max(0, toNumber(loan.monthly_emi) * tenure - principal);

      let completionPercentage = 0;
      if (loan.start_date && tenure > 0) {
        const start = new Date(loan.start_date);
        const now = new Date();
        if (!Number.isNaN(start.getTime())) {
          const elapsedMonths = Math.max(
            0,
            Math.min(
              tenure,
              (now.getFullYear() - start.getFullYear()) * 12 + (now.getMonth() - start.getMonth())
            )
          );
          completionPercentage = (elapsedMonths / tenure) * 100;
        }
      }

      return {
        ...loan,
        principal,
        interest,
        tenure,
        pendingAmount,
        totalInterestAmount,
        completionPercentage,
      };
    }).sort((a, b) => b.pendingAmount - a.pendingAmount);

    const totalLoanOutstanding = activeLoanBreakdown.reduce((sum, loan) => sum + loan.pendingAmount, 0);
    const totalMonthlyEmi = activeLoanBreakdown.reduce((sum, loan) => sum + toNumber(loan.monthly_emi), 0);
    const netWorth = totalPortfolioTrackedValue - totalLoanOutstanding;

    const portfolioSnapshot = buildPortfolioSnapshot(investments, equityTrades);
    const allocationData = portfolioSnapshot.allocationDetails.map((item, index) => ({
      name: item.assetClass.charAt(0).toUpperCase() + item.assetClass.slice(1),
      value: item.value,
      color: ASSET_COLORS[index % ASSET_COLORS.length],
    }));
    const allocationTotal = allocationData.reduce((sum, item) => sum + item.value, 0);

    const fyExpenses = expenses.filter((expense) => isWithinRange(expense.transaction_date, fyStart, fyEnd));
    const expenseMap = new Map<string, number>();
    fyExpenses.forEach((expense) => {
      const category = expense.category_name || expense.category || 'Other';
      expenseMap.set(category, (expenseMap.get(category) || 0) + toNumber(expense.amount));
    });
    const expenseBreakdown = Array.from(expenseMap.entries())
      .map(([name, value], index) => ({
        name,
        value,
        color: EXPENSE_COLORS[index % EXPENSE_COLORS.length],
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 5);

    const monthsToShow = Math.min(6, fyMonthCount);
    const months = Array.from({ length: monthsToShow }, (_, index) => {
      const date = new Date(fyVisibleEnd);
      date.setDate(1);
      date.setMonth(date.getMonth() - (monthsToShow - 1 - index));
      return {
        key: getMonthKey(date),
        month: monthFormatter.format(date),
        date,
      };
    });

    const monthlyTrend = months.map((month) => {
      const salary = salaryRanges.reduce((sum, salaryRange) => {
        const monthStart = new Date(month.date.getFullYear(), month.date.getMonth(), 1);
        const monthEnd = new Date(month.date.getFullYear(), month.date.getMonth() + 1, 0, 23, 59, 59, 999);
        const salaryStart = salaryRange.start!;
        const salaryEnd = salaryRange.rangeEnd || fyEnd;
        if (salaryStart > monthEnd || salaryEnd < monthStart) return sum;
        return sum + salaryRange.monthly_amount;
      }, 0);
      const otherIncome = otherIncomes.reduce((sum, income) => {
        return getMonthKey(income.date_received) === month.key ? sum + toNumber(income.amount) : sum;
      }, 0);
      const monthExpenses = expenses.reduce((sum, expense) => {
        return getMonthKey(expense.transaction_date) === month.key ? sum + toNumber(expense.amount) : sum;
      }, 0);
      const tradeGain = equityTrades.reduce((sum, trade) => {
        const tradeDate = trade.sell_date || trade.execution_date || trade.buy_date;
        return getMonthKey(tradeDate) === month.key ? sum + toNumber(trade.realized_gain) : sum;
      }, 0);

      return {
        month: month.month,
        value: salary + otherIncome + tradeGain - monthExpenses,
      };
    });

    const taxBenefitByCategory = investments.reduce((acc, investment) => {
      const category = inferTaxCategoryFromInvestment(investment);
      if (!category) return acc;
      if (!isWithinRange(getInvestmentContributionDate(investment), fyStart, fyEnd)) return acc;
      acc[category] = (acc[category] || 0) + toNumber(investment.principal_amount);
      return acc;
    }, {} as Record<string, number>);

    taxBenefits.forEach((entry) => {
      if (!isWithinRange(entry.contribution_date, fyStart, fyEnd)) return;
      taxBenefitByCategory[entry.benefit_category] = (taxBenefitByCategory[entry.benefit_category] || 0) + toNumber(entry.amount);
    });

    const fyTdsTracked = totalSalaryComponentForFy('tax_deduction');
    const fyPfTracked = totalSalaryComponentForFy('pf_deduction');
    const fyNpsTracked = totalSalaryComponentForFy('nps_deduction');
    const fyHraTracked = totalSalaryComponentForFy('hra');
    const fyProfessionalTaxTracked = totalSalaryComponentForFy('professional_tax');
    const fyOtherDeductionsTracked = totalSalaryComponentForFy('other_deductions');

    const total80CInvested = (taxBenefitByCategory['80C'] || 0) + fyPfTracked;
    const total80CCD1BInvested = (taxBenefitByCategory['80CCD(1B)'] || 0) + fyNpsTracked;
    const total80DInvested = taxBenefitByCategory['80D'] || 0;
    const totalDeductionBenefits = total80CInvested + total80CCD1BInvested + total80DInvested + fyProfessionalTaxTracked;
    const estimatedTaxableIncome = Math.max(0, currentYearIncome - totalDeductionBenefits);
    const estimatedTaxCalculated = estimateTaxByNewRegime(estimatedTaxableIncome);
    const estimatedTaxBracket = getTaxBracketLabel(estimatedTaxableIncome);

    const taxOptimizationRows = [
      {
        label: '80C invested',
        value: total80CInvested,
        status: getOptimizationStatus(total80CInvested, SECTION_80C_LIMIT),
        badgeText:
          total80CInvested >= SECTION_80C_LIMIT
            ? 'Complete'
            : total80CInvested > 0
              ? 'Partial'
              : 'Pending',
        ctaLabel: total80CInvested >= SECTION_80C_LIMIT ? '' : 'Add',
        draft: { benefitCategory: '80C', entryType: 'investment', description: '80C contribution' },
      },
      {
        label: '80C limit',
        value: SECTION_80C_LIMIT,
        status: total80CInvested >= SECTION_80C_LIMIT ? 'complete' : 'gap',
        badgeText:
          total80CInvested >= SECTION_80C_LIMIT
            ? 'No gap'
            : `${compactFormatter.format(SECTION_80C_LIMIT - total80CInvested)} gap`,
        ctaLabel: total80CInvested >= SECTION_80C_LIMIT ? '' : 'Contribute',
        draft: { benefitCategory: '80C', entryType: 'investment', description: '80C contribution' },
      },
      {
        label: '80D (health)',
        value: total80DInvested,
        status: getOptimizationStatus(total80DInvested, SECTION_80D_LIMIT),
        badgeText:
          total80DInvested >= SECTION_80D_LIMIT
            ? 'Complete'
            : total80DInvested > 0
              ? 'Partial'
              : 'Pending',
        ctaLabel: total80DInvested >= SECTION_80D_LIMIT ? '' : 'Add',
        draft: { benefitCategory: '80D', entryType: 'insurance', description: 'Health insurance premium' },
      },
      {
        label: 'HRA benefit',
        value: fyHraTracked,
        status: getOptimizationStatus(fyHraTracked),
        badgeText: fyHraTracked > 0 ? 'Claimed' : 'Not claimed',
        ctaLabel: fyHraTracked > 0 ? '' : 'Update salary',
        draft: null,
      },
    ];

    const trackedTaxRows = [
      {
        label: 'Taxable income',
        value: estimatedTaxableIncome,
        info: `Selected FY total income (${currencyFormatter.format(currentYearIncome)}) minus tracked deduction benefits (${currencyFormatter.format(totalDeductionBenefits)}). Deductions considered here: 80C, 80CCD(1B), 80D, and professional tax.`,
      },
      {
        label: 'Tax bracket',
        value: estimatedTaxBracket,
        info: `Estimated from selected FY taxable income of ${currencyFormatter.format(estimatedTaxableIncome)} using the app's current new-regime slab mapping.`,
      },
      {
        label: 'Tax collected',
        value: fyTdsTracked,
        info: `Same as tracked TDS from salary entries in ${selectedFy.label}. This comes from the tax deduction field recorded across salary history months that overlap the selected FY.`,
      },
      {
        label: 'Tax calculated',
        value: estimatedTaxCalculated,
        info: `Calculated on selected FY taxable income of ${currencyFormatter.format(estimatedTaxableIncome)} using the app's new-regime tax slab helper. This is an estimate, not a final filing value.`,
      },
      {
        label: 'TDS tracked',
        value: fyTdsTracked,
        info: `Sum of salary tax_deduction values for salary records overlapping ${selectedFy.label}.`,
      },
      {
        label: 'PF tracked',
        value: fyPfTracked,
        info: `Sum of salary PF deductions across the salary months that fall within ${selectedFy.label}. This PF amount is also counted toward 80C in tax optimisation.`,
      },
      {
        label: 'NPS tracked',
        value: fyNpsTracked,
        info: `Sum of salary NPS deductions across the salary months that fall within ${selectedFy.label}. This amount is also counted toward 80CCD(1B) in tax optimisation.`,
      },
      {
        label: 'HRA tracked',
        value: fyHraTracked,
        info: `Sum of HRA amounts from salary records overlapping ${selectedFy.label}.`,
      },
      {
        label: 'Professional tax tracked',
        value: fyProfessionalTaxTracked,
        info: `Sum of professional tax values from salary records overlapping ${selectedFy.label}. This amount is also included in the deduction total used for taxable income.`,
      },
      {
        label: 'Other deductions tracked',
        value: fyOtherDeductionsTracked,
        info: `Sum of the other_deductions field from salary records overlapping ${selectedFy.label}. This is shown for visibility but is not currently added into the taxable-income deduction total.`,
      },
      {
        label: '80C contributions',
        value: taxBenefitByCategory['80C'] || 0,
        info: `Manual or investment-linked 80C entries dated within ${selectedFy.label}, excluding PF. PF is shown separately under PF tracked and then added into the 80C total in tax optimisation.`,
      },
      {
        label: '80CCD(1B) contributions',
        value: total80CCD1BInvested,
        info: `Selected FY 80CCD(1B) entries plus tracked NPS salary deductions. Total considered here: ${currencyFormatter.format(total80CCD1BInvested)}.`,
      },
      {
        label: '80D health premiums',
        value: taxBenefitByCategory['80D'] || 0,
        info: `Tracked 80D entries dated within ${selectedFy.label}, typically health insurance premiums.`,
      },
    ].filter((row) => typeof row.value === 'string' || row.value > 0);

    const goalProgressRows = goals
      .map((goal) => {
        const targetAmount = toNumber(goal.target_amount);
        const currentAmount = toNumber(goal.current_amount);
        const progress = calculateGoalProgress(currentAmount, targetAmount);
        const displayName = goal.goal_type === 'Other' ? (goal.goal_name || 'Other goal') : goal.goal_type;
        return {
          id: goal.id,
          name: displayName,
          saved: currentAmount,
          target: targetAmount,
          progress,
          monthlyContribution: toNumber(goal.monthly_contribution),
          targetDate: goal.target_date || '',
        };
      })
      .sort((a, b) => b.progress - a.progress)
      .slice(0, 2);

    const goalGridClassName =
      goalProgressRows.length <= 1
        ? 'grid-cols-1'
        : goalProgressRows.length === 2
          ? 'md:grid-cols-2'
          : goalProgressRows.length === 3
            ? 'md:grid-cols-3'
            : 'md:grid-cols-4';

    const loanPreviewRows = activeLoanBreakdown.slice(0, 4);
    const loanGridClassName =
      loanPreviewRows.length <= 1
        ? 'grid-cols-1'
        : loanPreviewRows.length === 2
          ? 'md:grid-cols-2'
          : loanPreviewRows.length === 3
            ? 'md:grid-cols-3'
            : 'md:grid-cols-4';

    const monthlyDebtRatioPercent = fyAverageMonthlyIncome > 0 ? (totalMonthlyEmi / fyAverageMonthlyIncome) * 100 : 0;
    const savingsRateScore = clampScore(
      rollingSixMonthAverageSalary > 0
        ? (Math.max(0, rollingSixMonthAverageSalary - rollingSixMonthAverageExpense) / rollingSixMonthAverageSalary) * 100
        : 0
    );
    const debtScore = clampScore(100 - monthlyDebtRatioPercent * 2);
    const investmentCoverageScore = clampScore(currentYearIncome > 0 ? (totalPortfolioTrackedValue / currentYearIncome) * 10 : 0);
    const emergencyGoalRows = goals
      .filter((goal) => isEmergencyFundGoal(goal))
      .map((goal) => ({
        id: goal.id,
        name: goal.goal_name || goal.goal_type || 'Emergency Fund',
        currentAmount: toNumber(goal.current_amount),
        targetAmount: toNumber(goal.target_amount),
        monthlyContribution: toNumber(goal.monthly_contribution),
      }));
    const emergencyFundCurrent = emergencyGoalRows.reduce((sum, goal) => sum + goal.currentAmount, 0);
    const emergencyFundTarget = rollingSixMonthExpenseTotal;
    const emergencyFundScore = clampScore(
      emergencyFundTarget > 0 ? (emergencyFundCurrent / emergencyFundTarget) * 100 : 0
    );
    const computedHealthScore = Math.round((savingsRateScore + debtScore + investmentCoverageScore + emergencyFundScore) / 4);
    const healthScore = computedHealthScore;

    const investmentCoverageItems = [
      ...portfolioInvestments.map((investment) => ({
        id: `investment-${investment.id}`,
        name: investment.instrument_name || investment.commodity_type || investment.investment_type || 'Investment',
        amount: toNumber(investment.principal_amount) || toNumber(investment.quantity_units) * toNumber(investment.buy_price_per_unit),
        meta: investment.asset_category || 'Fixed investment',
      })),
      ...activeTradeHoldings.map((holding) => ({
        id: holding.id,
        name: holding.name,
        amount: holding.trackedValue,
        meta: `${holding.trades || 0} trade${holding.trades === 1 ? '' : 's'} uploaded`,
      })),
    ].filter((item) => item.amount > 0);

    return {
      name: userProfile.name || userProfile.email || 'User',
      initials: getInitials(userProfile.name, userProfile.email),
      monthlySalary: fyAverageMonthlySalary,
      monthlyIncome: fyAverageMonthlyIncome,
      monthlyExpenses: fyAverageMonthlyExpenses,
      monthlySavings: fyAverageMonthlySavings,
      annualSalary: currentYearSalary,
      currentYearIncome,
      currentMonthTradeGain,
      netWorth,
      totalInvestments,
      totalPortfolioTrackedValue,
      totalLoanOutstanding,
      totalMonthlyEmi,
      activeLoans: activeLoanBreakdown.length,
      totalActiveUnrealizedGain,
      totalRealizedGain,
      goals,
      loanBreakdown: activeLoanBreakdown,
      allHoldings,
      dashboardPortfolioHoldings,
      allocationData,
      allocationTotal,
      portfolioBreakdown: {
        equityTotal,
        fixedDepositTotal,
        commodityTotal,
      },
      expenseBreakdown,
      monthlyTrend,
      trackedTaxRows,
      taxOptimizationRows,
      goalProgressRows,
      goalGridClassName,
      loanPreviewRows,
      loanGridClassName,
      healthScore,
      healthScoreBreakdown: {
        savingsRateScore,
        debtScore,
        investmentCoverageScore,
        emergencyFundScore,
      },
      healthScoreDetails: {
        savings: {
          monthlyIncome: rollingSixMonthAverageSalary,
          monthlyExpenses: rollingSixMonthAverageExpense,
          monthlySavings: rollingSixMonthAverageSalary - rollingSixMonthAverageExpense,
          annualIncome: currentYearIncome,
          annualExpenses: currentYearExpenses,
        },
        debt: {
          totalMonthlyEmi,
          monthlyDebtRatioPercent,
          loans: activeLoanBreakdown.map((loan) => ({
            id: loan.id,
            name: loan.loan_type || 'Loan',
            monthlyEmi: toNumber(loan.monthly_emi),
            pendingAmount: loan.pendingAmount,
            endDate: loan.end_date || '',
          })),
        },
        investments: {
          totalPortfolioTrackedValue,
          annualIncome: currentYearIncome,
          items: investmentCoverageItems,
        },
        emergency: {
          currentAmount: emergencyFundCurrent,
          targetAmount: emergencyFundTarget,
          monthlyExpenses: rollingSixMonthAverageExpense,
          goals: emergencyGoalRows,
        },
      },
      selectedFyLabel: selectedFy.label,
      hasAnyData:
        currentYearSalary > 0 ||
        salaryHistory.length > 0 ||
        otherIncomes.length > 0 ||
        expenses.length > 0 ||
        investments.length > 0 ||
        goals.length > 0 ||
        taxBenefits.length > 0 ||
        loans.length > 0 ||
        equityTrades.length > 0,
    };
  }, [equityTrades, expenses, financialYears, goals, investments, loans, otherIncomes, salaryHistory, selectedFyId, taxBenefits, userProfile]);

  if (!data) return null;

  return (
    <div className="min-h-screen bg-[#FDFDF9] px-6 py-6">
      <div className="mx-auto max-w-7xl space-y-6 pb-40">
        <header className="flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100 text-sm font-semibold text-indigo-700">
              {data.initials}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-800">Welcome back, {data.name}</h1>
              <p className="text-sm text-slate-500">Track and update your finances across salary, investments, loans, and expenses.</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <HeaderIcon icon={<Bell className="h-4 w-4" />} />
            <HeaderIcon icon={<Clock3 className="h-4 w-4" />} />
            <button
              onClick={logout}
              className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 transition hover:border-slate-400 hover:text-slate-800"
            >
              Logout
            </button>
          </div>
        </header>

        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <NavTabs page={page} setPage={setPage} />
          <div className="flex items-center justify-end gap-3 rounded-3xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
            <span className="text-sm font-medium text-slate-500">Financial year</span>
            <select
              value={selectedFyId}
              onChange={(e) => setSelectedFyId(e.target.value)}
              className="rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-700"
            >
              {financialYears.map((fy) => (
                <option key={fy.id} value={fy.id}>{fy.label}</option>
              ))}
            </select>
          </div>
        </div>

        {page === 'overview' ? (
          <>
            {!data.hasAnyData ? (
              <section className="rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
                <h2 className="text-xl font-bold text-slate-800">No financial data yet</h2>
                <p className="mt-2 text-sm text-slate-600">
                  Use the pages above to add salaries, investments, loans, and expenses.
                </p>
              </section>
            ) : (
              <>
                <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
                  <MetricCard title="Net worth" value={data.netWorth} />
                  <MetricCard title={`${data.selectedFyLabel} avg monthly salary`} value={data.monthlySalary} />
                  <MetricCard title={`${data.selectedFyLabel} salary`} value={data.annualSalary} />
                  <MetricCard title={`${data.selectedFyLabel} total income`} value={data.currentYearIncome} />
                </section>

                <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <SmallCard label={`${data.selectedFyLabel} avg monthly expenses`} value={currencyFormatter.format(data.monthlyExpenses)} />
                  <SmallCard label={`${data.selectedFyLabel} avg monthly savings`} value={currencyFormatter.format(data.monthlySavings)} />
                </section>

                <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
                  <Card className="xl:col-span-8">
                    <div className="flex items-center justify-between">
                      <div>
                        <h2 className="text-xl font-bold text-slate-800">Net cash flow trend</h2>
                        <p className="mt-1 text-sm text-slate-500">{data.selectedFyLabel} cash flow based on tracked salary, income, expenses, and trade gains.</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <p className="text-sm font-semibold text-slate-700">{compactFormatter.format(data.netWorth)}</p>
                      </div>
                    </div>

                    <div className="mt-6 h-[300px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data.monthlyTrend} margin={{ top: 10, right: 10, left: -18, bottom: 0 }}>
                          <defs>
                            <linearGradient id="cashflow-fill" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.25} />
                              <stop offset="95%" stopColor="#6366f1" stopOpacity={0.04} />
                            </linearGradient>
                          </defs>
                          <Tooltip
                            formatter={(value: number) => currencyFormatter.format(value)}
                            contentStyle={{ borderRadius: 16, border: '1px solid #e2e8f0', boxShadow: '0 10px 30px rgba(15,23,42,0.08)' }}
                          />
                          <XAxis dataKey="month" tick={{ fontSize: 12, fill: '#64748b' }} />
                          <YAxis tickFormatter={(value) => compactFormatter.format(Number(value))} tick={{ fontSize: 12, fill: '#64748b' }} />
                          <Legend formatter={() => 'Net cash flow'} />
                          <Area
                            type="monotone"
                            dataKey="value"
                            stroke="#6366f1"
                            strokeWidth={3}
                            fill="url(#cashflow-fill)"
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </Card>

                  <Card className="xl:col-span-4">
                    <h2 className="text-xl font-bold text-slate-800">Asset allocation</h2>
                    {data.allocationData.length > 0 ? (
                      <>
                        <div className="mt-6 h-48">
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie data={data.allocationData} dataKey="value" innerRadius={52} outerRadius={72} paddingAngle={4}>
                                {data.allocationData.map((entry) => (
                                  <Cell key={entry.name} fill={entry.color} />
                                ))}
                              </Pie>
                            </PieChart>
                          </ResponsiveContainer>
                        </div>

                        <div className="space-y-3">
                          {data.allocationData.map((item) => (
                            <div key={item.name} className="flex items-center justify-between text-sm">
                              <div className="flex items-center gap-2">
                                <span className="h-3 w-3 rounded-full" style={{ backgroundColor: item.color }} />
                                <span className="text-slate-600">{item.name}</span>
                              </div>
                              <span className="font-semibold text-slate-800">
                                {Math.round((item.value / data.allocationTotal) * 100)}%
                              </span>
                            </div>
                          ))}
                        </div>
                      </>
                    ) : (
                      <EmptyState text="Add investments to see allocation." />
                    )}
                  </Card>
                </div>

                <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
                  <Card className="xl:col-span-6">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <h2 className="text-xl font-bold text-slate-800">Portfolio summary</h2>
                        <p className="mt-1 text-sm text-slate-500">Only current holdings are shown here, capped to the top 2 positions on the dashboard.</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setPage('investments')}
                        className="text-sm font-medium text-indigo-600 hover:underline"
                      >
                        View more
                      </button>
                    </div>
                    <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
                      <div className="rounded-2xl bg-slate-50 px-4 py-4">
                        <div className="flex items-center gap-2">
                          <p className="text-sm text-slate-500">Total value</p>
                          <div className="group relative">
                            <Info className="h-4 w-4 cursor-help text-slate-400" />
                            <div className="pointer-events-none absolute left-0 top-6 z-10 hidden w-72 rounded-2xl border border-slate-200 bg-white p-3 text-xs text-slate-600 shadow-lg group-hover:block">
                              <p className="font-medium text-slate-800">Portfolio value breakdown</p>
                              <div className="mt-2 space-y-2">
                                <div className="flex items-center justify-between">
                                  <span>Equity / Mutual Funds / ETFs</span>
                                  <span>{currencyFormatter.format(data.portfolioBreakdown.equityTotal)}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                  <span>FDs / Debt holdings</span>
                                  <span>{currencyFormatter.format(data.portfolioBreakdown.fixedDepositTotal)}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                  <span>Commodities</span>
                                  <span>{currencyFormatter.format(data.portfolioBreakdown.commodityTotal)}</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                        <p className="mt-2 text-2xl font-bold text-slate-800">{currencyFormatter.format(data.totalPortfolioTrackedValue)}</p>
                      </div>
                      <div className="rounded-2xl bg-slate-50 px-4 py-4">
                        <p className="text-sm text-slate-500">Unrealized gains</p>
                        <p className={`mt-2 text-2xl font-bold ${data.totalActiveUnrealizedGain >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>{currencyFormatter.format(data.totalActiveUnrealizedGain)}</p>
                      </div>
                      <div className="rounded-2xl bg-slate-50 px-4 py-4">
                        <p className="text-sm text-slate-500">Realized gain</p>
                        <p className={`mt-2 text-2xl font-bold ${data.totalRealizedGain >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>{currencyFormatter.format(data.totalRealizedGain)}</p>
                      </div>
                    </div>
                    {data.dashboardPortfolioHoldings.length > 0 ? (
                      <div className="mt-6 space-y-4">
                        {data.dashboardPortfolioHoldings.map((holding: any) => (
                          <div key={holding.id} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                            <div className="flex items-start justify-between gap-4">
                              <div>
                                <p className="font-semibold text-slate-800">{holding.name}</p>
                                <p className="text-sm text-slate-500">{holding.assetClass || 'Holding'} currently in portfolio</p>
                              </div>
                              <div className="text-right">
                                <p className="text-xs text-slate-500">Tracked value</p>
                                <p className="font-semibold text-slate-800">{currencyFormatter.format(holding.trackedValue)}</p>
                              </div>
                            </div>
                            <div className="mt-3 flex items-center justify-between text-sm">
                              <span className="text-slate-500">Unrealized gain</span>
                              <span className={`font-medium ${toNumber(holding.unrealizedGain) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>{currencyFormatter.format(toNumber(holding.unrealizedGain))}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <EmptyState text="Add or upload active holdings to see current portfolio positions here." />
                    )}
                  </Card>

                  <Card className="xl:col-span-6">
                    <div>
                      <h2 className="text-xl font-bold text-slate-800">Expense breakdown</h2>
                      <p className="mt-1 text-sm text-slate-500">{data.selectedFyLabel} spending based only on tracked entries in that year.</p>
                    </div>
                    {data.expenseBreakdown.length > 0 ? (
                      <div className="mt-6 space-y-4">
                        {data.expenseBreakdown.map((item, index) => {
                          const maxValue = data.expenseBreakdown[0]?.value || 1;
                          const width = (item.value / maxValue) * 100;
                          return (
                            <div key={item.name} className="grid grid-cols-[1fr_120px] items-center gap-4">
                              <div>
                                <div className="flex items-center justify-between text-sm">
                                  <span className="font-medium text-slate-700">{item.name}</span>
                                </div>
                                <div className="mt-2 h-2 rounded-full bg-slate-100">
                                  <div
                                    className="h-2 rounded-full"
                                    style={{ width: `${width}%`, backgroundColor: item.color || EXPENSE_COLORS[index % EXPENSE_COLORS.length] }}
                                  />
                                </div>
                              </div>
                              <span className="text-right font-semibold text-slate-800">
                                {currencyFormatter.format(item.value)}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <EmptyState text="Add expenses to see category-wise spending." />
                    )}
                  </Card>
                </div>

                <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
                  <Card className="xl:col-span-6">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <h2 className="text-xl font-bold text-slate-800">Goals ({goals.length})</h2>
                        <p className="mt-1 text-sm text-slate-500">
                          {goals.length > 2
                            ? `${goals.length} goals tracked. Showing the first 2 here.`
                            : 'Track your top savings targets and how far along you are.'}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setPage('goals')}
                        className="text-sm font-medium text-indigo-600 hover:underline"
                      >
                        View more
                      </button>
                    </div>
                    {data.goalProgressRows.length > 0 ? (
                      <div className="mt-6 space-y-4">
                        {data.goalProgressRows.map((goal: any) => (
                          <div key={goal.id} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                            <div className="flex items-start justify-between gap-4">
                              <div>
                                <p className="font-semibold text-slate-800">{goal.name}</p>
                                <p className="text-sm text-slate-500">
                                  {currencyFormatter.format(goal.saved)} of {currencyFormatter.format(goal.target)}
                                </p>
                              </div>
                              <div className="text-right">
                                <p className="text-xs text-slate-500">Progress</p>
                                <p className="font-semibold text-slate-800">{Math.round(goal.progress)}%</p>
                              </div>
                            </div>
                            <div className="mt-3 h-2 rounded-full bg-slate-100">
                              <div className="h-2 rounded-full bg-indigo-600" style={{ width: `${goal.progress}%` }} />
                            </div>
                            <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                              <span>{goal.monthlyContribution > 0 ? `${currencyFormatter.format(goal.monthlyContribution)}/mo` : 'No monthly contribution yet'}</span>
                              <span>{goal.targetDate ? `Target ${goal.targetDate}` : 'No target date'}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <EmptyState text="Add goals to track your progress here." />
                    )}
                  </Card>

                  <Card className="xl:col-span-6">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <h2 className="text-xl font-bold text-slate-800">Health score</h2>
                        <p className="mt-1 text-sm text-slate-500">Based on the goal-planning scoring categories already defined in the agent.</p>
                      </div>
                      <div className="text-right">
                        <p className="text-3xl font-bold text-slate-800">{Math.round(data.healthScore)}/100</p>
                      </div>
                    </div>
                    <div className="mt-6 space-y-4">
                      {([
                        { id: 'savings', label: 'Savings', value: data.healthScoreBreakdown.savingsRateScore, color: '#10b981' },
                        { id: 'debt', label: 'Debt', value: data.healthScoreBreakdown.debtScore, color: '#f59e0b' },
                        { id: 'investments', label: 'Investments', value: data.healthScoreBreakdown.investmentCoverageScore, color: '#6366f1' },
                        { id: 'emergency', label: 'Emergency', value: data.healthScoreBreakdown.emergencyFundScore, color: '#ef4444' },
                      ] as const).map((item) => (
                        <div key={item.label} className="space-y-3">
                          <div className="grid grid-cols-[120px_1fr_88px] items-center gap-4">
                            <button
                              type="button"
                              onClick={() => setActiveHealthInfo((current) => current === item.id ? null : item.id)}
                              className="inline-flex items-center gap-1 text-left text-sm font-medium text-slate-700 hover:text-slate-900"
                            >
                              <span>{item.label}</span>
                              <Info className="h-4 w-4 text-slate-400" />
                            </button>
                            <div className="h-2 rounded-full bg-slate-100">
                              <div
                                className="h-2 rounded-full"
                                style={{ width: `${Math.max(0, Math.min(100, item.value))}%`, backgroundColor: item.color }}
                              />
                            </div>
                            <span className="text-right text-sm font-semibold text-slate-800">{Math.round(item.value)}</span>
                          </div>
                          {activeHealthInfo === item.id ? (
                            <HealthInfoPanel
                              kind={item.id}
                              details={data.healthScoreDetails}
                            />
                          ) : null}
                        </div>
                      ))}
                    </div>
                  </Card>
                </div>

                <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
                  <Card className="xl:col-span-6">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <h2 className="text-xl font-bold text-slate-800">Tax optimisation</h2>
                        <p className="mt-1 text-sm text-slate-500">{data.selectedFyLabel} view of key deduction buckets and remaining room.</p>
                      </div>
                    </div>
                    <div className="mt-6 space-y-4">
                      {data.taxOptimizationRows.map((row) => (
                        <div key={row.label} className="flex items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                          <div>
                            <p className="text-sm font-medium text-slate-700">{row.label}</p>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-sm font-semibold text-slate-800">{currencyFormatter.format(row.value)}</span>
                            <StatusBadge status={row.status} text={row.badgeText} />
                            {row.ctaLabel ? (
                              <button
                                type="button"
                                onClick={() => {
                                  if (row.label === 'HRA benefit') {
                                    setPage('salary');
                                    return;
                                  }
                                  if (row.draft) {
                                    setTaxBenefitDraft(row.draft);
                                    setPage('tax');
                                  }
                                }}
                                className="rounded-lg border border-indigo-200 px-3 py-1.5 text-xs font-semibold text-indigo-700 transition hover:border-indigo-300 hover:bg-indigo-50"
                              >
                                {row.ctaLabel}
                              </button>
                            ) : null}
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>

                  <Card className="xl:col-span-6">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <h2 className="text-xl font-bold text-slate-800">Tracked tax and deductions</h2>
                        <p className="mt-1 text-sm text-slate-500">{data.selectedFyLabel} totals across salary entries and tax-saving investments.</p>
                      </div>
                    </div>
                    {data.trackedTaxRows.length > 0 ? (
                      <div className="mt-6 space-y-4">
                        {data.trackedTaxRows.map((row) => (
                          <div key={row.label} className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3 text-sm">
                            <div className="flex items-center gap-2">
                              <span className="text-slate-600">{row.label}</span>
                              <div className="group relative">
                                <Info className="h-4 w-4 cursor-help text-slate-400" />
                                <div className="pointer-events-none absolute left-0 top-6 z-10 hidden w-80 rounded-2xl border border-slate-200 bg-white p-3 text-xs text-slate-600 shadow-lg group-hover:block">
                                  {row.info}
                                </div>
                              </div>
                            </div>
                            <span className="font-semibold text-slate-800">
                              {typeof row.value === 'number' ? currencyFormatter.format(row.value) : row.value}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <EmptyState text="Salary deduction details will appear here once tracked in onboarding." />
                    )}
                  </Card>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  <SmallCard label="Active loans tracked" value={String(data.activeLoans)} />
                  <SmallCard label="Loan outstanding tracked" value={currencyFormatter.format(data.totalLoanOutstanding)} />
                  <SmallCard label="Total monthly EMI" value={currencyFormatter.format(data.totalMonthlyEmi)} />
                </div>

                <Card>
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <h2 className="text-xl font-bold text-slate-800">Active loans ({data.loanBreakdown.length})</h2>
                      <p className="mt-1 text-sm text-slate-500">
                        {data.loanBreakdown.length > 4
                          ? `${data.loanBreakdown.length} active loans tracked. Showing the first 4 here.`
                          : 'Track pending balances, EMI, and completion percentage.'}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setPage('loans')}
                      className="text-sm font-medium text-indigo-600 hover:underline"
                    >
                      View more
                    </button>
                  </div>
                  {data.loanPreviewRows.length > 0 ? (
                    <div className="mt-6 space-y-4">
                      {data.loanPreviewRows.map((loan: any, index: number) => (
                        <div key={loan.id} className="grid grid-cols-[1fr_140px] items-center gap-4">
                          <div>
                            <div className="flex items-center justify-between text-sm">
                              <span className="font-medium text-slate-700">{loan.loan_type}</span>
                              <span className="text-slate-500">{loan.interest}% interest</span>
                            </div>
                            <div className="mt-2 h-2 rounded-full bg-slate-100">
                              <div
                                className="h-2 rounded-full"
                                style={{ width: `${Math.max(0, Math.min(100, loan.completionPercentage))}%`, backgroundColor: EXPENSE_COLORS[index % EXPENSE_COLORS.length] }}
                              />
                            </div>
                            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                              <span>EMI {currencyFormatter.format(toNumber(loan.monthly_emi))}</span>
                              <span>Start {loan.start_date || '--'}</span>
                              <span>End {loan.end_date || '--'}</span>
                            </div>
                            <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                              <span>Interest amount {currencyFormatter.format(Math.round(loan.totalInterestAmount || 0))}</span>
                              <span>{Math.round(loan.completionPercentage || 0)}% completed</span>
                            </div>
                          </div>
                          <span className="text-right font-semibold text-slate-800">
                            {currencyFormatter.format(Math.round(loan.pendingAmount))}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState text="Add loans to track pending balances, EMI, and completion percentage." />
                  )}
                </Card>
              </>
            )}
          </>
        ) : null}

        {page === 'salary' ? <SalaryPage salaryHistory={salaryHistory} refreshProfile={refreshProfile} /> : null}
        {page === 'investments' ? <InvestmentsPage investments={investments} equityTrades={equityTrades} refreshProfile={refreshProfile} /> : null}
        {page === 'goals' ? <GoalsPage goals={goals} refreshProfile={refreshProfile} /> : null}
        {page === 'tax' ? (
          <TaxBenefitsPage
            taxBenefits={taxBenefits}
            refreshProfile={refreshProfile}
            taxBenefitDraft={taxBenefitDraft}
            clearTaxBenefitDraft={() => setTaxBenefitDraft(null)}
            selectedFy={financialYears.find((fy) => fy.id === selectedFyId) || financialYears[0]}
          />
        ) : null}
        {page === 'loans' ? <LoansPage loans={loans} refreshProfile={refreshProfile} /> : null}
        {page === 'expenses' ? <ExpensesPage expenses={expenses} refreshProfile={refreshProfile} /> : null}
      </div>

      <AIChat />
    </div>
  );
}

function NavTabs({
  page,
  setPage,
}: {
  page: DashboardPage;
  setPage: (page: DashboardPage) => void;
}) {
  const tabs: Array<{ id: DashboardPage; label: string }> = [
    { id: 'overview', label: 'Overview' },
    { id: 'salary', label: 'Salary' },
    { id: 'investments', label: 'Investments' },
    { id: 'goals', label: 'Goals' },
    { id: 'tax', label: 'Tax Benefits' },
    { id: 'loans', label: 'Loans' },
    { id: 'expenses', label: 'Expenses' },
  ];

  return (
    <div className="flex flex-wrap gap-2 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => setPage(tab.id)}
          className={`rounded-full px-4 py-2 text-sm font-medium transition ${
            page === tab.id
              ? 'bg-indigo-600 text-white'
              : 'border border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:text-slate-800'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

function StatusBadge({
  status,
  text,
}: {
  status: 'complete' | 'partial' | 'claimed' | 'gap' | 'pending';
  text: string;
}) {
  const styles = {
    complete: 'bg-emerald-50 text-emerald-700',
    claimed: 'bg-emerald-50 text-emerald-700',
    partial: 'bg-amber-50 text-amber-700',
    gap: 'bg-rose-50 text-rose-700',
    pending: 'bg-slate-100 text-slate-600',
  };

  return (
    <span className={`rounded-lg px-2.5 py-1 text-xs font-semibold ${styles[status]}`}>
      {text}
    </span>
  );
}

function SalaryPage({
  salaryHistory,
  refreshProfile,
}: {
  salaryHistory: any[];
  refreshProfile: () => Promise<void>;
}) {
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [salary, setSalary] = useState({
    employerName: '',
    effectiveFrom: '',
    effectiveTo: '',
    monthlyAmount: '',
    grossMonthly: '',
    basicSalary: '',
    hra: '',
    specialAllowance: '',
    lta: '',
    taxDeduction: '',
    pfDeduction: '',
    npsDeduction: '',
    professionalTax: '',
    otherDeductions: '',
  });
  const pagedSalaries = salaryHistory.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const save = async () => {
    try {
      setSaving(true);
      setStatus('');
      const payload = {
        employer_name: salary.employerName || 'Current Employer',
        effective_from: salary.effectiveFrom || new Date().toISOString().split('T')[0],
        effective_to: salary.effectiveTo || null,
        monthly_amount: Number(salary.monthlyAmount) || 0,
        gross_monthly: Number(salary.grossMonthly) || null,
        basic_salary: Number(salary.basicSalary) || null,
        hra: Number(salary.hra) || null,
        special_allowance: Number(salary.specialAllowance) || null,
        lta: Number(salary.lta) || null,
        tax_deduction: Number(salary.taxDeduction) || null,
        pf_deduction: Number(salary.pfDeduction) || null,
        nps_deduction: Number(salary.npsDeduction) || null,
        professional_tax: Number(salary.professionalTax) || null,
        other_deductions: Number(salary.otherDeductions) || null,
      };
      if (editingId) {
        await apiClient.updateSalary(editingId, payload);
      } else {
        await apiClient.addSalary(payload);
      }
      setSalary({
        employerName: '',
        effectiveFrom: '',
        effectiveTo: '',
        monthlyAmount: '',
        grossMonthly: '',
        basicSalary: '',
        hra: '',
        specialAllowance: '',
        lta: '',
        taxDeduction: '',
        pfDeduction: '',
        npsDeduction: '',
        professionalTax: '',
        otherDeductions: '',
      });
      setEditingId(null);
      await refreshProfile();
      setStatus(editingId ? 'Salary updated.' : 'Salary added.');
    } catch (error: any) {
      setStatus(error.message || 'Failed to save salary.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
      <Card className="xl:col-span-7">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-slate-800">Salary history</h2>
          {status ? <span className="text-sm text-indigo-600">{status}</span> : null}
        </div>
        {salaryHistory.length > 0 ? (
          <div className="mt-6 space-y-4">
            {pagedSalaries.map((salary) => (
              <div key={salary.id} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-semibold text-slate-800">{salary.employer_name || 'Employer'}</p>
                    <p className="text-sm text-slate-500">From {salary.effective_from || '--'} {salary.effective_to ? `to ${salary.effective_to}` : ''}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500">Monthly salary</p>
                    <p className="font-semibold text-slate-800">{currencyFormatter.format(toNumber(salary.monthly_amount))}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setEditingId(salary.id);
                    setSalary({
                      employerName: salary.employer_name || '',
                      effectiveFrom: salary.effective_from || '',
                      effectiveTo: salary.effective_to || '',
                      monthlyAmount: String(toNumber(salary.monthly_amount) || ''),
                      grossMonthly: String(toNumber(salary.gross_monthly) || ''),
                      basicSalary: String(toNumber(salary.basic_salary) || ''),
                      hra: String(toNumber(salary.hra) || ''),
                      specialAllowance: String(toNumber(salary.special_allowance) || ''),
                      lta: String(toNumber(salary.lta) || ''),
                      taxDeduction: String(toNumber(salary.tax_deduction) || ''),
                      pfDeduction: String(toNumber(salary.pf_deduction) || ''),
                      npsDeduction: String(toNumber(salary.nps_deduction) || ''),
                      professionalTax: String(toNumber(salary.professional_tax) || ''),
                      otherDeductions: String(toNumber(salary.other_deductions) || ''),
                    });
                  }}
                  className="mt-3 text-sm font-medium text-indigo-600 hover:underline"
                >
                  Edit
                </button>
              </div>
            ))}
            <PaginationControls total={salaryHistory.length} page={page} setPage={setPage} />
          </div>
        ) : (
          <EmptyState text="No salary history added yet." />
        )}
      </Card>

      <Card className="xl:col-span-5">
        <h2 className="text-xl font-bold text-slate-800">{editingId ? 'Edit salary' : 'Add salary'}</h2>
        <div className="mt-6 space-y-4">
          <input value={salary.employerName} onChange={(e) => setSalary({ ...salary, employerName: e.target.value })} placeholder="Employer name" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <input type="date" value={salary.effectiveFrom} onChange={(e) => setSalary({ ...salary, effectiveFrom: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <input type="date" value={salary.effectiveTo} onChange={(e) => setSalary({ ...salary, effectiveTo: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <input type="number" value={salary.monthlyAmount} onChange={(e) => setSalary({ ...salary, monthlyAmount: e.target.value })} placeholder="Monthly net salary" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <input type="number" value={salary.grossMonthly} onChange={(e) => setSalary({ ...salary, grossMonthly: e.target.value })} placeholder="Monthly gross salary" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <input type="number" value={salary.basicSalary} onChange={(e) => setSalary({ ...salary, basicSalary: e.target.value })} placeholder="Basic salary" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <input type="number" value={salary.hra} onChange={(e) => setSalary({ ...salary, hra: e.target.value })} placeholder="HRA" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <input type="number" value={salary.taxDeduction} onChange={(e) => setSalary({ ...salary, taxDeduction: e.target.value })} placeholder="Tax deducted" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <input type="number" value={salary.pfDeduction} onChange={(e) => setSalary({ ...salary, pfDeduction: e.target.value })} placeholder="PF deduction" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <ActionButton loading={saving} onClick={save}>Save salary</ActionButton>
        </div>
      </Card>
    </div>
  );
}

function InvestmentsPage({
  investments,
  equityTrades,
  refreshProfile,
}: {
  investments: any[];
  equityTrades: any[];
  refreshProfile: () => Promise<void>;
}) {
  const [saving, setSaving] = useState<string | null>(null);
  const [status, setStatus] = useState('');
  const [mode, setMode] = useState<'none' | 'fd' | 'trades'>('none');
  const [filter, setFilter] = useState<InvestmentFilter>('debt');
  const [page, setPage] = useState(1);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [investment, setInvestment] = useState({
    type: 'Fixed Deposit',
    instrumentName: '',
    assetCategory: 'Debt',
    commodityType: 'Gold',
    principal: '',
    rate: '',
    quantityUnits: '',
    buyPricePerUnit: '',
    startDate: '',
    purchaseDate: '',
    tenureMonths: '',
    taxExemptionCategory: '',
  });
  const portfolioInvestments = investments.filter((item) => !isInsuranceType(item.investment_type));
  const filteredInvestments = portfolioInvestments.filter((item) => getInvestmentFilter(item) === filter);
  const tradeSnapshots = getTradeSnapshots(equityTrades.filter((trade) => getTradeFilter(trade) === filter));
  const activeTradeRecords = tradeSnapshots.active;
  const pastTradeRecords = tradeSnapshots.past;
  const combinedRecords = [
    ...filteredInvestments.map((item) => ({ kind: 'investment' as const, item })),
    ...activeTradeRecords.map((item) => ({ kind: 'active_trade' as const, item })),
    ...pastTradeRecords.map((item) => ({ kind: 'past_trade' as const, item })),
  ];
  const pagedRecords = combinedRecords.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const isCommodity = investment.type === 'Commodity';
  const isMarketBased = ['Equity', 'Mutual Fund', 'ETF'].includes(investment.type);

  const saveInvestment = async () => {
    try {
      setSaving('investment');
      setStatus('');
      const derivedPrincipal = (isCommodity || isMarketBased)
        ? (Number(investment.quantityUnits) || 0) * (Number(investment.buyPricePerUnit) || 0)
        : Number(investment.principal) || 0;
      const startDate = (isCommodity || isMarketBased) ? (investment.purchaseDate || investment.startDate) : investment.startDate;
      const maturityDate = (isCommodity || isMarketBased) ? null : addMonthsToDate(investment.startDate, Number(investment.tenureMonths));
      const maturityAmount = (isCommodity || isMarketBased) ? null : calculateFdMaturityAmount(derivedPrincipal, Number(investment.rate), Number(investment.tenureMonths));
      const payload = {
        investment_type: investment.type,
        instrument_name: isMarketBased ? investment.instrumentName || null : null,
        asset_category: isCommodity ? 'Commodity' : isMarketBased ? investment.type : investment.assetCategory,
        commodity_type: isCommodity ? investment.commodityType : null,
        principal_amount: derivedPrincipal,
        interest_rate: (isCommodity || isMarketBased) ? 0 : Number(investment.rate) || 0,
        quantity_units: (isCommodity || isMarketBased) ? Number(investment.quantityUnits) || 0 : null,
        buy_price_per_unit: (isCommodity || isMarketBased) ? Number(investment.buyPricePerUnit) || 0 : null,
        start_date: startDate,
        purchase_date: (isCommodity || isMarketBased) ? startDate : null,
        maturity_date: maturityDate,
        tenure_months: (isCommodity || isMarketBased) ? null : Number(investment.tenureMonths) || 0,
        maturity_amount: maturityAmount,
        tax_exemption_category: investment.taxExemptionCategory || null,
      };
      if (editingId) {
        await apiClient.updateInvestment(editingId, payload);
      } else {
        await apiClient.addInvestment(payload);
      }
      setInvestment({
        type: 'Fixed Deposit',
        instrumentName: '',
        assetCategory: 'Debt',
        commodityType: 'Gold',
        principal: '',
        rate: '',
        quantityUnits: '',
        buyPricePerUnit: '',
        startDate: '',
        purchaseDate: '',
        tenureMonths: '',
        taxExemptionCategory: '',
      });
      setEditingId(null);
      await refreshProfile();
      setStatus(editingId ? 'Investment updated.' : 'Investment added.');
    } catch (error: any) {
      setStatus(error.message || 'Failed to save investment.');
    } finally {
      setSaving(null);
    }
  };

  const uploadTrades = async (file: File) => {
    try {
      setSaving('trades');
      setStatus('');
      const trades = await parseEquityPL(file);
      const results = await Promise.all(trades.map((trade) => apiClient.addTrade(buildTradePayloadFromParsedTrade({
        ...trade,
        asset_class: trade.asset_class || getTradeAssetClass(trade),
      }))));
      const inserted = results.filter((result) => result?.action === 'inserted').length;
      const updated = results.filter((result) => result?.action === 'updated').length;
      await refreshProfile();
      setStatus(`P&L uploaded. ${inserted} new rows added, ${updated} matching rows refreshed.`);
    } catch (error: any) {
      setStatus(error.message || 'Failed to upload P&L.');
    } finally {
      setSaving(null);
    }
  };

  const deleteInvestment = async (id: number) => {
    try {
      setSaving(`delete-investment-${id}`);
      setStatus('');
      await apiClient.deleteInvestment(id);
      if (editingId === id) {
        setEditingId(null);
        setInvestment({
          type: 'Fixed Deposit',
          instrumentName: '',
          assetCategory: 'Debt',
          commodityType: 'Gold',
          principal: '',
          rate: '',
          quantityUnits: '',
          buyPricePerUnit: '',
          startDate: '',
          purchaseDate: '',
          tenureMonths: '',
          taxExemptionCategory: '',
        });
      }
      await refreshProfile();
      setStatus('Investment deleted.');
    } catch (error: any) {
      setStatus(error.message || 'Failed to delete investment.');
    } finally {
      setSaving(null);
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
      <Card className="xl:col-span-7">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-slate-800">All investments</h2>
          {status ? <span className="text-sm text-indigo-600">{status}</span> : null}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {INVESTMENT_FILTERS.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => {
                setFilter(item);
                setPage(1);
              }}
              className={`rounded-full px-4 py-2 text-sm font-medium ${
                filter === item ? 'bg-indigo-600 text-white' : 'border border-slate-200 bg-white text-slate-600'
              }`}
            >
              {getInvestmentFilterLabel(item)}
            </button>
          ))}
        </div>
        <div className="mt-6 space-y-4">
          {pagedRecords.map((record) => record.kind === 'investment' ? (
            <div key={`fixed-${record.item.id}`} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                  <p className="font-semibold text-slate-800">{record.item.instrument_name || record.item.commodity_type || record.item.investment_type}</p>
                  <p className="text-sm text-slate-500">
                    {record.item.investment_type === 'Commodity'
                      ? `${record.item.commodity_type || 'Commodity'} • Total value ${currencyFormatter.format(toNumber(record.item.principal_amount))}`
                      : ['Equity', 'Mutual Fund', 'ETF'].includes(record.item.investment_type)
                        ? `${record.item.investment_type} • ${toNumber(record.item.quantity_units)} units at ${currencyFormatter.format(toNumber(record.item.buy_price_per_unit))}`
                      : `${toNumber(record.item.interest_rate)}% interest`}
                  </p>
                  {(record.item.investment_type === 'Commodity' || ['Equity', 'Mutual Fund', 'ETF'].includes(record.item.investment_type)) && toNumber(record.item.quantity_units) > 0 && toNumber(record.item.buy_price_per_unit) > 0 ? (
                    <p className="mt-1 text-xs text-slate-500">
                      {toNumber(record.item.quantity_units)} units at {currencyFormatter.format(toNumber(record.item.buy_price_per_unit))}
                    </p>
                  ) : null}
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500">Tracked value</p>
                  <p className="font-semibold text-slate-800">{currencyFormatter.format(toNumber(record.item.principal_amount))}</p>
                </div>
              </div>
              <div className="mt-3 flex items-center gap-4">
                <button
                  type="button"
                  onClick={() => {
                    setMode('fd');
                    setEditingId(record.item.id);
                    setInvestment({
                      type: record.item.investment_type || 'Fixed Deposit',
                      instrumentName: record.item.instrument_name || '',
                      assetCategory: record.item.asset_category || 'Debt',
                      commodityType: record.item.commodity_type || 'Gold',
                      principal: String(toNumber(record.item.principal_amount) || ''),
                      rate: String(toNumber(record.item.interest_rate) || ''),
                      quantityUnits: String(toNumber(record.item.quantity_units) || ''),
                      buyPricePerUnit: String(toNumber(record.item.buy_price_per_unit) || ''),
                      startDate: record.item.start_date || '',
                      purchaseDate: record.item.purchase_date || '',
                      tenureMonths: String(toNumber(record.item.tenure_months) || ''),
                      taxExemptionCategory: record.item.tax_exemption_category || '',
                    });
                  }}
                  className="text-sm font-medium text-indigo-600 hover:underline"
                >
                  Edit
                </button>
                <button
                  type="button"
                  onClick={() => {
                    if (window.confirm('Delete this investment?')) void deleteInvestment(record.item.id);
                  }}
                  disabled={saving === `delete-investment-${record.item.id}`}
                  className="inline-flex items-center gap-1 text-sm font-medium text-rose-600 hover:underline disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete
                </button>
              </div>
            </div>
          ) : record.kind === 'active_trade' ? (
            <div key={`trade-active-${record.item.id}`} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-semibold text-slate-800">{record.item.name}</p>
                  <p className="text-sm text-slate-500">{record.item.assetClass} • Active holding</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {toNumber(record.item.openQuantity)} units at {currencyFormatter.format(toNumber(record.item.currentPrice))}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500">Unrealized gain</p>
                  <p className={`font-semibold ${toNumber(record.item.unrealizedGain) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                    {currencyFormatter.format(toNumber(record.item.unrealizedGain))}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div key={`trade-past-${record.item.id}`} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-semibold text-slate-800">{record.item.name}</p>
                  <p className="text-sm text-slate-500">{record.item.assetClass} • Past holding</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {toNumber(record.item.soldQuantity)} units exited
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500">Realized gain</p>
                  <p className={`font-semibold ${toNumber(record.item.realizedGain) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                    {currencyFormatter.format(toNumber(record.item.realizedGain))}
                  </p>
                </div>
              </div>
            </div>
          ))}
          {combinedRecords.length === 0 ? <EmptyState text={`No ${getInvestmentFilterLabel(filter).toLowerCase()} investments added yet.`} /> : <PaginationControls total={combinedRecords.length} page={page} setPage={setPage} />}
        </div>
      </Card>

      <Card className="xl:col-span-5">
        <h2 className="text-xl font-bold text-slate-800">Add investment</h2>
        <div className="mt-6 flex flex-wrap gap-2">
          <button type="button" onClick={() => setMode('fd')} className={`rounded-full px-4 py-2 text-sm font-medium ${mode === 'fd' ? 'bg-indigo-600 text-white' : 'border border-slate-200 bg-white text-slate-600'}`}>Add FD / investment</button>
          <button type="button" onClick={() => setMode('trades')} className={`rounded-full px-4 py-2 text-sm font-medium ${mode === 'trades' ? 'bg-indigo-600 text-white' : 'border border-slate-200 bg-white text-slate-600'}`}>Upload P&amp;L</button>
        </div>

        {mode === 'fd' ? (
          <div className="mt-6 space-y-4">
            <select value={investment.type} onChange={(e) => setInvestment({ ...investment, type: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2">
              {['Fixed Deposit', 'Equity', 'Mutual Fund', 'ETF', 'Commodity', 'PPF', 'NSC', 'NPS', 'Real Estate', 'Other'].map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
            {isCommodity ? (
              <>
                <select value={investment.commodityType} onChange={(e) => setInvestment({ ...investment, commodityType: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2">
                  {['Gold', 'Silver', 'Crude Oil', 'Copper', 'Other Commodity'].map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
                <input type="number" value={investment.quantityUnits} onChange={(e) => setInvestment({ ...investment, quantityUnits: e.target.value })} placeholder="Quantity / units" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
                <input type="number" value={investment.buyPricePerUnit} onChange={(e) => setInvestment({ ...investment, buyPricePerUnit: e.target.value })} placeholder="Buy price per unit" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
                <input type="date" value={investment.purchaseDate} onChange={(e) => setInvestment({ ...investment, purchaseDate: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2" />
                <div className="rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
                  Tracked value: {currencyFormatter.format((Number(investment.quantityUnits) || 0) * (Number(investment.buyPricePerUnit) || 0))}
                </div>
              </>
            ) : isMarketBased ? (
              <>
                <input value={investment.instrumentName} onChange={(e) => setInvestment({ ...investment, instrumentName: e.target.value })} placeholder={`${investment.type} name`} className="w-full rounded-xl border border-slate-300 px-3 py-2" />
                <input type="number" value={investment.buyPricePerUnit} onChange={(e) => setInvestment({ ...investment, buyPricePerUnit: e.target.value })} placeholder="Average buy value per unit" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
                <input type="number" value={investment.quantityUnits} onChange={(e) => setInvestment({ ...investment, quantityUnits: e.target.value })} placeholder="Quantity / units" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
                <input type="date" value={investment.purchaseDate} onChange={(e) => setInvestment({ ...investment, purchaseDate: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2" />
                <div className="rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
                  Total invested value: {currencyFormatter.format((Number(investment.quantityUnits) || 0) * (Number(investment.buyPricePerUnit) || 0))}
                </div>
              </>
            ) : (
              <>
                <input type="number" value={investment.principal} onChange={(e) => setInvestment({ ...investment, principal: e.target.value })} placeholder="Principal amount" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
                <input type="number" value={investment.rate} onChange={(e) => setInvestment({ ...investment, rate: e.target.value })} placeholder="Interest rate %" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
                <input type="date" value={investment.startDate} onChange={(e) => setInvestment({ ...investment, startDate: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2" />
                <input type="number" value={investment.tenureMonths} onChange={(e) => setInvestment({ ...investment, tenureMonths: e.target.value })} placeholder="Tenure (months)" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
              </>
            )}
            <select value={investment.taxExemptionCategory} onChange={(e) => setInvestment({ ...investment, taxExemptionCategory: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2">
              <option value="">No tax benefit</option>
              <option value="80C">80C</option>
              <option value="80CCD(1B)">80CCD(1B)</option>
            </select>
            <ActionButton loading={saving === 'investment'} onClick={saveInvestment}>Save investment</ActionButton>
          </div>
        ) : null}

        {mode === 'trades' ? (
          <div className="mt-6 space-y-3">
            <label className="flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-dashed border-slate-300 px-4 py-4 text-sm text-slate-600 hover:bg-slate-50">
              <Upload className="h-4 w-4" />
              Upload P&amp;L file
              <input
                type="file"
                className="hidden"
                accept=".pdf,.csv,.xls,.xlsx"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) void uploadTrades(file);
                  e.currentTarget.value = '';
                }}
              />
            </label>
            <p className="text-xs text-slate-500">
              Multiple statement uploads are supported. Matching trades are refreshed instead of duplicated, and active holdings keep their latest uploaded market price when available.
            </p>
          </div>
        ) : null}

        {mode === 'none' ? <p className="mt-6 text-sm text-slate-500">Choose an action above to add a fixed investment or upload a P&amp;L statement.</p> : null}
      </Card>
    </div>
  );
}

function GoalsPage({
  goals,
  refreshProfile,
}: {
  goals: any[];
  refreshProfile: () => Promise<void>;
}) {
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [goal, setGoal] = useState({
    goalName: '',
    goalType: 'Home',
    targetAmount: '',
    currentAmount: '',
    targetDate: '',
    monthlyContribution: '',
    notes: '',
  });
  const pagedGoals = goals.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const requiresCustomGoalName = goal.goalType === 'Other';

  useEffect(() => {
    if (goal.goalType !== 'Other' && goal.goalName) {
      setGoal((current) => ({ ...current, goalName: '' }));
    }
  }, [goal.goalName, goal.goalType]);

  const saveGoal = async () => {
    try {
      setSaving(true);
      setStatus('');
      const payload = {
        goal_name: requiresCustomGoalName ? goal.goalName : goal.goalType,
        goal_type: goal.goalType,
        target_amount: Number(goal.targetAmount) || 0,
        current_amount: Number(goal.currentAmount) || 0,
        target_date: goal.targetDate || null,
        monthly_contribution: Number(goal.monthlyContribution) || 0,
        notes: goal.notes || null,
      };
      if (editingId) {
        await apiClient.updateGoal(editingId, payload);
      } else {
        await apiClient.addGoal(payload);
      }
      setGoal({
        goalName: '',
        goalType: 'Home',
        targetAmount: '',
        currentAmount: '',
        targetDate: '',
        monthlyContribution: '',
        notes: '',
      });
      setEditingId(null);
      await refreshProfile();
      setStatus(editingId ? 'Goal updated.' : 'Goal added.');
    } catch (error: any) {
      setStatus(error.message || 'Failed to save goal.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
      <Card className="xl:col-span-7">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-slate-800">Goals</h2>
          {status ? <span className="text-sm text-indigo-600">{status}</span> : null}
        </div>
        {goals.length > 0 ? (
          <div className="mt-6 space-y-4">
            {pagedGoals.map((item) => {
              const progress = calculateGoalProgress(toNumber(item.current_amount), toNumber(item.target_amount));
              return (
                <div key={item.id} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-semibold text-slate-800">{item.goal_name}</p>
                      <p className="text-sm text-slate-500">{item.goal_type}</p>
                      <p className="mt-1 text-xs text-slate-500">Target {item.target_date || '--'}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-slate-500">Progress</p>
                      <p className="font-semibold text-slate-800">{Math.round(progress)}%</p>
                    </div>
                  </div>
                  <div className="mt-3 h-2 rounded-full bg-slate-100">
                    <div className="h-2 rounded-full bg-indigo-600" style={{ width: `${progress}%` }} />
                  </div>
                  <div className="mt-3 flex items-center justify-between text-sm text-slate-600">
                    <span>{currencyFormatter.format(toNumber(item.current_amount))} saved</span>
                    <span>of {currencyFormatter.format(toNumber(item.target_amount))}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setEditingId(item.id);
                      const normalizedGoalType = ['Home', 'Retirement', 'Emergency Fund', 'Travel', 'Education', 'Vehicle', 'Other'].includes(item.goal_type)
                        ? item.goal_type
                        : 'Other';
                      setGoal({
                        goalName: item.goal_type === 'Other' ? (item.goal_name || '') : '',
                        goalType: normalizedGoalType || 'Home',
                        targetAmount: String(toNumber(item.target_amount) || ''),
                        currentAmount: String(toNumber(item.current_amount) || ''),
                        targetDate: item.target_date || '',
                        monthlyContribution: String(toNumber(item.monthly_contribution) || ''),
                        notes: item.notes || '',
                      });
                    }}
                    className="mt-3 text-sm font-medium text-indigo-600 hover:underline"
                  >
                    Edit
                  </button>
                </div>
              );
            })}
            <PaginationControls total={goals.length} page={page} setPage={setPage} />
          </div>
        ) : (
          <EmptyState text="No goals added yet." />
        )}
      </Card>

      <Card className="xl:col-span-5">
        <h2 className="text-xl font-bold text-slate-800">{editingId ? 'Edit goal' : 'Add goal'}</h2>
        <div className="mt-6 space-y-4">
          <select value={goal.goalType} onChange={(e) => setGoal({ ...goal, goalType: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2">
            {['Home', 'Retirement', 'Emergency Fund', 'Travel', 'Education', 'Vehicle', 'Other'].map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          {requiresCustomGoalName ? (
            <input value={goal.goalName} onChange={(e) => setGoal({ ...goal, goalName: e.target.value })} placeholder="Goal name" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          ) : null}
          <input type="number" value={goal.targetAmount} onChange={(e) => setGoal({ ...goal, targetAmount: e.target.value })} placeholder="Target amount" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <input type="number" value={goal.currentAmount} onChange={(e) => setGoal({ ...goal, currentAmount: e.target.value })} placeholder="Current amount" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <input type="number" value={goal.monthlyContribution} onChange={(e) => setGoal({ ...goal, monthlyContribution: e.target.value })} placeholder="Monthly contribution" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <input type="date" value={goal.targetDate} onChange={(e) => setGoal({ ...goal, targetDate: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <input value={goal.notes} onChange={(e) => setGoal({ ...goal, notes: e.target.value })} placeholder="Notes" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <ActionButton loading={saving} onClick={saveGoal}>Save goal</ActionButton>
        </div>
      </Card>
    </div>
  );
}

function TaxBenefitsPage({
  taxBenefits,
  refreshProfile,
  taxBenefitDraft,
  clearTaxBenefitDraft,
  selectedFy,
}: {
  taxBenefits: any[];
  refreshProfile: () => Promise<void>;
  taxBenefitDraft: { benefitCategory: string; entryType: string; description: string } | null;
  clearTaxBenefitDraft: () => void;
  selectedFy: { id: string; label: string; start: Date; end: Date };
}) {
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState({
    benefitCategory: '80C',
    entryType: 'investment',
    amount: '',
    contributionDate: new Date().toISOString().split('T')[0],
    description: '',
  });
  const fyTaxBenefits = taxBenefits.filter((entry) => isWithinRange(entry.contribution_date, selectedFy.start, selectedFy.end));
  const pagedEntries = fyTaxBenefits.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  useEffect(() => {
    if (!taxBenefitDraft) return;
    setForm((current) => ({
      ...current,
      benefitCategory: taxBenefitDraft.benefitCategory,
      entryType: taxBenefitDraft.entryType,
      description: taxBenefitDraft.description,
    }));
    clearTaxBenefitDraft();
  }, [clearTaxBenefitDraft, taxBenefitDraft]);

  useEffect(() => {
    setPage(1);
  }, [selectedFy.id]);

  const saveTaxBenefit = async () => {
    try {
      setSaving(true);
      setStatus('');
      const payload = {
        benefit_category: form.benefitCategory,
        entry_type: form.entryType,
        amount: Number(form.amount) || 0,
        contribution_date: form.contributionDate || new Date().toISOString().split('T')[0],
        description: form.description || null,
      };
      if (editingId) {
        await apiClient.updateTaxBenefit(editingId, payload);
      } else {
        await apiClient.addTaxBenefit(payload);
      }
      setForm({
        benefitCategory: '80C',
        entryType: 'investment',
        amount: '',
        contributionDate: new Date().toISOString().split('T')[0],
        description: '',
      });
      setEditingId(null);
      await refreshProfile();
      setStatus(editingId ? 'Tax benefit updated.' : 'Tax benefit added.');
    } catch (error: any) {
      setStatus(error.message || 'Failed to save tax benefit.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
      <Card className="xl:col-span-7">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-800">Tax benefit entries</h2>
            <p className="mt-1 text-sm text-slate-500">{selectedFy.label} entries only.</p>
          </div>
          {status ? <span className="text-sm text-indigo-600">{status}</span> : null}
        </div>
        {fyTaxBenefits.length > 0 ? (
          <div className="mt-6 space-y-4">
            {pagedEntries.map((entry) => (
              <div key={entry.id} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-semibold text-slate-800">{entry.benefit_category}</p>
                    <p className="text-sm text-slate-500">{entry.description || entry.entry_type || 'Tax benefit entry'}</p>
                    <p className="mt-1 text-xs text-slate-500">Date {entry.contribution_date || '--'}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500">Amount</p>
                    <p className="font-semibold text-slate-800">{currencyFormatter.format(toNumber(entry.amount))}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setEditingId(entry.id);
                    setForm({
                      benefitCategory: entry.benefit_category || '80C',
                      entryType: entry.entry_type || 'investment',
                      amount: String(toNumber(entry.amount) || ''),
                      contributionDate: entry.contribution_date || new Date().toISOString().split('T')[0],
                      description: entry.description || '',
                    });
                  }}
                  className="mt-3 text-sm font-medium text-indigo-600 hover:underline"
                >
                  Edit
                </button>
              </div>
            ))}
            <PaginationControls total={fyTaxBenefits.length} page={page} setPage={setPage} />
          </div>
        ) : (
          <EmptyState text={`No tax benefit entries found for ${selectedFy.label}.`} />
        )}
      </Card>

      <Card className="xl:col-span-5">
        <h2 className="text-xl font-bold text-slate-800">{editingId ? 'Edit tax benefit' : 'Add tax benefit'}</h2>
        <div className="mt-6 space-y-4">
          <select value={form.benefitCategory} onChange={(e) => setForm({ ...form, benefitCategory: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2">
            <option value="80C">80C</option>
            <option value="80CCD(1B)">80CCD(1B)</option>
            <option value="80D">80D</option>
          </select>
          <select value={form.entryType} onChange={(e) => setForm({ ...form, entryType: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2">
            <option value="investment">Investment</option>
            <option value="insurance">Insurance premium</option>
            <option value="deduction">Deduction</option>
          </select>
          <input type="number" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} placeholder="Amount" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <input type="date" value={form.contributionDate} onChange={(e) => setForm({ ...form, contributionDate: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Description (optional)" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <ActionButton loading={saving} onClick={saveTaxBenefit}>Save tax benefit</ActionButton>
        </div>
      </Card>
    </div>
  );
}

function LoansPage({
  loans,
  refreshProfile,
}: {
  loans: any[];
  refreshProfile: () => Promise<void>;
}) {
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState('');
  const [tab, setTab] = useState<'active' | 'past'>('active');
  const [page, setPage] = useState(1);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [loan, setLoan] = useState({ type: 'Home Loan', amount: '', rate: '', startDate: '', tenureMonths: '' });
  const filteredLoans = loans.filter((item) => {
    if (!item.end_date) return tab === 'active';
    const endDate = new Date(item.end_date);
    const isPast = !Number.isNaN(endDate.getTime()) && endDate < new Date();
    return tab === 'past' ? isPast : !isPast;
  });
  const pagedLoans = filteredLoans.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const saveLoan = async () => {
    try {
      setSaving(true);
      setStatus('');
      const payload = {
        loan_type: loan.type,
        principal_amount: Number(loan.amount) || 0,
        interest_rate: Number(loan.rate) || 0,
        start_date: loan.startDate,
        end_date: addMonthsToDate(loan.startDate, Number(loan.tenureMonths)),
        tenure_months: Number(loan.tenureMonths) || 0,
        monthly_emi: calculateLoanEmi(Number(loan.amount), Number(loan.rate), Number(loan.tenureMonths)),
      };
      if (editingId) {
        await apiClient.updateLoan(editingId, payload);
      } else {
        await apiClient.addLoan(payload);
      }
      setLoan({ type: 'Home Loan', amount: '', rate: '', startDate: '', tenureMonths: '' });
      setEditingId(null);
      await refreshProfile();
      setStatus(editingId ? 'Loan updated.' : 'Loan added.');
    } catch (error: any) {
      setStatus(error.message || 'Failed to save loan.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
      <Card className="xl:col-span-7">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-slate-800">All active loans</h2>
          {status ? <span className="text-sm text-indigo-600">{status}</span> : null}
        </div>
        <div className="mt-4 flex gap-2">
          <button type="button" onClick={() => { setTab('active'); setPage(1); }} className={`rounded-full px-4 py-2 text-sm font-medium ${tab === 'active' ? 'bg-indigo-600 text-white' : 'border border-slate-200 bg-white text-slate-600'}`}>Active</button>
          <button type="button" onClick={() => { setTab('past'); setPage(1); }} className={`rounded-full px-4 py-2 text-sm font-medium ${tab === 'past' ? 'bg-indigo-600 text-white' : 'border border-slate-200 bg-white text-slate-600'}`}>Past</button>
        </div>
        {filteredLoans.length > 0 ? (
          <div className="mt-6 space-y-4">
            {pagedLoans.map((item) => (
              <div key={item.id} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-semibold text-slate-800">{item.loan_type}</p>
                    <p className="text-sm text-slate-500">{toNumber(item.interest_rate)}% interest</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500">Principal</p>
                    <p className="font-semibold text-slate-800">{currencyFormatter.format(toNumber(item.principal_amount))}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setEditingId(item.id);
                    setLoan({
                      type: item.loan_type || 'Home Loan',
                      amount: String(toNumber(item.principal_amount) || ''),
                      rate: String(toNumber(item.interest_rate) || ''),
                      startDate: item.start_date || '',
                      tenureMonths: String(toNumber(item.tenure_months) || ''),
                    });
                  }}
                  className="mt-3 text-sm font-medium text-indigo-600 hover:underline"
                >
                  Edit
                </button>
              </div>
            ))}
            <PaginationControls total={filteredLoans.length} page={page} setPage={setPage} />
          </div>
        ) : (
          <EmptyState text={`No ${tab} loans added yet.`} />
        )}
      </Card>

      <Card className="xl:col-span-5">
        <h2 className="text-xl font-bold text-slate-800">{editingId ? 'Edit loan' : 'Add loan'}</h2>
        <div className="mt-6 space-y-4">
          <select value={loan.type} onChange={(e) => setLoan({ ...loan, type: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2">
            {['Home Loan', 'Car Loan', 'Personal Loan', 'Education Loan', 'Credit Card', 'Other'].map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          <input type="number" value={loan.amount} onChange={(e) => setLoan({ ...loan, amount: e.target.value })} placeholder="Loan amount" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <input type="number" value={loan.rate} onChange={(e) => setLoan({ ...loan, rate: e.target.value })} placeholder="Interest rate %" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <input type="date" value={loan.startDate} onChange={(e) => setLoan({ ...loan, startDate: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <input type="number" value={loan.tenureMonths} onChange={(e) => setLoan({ ...loan, tenureMonths: e.target.value })} placeholder="Tenure (months)" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
          <ActionButton loading={saving} onClick={saveLoan}>Save loan</ActionButton>
        </div>
      </Card>
    </div>
  );
}

function ExpensesPage({
  expenses,
  refreshProfile,
}: {
  expenses: any[];
  refreshProfile: () => Promise<void>;
}) {
  const [saving, setSaving] = useState<string | null>(null);
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [manualExpense, setManualExpense] = useState({
    amount: '',
    date: new Date().toISOString().split('T')[0],
    description: '',
    category: 'Other',
  });
  const pagedExpenses = expenses.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const saveExpense = async () => {
    try {
      setSaving('manual');
      setStatus('');
      const payload = {
        amount: Number(manualExpense.amount) || 0,
        transaction_date: manualExpense.date,
        description: manualExpense.description,
        category_name: manualExpense.category,
      };
      if (editingId) {
        await apiClient.updateExpense(editingId, payload);
      } else {
        await apiClient.addExpense(payload);
      }
      setManualExpense({
        amount: '',
        date: new Date().toISOString().split('T')[0],
        description: '',
        category: 'Other',
      });
      setEditingId(null);
      await refreshProfile();
      setStatus(editingId ? 'Expense updated.' : 'Expense added.');
    } catch (error: any) {
      setStatus(error.message || 'Failed to save expense.');
    } finally {
      setSaving(null);
    }
  };

  const uploadStatement = async (file: File) => {
    try {
      setSaving('upload');
      setStatus('');
      const parsed = await parseExpenses(file);
      await Promise.all(parsed.map((expense) => apiClient.addExpense({
        amount: expense.amount,
        transaction_date: expense.date,
        description: expense.description,
        category_name: expense.category,
      })));
      await refreshProfile();
      setStatus('Statement imported.');
    } catch (error: any) {
      setStatus(error.message || 'Failed to import statement.');
    } finally {
      setSaving(null);
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
      <Card className="xl:col-span-7">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-slate-800">All expenses</h2>
          {status ? <span className="text-sm text-indigo-600">{status}</span> : null}
        </div>
        {expenses.length > 0 ? (
          <div className="mt-6 space-y-4">
            {pagedExpenses.map((expense) => (
              <div key={expense.id} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-semibold text-slate-800">{expense.description || expense.category_name || 'Expense'}</p>
                    <p className="text-sm text-slate-500">{expense.category_name || 'Other'} • {expense.transaction_date || '--'}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500">Amount</p>
                    <p className="font-semibold text-slate-800">{currencyFormatter.format(toNumber(expense.amount))}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setEditingId(expense.id);
                    setManualExpense({
                      amount: String(toNumber(expense.amount) || ''),
                      date: expense.transaction_date || new Date().toISOString().split('T')[0],
                      description: expense.description || '',
                      category: expense.category_name || 'Other',
                    });
                  }}
                  className="mt-3 text-sm font-medium text-indigo-600 hover:underline"
                >
                  Edit
                </button>
              </div>
            ))}
            <PaginationControls total={expenses.length} page={page} setPage={setPage} />
          </div>
        ) : (
          <EmptyState text="No expenses added yet." />
        )}
      </Card>

      <Card className="xl:col-span-5">
        <h2 className="text-xl font-bold text-slate-800">{editingId ? 'Edit expense' : 'Add expense'}</h2>
        <div className="mt-6 space-y-6">
          <div className="space-y-4">
            <p className="text-sm font-medium text-slate-700">Manual entry</p>
            <input type="number" value={manualExpense.amount} onChange={(e) => setManualExpense({ ...manualExpense, amount: e.target.value })} placeholder="Amount" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
            <input type="date" value={manualExpense.date} onChange={(e) => setManualExpense({ ...manualExpense, date: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2" />
            <input type="text" value={manualExpense.description} onChange={(e) => setManualExpense({ ...manualExpense, description: e.target.value })} placeholder="Description" className="w-full rounded-xl border border-slate-300 px-3 py-2" />
            <select value={manualExpense.category} onChange={(e) => setManualExpense({ ...manualExpense, category: e.target.value })} className="w-full rounded-xl border border-slate-300 px-3 py-2">
              {['Food', 'Rent', 'Utilities', 'Shopping', 'Travel', 'Entertainment', 'Health', 'Other'].map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
            <ActionButton loading={saving === 'manual'} onClick={saveExpense}>Save expense</ActionButton>
          </div>

          <div className="space-y-4 border-t border-slate-200 pt-6">
            <p className="text-sm font-medium text-slate-700">Upload bank statement</p>
            <label className="flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-dashed border-slate-300 px-4 py-4 text-sm text-slate-600 hover:bg-slate-50">
              <Upload className="h-4 w-4" />
              Upload statement
              <input
                type="file"
                className="hidden"
                accept=".pdf,.csv,.xls,.xlsx"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) void uploadStatement(file);
                  e.currentTarget.value = '';
                }}
              />
            </label>
          </div>
        </div>
      </Card>
    </div>
  );
}

function HeaderIcon({ icon }: { icon: React.ReactNode }) {
  return (
    <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-500 shadow-sm">
      {icon}
    </div>
  );
}

function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return <section className={`rounded-3xl border border-slate-200 bg-white p-6 shadow-sm ${className}`}>{children}</section>;
}

function MetricCard({ title, value }: { title: string; value: number }) {
  return (
    <motion.div whileHover={{ y: -2 }} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="mt-2 text-3xl font-bold text-slate-800">{currencyFormatter.format(value)}</p>
    </motion.div>
  );
}

function ScoreMetricCard({ title, score }: { title: string; score: number }) {
  return (
    <motion.div whileHover={{ y: -2 }} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="mt-2 text-3xl font-bold text-slate-800">{Math.round(score)}/100</p>
    </motion.div>
  );
}

function SmallCard({ label, value }: { label: string; value: string }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-xl font-bold text-slate-800">{value}</p>
    </section>
  );
}

function HealthInfoPanel({
  kind,
  details,
}: {
  kind: 'savings' | 'debt' | 'investments' | 'emergency';
  details: any;
}) {
  if (kind === 'savings') {
    return (
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
        <p className="font-medium text-slate-800">Savings score uses the last 6 months of average monthly salary minus the last 6 months of average monthly expenses.</p>
        <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-3">
          <span>Avg income: {currencyFormatter.format(details.savings.monthlyIncome)}</span>
          <span>Avg expenses: {currencyFormatter.format(details.savings.monthlyExpenses)}</span>
          <span>Avg savings: {currencyFormatter.format(details.savings.monthlySavings)}</span>
        </div>
      </div>
    );
  }

  if (kind === 'debt') {
    return (
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
        <p className="font-medium text-slate-800">Debt score is based on active-loan EMI burden versus average monthly income.</p>
        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2">
          <span>Total EMI counted: {currencyFormatter.format(details.debt.totalMonthlyEmi)}</span>
          <span>Debt-to-income ratio: {details.debt.monthlyDebtRatioPercent.toFixed(1)}%</span>
        </div>
        <div className="mt-3 space-y-2">
          {details.debt.loans.length > 0 ? details.debt.loans.map((loan: any) => (
            <div key={loan.id} className="flex items-center justify-between rounded-xl bg-white px-3 py-2">
              <span>{loan.name}</span>
              <span>EMI {currencyFormatter.format(loan.monthlyEmi)} • Outstanding {currencyFormatter.format(Math.round(loan.pendingAmount))}</span>
            </div>
          )) : <span>No active loans are currently being counted.</span>}
        </div>
      </div>
    );
  }

  if (kind === 'investments') {
    return (
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
        <p className="font-medium text-slate-800">Investment score compares tracked portfolio value against selected-year income.</p>
        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2">
          <span>Portfolio counted: {currencyFormatter.format(details.investments.totalPortfolioTrackedValue)}</span>
          <span>Income compared against: {currencyFormatter.format(details.investments.annualIncome)}</span>
        </div>
        <div className="mt-3 space-y-2">
          {details.investments.items.length > 0 ? details.investments.items.map((item: any) => (
            <div key={item.id} className="flex items-center justify-between rounded-xl bg-white px-3 py-2">
              <span>{item.name} <span className="text-xs text-slate-400">({item.meta})</span></span>
              <span>{currencyFormatter.format(item.amount)}</span>
            </div>
          )) : <span>No investments or uploaded equity trades are being counted yet.</span>}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
      <p className="font-medium text-slate-800">Emergency fund score uses goals whose name or type includes “Emergency”.</p>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2">
        <span>Current emergency corpus: {currencyFormatter.format(details.emergency.currentAmount)}</span>
        <span>Target corpus: {currencyFormatter.format(details.emergency.targetAmount)}</span>
        <span>Based on 6 months of expenses: {currencyFormatter.format(details.emergency.monthlyExpenses)}/month</span>
      </div>
      <div className="mt-3 space-y-2">
        {details.emergency.goals.length > 0 ? details.emergency.goals.map((goal: any) => (
          <div key={goal.id} className="flex items-center justify-between rounded-xl bg-white px-3 py-2">
            <span>{goal.name}</span>
            <span>{currencyFormatter.format(goal.currentAmount)} saved of {currencyFormatter.format(goal.targetAmount)}</span>
          </div>
        )) : <span>No emergency-fund goal is being counted right now. Add or update a goal named/type “Emergency Fund”.</span>}
      </div>
    </div>
  );
}

function ActionButton({
  loading,
  onClick,
  children,
}: {
  loading: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={loading}
      className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:opacity-60"
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
      {children}
    </button>
  );
}

function PaginationControls({
  total,
  page,
  setPage,
}: {
  total: number;
  page: number;
  setPage: (page: number) => void;
}) {
  const totalPages = Math.ceil(total / PAGE_SIZE);
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between pt-2 text-sm text-slate-600">
      <span>Page {page} of {totalPages}</span>
      <div className="flex gap-2">
        <button
          type="button"
          disabled={page === 1}
          onClick={() => setPage(page - 1)}
          className="rounded-lg border border-slate-200 px-3 py-1.5 disabled:opacity-50"
        >
          Previous
        </button>
        <button
          type="button"
          disabled={page === totalPages}
          onClick={() => setPage(page + 1)}
          className="rounded-lg border border-slate-200 px-3 py-1.5 disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return <p className="mt-6 text-sm text-slate-500">{text}</p>;
}
