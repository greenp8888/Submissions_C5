import React, { useState } from 'react';
import { useFirebase } from './FirebaseProvider';
import { Wallet, Loader2 } from 'lucide-react';
import { apiClient } from '../lib/api';

type AuthMode = 'login' | 'register' | 'reset';

export default function Login() {
  const { login, register } = useFirebase();
  const [mode, setMode] = useState<AuthMode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const normalizedEmail = email.trim().toLowerCase();

      if (mode === 'login') {
        const result = await login({ email: normalizedEmail, password });
        if (result.error) throw new Error(result.error);
      } else if (mode === 'register') {
        if (!name.trim()) {
          throw new Error('Name is required for registration.');
        }
        if (password.length < 8) {
          throw new Error('Password must be at least 8 characters.');
        }
        const result = await register({ email: normalizedEmail, password, name: name.trim() });
        if (result.error) throw new Error(result.error);
      } else {
        if (password.length < 8) {
          throw new Error('Password must be at least 8 characters.');
        }
        if (password !== confirmPassword) {
          throw new Error('Passwords do not match.');
        }
        const result = await apiClient.resetPassword({ email: normalizedEmail, password });
        if (result.error) throw new Error(result.error);
        setSuccess('Password reset successful. You can sign in now.');
        setMode('login');
        setPassword('');
        setConfirmPassword('');
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred during authentication.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FDFDF9] flex items-center justify-center p-6">
      <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm max-w-md w-full space-y-6">
        <div className="text-center">
          <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Wallet className="w-8 h-8 text-indigo-600" />
          </div>
          <h1 className="text-2xl font-bold text-slate-800">
            {mode === 'login' ? 'Welcome Back' : mode === 'register' ? 'Create an Account' : 'Reset Password'}
          </h1>
          <p className="text-slate-600 text-sm mt-2">
            {mode === 'login'
              ? 'Sign in to continue to your financial dashboard.'
              : mode === 'register'
                ? 'Sign up to start your journey towards financial freedom.'
                : 'Enter your email and choose a new password for this local account.'}
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
              <input 
                type="text" 
                required 
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                placeholder="John Doe"
              />
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Email Address</label>
            <input 
              type="email" 
              required 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
              placeholder="you@example.com"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
            <input 
              type="password" 
              required 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
              placeholder="••••••••"
            />
          </div>

          {mode === 'reset' && (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Confirm Password</label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                placeholder="••••••••"
              />
            </div>
          )}

          {success && (
            <div className="p-3 bg-emerald-50 text-emerald-700 text-sm rounded-lg border border-emerald-100">
              {success}
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-100 flex flex-col gap-2">
              <span>{error}</span>
              {error.includes('already') && mode === 'register' && (
                <button 
                  type="button"
                  onClick={() => {
                    setMode('login');
                    setError('');
                  }}
                  className="text-indigo-600 font-bold hover:underline text-left"
                >
                  Switch to Sign In
                </button>
              )}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-medium flex items-center justify-center gap-2 transition-colors disabled:opacity-70"
          >
            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
            {mode === 'login' ? 'Sign In' : mode === 'register' ? 'Create Account' : 'Reset Password'}
          </button>
        </form>

        <div className="text-center text-sm text-slate-600">
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <button 
            onClick={() => {
              setMode(mode === 'login' ? 'register' : 'login');
              setError('');
              setSuccess('');
            }} 
            className="text-indigo-600 font-medium hover:underline"
          >
            {mode === 'login' ? 'Sign up' : 'Sign in'}
          </button>
        </div>

        {mode === 'login' && (
          <div className="text-center text-sm">
            <button
              type="button"
              onClick={() => {
                setMode('reset');
                setError('');
                setSuccess('');
                setPassword('');
                setConfirmPassword('');
              }}
              className="text-indigo-600 font-medium hover:underline"
            >
              Forgot password?
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
