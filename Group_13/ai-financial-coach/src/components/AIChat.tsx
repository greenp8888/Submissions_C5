import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, Bot, User, BrainCircuit, Loader2, ArrowUpRight, Paperclip, X
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { apiClient } from '../lib/api';

type ProgressStep = {
  step: string;
  label: string;
  detail?: string;
};

type Message = {
  id: string;
  role: 'user' | 'model';
  content: string;
  isError?: boolean;
  dashboardUpdates?: any;
  routedAgent?: string | null;
  vectorDatabase?: string | null;
  retrievedDocuments?: Array<{ title: string; sourceType: string; score: number }>;
  progressSteps?: ProgressStep[];
};

type Attachment = {
  filename: string;
  mimeType: string;
  data: string;
};

const currencyFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
});

const percentFormatter = (value: unknown, digits = 1) => `${Number(value || 0).toFixed(digits)}%`;

export default function AIChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [progressSteps, setProgressSteps] = useState<ProgressStep[]>([]);
  const [attachment, setAttachment] = useState<Attachment | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const progressStepsRef = useRef<ProgressStep[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isChatOpen) scrollToBottom();
  }, [messages, isChatOpen]);

  const handleSend = async (text: string = input) => {
    if ((!text.trim() && !attachment) || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text.trim() || (attachment ? `Uploaded document: ${attachment.filename}` : ''),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setIsChatOpen(true);
    setProgressSteps([]);
    progressStepsRef.current = [];

    try {
      const history = messages.map((message) => ({
        role: message.role,
        content: message.content,
        dashboardUpdates: message.dashboardUpdates,
        routedAgent: message.routedAgent,
      }));
      let resultPayload: any = null;
      await apiClient.chatStream({
        message: text.trim(),
        history,
        attachment,
      }, {
        onStatus: (event) => {
          setProgressSteps((prev) => {
            const next = prev.filter((item) => item.step !== event.step);
            next.push({
              step: event.step,
              label: event.label,
              detail: event.detail,
            });
            progressStepsRef.current = next;
            return next;
          });
        },
        onResult: (payload) => {
          resultPayload = payload;
        }
      });

      const modelMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'model',
        content: resultPayload?.reply || "I processed your request.",
        dashboardUpdates: resultPayload?.dashboardUpdates || {},
        routedAgent: resultPayload?.routedAgent || null,
        vectorDatabase: resultPayload?.vectorDatabase || null,
        retrievedDocuments: resultPayload?.retrievedDocuments || [],
        progressSteps: [...progressStepsRef.current, { step: 'done', label: 'Response ready' }],
      };

      setMessages((prev) => [...prev, modelMessage]);
      setAttachment(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (error) {
      console.error("Error generating response:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'model',
        content: "I'm sorry, I encountered an error connecting to the AI agent.",
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setProgressSteps([]);
      progressStepsRef.current = [];
    }
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      setAttachment({
        filename: file.name,
        mimeType: file.type || 'application/octet-stream',
        data: String(reader.result || ''),
      });
      setIsChatOpen(true);
    };
    reader.readAsDataURL(file);
  };

  const renderProgressSteps = (steps: ProgressStep[], active = false) => (
    <div className="mt-3 rounded-xl border border-slate-100 bg-slate-50 p-3">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Pipeline activity</p>
      <div className="mt-2 space-y-2">
        {steps.map((item, index) => {
          const isLatest = active && index === steps.length - 1;
          return (
            <div key={`${item.step}-${index}`} className="flex items-start gap-2 text-xs text-slate-600">
              <span className={`mt-0.5 h-2.5 w-2.5 rounded-full ${isLatest ? 'bg-indigo-500 animate-pulse' : 'bg-emerald-500'}`} />
              <div>
                <p className="font-medium text-slate-700">{item.label}</p>
                {item.detail ? <p className="text-slate-500">{item.detail}</p> : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  const renderDebtCard = (msg: Message) => {
    const debt = msg.dashboardUpdates?.debtAnalysis;
    if (!debt) return null;

    const riskTone = debt.dti_risk_level === 'HIGH'
      ? 'text-red-700 bg-red-50 border-red-100'
      : debt.dti_risk_level === 'MEDIUM'
        ? 'text-amber-700 bg-amber-50 border-amber-100'
        : 'text-emerald-700 bg-emerald-50 border-emerald-100';

    return (
      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Debt analysis</p>
            <p className="mt-1 text-sm font-semibold text-slate-800">
              {String(debt.recommended_strategy || '').toUpperCase()} strategy recommended
            </p>
          </div>
          <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${riskTone}`}>
            {debt.dti_risk_level} risk
          </span>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3 text-xs text-slate-600">
          <div className="rounded-xl bg-white px-3 py-3">
            <p className="uppercase tracking-wide text-slate-400">DTI ratio</p>
            <p className="mt-1 text-lg font-semibold text-slate-800">{Number(debt.dti_ratio || 0).toFixed(2)}%</p>
          </div>
          <div className="rounded-xl bg-white px-3 py-3">
            <p className="uppercase tracking-wide text-slate-400">Total debt</p>
            <p className="mt-1 text-lg font-semibold text-slate-800">{currencyFormatter.format(Number(debt.total_outstanding_debt || 0))}</p>
          </div>
          <div className="rounded-xl bg-white px-3 py-3">
            <p className="uppercase tracking-wide text-slate-400">Monthly EMI</p>
            <p className="mt-1 text-lg font-semibold text-slate-800">{currencyFormatter.format(Number(debt.monthly_emi_total || 0))}</p>
          </div>
        </div>

        {debt.debt_breakdown?.length ? (
          <div className="mt-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Active loans</p>
            <div className="mt-2 space-y-2">
              {debt.debt_breakdown.map((loan: any, index: number) => (
                <div key={`${loan.name}-${index}`} className="rounded-xl bg-white px-3 py-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-slate-800">{loan.name}</p>
                    <p className="text-sm text-slate-500">{loan.interest_rate}% interest</p>
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-slate-600 sm:grid-cols-3">
                    <div>
                      <p className="text-slate-400">Outstanding</p>
                      <p className="mt-1 font-semibold text-slate-800">{currencyFormatter.format(Number(loan.outstanding || 0))}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">EMI</p>
                      <p className="mt-1 font-semibold text-slate-800">{currencyFormatter.format(Number(loan.monthly_emi || 0))}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Months left</p>
                      <p className="mt-1 font-semibold text-slate-800">{Number(loan.months_remaining || 0)}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        <div className="mt-4 rounded-xl bg-white px-3 py-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Recommendation</p>
          <p className="mt-2 text-sm leading-relaxed text-slate-700">{debt.recommendation_reason}</p>
          <p className="mt-2 text-sm font-semibold text-slate-800">
            Potential interest savings: {currencyFormatter.format(Number(debt.interest_savings_by_choosing_recommended || 0))}
          </p>
        </div>

        {msg.dashboardUpdates?.action_items?.length ? (
          <div className="mt-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Next action items</p>
            <div className="mt-2 space-y-2">
              {msg.dashboardUpdates.action_items.map((item: string, index: number) => (
                <div key={`debt-action-${index}`} className="rounded-xl bg-white px-3 py-2 text-sm text-slate-700">
                  {item}
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {msg.progressSteps?.length ? renderProgressSteps(msg.progressSteps) : null}
      </div>
    );
  };

  const renderBudgetCard = (msg: Message) => {
    const budget = msg.dashboardUpdates?.budgetAnalysis;
    if (!budget) return null;

    return (
      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Budget analysis</p>
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3 text-xs text-slate-600">
          <div className="rounded-xl bg-white px-3 py-3">
            <p className="uppercase tracking-wide text-slate-400">Total spent</p>
            <p className="mt-1 text-lg font-semibold text-slate-800">{currencyFormatter.format(Number(budget.total_spent || 0))}</p>
          </div>
          <div className="rounded-xl bg-white px-3 py-3">
            <p className="uppercase tracking-wide text-slate-400">Budget</p>
            <p className="mt-1 text-lg font-semibold text-slate-800">{currencyFormatter.format(Number(budget.total_budget || 0))}</p>
          </div>
          <div className="rounded-xl bg-white px-3 py-3">
            <p className="uppercase tracking-wide text-slate-400">Potential savings</p>
            <p className="mt-1 text-lg font-semibold text-slate-800">{currencyFormatter.format(Number(budget.total_potential_saving || 0))}</p>
          </div>
        </div>

        {budget.category_breakdown?.length ? (
          <div className="mt-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Category breakdown</p>
            <div className="mt-2 space-y-2">
              {budget.category_breakdown.slice(0, 6).map((item: any, index: number) => (
                <div key={`${item.category}-${index}`} className="flex items-center justify-between rounded-xl bg-white px-3 py-2 text-sm">
                  <div>
                    <p className="font-semibold text-slate-800">{item.category}</p>
                    <p className="text-xs text-slate-500">{item.status} · overspend {percentFormatter(item.overspend_pct || 0)}</p>
                  </div>
                  <p className="font-semibold text-slate-800">{currencyFormatter.format(Number(item.spent || 0))}</p>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {budget.reduction_suggestions?.length ? (
          <div className="mt-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Top reduction suggestions</p>
            <div className="mt-2 space-y-2">
              {budget.reduction_suggestions.map((item: any, index: number) => (
                <div key={`budget-suggestion-${index}`} className="rounded-xl bg-white px-3 py-3">
                  <p className="text-sm font-semibold text-slate-800">{item.title}</p>
                  <p className="mt-1 text-sm text-slate-600">{item.description}</p>
                  <p className="mt-2 text-sm font-semibold text-slate-800">Save about {currencyFormatter.format(Number(item.estimated_monthly_saving || 0))}/month</p>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {budget.finance_tip ? (
          <div className="mt-4 rounded-xl bg-white px-3 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Tip</p>
            <p className="mt-2 text-sm text-slate-700">{budget.finance_tip}</p>
          </div>
        ) : null}
        {msg.progressSteps?.length ? renderProgressSteps(msg.progressSteps) : null}
      </div>
    );
  };

  const renderSavingsCard = (msg: Message) => {
    const savings = msg.dashboardUpdates?.savingsPlan;
    if (!savings) return null;

    return (
      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Savings strategy</p>
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3 text-xs text-slate-600">
          <div className="rounded-xl bg-white px-3 py-3">
            <p className="uppercase tracking-wide text-slate-400">Monthly surplus</p>
            <p className="mt-1 text-lg font-semibold text-slate-800">{currencyFormatter.format(Number(savings.monthly_surplus || 0))}</p>
          </div>
          <div className="rounded-xl bg-white px-3 py-3">
            <p className="uppercase tracking-wide text-slate-400">Emergency fund gap</p>
            <p className="mt-1 text-lg font-semibold text-slate-800">{currencyFormatter.format(Number(savings.emergency_fund_gap || 0))}</p>
          </div>
          <div className="rounded-xl bg-white px-3 py-3">
            <p className="uppercase tracking-wide text-slate-400">Surplus after SIPs</p>
            <p className="mt-1 text-lg font-semibold text-slate-800">{currencyFormatter.format(Number(savings.surplus_after_all_sips || 0))}</p>
          </div>
        </div>
        {savings.goal_sip_plan?.length ? (
          <div className="mt-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Goal SIP plan</p>
            <div className="mt-2 space-y-2">
              {savings.goal_sip_plan.map((goal: any, index: number) => (
                <div key={`sip-${index}`} className="rounded-xl bg-white px-3 py-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-slate-800">{goal.goal_name}</p>
                    <p className="text-sm text-slate-500">{goal.on_track ? 'On track' : 'Needs attention'}</p>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">Invest {currencyFormatter.format(Number(goal.required_monthly_sip || 0))}/month for {goal.months_remaining} months</p>
                  <p className="mt-1 text-sm text-slate-600">Suggested category: {goal.recommended_fund_category}</p>
                </div>
              ))}
            </div>
          </div>
        ) : null}
        {savings.warnings?.length ? (
          <div className="mt-4 space-y-2">
            {savings.warnings.map((warning: string, index: number) => (
              <div key={`saving-warning-${index}`} className="rounded-xl border border-amber-100 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                {warning}
              </div>
            ))}
          </div>
        ) : null}
        {msg.progressSteps?.length ? renderProgressSteps(msg.progressSteps) : null}
      </div>
    );
  };

  const renderPortfolioCard = (msg: Message) => {
    const portfolio = msg.dashboardUpdates?.portfolioAnalysis?.portfolio_summary || msg.dashboardUpdates?.portfolioSuggestion;
    if (!portfolio) return null;
    const stressTests = msg.dashboardUpdates?.portfolioAnalysis?.stress_test || msg.dashboardUpdates?.portfolioStressTest || [];

    return (
      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Portfolio analysis</p>
        <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-slate-600">
          {Object.entries(portfolio.current_allocation || {}).map(([assetClass, value]) => (
            <div key={`portfolio-current-${assetClass}`} className="rounded-xl bg-white px-3 py-3">
              <p className="uppercase tracking-wide text-slate-400">Current {assetClass}</p>
              <p className="mt-1 text-lg font-semibold text-slate-800">{percentFormatter(value || 0)}</p>
            </div>
          ))}
        </div>
        {portfolio.rebalancing_actions?.length ? (
          <div className="mt-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Exact action items</p>
            <div className="mt-2 space-y-2">
              {portfolio.rebalancing_actions.map((action: any, index: number) => (
                <div key={`portfolio-action-${index}`} className="rounded-xl bg-white px-3 py-3 text-sm">
                  <p className="font-semibold text-slate-800">{String(action.action || '').toUpperCase()} {currencyFormatter.format(Number(action.amount || 0))} of {action.asset_class}</p>
                  {action.reason ? <p className="mt-1 text-slate-600">{action.reason}</p> : null}
                </div>
              ))}
            </div>
          </div>
        ) : null}
        {stressTests?.length ? (
          <div className="mt-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Stress test</p>
            <div className="mt-2 space-y-2">
              {stressTests.map((item: any, index: number) => (
                <div key={`stress-${index}`} className="flex items-center justify-between rounded-xl bg-white px-3 py-2 text-sm">
                  <span className="text-slate-700">{item.scenario}</span>
                  <span className="font-semibold text-slate-800">{currencyFormatter.format(Number(item.estimated_loss_amount || 0))}</span>
                </div>
              ))}
            </div>
          </div>
        ) : null}
        {msg.progressSteps?.length ? renderProgressSteps(msg.progressSteps) : null}
      </div>
    );
  };

  const renderTaxCard = (msg: Message) => {
    const tax = msg.dashboardUpdates?.taxAnalysis?.tax_summary;
    if (!tax) return null;
    return (
      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Tax optimization</p>
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3 text-xs text-slate-600">
          <div className="rounded-xl bg-white px-3 py-3">
            <p className="uppercase tracking-wide text-slate-400">80C used</p>
            <p className="mt-1 text-lg font-semibold text-slate-800">{currencyFormatter.format(Number(tax.section_80c_invested || 0))}</p>
          </div>
          <div className="rounded-xl bg-white px-3 py-3">
            <p className="uppercase tracking-wide text-slate-400">80C gap</p>
            <p className="mt-1 text-lg font-semibold text-slate-800">{currencyFormatter.format(Number(tax.section_80c_gap || 0))}</p>
          </div>
          <div className="rounded-xl bg-white px-3 py-3">
            <p className="uppercase tracking-wide text-slate-400">Potential savings</p>
            <p className="mt-1 text-lg font-semibold text-slate-800">{currencyFormatter.format(Number(tax.potential_additional_tax_saving || 0))}</p>
          </div>
        </div>
        {tax.recommended_instruments?.length ? (
          <div className="mt-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Recommended instruments</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {tax.recommended_instruments.map((instrument: string, index: number) => (
                <span key={`instrument-${index}`} className="rounded-full border border-slate-200 bg-white px-3 py-1 text-sm text-slate-700">{instrument}</span>
              ))}
            </div>
          </div>
        ) : null}
        {msg.dashboardUpdates?.action_items?.length ? (
          <div className="mt-4 space-y-2">
            {msg.dashboardUpdates.action_items.map((item: string, index: number) => (
              <div key={`tax-action-${index}`} className="rounded-xl bg-white px-3 py-2 text-sm text-slate-700">{item}</div>
            ))}
          </div>
        ) : null}
        {msg.progressSteps?.length ? renderProgressSteps(msg.progressSteps) : null}
      </div>
    );
  };

  const renderGoalsCard = (msg: Message) => {
    const goals = msg.dashboardUpdates?.goalPlan;
    if (!goals) return null;
    return (
      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Goal planning</p>
        {goals.financial_health_score ? (
          <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-slate-600 sm:grid-cols-4">
            <div className="rounded-xl bg-white px-3 py-3"><p className="text-slate-400">Overall</p><p className="mt-1 text-lg font-semibold text-slate-800">{Number(goals.financial_health_score.overall || 0)}</p></div>
            <div className="rounded-xl bg-white px-3 py-3"><p className="text-slate-400">Savings</p><p className="mt-1 text-lg font-semibold text-slate-800">{Number(goals.financial_health_score.savings_rate_score || 0)}</p></div>
            <div className="rounded-xl bg-white px-3 py-3"><p className="text-slate-400">Debt</p><p className="mt-1 text-lg font-semibold text-slate-800">{Number(goals.financial_health_score.debt_score || 0)}</p></div>
            <div className="rounded-xl bg-white px-3 py-3"><p className="text-slate-400">Emergency</p><p className="mt-1 text-lg font-semibold text-slate-800">{Number(goals.financial_health_score.emergency_fund_score || 0)}</p></div>
          </div>
        ) : null}
        {goals.goals?.length ? (
          <div className="mt-4 space-y-2">
            {goals.goals.map((goal: any, index: number) => (
              <div key={`goal-${index}`} className="rounded-xl bg-white px-3 py-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-slate-800">{goal.name}</p>
                  <p className="text-sm text-slate-500">{percentFormatter(goal.progress_pct || 0)}</p>
                </div>
                <p className="mt-1 text-sm text-slate-600">{currencyFormatter.format(Number(goal.current_saved || 0))} saved of {currencyFormatter.format(Number(goal.target_inflation_adjusted || 0))}</p>
                <p className="mt-1 text-sm text-slate-600">Need {currencyFormatter.format(Number(goal.required_monthly_sip || 0))}/month for {goal.months_remaining} months</p>
                {goal.at_risk ? <p className="mt-2 text-sm text-red-700">{goal.risk_reason}</p> : null}
              </div>
            ))}
          </div>
        ) : null}
        {goals.what_if_scenario ? (
          <div className="mt-4 rounded-xl bg-white px-3 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">What-if scenario</p>
            <p className="mt-2 text-sm text-slate-700">{goals.what_if_scenario.impact}</p>
          </div>
        ) : null}
        {msg.progressSteps?.length ? renderProgressSteps(msg.progressSteps) : null}
      </div>
    );
  };

  const renderCoachCard = (msg: Message) => {
    const coach = msg.dashboardUpdates?.coachSummary;
    if (!coach) return null;
    return (
      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Financial coach</p>
            <p className="mt-1 text-lg font-semibold text-slate-800">{coach.score_label}</p>
          </div>
        </div>
        <p className="mt-4 rounded-xl bg-white px-3 py-3 text-sm text-slate-700">{coach.headline}</p>
        {coach.strengths?.length ? (
          <div className="mt-4 space-y-2">
            {coach.strengths.map((item: string, index: number) => (
              <div key={`strength-${index}`} className="rounded-xl bg-white px-3 py-2 text-sm text-slate-700">{item}</div>
            ))}
          </div>
        ) : null}
        {coach.priority_actions?.length ? (
          <div className="mt-4 space-y-2">
            {coach.priority_actions.map((item: string, index: number) => (
              <div key={`coach-action-${index}`} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">{item}</div>
            ))}
          </div>
        ) : null}
        {coach.motivation_line ? <p className="mt-4 text-sm italic text-slate-600">{coach.motivation_line}</p> : null}
        {msg.progressSteps?.length ? renderProgressSteps(msg.progressSteps) : null}
      </div>
    );
  };

  const renderLiteracyCard = (msg: Message) => {
    const literacy = msg.dashboardUpdates?.literacyLesson;
    if (!literacy) return null;
    const quiz = literacy.quiz;
    const quizResult = msg.dashboardUpdates?.quizResult;
    const review = literacy.review;
    return (
      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Financial literacy</p>
        {literacy.topic ? <p className="mt-1 text-lg font-semibold text-slate-800">{literacy.topic}</p> : null}
        {literacy.daily_tip ? (
          <div className="mt-4 rounded-xl bg-white px-3 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Daily tip</p>
            <p className="mt-2 text-sm text-slate-700">{literacy.daily_tip.text}</p>
          </div>
        ) : null}
        {literacy.micro_lesson ? (
          <div className="mt-4 rounded-xl bg-white px-3 py-3">
            <p className="text-sm font-semibold text-slate-800">{literacy.micro_lesson.title}</p>
            <div className="mt-2 space-y-1">
              {(literacy.micro_lesson.bullets || []).map((bullet: string, index: number) => (
                <p key={`bullet-${index}`} className="text-sm text-slate-700">{bullet}</p>
              ))}
            </div>
          </div>
        ) : null}
        {quiz ? (
          <div className="mt-4 rounded-xl border border-indigo-100 bg-white px-3 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Question {quiz.questionNumber} of {quiz.totalQuestions}
            </p>
            <p className="text-sm font-semibold text-slate-800">{quiz.question}</p>
            <div className="mt-2 space-y-2">
              {(quiz.options || []).map((option: string, index: number) => (
                <div key={`option-${index}`} className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">{option}</div>
              ))}
            </div>
            <p className="mt-3 text-xs text-slate-500">Reply with just the option letter to continue.</p>
          </div>
        ) : null}
        {review ? (
          <div className="mt-4 rounded-xl bg-white px-3 py-3">
            <p className="text-sm font-semibold text-slate-800">Score: {review.score}/{review.totalQuestions}</p>
            {review.improvementAreas?.length ? (
              <div className="mt-3 space-y-2">
                {review.improvementAreas.map((item: string, index: number) => (
                  <div key={`improvement-${index}`} className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">{item}</div>
                ))}
              </div>
            ) : null}
            {review.suggestion ? <p className="mt-3 text-sm text-slate-700">{review.suggestion}</p> : null}
          </div>
        ) : null}
        {quizResult ? (
          <div className={`mt-4 rounded-xl px-3 py-2 text-sm ${quizResult.isCorrect ? 'bg-emerald-50 text-emerald-800' : 'bg-amber-50 text-amber-800'}`}>
            {quiz ? (quizResult.isCorrect ? 'Correct answer recorded.' : `That one was incorrect. The correct answer was ${quizResult.expectedAnswer}.`) : msg.content}
          </div>
        ) : null}
        {literacy.points_awarded ? <p className="mt-4 text-sm font-semibold text-slate-800">Points awarded: +{literacy.points_awarded}</p> : null}
        {literacy.badge_unlocked ? <p className="mt-1 text-sm text-slate-600">Badge unlocked: {literacy.badge_unlocked}</p> : null}
        {msg.progressSteps?.length ? renderProgressSteps(msg.progressSteps) : null}
      </div>
    );
  };

  const renderDocumentCard = (msg: Message) => {
    const document = msg.dashboardUpdates?.documentAnalysis;
    if (!document) return null;
    return (
      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Document parser</p>
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 text-xs text-slate-600">
          <div className="rounded-xl bg-white px-3 py-3">
            <p className="uppercase tracking-wide text-slate-400">Document type</p>
            <p className="mt-1 text-lg font-semibold text-slate-800">{String(document.document_type || 'unknown').replace(/_/g, ' ')}</p>
          </div>
          <div className="rounded-xl bg-white px-3 py-3">
            <p className="uppercase tracking-wide text-slate-400">Account holder</p>
            <p className="mt-1 text-lg font-semibold text-slate-800">{document.account_holder_name || 'Not found'}</p>
          </div>
        </div>
        {document.key_summary_figures ? (
          <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-slate-600 sm:grid-cols-3">
            {Object.entries(document.key_summary_figures).filter(([, value]) => value !== undefined && value !== null && value !== '').map(([key, value]) => (
              <div key={`summary-${key}`} className="rounded-xl bg-white px-3 py-3">
                <p className="uppercase tracking-wide text-slate-400">{key.replace(/_/g, ' ')}</p>
                <p className="mt-1 text-sm font-semibold text-slate-800">{typeof value === 'number' ? currencyFormatter.format(Number(value)) : String(value)}</p>
              </div>
            ))}
          </div>
        ) : null}
        {document.tables?.length ? <p className="mt-4 text-sm text-slate-700">{document.tables.length} table(s) extracted</p> : null}
        {document.extraction_notes?.length ? (
          <div className="mt-4 space-y-2">
            {document.extraction_notes.map((note: string, index: number) => (
              <div key={`doc-note-${index}`} className="rounded-xl bg-white px-3 py-2 text-sm text-slate-700">{note}</div>
            ))}
          </div>
        ) : null}
        {msg.progressSteps?.length ? renderProgressSteps(msg.progressSteps) : null}
      </div>
    );
  };

  const quickPrompts = [
    "Analyze my debt and suggest avalanche vs snowball payoff",
    "Build a savings plan for my emergency fund and goals",
    "Show where I can reduce my monthly expenses",
    "Rebalance my portfolio based on my current holdings",
    "Find tax-saving opportunities under 80C and 80D",
    "Am I on track for my goals?",
    "Explain my financial health score simply",
    "Teach me budgeting with a quiz based on my finances"
  ];

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-slate-200 bg-[#FDFDF9]/95 p-4 backdrop-blur-xl shadow-[0_-10px_40px_-15px_rgba(15,23,42,0.08)]">
      <div className={`${messages.some((msg) => msg.content.length > 500 || JSON.stringify(msg.dashboardUpdates || {}).length > 1200) ? 'max-w-[90vw]' : 'max-w-4xl'} mx-auto transition-all duration-300`}>
        <AnimatePresence>
          {isChatOpen && (
            <motion.div 
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: messages.some((msg) => msg.content.length > 500 || JSON.stringify(msg.dashboardUpdates || {}).length > 1200) ? '75vh' : '400px', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="mb-4 flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
            >
              <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 p-3">
                <div className="flex items-center gap-2">
                  <BrainCircuit className="w-5 h-5 text-indigo-600" />
                  <span className="font-semibold text-sm text-slate-800">AI Financial Advisor</span>
                </div>
                <button onClick={() => setIsChatOpen(false)} className="text-slate-400 hover:text-slate-600 text-sm font-medium px-2">
                  Close
                </button>
              </div>
              
              <div className="flex-1 space-y-4 overflow-y-auto bg-[#FDFDF9] p-4">
                {messages.map((msg) => (
                  <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                      msg.role === 'user' ? 'bg-slate-800' : 'bg-indigo-100'
                    }`}>
                      {msg.role === 'user' ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-indigo-600" />}
                    </div>
                    <div className={`max-w-[85%] rounded-2xl p-3 text-sm ${
                      msg.role === 'user' 
                        ? 'bg-slate-800 text-white rounded-tr-sm' 
                        : msg.isError 
                          ? 'bg-red-50 text-red-800 border border-red-100 rounded-tl-sm'
                          : 'bg-white border border-slate-200 text-slate-800 rounded-tl-sm shadow-sm'
                    }`}>
                      {msg.routedAgent && (
                        <div className="mb-3 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                          <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 font-medium">
                            Agent: {msg.routedAgent.replace(/_/g, ' ')}
                          </span>
                          {msg.vectorDatabase && (
                            <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 font-medium">
                              Vector DB: {msg.vectorDatabase}
                            </span>
                          )}
                        </div>
                      )}
                      {msg.dashboardUpdates?.debtAnalysis ? (
                        renderDebtCard(msg)
                      ) : msg.dashboardUpdates?.budgetAnalysis ? (
                        renderBudgetCard(msg)
                      ) : msg.dashboardUpdates?.savingsPlan ? (
                        renderSavingsCard(msg)
                      ) : msg.dashboardUpdates?.portfolioSuggestion || msg.dashboardUpdates?.portfolioAnalysis ? (
                        renderPortfolioCard(msg)
                      ) : msg.dashboardUpdates?.taxAnalysis ? (
                        renderTaxCard(msg)
                      ) : msg.dashboardUpdates?.goalPlan ? (
                        renderGoalsCard(msg)
                      ) : msg.dashboardUpdates?.coachSummary ? (
                        renderCoachCard(msg)
                      ) : msg.dashboardUpdates?.literacyLesson ? (
                        renderLiteracyCard(msg)
                      ) : msg.dashboardUpdates?.documentAnalysis ? (
                        renderDocumentCard(msg)
                      ) : (
                        <>
                          <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                          {msg.progressSteps?.length ? renderProgressSteps(msg.progressSteps) : null}
                          {msg.retrievedDocuments?.length ? (
                            <div className="mt-3 rounded-xl border border-slate-100 bg-slate-50 p-3">
                              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Retrieved context</p>
                              <div className="mt-2 flex flex-wrap gap-2">
                                {msg.retrievedDocuments.map((doc) => (
                                  <span key={`${doc.sourceType}-${doc.title}`} className="rounded-full bg-white px-2.5 py-1 text-[11px] text-slate-600 border border-slate-200">
                                    {doc.title} · {doc.sourceType} · {doc.score}
                                  </span>
                                ))}
                              </div>
                            </div>
                          ) : null}
                        </>
                      )}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center shrink-0">
                      <Bot className="w-4 h-4 text-indigo-600" />
                    </div>
                    <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm p-3 text-slate-500 shadow-sm">
                      <div className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span className="text-sm">Analyzing your finances...</span>
                      </div>
                      {progressSteps.length ? renderProgressSteps(progressSteps, true) : null}
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {!isChatOpen && (
          <div className="flex gap-2 overflow-x-auto pb-3 scrollbar-hide">
            {quickPrompts.map((prompt) => (
              <button
                key={prompt}
                onClick={() => handleSend(prompt)}
                className="flex items-center gap-1.5 whitespace-nowrap rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm transition-colors hover:border-slate-300 hover:bg-slate-50"
              >
                {prompt} <ArrowUpRight className="w-3 h-3 text-slate-400" />
              </button>
            ))}
          </div>
        )}

        {attachment && (
          <div className="mb-3 flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
            <div>
              <p className="font-medium">{attachment.filename}</p>
              <p className="text-xs text-slate-500">Attached to next chat message</p>
            </div>
            <button
              onClick={() => {
                setAttachment(null);
                if (fileInputRef.current) fileInputRef.current.value = '';
              }}
              className="rounded-full p-2 text-slate-400 hover:bg-slate-50 hover:text-slate-600"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        <div className="relative flex items-center gap-2 rounded-full border border-slate-300 bg-white p-1.5 shadow-sm transition-all focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.csv,.xlsx,.xls,image/*"
            onChange={handleFileChange}
            className="hidden"
          />
          <div className="pl-3 text-slate-400">
            <Bot className="w-5 h-5" />
          </div>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask anything about your finances..."
            className="flex-1 bg-transparent border-none focus:ring-0 py-2 px-2 text-sm text-slate-800 placeholder-slate-400 outline-none"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            type="button"
            className="h-10 w-10 rounded-full text-slate-500 hover:bg-slate-50 hover:text-slate-700 flex items-center justify-center"
            title="Attach document"
          >
            <Paperclip className="h-4 w-4" />
          </button>
          <button
            onClick={() => handleSend()}
            disabled={(!input.trim() && !attachment) || isLoading}
            className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center shrink-0 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:hover:bg-indigo-600 transition-colors"
          >
            <Send className="w-4 h-4 ml-0.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
