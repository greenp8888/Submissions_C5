import React, { useState, useCallback } from 'react';
import { useFirebase } from './FirebaseProvider';
import { 
  Upload, Loader2, FileText, CheckCircle2, ArrowRight, ArrowLeft, 
  AlertCircle, Plus, Trash2, Landmark, Wallet, PieChart, TrendingUp, 
  Receipt, LogOut, X
} from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { parseSalarySlip } from '../lib/agents/salaryParser';
import { parseEquityPL, EquityTrade } from '../lib/agents/equityParser';
import { parseExpenses, Expense } from '../lib/agents/expenseParser';
import { apiClient } from '../lib/api';

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

export default function Onboarding() {
  const { user, refreshProfile, logout } = useFirebase();
  const [step, setStep] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Step 1: Salary
  const [salaryData, setSalaryData] = useState({
    employerName: '',
    effectiveFrom: new Date().toISOString().split('T')[0],
    netSalary: '',
    grossSalary: '',
    basicSalary: '',
    hra: '',
    specialAllowance: '',
    lta: '',
    taxDeduction: '',
    pfDeduction: '',
    npsDeduction: '',
    professionalTax: '',
    otherDeductions: ''
  });
  const [pastSalaries, setPastSalaries] = useState<Array<{
    id: number;
    employerName: string;
    monthlyAmount: string;
    grossSalary: string;
    basicSalary: string;
    hra: string;
    specialAllowance: string;
    lta: string;
    taxDeduction: string;
    pfDeduction: string;
    npsDeduction: string;
    professionalTax: string;
    otherDeductions: string;
    effectiveFrom: string;
    effectiveTo: string;
  }>>([]);

  // Step 2: Other Incomes (Manual)
  const [otherIncomes, setOtherIncomes] = useState<any[]>([]);
  const [newIncome, setNewIncome] = useState({
    description: '',
    amount: '',
    category: 'Rental Income',
    date: new Date().toISOString().split('T')[0]
  });

  // Step 3: Equity Portfolio (Tax P&L)
  const [equityTrades, setEquityTrades] = useState<EquityTrade[]>([]);
  const [totalEquityGain, setTotalEquityGain] = useState(0);

  // Step 4: Expenses (Bank Statement)
  const [parsedExpenses, setParsedExpenses] = useState<Expense[]>([]);
  const [totalMonthlyExpense, setTotalMonthlyExpense] = useState(0);

  // Step 5: Traditional Investments
  const [investments, setInvestments] = useState<any[]>([]);
  const [newInvestment, setNewInvestment] = useState({
    type: 'FD',
    principal: '',
    rate: '',
    startDate: '',
    tenureMonths: '',
    taxExemptionCategory: '',
  });
  const [loans, setLoans] = useState<any[]>([]);
  const [newLoan, setNewLoan] = useState({
    type: 'Home Loan',
    amount: '',
    rate: '',
    startDate: '',
    tenureMonths: '',
  });

  const [isFinishing, setIsFinishing] = useState(false);

  // File Handlers
  const onDropSalary = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    const file = acceptedFiles[0];
    setIsProcessing(true);
    setError(null);
    try {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = async () => {
        try {
          const parsed = await parseSalarySlip(reader.result as string);
          const getVal = (val: any) => (val === null || val === undefined) ? '' : val.toString();
          setSalaryData({
            employerName: '',
            effectiveFrom: new Date().toISOString().split('T')[0],
            netSalary: getVal(parsed.net_salary),
            grossSalary: getVal(parsed.gross_salary),
            basicSalary: getVal(parsed.basic_salary),
            hra: getVal(parsed.hra),
            specialAllowance: getVal(parsed.special_allowance),
            lta: getVal(parsed.lta),
            taxDeduction: getVal(parsed.tax_deduction),
            pfDeduction: getVal(parsed.pf_deduction),
            npsDeduction: getVal(parsed.nps_deduction),
            professionalTax: getVal(parsed.professional_tax),
            otherDeductions: getVal(parsed.other_deductions)
          });
        } catch (e) {
          setError("Failed to parse salary slip. Please enter manually.");
        }
        setIsProcessing(false);
      };
    } catch (e) {
      setIsProcessing(false);
      setError("Error reading file.");
    }
  }, []);

  const onDropEquity = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    const file = acceptedFiles[0];
    setIsProcessing(true);
    setError(null);
    try {
      const trades = await parseEquityPL(file);
      setEquityTrades(trades);
      const gain = trades.reduce((acc, curr) => acc + (curr.realized_gain || 0), 0);
      setTotalEquityGain(gain);
      setIsProcessing(false);
    } catch (e) {
      setIsProcessing(false);
      setError("Failed to parse Tax P&L statement.");
    }
  }, []);

  const onDropExpenses = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    const file = acceptedFiles[0];
    setIsProcessing(true);
    setError(null);
    try {
      const expenses = await parseExpenses(file);
      setParsedExpenses(expenses);
      const total = expenses.reduce((acc, curr) => acc + (curr.amount || 0), 0);
      setTotalMonthlyExpense(Math.round(total / 12)); // Average monthly if it's a yearly statement
      setIsProcessing(false);
    } catch (e) {
      setIsProcessing(false);
      setError("Failed to parse bank transactions.");
    }
  }, []);

  const { getRootProps: getSalaryProps, getInputProps: getSalaryInput } = useDropzone({ onDrop: onDropSalary, accept: { 'image/*': [] } } as any);
  const { getRootProps: getEquityProps, getInputProps: getEquityInput } = useDropzone({ onDrop: onDropEquity, accept: { 'application/pdf': [], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': [], 'application/vnd.ms-excel': [], 'text/csv': [] } } as any);
  const { getRootProps: getExpenseProps, getInputProps: getExpenseInput } = useDropzone({ onDrop: onDropExpenses, accept: { 'application/pdf': [], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': [], 'application/vnd.ms-excel': [], 'text/csv': [] } } as any);

  const handleAddIncome = () => {
    if (!newIncome.description || !newIncome.amount) return;
    setOtherIncomes([...otherIncomes, { ...newIncome, id: Date.now() }]);
    setNewIncome({ description: '', amount: '', category: 'Rental Income', date: new Date().toISOString().split('T')[0] });
  };

  const handleAddInvestment = () => {
    if (!newInvestment.principal || !newInvestment.rate || !newInvestment.startDate || !newInvestment.tenureMonths) return;
    const principal = Number(newInvestment.principal);
    const rate = Number(newInvestment.rate);
    const tenureMonths = Number(newInvestment.tenureMonths);
    const maturityDate = addMonthsToDate(newInvestment.startDate, tenureMonths);
    const maturityAmount = calculateFdMaturityAmount(principal, rate, tenureMonths);
    setInvestments([...investments, { ...newInvestment, maturityDate, maturityAmount, id: Date.now() }]);
    setNewInvestment({ type: 'FD', principal: '', rate: '', startDate: '', tenureMonths: '', taxExemptionCategory: '' });
  };

  const handleAddLoan = () => {
    if (!newLoan.amount || !newLoan.rate || !newLoan.startDate || !newLoan.tenureMonths) return;
    const amount = Number(newLoan.amount);
    const rate = Number(newLoan.rate);
    const tenureMonths = Number(newLoan.tenureMonths);
    const endDate = addMonthsToDate(newLoan.startDate, tenureMonths);
    const monthlyEmi = calculateLoanEmi(amount, rate, tenureMonths);
    setLoans([...loans, { ...newLoan, endDate, monthlyEmi, id: Date.now() }]);
    setNewLoan({ type: 'Home Loan', amount: '', rate: '', startDate: '', tenureMonths: '' });
  };

  const handleAddPastSalary = () => {
    if (pastSalaries.length >= 3) return;
    setPastSalaries([
      ...pastSalaries,
      {
        id: Date.now(),
        employerName: '',
        monthlyAmount: '',
        grossSalary: '',
        basicSalary: '',
        hra: '',
        specialAllowance: '',
        lta: '',
        taxDeduction: '',
        pfDeduction: '',
        npsDeduction: '',
        professionalTax: '',
        otherDeductions: '',
        effectiveFrom: '',
        effectiveTo: '',
      }
    ]);
  };

  const handleUpdatePastSalary = (id: number, field: string, value: string) => {
    setPastSalaries((current) =>
      current.map((salary) => salary.id === id ? { ...salary, [field]: value } : salary)
    );
  };

  const handleRemovePastSalary = (id: number) => {
    setPastSalaries((current) => current.filter((salary) => salary.id !== id));
  };

  const handleFinish = async () => {
    if (!user) return;
    setIsFinishing(true);
    try {
      // 1. Update Profile Status
      await apiClient.updateProfile({ onboarding_completed: 1 });

      // 2. Save Salary History
      const salaryEntries = [
        {
          monthly_amount: Number(salaryData.netSalary) || 0,
          employer_name: salaryData.employerName.trim() || 'Current Employer',
          effective_from: salaryData.effectiveFrom || new Date().toISOString().split('T')[0],
          gross_monthly: Number(salaryData.grossSalary) || null,
          basic_salary: Number(salaryData.basicSalary) || null,
          hra: Number(salaryData.hra) || null,
          special_allowance: Number(salaryData.specialAllowance) || null,
          lta: Number(salaryData.lta) || null,
          tax_deduction: Number(salaryData.taxDeduction) || null,
          pf_deduction: Number(salaryData.pfDeduction) || null,
          nps_deduction: Number(salaryData.npsDeduction) || null,
          professional_tax: Number(salaryData.professionalTax) || null,
          other_deductions: Number(salaryData.otherDeductions) || null,
        },
        ...pastSalaries
          .filter((salary) => salary.monthlyAmount && salary.effectiveFrom)
          .map((salary) => ({
            monthly_amount: Number(salary.monthlyAmount) || 0,
            employer_name: salary.employerName.trim() || 'Previous Employer',
            effective_from: salary.effectiveFrom,
            effective_to: salary.effectiveTo || null,
            gross_monthly: Number(salary.grossSalary) || null,
            basic_salary: Number(salary.basicSalary) || null,
            hra: Number(salary.hra) || null,
            special_allowance: Number(salary.specialAllowance) || null,
            lta: Number(salary.lta) || null,
            tax_deduction: Number(salary.taxDeduction) || null,
            pf_deduction: Number(salary.pfDeduction) || null,
            nps_deduction: Number(salary.npsDeduction) || null,
            professional_tax: Number(salary.professionalTax) || null,
            other_deductions: Number(salary.otherDeductions) || null,
          }))
      ];

      await Promise.all(salaryEntries.map((entry) => apiClient.addSalary(entry)));

      // 3. Batch save subcollections via API
      await Promise.all([
        ...otherIncomes.map(income => apiClient.addOtherIncome({
          income_source: income.description,
          amount: Number(income.amount),
          is_taxable: 1,
          date_received: income.date
        })),
        ...equityTrades.map(trade => apiClient.addTrade({
          ticker: trade.symbol,
          trade_type: 'SELL', // Assuming realized gains come from sells
          quantity: trade.quantity,
          price_per_unit: trade.sell_price,
          execution_date: trade.sell_date,
          brokerage_fees: 0,
          ticker_name: trade.symbol,
          asset_class: 'Equity',
          buy_date: trade.buy_date,
          sell_date: trade.sell_date,
          realized_gain: trade.realized_gain,
          holding_type: trade.holding_type,
        })),
        ...parsedExpenses.map(exp => apiClient.addExpense({
          amount: exp.amount,
          transaction_date: exp.date,
          description: exp.description,
          category_name: exp.category
        })),
        ...investments.map(inv => apiClient.addInvestment({
          investment_type: inv.type,
          principal_amount: Number(inv.principal),
          interest_rate: Number(inv.rate),
          start_date: inv.startDate,
          maturity_date: inv.maturityDate,
          tenure_months: Number(inv.tenureMonths),
          maturity_amount: Number(inv.maturityAmount),
          tax_exemption_category: inv.taxExemptionCategory || null,
        })),
        ...loans.map(loan => apiClient.addLoan({
          loan_type: loan.type,
          principal_amount: Number(loan.amount),
          interest_rate: Number(loan.rate),
          start_date: loan.startDate,
          end_date: loan.endDate,
          tenure_months: Number(loan.tenureMonths),
          monthly_emi: Number(loan.monthlyEmi),
        }))
      ]);

      setStep(7);
      setTimeout(() => refreshProfile(), 2000);
    } catch (err) {
      console.error("Finish error:", err);
      setError("Failed to save profile to SQL database.");
      setIsFinishing(false);
    }
  };

  if (step === 7) {
    return (
      <div className="min-h-screen bg-[#FDFDF9] flex items-center justify-center p-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm max-w-md w-full text-center space-y-4">
          <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-8 h-8 text-emerald-600" />
          </div>
          <h2 className="text-2xl font-bold text-slate-800">All Set!</h2>
          <p className="text-slate-600">Your financial profile is ready. Redirecting to dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FDFDF9] flex flex-col items-center justify-center p-6 relative">
      <button 
        onClick={logout}
        className="absolute top-6 right-6 flex items-center gap-2 px-4 py-2 text-slate-600 hover:text-red-600 transition-colors font-medium"
      >
        <LogOut className="w-4 h-4" /> Logout
      </button>

      <div className={`bg-white rounded-2xl border border-slate-200 p-8 shadow-sm w-full transition-all duration-300 ${[1, 2, 3, 4, 5].includes(step) ? 'max-w-5xl' : 'max-w-md'}`}>
        
        {/* Progress Bar */}
        <div className="flex gap-2 mb-8">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className={`h-1.5 flex-1 rounded-full ${step >= i ? 'bg-indigo-600' : 'bg-slate-100'}`} />
          ))}
        </div>

        {/* Step 1: Salary */}
        {step === 1 && (
          <div className="animate-in fade-in slide-in-from-bottom-4">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-slate-800">Step 1: Primary Income</h2>
              <p className="text-slate-600 text-sm mt-1">Upload your salary slip (Image) to auto-fill details.</p>
            </div>
            <div className="grid md:grid-cols-12 gap-8">
              <div className="md:col-span-4 space-y-4">
                <div {...getSalaryProps()} className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:bg-slate-50 transition-colors cursor-pointer h-48 flex flex-col items-center justify-center">
                  <input {...getSalaryInput()} />
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-12 h-12 bg-indigo-50 rounded-full flex items-center justify-center">
                      {isProcessing ? <Loader2 className="w-6 h-6 text-indigo-600 animate-spin" /> : <Upload className="w-6 h-6 text-indigo-600" />}
                    </div>
                    <p className="font-medium text-slate-800 text-sm">Drop Salary Slip here</p>
                  </div>
                </div>
                {error && <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm border border-red-100 flex gap-2"><AlertCircle className="w-4 h-4 shrink-0" /> {error}</div>}
              </div>
              <div className="md:col-span-8 bg-slate-50 p-6 rounded-xl border border-slate-200">
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1">Employer Name</label>
                    <input type="text" value={salaryData.employerName} onChange={(e) => setSalaryData({...salaryData, employerName: e.target.value})} placeholder="Current Employer" className="w-full px-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1">Effective From</label>
                    <input type="date" value={salaryData.effectiveFrom} onChange={(e) => setSalaryData({...salaryData, effectiveFrom: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1">Net Salary (₹) *</label>
                    <input type="number" value={salaryData.netSalary} onChange={(e) => setSalaryData({...salaryData, netSalary: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1">Gross Salary (₹)</label>
                    <input type="number" value={salaryData.grossSalary} onChange={(e) => setSalaryData({...salaryData, grossSalary: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="text-xs font-semibold text-slate-500 uppercase border-b pb-1">Earnings</h4>
                    <input type="number" placeholder="Basic" value={salaryData.basicSalary} onChange={(e) => setSalaryData({...salaryData, basicSalary: e.target.value})} className="w-full px-3 py-2 border rounded-lg" />
                    <input type="number" placeholder="HRA" value={salaryData.hra} onChange={(e) => setSalaryData({...salaryData, hra: e.target.value})} className="w-full px-3 py-2 border rounded-lg" />
                    <input type="number" placeholder="Special Allowance" value={salaryData.specialAllowance} onChange={(e) => setSalaryData({...salaryData, specialAllowance: e.target.value})} className="w-full px-3 py-2 border rounded-lg" />
                  </div>
                  <div className="space-y-4">
                    <h4 className="text-xs font-semibold text-slate-500 uppercase border-b pb-1">Deductions</h4>
                    <input type="number" placeholder="Tax/TDS" value={salaryData.taxDeduction} onChange={(e) => setSalaryData({...salaryData, taxDeduction: e.target.value})} className="w-full px-3 py-2 border rounded-lg" />
                    <input type="number" placeholder="PF" value={salaryData.pfDeduction} onChange={(e) => setSalaryData({...salaryData, pfDeduction: e.target.value})} className="w-full px-3 py-2 border rounded-lg" />
                    <input type="number" placeholder="NPS" value={salaryData.npsDeduction} onChange={(e) => setSalaryData({...salaryData, npsDeduction: e.target.value})} className="w-full px-3 py-2 border rounded-lg" />
                  </div>
                </div>
                <div className="mt-6 rounded-xl border border-slate-200 bg-white p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h4 className="text-sm font-semibold text-slate-800">Optional: add up to 3 previous salaries</h4>
                      <p className="mt-1 text-xs text-slate-500">These help us calculate annual salary history and income for the current year more accurately.</p>
                    </div>
                    <button
                      type="button"
                      onClick={handleAddPastSalary}
                      disabled={pastSalaries.length >= 3}
                      className="rounded-lg bg-indigo-100 px-3 py-2 text-xs font-medium text-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Add Past Salary
                    </button>
                  </div>

                  {pastSalaries.length > 0 ? (
                    <div className="mt-4 space-y-4">
                      {pastSalaries.map((salary, index) => (
                        <div key={salary.id} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                          <div className="mb-3 flex items-center justify-between">
                            <p className="text-sm font-medium text-slate-700">Previous Salary {index + 1}</p>
                            <button type="button" onClick={() => handleRemovePastSalary(salary.id)} className="text-slate-400 hover:text-red-500">
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                            <input type="text" value={salary.employerName} onChange={(e) => handleUpdatePastSalary(salary.id, 'employerName', e.target.value)} placeholder="Employer Name" className="w-full rounded-lg border border-slate-300 px-3 py-2" />
                            <input type="number" value={salary.monthlyAmount} onChange={(e) => handleUpdatePastSalary(salary.id, 'monthlyAmount', e.target.value)} placeholder="Monthly Net Salary (₹)" className="w-full rounded-lg border border-slate-300 px-3 py-2" />
                            <input type="number" value={salary.grossSalary} onChange={(e) => handleUpdatePastSalary(salary.id, 'grossSalary', e.target.value)} placeholder="Monthly Gross Salary (₹)" className="w-full rounded-lg border border-slate-300 px-3 py-2" />
                            <input type="number" value={salary.basicSalary} onChange={(e) => handleUpdatePastSalary(salary.id, 'basicSalary', e.target.value)} placeholder="Basic Salary" className="w-full rounded-lg border border-slate-300 px-3 py-2" />
                            <input type="number" value={salary.hra} onChange={(e) => handleUpdatePastSalary(salary.id, 'hra', e.target.value)} placeholder="HRA" className="w-full rounded-lg border border-slate-300 px-3 py-2" />
                            <input type="number" value={salary.taxDeduction} onChange={(e) => handleUpdatePastSalary(salary.id, 'taxDeduction', e.target.value)} placeholder="Tax Deducted" className="w-full rounded-lg border border-slate-300 px-3 py-2" />
                            <div>
                              <label className="mb-1 block text-xs font-medium text-slate-600">Effective From</label>
                              <input type="date" value={salary.effectiveFrom} onChange={(e) => handleUpdatePastSalary(salary.id, 'effectiveFrom', e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2" />
                            </div>
                            <div>
                              <label className="mb-1 block text-xs font-medium text-slate-600">Effective To</label>
                              <input type="date" value={salary.effectiveTo} onChange={(e) => handleUpdatePastSalary(salary.id, 'effectiveTo', e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2" />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-4 text-sm text-slate-500">No previous salary entries added.</p>
                  )}
                </div>
                <button onClick={() => setStep(2)} className="w-full mt-6 py-3 bg-indigo-600 text-white rounded-xl font-medium flex items-center justify-center gap-2">Next Step <ArrowRight className="w-4 h-4" /></button>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Other Incomes */}
        {step === 2 && (
          <div className="animate-in fade-in slide-in-from-right-4">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-slate-800">Step 2: Other Incomes</h2>
              <p className="text-slate-600 text-sm mt-1">Add any additional income sources like rent, dividends, or freelance work.</p>
            </div>
            <div className="grid md:grid-cols-12 gap-8">
              <div className="md:col-span-5 bg-slate-50 p-6 rounded-xl border border-slate-200 space-y-4">
                <h3 className="font-semibold text-slate-800 mb-2 flex items-center gap-2"><Plus className="w-4 h-4" /> Add Income</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1">Description</label>
                    <input type="text" value={newIncome.description} onChange={(e) => setNewIncome({...newIncome, description: e.target.value})} placeholder="e.g. Apartment Rent" className="w-full px-3 py-2 border rounded-lg outline-none" />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-slate-600 mb-1">Amount (₹)</label>
                      <input type="number" value={newIncome.amount} onChange={(e) => setNewIncome({...newIncome, amount: e.target.value})} className="w-full px-3 py-2 border rounded-lg outline-none" />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-600 mb-1">Category</label>
                      <select value={newIncome.category} onChange={(e) => setNewIncome({...newIncome, category: e.target.value})} className="w-full px-3 py-2 border rounded-lg outline-none">
                        {['Rental Income', 'Dividend', 'Freelance', 'Interest', 'Refund', 'Other'].map(c => <option key={c} value={c}>{c}</option>)}
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1">Date</label>
                    <input type="date" value={newIncome.date} onChange={(e) => setNewIncome({...newIncome, date: e.target.value})} className="w-full px-3 py-2 border rounded-lg outline-none" />
                  </div>
                </div>
                <button onClick={handleAddIncome} className="w-full py-3 bg-indigo-100 text-indigo-700 rounded-xl font-medium hover:bg-indigo-200 transition-colors">Add Income</button>
              </div>
              <div className="md:col-span-7 space-y-4">
                <h3 className="font-semibold text-slate-800">Your Other Incomes</h3>
                <div className="space-y-3 max-h-[350px] overflow-y-auto pr-2">
                  {otherIncomes.length === 0 ? (
                    <div className="text-center py-12 border-2 border-dashed rounded-xl text-slate-400">No other incomes added yet.</div>
                  ) : (
                    otherIncomes.map((inc) => (
                      <div key={inc.id} className="bg-white p-4 rounded-xl border border-slate-200 flex items-center justify-between shadow-sm">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-emerald-50 rounded-full flex items-center justify-center text-emerald-600"><TrendingUp className="w-5 h-5" /></div>
                          <div>
                            <p className="text-sm font-bold text-slate-800">{inc.description}</p>
                            <p className="text-xs text-slate-500">{inc.category} • ₹{Number(inc.amount).toLocaleString()}</p>
                          </div>
                        </div>
                        <button onClick={() => setOtherIncomes(otherIncomes.filter(i => i.id !== inc.id))} className="text-slate-300 hover:text-red-500"><Trash2 className="w-4 h-4" /></button>
                      </div>
                    ))
                  )}
                </div>
                <div className="flex gap-3 pt-4">
                  <button onClick={() => setStep(1)} className="px-4 py-3 border rounded-xl hover:bg-slate-100"><ArrowLeft className="w-5 h-5" /></button>
                  <button onClick={() => setStep(3)} className="flex-1 py-3 bg-indigo-600 text-white rounded-xl font-medium flex items-center justify-center gap-2">Continue <ArrowRight className="w-4 h-4" /></button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Equity Portfolio */}
        {step === 3 && (
          <div className="animate-in fade-in slide-in-from-right-4">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-slate-800">Step 3: Equity Portfolio</h2>
              <p className="text-slate-600 text-sm mt-1">Upload your Tax P&L Statement (Excel/PDF) to calculate gains.</p>
            </div>
            <div className="grid md:grid-cols-12 gap-8">
              <div className="md:col-span-4 space-y-4">
                <div {...getEquityProps()} className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:bg-slate-50 transition-colors cursor-pointer h-48 flex flex-col items-center justify-center">
                  <input {...getEquityInput()} />
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-12 h-12 bg-indigo-50 rounded-full flex items-center justify-center">
                      {isProcessing ? <Loader2 className="w-6 h-6 text-indigo-600 animate-spin" /> : <PieChart className="w-6 h-6 text-indigo-600" />}
                    </div>
                    <p className="font-medium text-slate-800 text-sm">Drop Tax P&L here</p>
                    <p className="text-xs text-slate-400">Excel or PDF</p>
                  </div>
                </div>
                {error && <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm border border-red-100 flex gap-2"><AlertCircle className="w-4 h-4 shrink-0" /> {error}</div>}
              </div>
              <div className="md:col-span-8 bg-slate-50 p-6 rounded-xl border border-slate-200">
                <div className="mb-6 p-4 bg-white rounded-xl border border-slate-200 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-slate-500 uppercase">Total Realized Gain</p>
                    <p className={`text-2xl font-bold ${totalEquityGain >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>₹{totalEquityGain.toLocaleString()}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-medium text-slate-500 uppercase">Trades Found</p>
                    <p className="text-2xl font-bold text-slate-800">{equityTrades.length}</p>
                  </div>
                </div>
                <div className="space-y-2 max-h-[200px] overflow-y-auto pr-2">
                  {equityTrades.slice(0, 5).map((trade, i) => (
                    <div key={i} className="text-xs flex justify-between p-2 border-b border-slate-100">
                      <span className="font-medium">{trade.symbol}</span>
                      <span className={trade.realized_gain >= 0 ? 'text-emerald-600' : 'text-red-600'}>₹{trade.realized_gain.toLocaleString()}</span>
                    </div>
                  ))}
                  {equityTrades.length > 5 && <p className="text-[10px] text-center text-slate-400">...and {equityTrades.length - 5} more trades</p>}
                </div>
                <div className="flex gap-3 mt-6">
                  <button onClick={() => setStep(2)} className="px-4 py-3 border rounded-xl hover:bg-slate-100"><ArrowLeft className="w-5 h-5" /></button>
                  <button onClick={() => setStep(4)} className="flex-1 py-3 bg-indigo-600 text-white rounded-xl font-medium flex items-center justify-center gap-2">Continue <ArrowRight className="w-4 h-4" /></button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Expenses */}
        {step === 4 && (
          <div className="animate-in fade-in slide-in-from-right-4">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-slate-800">Step 4: Expenses & Transactions</h2>
              <p className="text-slate-600 text-sm mt-1">Upload your Bank Statement (Excel/PDF) to categorize expenses.</p>
            </div>
            <div className="grid md:grid-cols-12 gap-8">
              <div className="md:col-span-4 space-y-4">
                <div {...getExpenseProps()} className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:bg-slate-50 transition-colors cursor-pointer h-48 flex flex-col items-center justify-center">
                  <input {...getExpenseInput()} />
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-12 h-12 bg-indigo-50 rounded-full flex items-center justify-center">
                      {isProcessing ? <Loader2 className="w-6 h-6 text-indigo-600 animate-spin" /> : <Receipt className="w-6 h-6 text-indigo-600" />}
                    </div>
                    <p className="font-medium text-slate-800 text-sm">Drop Bank Statement here</p>
                    <p className="text-xs text-slate-400">Excel or PDF</p>
                  </div>
                </div>
                {error && <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm border border-red-100 flex gap-2"><AlertCircle className="w-4 h-4 shrink-0" /> {error}</div>}
              </div>
              <div className="md:col-span-8 bg-slate-50 p-6 rounded-xl border border-slate-200">
                <div className="mb-6 p-4 bg-white rounded-xl border border-slate-200 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-slate-500 uppercase">Avg. Monthly Expense</p>
                    <p className="text-2xl font-bold text-slate-800">₹{totalMonthlyExpense.toLocaleString()}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-medium text-slate-500 uppercase">Transactions</p>
                    <p className="text-2xl font-bold text-slate-800">{parsedExpenses.length}</p>
                  </div>
                </div>
                <div className="space-y-2 max-h-[200px] overflow-y-auto pr-2">
                  {parsedExpenses.slice(0, 5).map((exp, i) => (
                    <div key={i} className="text-xs flex justify-between p-2 border-b border-slate-100">
                      <span className="truncate max-w-[150px]">{exp.description}</span>
                      <span className="text-slate-500">{exp.category}</span>
                      <span className="font-medium">₹{exp.amount.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
                <div className="flex gap-3 mt-6">
                  <button onClick={() => setStep(3)} className="px-4 py-3 border rounded-xl hover:bg-slate-100"><ArrowLeft className="w-5 h-5" /></button>
                  <button onClick={() => setStep(5)} className="flex-1 py-3 bg-indigo-600 text-white rounded-xl font-medium flex items-center justify-center gap-2">Continue <ArrowRight className="w-4 h-4" /></button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 5: Traditional Investments & Loans */}
        {step === 5 && (
          <div className="animate-in fade-in slide-in-from-right-4">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-slate-800">Step 5: Fixed Investments & Active Loans</h2>
              <p className="text-slate-600 text-sm mt-1">Add your FDs and active loans. EMI, maturity amount, and end dates are auto-calculated from the inputs.</p>
            </div>
            <div className="grid gap-8 xl:grid-cols-12">
              <div className="space-y-8 xl:col-span-5">
                <div className="bg-slate-50 p-6 rounded-xl border border-slate-200 space-y-4">
                <h3 className="font-semibold text-slate-800 mb-2 flex items-center gap-2"><Plus className="w-4 h-4" /> Add Investment</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div className="col-span-2">
                    <label className="block text-xs font-medium text-slate-600 mb-1">Type</label>
                    <select value={newInvestment.type} onChange={(e) => setNewInvestment({...newInvestment, type: e.target.value})} className="w-full px-3 py-2 border rounded-lg outline-none">
                      {['FD', 'PPF', 'NSC', 'Real Estate', 'Other'].map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1">Principal (₹)</label>
                    <input type="number" value={newInvestment.principal} onChange={(e) => setNewInvestment({...newInvestment, principal: e.target.value})} className="w-full px-3 py-2 border rounded-lg outline-none" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1">Rate (%)</label>
                    <input type="number" value={newInvestment.rate} onChange={(e) => setNewInvestment({...newInvestment, rate: e.target.value})} className="w-full px-3 py-2 border rounded-lg outline-none" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1">Start Date</label>
                    <input type="date" value={newInvestment.startDate} onChange={(e) => setNewInvestment({...newInvestment, startDate: e.target.value})} className="w-full px-3 py-2 border rounded-lg outline-none" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1">Tenure (Months)</label>
                    <input type="number" value={newInvestment.tenureMonths} onChange={(e) => setNewInvestment({...newInvestment, tenureMonths: e.target.value})} className="w-full px-3 py-2 border rounded-lg outline-none" />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-xs font-medium text-slate-600 mb-1">Tax Benefit</label>
                    <select value={newInvestment.taxExemptionCategory} onChange={(e) => setNewInvestment({...newInvestment, taxExemptionCategory: e.target.value})} className="w-full px-3 py-2 border rounded-lg outline-none">
                      <option value="">No tax benefit</option>
                      <option value="80C">80C</option>
                      <option value="80CCD(1B)">80CCD(1B)</option>
                      <option value="80D">80D</option>
                    </select>
                  </div>
                </div>
                {newInvestment.principal && newInvestment.rate && newInvestment.startDate && newInvestment.tenureMonths && (
                  <div className="rounded-xl border border-indigo-100 bg-indigo-50 p-4 text-sm text-slate-700">
                    <div className="flex items-center justify-between">
                      <span>Maturity Date</span>
                      <span className="font-semibold">{addMonthsToDate(newInvestment.startDate, Number(newInvestment.tenureMonths))}</span>
                    </div>
                    <div className="mt-2 flex items-center justify-between">
                      <span>Maturity Amount</span>
                      <span className="font-semibold">₹{Math.round(calculateFdMaturityAmount(Number(newInvestment.principal), Number(newInvestment.rate), Number(newInvestment.tenureMonths))).toLocaleString()}</span>
                    </div>
                  </div>
                )}
                <button onClick={handleAddInvestment} className="w-full py-3 bg-indigo-100 text-indigo-700 rounded-xl font-medium hover:bg-indigo-200 transition-colors">Add to Portfolio</button>
              </div>
                <div className="bg-slate-50 p-6 rounded-xl border border-slate-200 space-y-4">
                  <h3 className="font-semibold text-slate-800 mb-2 flex items-center gap-2"><Plus className="w-4 h-4" /> Add Active Loan</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="col-span-2">
                      <label className="block text-xs font-medium text-slate-600 mb-1">Loan Type</label>
                      <select value={newLoan.type} onChange={(e) => setNewLoan({...newLoan, type: e.target.value})} className="w-full px-3 py-2 border rounded-lg outline-none">
                        {['Home Loan', 'Car Loan', 'Personal Loan', 'Education Loan', 'Credit Card', 'Other'].map(t => <option key={t} value={t}>{t}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-600 mb-1">Loan Amount (₹)</label>
                      <input type="number" value={newLoan.amount} onChange={(e) => setNewLoan({...newLoan, amount: e.target.value})} className="w-full px-3 py-2 border rounded-lg outline-none" />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-600 mb-1">Interest Rate (%)</label>
                      <input type="number" value={newLoan.rate} onChange={(e) => setNewLoan({...newLoan, rate: e.target.value})} className="w-full px-3 py-2 border rounded-lg outline-none" />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-600 mb-1">Start Date</label>
                      <input type="date" value={newLoan.startDate} onChange={(e) => setNewLoan({...newLoan, startDate: e.target.value})} className="w-full px-3 py-2 border rounded-lg outline-none" />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-600 mb-1">Tenure (Months)</label>
                      <input type="number" value={newLoan.tenureMonths} onChange={(e) => setNewLoan({...newLoan, tenureMonths: e.target.value})} className="w-full px-3 py-2 border rounded-lg outline-none" />
                    </div>
                  </div>
                  {newLoan.amount && newLoan.rate && newLoan.startDate && newLoan.tenureMonths && (
                    <div className="rounded-xl border border-emerald-100 bg-emerald-50 p-4 text-sm text-slate-700">
                      <div className="flex items-center justify-between">
                        <span>Loan End Date</span>
                        <span className="font-semibold">{addMonthsToDate(newLoan.startDate, Number(newLoan.tenureMonths))}</span>
                      </div>
                      <div className="mt-2 flex items-center justify-between">
                        <span>Estimated EMI</span>
                        <span className="font-semibold">₹{Math.round(calculateLoanEmi(Number(newLoan.amount), Number(newLoan.rate), Number(newLoan.tenureMonths))).toLocaleString()}</span>
                      </div>
                    </div>
                  )}
                  <button onClick={handleAddLoan} className="w-full py-3 bg-emerald-100 text-emerald-700 rounded-xl font-medium hover:bg-emerald-200 transition-colors">Add Loan</button>
                </div>
              </div>
              <div className="space-y-6 xl:col-span-7">
                <div className="space-y-4">
                <h3 className="font-semibold text-slate-800">Your Fixed Assets</h3>
                <div className="space-y-3 max-h-[350px] overflow-y-auto pr-2">
                  {investments.length === 0 ? (
                    <div className="text-center py-12 border-2 border-dashed rounded-xl text-slate-400">No investments added yet.</div>
                  ) : (
                    investments.map((inv) => (
                      <div key={inv.id} className="bg-white p-4 rounded-xl border border-slate-200 flex items-center justify-between shadow-sm">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-indigo-50 rounded-full flex items-center justify-center text-indigo-600 font-bold text-xs">{inv.type}</div>
                          <div>
                            <p className="text-sm font-bold text-slate-800">₹{Number(inv.principal).toLocaleString()}</p>
                            <p className="text-xs text-slate-500">{inv.rate}% Interest • {inv.startDate} • {inv.tenureMonths} mo</p>
                            <p className="text-xs text-slate-500">Matures on {inv.maturityDate} • ₹{Math.round(Number(inv.maturityAmount) || 0).toLocaleString()}</p>
                          </div>
                        </div>
                        <button onClick={() => setInvestments(investments.filter(i => i.id !== inv.id))} className="text-slate-300 hover:text-red-500"><Trash2 className="w-4 h-4" /></button>
                      </div>
                    ))
                  )}
                </div>
                </div>
                <div className="space-y-4">
                  <h3 className="font-semibold text-slate-800">Your Active Loans</h3>
                  <div className="space-y-3 max-h-[250px] overflow-y-auto pr-2">
                    {loans.length === 0 ? (
                      <div className="text-center py-12 border-2 border-dashed rounded-xl text-slate-400">No loans added yet.</div>
                    ) : (
                      loans.map((loan) => (
                        <div key={loan.id} className="bg-white p-4 rounded-xl border border-slate-200 flex items-center justify-between shadow-sm">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-emerald-50 rounded-full flex items-center justify-center text-emerald-600 font-bold text-[10px] text-center">{loan.type}</div>
                            <div>
                              <p className="text-sm font-bold text-slate-800">₹{Number(loan.amount).toLocaleString()}</p>
                              <p className="text-xs text-slate-500">{loan.rate}% Interest • {loan.tenureMonths} mo • EMI ₹{Math.round(Number(loan.monthlyEmi) || 0).toLocaleString()}</p>
                              <p className="text-xs text-slate-500">Ends on {loan.endDate}</p>
                            </div>
                          </div>
                          <button onClick={() => setLoans(loans.filter((item) => item.id !== loan.id))} className="text-slate-300 hover:text-red-500"><Trash2 className="w-4 h-4" /></button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
                <div className="flex gap-3 pt-4">
                  <button onClick={() => setStep(4)} className="px-4 py-3 border rounded-xl hover:bg-slate-100"><ArrowLeft className="w-5 h-5" /></button>
                  <button onClick={() => setStep(6)} className="flex-1 py-3 bg-indigo-600 text-white rounded-xl font-medium flex items-center justify-center gap-2">Continue <ArrowRight className="w-4 h-4" /></button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 6: Summary & Finish */}
        {step === 6 && (
          <div className="space-y-6 animate-in fade-in slide-in-from-right-4">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold text-slate-800">Review & Finish</h2>
              <p className="text-slate-600 text-sm">We've gathered your financial profile. Ready to see your dashboard?</p>
            </div>
            <div className="bg-slate-50 rounded-xl p-6 border border-slate-200 space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Monthly Net Salary</span>
                <span className="font-bold text-slate-800">₹{Number(salaryData.netSalary).toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Equity Gains (FY)</span>
                <span className="font-bold text-emerald-600">₹{totalEquityGain.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Avg. Monthly Expenses</span>
                <span className="font-bold text-red-600">₹{totalMonthlyExpense.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Fixed Investments</span>
                <span className="font-bold text-slate-800">{investments.length} Assets</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Active Loans</span>
                <span className="font-bold text-slate-800">{loans.length} Loans</span>
              </div>
            </div>
            <div className="flex gap-3 pt-4">
              <button onClick={() => setStep(5)} className="px-4 py-3 border rounded-xl hover:bg-slate-100"><ArrowLeft className="w-5 h-5" /></button>
              <button onClick={handleFinish} disabled={isFinishing} className="flex-1 py-3 bg-indigo-600 text-white rounded-xl font-medium flex items-center justify-center gap-2">
                {isFinishing ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Finish Setup'}
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
