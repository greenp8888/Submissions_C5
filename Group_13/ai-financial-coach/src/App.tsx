import React, { useState } from 'react';
import { FirebaseProvider, useFirebase } from './components/FirebaseProvider';
import Landing from './components/Landing';
import Login from './components/Login';
import Onboarding from './components/Onboarding';
import Dashboard from './components/Dashboard';
import { Loader2 } from 'lucide-react';

function AppContent() {
  const { user, userProfile, loading } = useFirebase();
  const [showAuth, setShowAuth] = useState(false);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#FDFDF9] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (!user) {
    return showAuth ? <Login /> : <Landing onGetStarted={() => setShowAuth(true)} />;
  }

  if (!userProfile?.onboarding_completed) {
    return <Onboarding />;
  }

  return <Dashboard />;
}

export default function App() {
  return (
    <FirebaseProvider>
      <AppContent />
    </FirebaseProvider>
  );
}
