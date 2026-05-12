import { useState } from 'react';
import { signInWithPopup } from 'firebase/auth';
import { auth, googleProvider } from '@/lib/firebase';
import { useAuth } from '@/contexts/AuthContext';
import { Navigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';

export function LoginPage() {
  const { user, loading } = useAuth();
  const [signingIn, setSigningIn] = useState(false);
  const [error, setError] = useState(false);

  if (loading) return null;
  if (user) return <Navigate to="/" replace />;

  async function handleSignIn() {
    setSigningIn(true);
    setError(false);
    try {
      await signInWithPopup(auth, googleProvider);
    } catch {
      setError(true);
    } finally {
      setSigningIn(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-[360px] bg-card rounded-lg p-8 flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold text-[#58a6ff]">Finance Tracker</h1>
          <p className="text-[13px] text-muted-foreground">Your net worth at a glance.</p>
        </div>
        <div className="flex flex-col gap-3">
          <Button
            className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
            disabled={signingIn}
            onClick={handleSignIn}
          >
            {signingIn ? 'Signing in...' : 'Sign in with Google'}
          </Button>
          {error && (
            <p className="text-destructive text-[13px]">Sign-in failed. Please try again.</p>
          )}
        </div>
      </div>
    </div>
  );
}
