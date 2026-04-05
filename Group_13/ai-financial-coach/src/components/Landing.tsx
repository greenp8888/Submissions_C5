import React from 'react';
import { Wallet, ArrowRight, ShieldCheck, TrendingUp, Target } from 'lucide-react';

export default function Landing({ onGetStarted }: { onGetStarted: () => void }) {
  return (
    <div className="min-h-screen bg-[#FDFDF9] text-slate-900 font-sans selection:bg-indigo-100 selection:text-indigo-900">
      {/* Navigation */}
      <nav className="px-6 py-6 max-w-7xl mx-auto flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center">
            <Wallet className="w-6 h-6 text-white" />
          </div>
          <span className="font-bold text-xl tracking-tight">FinCoach AI</span>
        </div>
        <button 
          onClick={onGetStarted}
          className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
        >
          Sign In
        </button>
      </nav>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-6 pt-20 pb-32">
        <div className="max-w-3xl mx-auto text-center space-y-8">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-sm font-medium mb-4">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            Your Personal AI Financial Advisor
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-slate-900 leading-[1.1]">
            Master your money with <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-violet-600">intelligent guidance.</span>
          </h1>
          
          <p className="text-lg md:text-xl text-slate-600 leading-relaxed max-w-2xl mx-auto">
            Upload your documents, track your goals, and get personalized, jargon-free advice to build wealth and achieve financial freedom.
          </p>
          
          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button 
              onClick={onGetStarted}
              className="w-full sm:w-auto px-8 py-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full font-medium text-lg flex items-center justify-center gap-2 transition-all shadow-lg shadow-indigo-200 hover:shadow-xl hover:shadow-indigo-200 hover:-translate-y-0.5"
            >
              Get Started <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mt-32 max-w-5xl mx-auto">
          <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
            <div className="w-12 h-12 bg-blue-50 rounded-2xl flex items-center justify-center mb-6">
              <ShieldCheck className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Smart Document Parsing</h3>
            <p className="text-slate-600 leading-relaxed">Simply upload your salary slips or bank statements. We automatically extract the data to build your profile.</p>
          </div>
          <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
            <div className="w-12 h-12 bg-emerald-50 rounded-2xl flex items-center justify-center mb-6">
              <TrendingUp className="w-6 h-6 text-emerald-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Actionable Insights</h3>
            <p className="text-slate-600 leading-relaxed">Get specific, numbered action items to optimize your taxes, reduce debt, and grow your investments.</p>
          </div>
          <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
            <div className="w-12 h-12 bg-amber-50 rounded-2xl flex items-center justify-center mb-6">
              <Target className="w-6 h-6 text-amber-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Goal Tracking</h3>
            <p className="text-slate-600 leading-relaxed">Set targets for retirement, a new home, or an emergency fund, and let AI guide you there faster.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
