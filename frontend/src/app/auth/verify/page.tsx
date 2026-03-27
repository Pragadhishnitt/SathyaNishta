"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Mail, CheckCircle, XCircle, Loader2, ArrowRight } from "lucide-react";

function VerifyEmailPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    
    if (!token) {
      setStatus('error');
      setMessage('Invalid verification link');
      return;
    }

    const verifyEmail = async () => {
      try {
        const response = await fetch('/api/auth/verify-email', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token })
        });

        const data = await response.json();

        if (response.ok) {
          setStatus('success');
          setMessage('Email verified successfully! You can now sign in.');
        } else {
          setStatus('error');
          setMessage(data.detail || 'Verification failed');
        }
      } catch (error) {
        setStatus('error');
        setMessage('Network error. Please try again.');
      }
    };

    verifyEmail();
  }, [searchParams]);

  return (
    <div className="min-h-screen auth-bg flex flex-col items-center justify-center py-12 px-4 relative overflow-y-auto">
      {/* Background orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-neon-indigo/[0.07] rounded-full blur-[100px] animate-float" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-purple-600/[0.05] rounded-full blur-[100px] animate-float" style={{ animationDelay: '1.5s' }} />
        <div className="absolute top-1/2 left-1/2 w-[300px] h-[300px] bg-neon-cyan/[0.03] rounded-full blur-[80px]" />
      </div>

      <div className="w-full max-w-md relative z-10 animate-slide-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2.5 mb-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-neon-indigo/20 to-purple-600/20 flex items-center justify-center border border-neon-indigo/20 animate-pulse-glow">
              <Mail size={22} className="text-neon-indigo" />
            </div>
          </div>
          <h1 className="text-2xl font-bold gradient-text mb-1">Email Verification</h1>
          <p className="text-gray-500 text-sm">Sathya Nishta</p>
        </div>

        {/* Verification Card */}
        <div className="glass-card neon-border-indigo p-8 text-center">
          {status === 'loading' && (
            <div className="space-y-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-neon-indigo/10 flex items-center justify-center">
                <Loader2 size={24} className="animate-spin text-neon-indigo" />
              </div>
              <h2 className="text-lg font-semibold text-white">Verifying your email...</h2>
              <p className="text-gray-400 text-sm">Please wait while we confirm your email address.</p>
            </div>
          )}

          {status === 'success' && (
            <div className="space-y-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-neon-emerald/10 flex items-center justify-center animate-pulse-glow-emerald">
                <CheckCircle size={24} className="text-neon-emerald" />
              </div>
              <h2 className="text-lg font-semibold text-white">Email Verified!</h2>
              <p className="text-gray-400 text-sm">{message}</p>
              <button
                onClick={() => router.push('/auth/login')}
                className="btn-primary w-full flex items-center justify-center gap-2 py-3 mt-6"
              >
                Sign In Now
                <ArrowRight size={15} />
              </button>
            </div>
          )}

          {status === 'error' && (
            <div className="space-y-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-neon-red/10 flex items-center justify-center">
                <XCircle size={24} className="text-neon-red" />
              </div>
              <h2 className="text-lg font-semibold text-white">Verification Failed</h2>
              <p className="text-gray-400 text-sm">{message}</p>
              <div className="space-y-2 mt-6">
                <button
                  onClick={() => router.push('/auth/login')}
                  className="btn-primary w-full flex items-center justify-center gap-2 py-3"
                >
                  Back to Sign In
                  <ArrowRight size={15} />
                </button>
                <button
                  onClick={() => router.push('/auth/forgot-password')}
                  className="btn-ghost w-full py-3 text-sm"
                >
                  Request New Verification Email
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-gray-600 text-[11px]">
            Secured by Sathya Nishta Authentication Layer
          </p>
        </div>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen auth-bg flex items-center justify-center p-4">
        <div className="w-full max-w-md relative z-10">
          <div className="glass-card neon-border-indigo p-8 text-center">
            <Loader2 size={32} className="animate-spin text-neon-indigo mx-auto mb-4" />
            <p className="text-gray-400">Loading...</p>
          </div>
        </div>
      </div>
    }>
      <VerifyEmailPageContent />
    </Suspense>
  );
}
