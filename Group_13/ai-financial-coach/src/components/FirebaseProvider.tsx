import React, { createContext, useContext, useEffect, useState } from 'react';
import { apiClient } from '../lib/api';

interface AuthContextType {
  user: any | null;
  userProfile: any | null;
  latestSalary: any | null;
  salaryHistory: any[];
  healthScores: any[];
  otherIncomes: any[];
  investments: any[];
  goals: any[];
  taxBenefits: any[];
  loans: any[];
  equityTrades: any[];
  expenses: any[];
  loading: boolean;
  refreshProfile: () => Promise<void>;
  logout: () => void;
  login: (data: any) => Promise<any>;
  register: (data: any) => Promise<any>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  userProfile: null,
  latestSalary: null,
  salaryHistory: [],
  healthScores: [],
  otherIncomes: [],
  investments: [],
  goals: [],
  taxBenefits: [],
  loans: [],
  equityTrades: [],
  expenses: [],
  loading: true,
  refreshProfile: async () => {},
  logout: () => {},
  login: async () => {},
  register: async () => {},
});

export const useFirebase = () => useContext(AuthContext); // Keeping name for compatibility

export const FirebaseProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<any | null>(null);
  const [userProfile, setUserProfile] = useState<any | null>(null);
  const [latestSalary, setLatestSalary] = useState<any | null>(null);
  const [salaryHistory, setSalaryHistory] = useState<any[]>([]);
  const [healthScores, setHealthScores] = useState<any[]>([]);
  const [otherIncomes, setOtherIncomes] = useState<any[]>([]);
  const [investments, setInvestments] = useState<any[]>([]);
  const [goals, setGoals] = useState<any[]>([]);
  const [taxBenefits, setTaxBenefits] = useState<any[]>([]);
  const [loans, setLoans] = useState<any[]>([]);
  const [equityTrades, setEquityTrades] = useState<any[]>([]);
  const [expenses, setExpenses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [
        profileResult,
        salaryResult,
        salariesResult,
        healthScoresResult,
        incomesResult,
        investmentsResult,
        goalsResult,
        taxBenefitsResult,
        loansResult,
        tradesResult,
        expensesResult,
      ] = await Promise.allSettled([
        apiClient.getProfile(),
        apiClient.getLatestSalary(),
        apiClient.getSalaryHistory(),
        apiClient.getHealthScores(),
        apiClient.getOtherIncomes(),
        apiClient.getInvestments(),
        apiClient.getGoals(),
        apiClient.getTaxBenefits(),
        apiClient.getLoans(),
        apiClient.getTrades(),
        apiClient.getExpenses()
      ]);

      if (profileResult.status !== 'fulfilled') {
        throw profileResult.reason;
      }

      const profile = profileResult.value;
      const salary = salaryResult.status === 'fulfilled' ? salaryResult.value : null;
      const salaries = salariesResult.status === 'fulfilled' ? salariesResult.value : [];
      const scores = healthScoresResult.status === 'fulfilled' ? healthScoresResult.value : [];
      const incomes = incomesResult.status === 'fulfilled' ? incomesResult.value : [];
      const invs = investmentsResult.status === 'fulfilled' ? investmentsResult.value : [];
      const goalsData = goalsResult.status === 'fulfilled' ? goalsResult.value : [];
      const benefitEntries = taxBenefitsResult.status === 'fulfilled' ? taxBenefitsResult.value : [];
      const fetchedLoans = loansResult.status === 'fulfilled' ? loansResult.value : [];
      const trades = tradesResult.status === 'fulfilled' ? tradesResult.value : [];
      const exps = expensesResult.status === 'fulfilled' ? expensesResult.value : [];

      setUser(profile);
      setUserProfile(profile);
      setLatestSalary(salary);
      setSalaryHistory(salaries);
      setHealthScores(scores);
      setOtherIncomes(incomes);
      setInvestments(invs);
      setGoals(goalsData);
      setTaxBenefits(benefitEntries);
      setLoans(fetchedLoans);
      setEquityTrades(trades);
      setExpenses(exps);

      if (taxBenefitsResult.status !== 'fulfilled') {
        console.warn('Tax benefits could not be loaded. Continuing without them.', taxBenefitsResult.reason);
      }
    } catch (err) {
      console.error("Error fetching data from SQL:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      fetchData();
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (data: any) => {
    const result = await apiClient.login(data);
    if (result.user) {
      setUser(result.user);
      setUserProfile(result.user);
      await fetchData();
    }
    return result;
  };

  const register = async (data: any) => {
    const result = await apiClient.register(data);
    if (result.user) {
      setUser(result.user);
      setUserProfile(result.user);
      await fetchData();
    }
    return result;
  };

  const logout = () => {
    apiClient.logout();
    setUser(null);
    setUserProfile(null);
    setLatestSalary(null);
    setSalaryHistory([]);
    setHealthScores([]);
    setOtherIncomes([]);
    setInvestments([]);
    setGoals([]);
    setTaxBenefits([]);
    setLoans([]);
    setEquityTrades([]);
    setExpenses([]);
  };

  const refreshProfile = async () => {
    await fetchData();
  };

  return (
      <AuthContext.Provider value={{ 
        user, 
        userProfile, 
        latestSalary,
        salaryHistory,
        healthScores,
        otherIncomes, 
        investments, 
        goals,
        taxBenefits,
        loans,
        equityTrades, 
      expenses, 
      loading, 
      refreshProfile, 
      logout,
      login,
      register
    }}>
      {children}
    </AuthContext.Provider>
  );
};
