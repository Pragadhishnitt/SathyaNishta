"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Mail, ArrowLeft, CheckCircle, AlertCircle, Loader2 } from "lucide-react";

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState("");

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email) {
      setError("Email is required");
      return;
    }

    if (!validateEmail(email)) {
      setError("Please enter a valid email address");
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      const data = await response.json();

      if (response.ok) {
        setIsSuccess(true);
        setEmail("");
      } else {
        setError(data.detail || 'Failed to send reset email');
      }
    } catch (error) {
      console.error('Password reset error:', error);
      setError('Network error. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen auth-bg flex flex-col items-center justify-center py-12 px-4 relative overflow-y-auto">
      {/* Background orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-neon-indigo/[0.07] rounded-full blur-[100px] animate-float" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-purple-600/[0.05] rounded-full blur-[100px] animate-float" style={{ animationDelay: '1.5s' }} />
        <div className="absolute top-1/2 left-1/2 w-[300px] h-[300px] bg-neon-cyan/[0.03] rounded-full blur-[80px]" />
      </div>

      <div className="w-full max-w-md relative z-10 animate-slide-up my-8 max-h-[90vh] overflow-y-auto">
        {/* Logo */}
        <div className="text-center mb-8">
          <button
            onClick={() => router.back()}
            className="mb-4 flex items-center gap-2 text-gray-500 hover:text-gray-300 transition-colors text-sm"
          >
            <ArrowLeft size={16} />
            Back to Sign In
          </button>
          <div className="flex items-center justify-center gap-2.5 mb-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-neon-indigo/20 to-purple-600/20 flex items-center justify-center border border-neon-indigo/20 animate-pulse-glow">
              <Mail size={22} className="text-neon-indigo" />
            </div>
          </div>
          <h1 className="text-2xl font-bold gradient-text mb-1">Reset Password</h1>
          <p className="text-gray-500 text-sm">We'll send you a reset link</p>
        </div>

        {/* Reset Card */}
        <div className="glass-card neon-border-indigo p-6">
          {!isSuccess ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email */}
              <div className="space-y-1">
                <div className="relative group">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-neon-indigo transition-colors" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (error) setError("");
                    }}
                    placeholder="Enter your email address"
                    className={`w-full pl-10 pr-4 py-3 bg-white/[0.03] border rounded-xl text-white text-sm placeholder-gray-600 focus:outline-none focus:bg-white/[0.05] transition-all ${
                      error 
                        ? 'border-neon-red/40 focus:border-neon-red/60' 
                        : 'border-white/[0.06] focus:border-neon-indigo/40'
                    }`}
                  />
                </div>
                {error && (
                  <p className="text-xs text-neon-red flex items-center gap-1 px-1">
                    <AlertCircle size={10} />
                    {error}
                  </p>
                )}
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full flex items-center justify-center gap-2 py-3 disabled:opacity-50"
              >
                {isLoading ? (
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    Send Reset Link
                    <Mail size={15} />
                  </>
                )}
              </button>
            </form>
          ) : (
            <div className="text-center space-y-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-neon-emerald/10 flex items-center justify-center animate-pulse-glow-emerald">
                <CheckCircle size={24} className="text-neon-emerald" />
              </div>
              <h2 className="text-lg font-semibold text-white">Check Your Email</h2>
              <p className="text-gray-400 text-sm">
                We've sent a password reset link to your email address. 
                Please check your inbox and follow the instructions.
              </p>
              <div className="space-y-2 text-xs text-gray-500">
                <p>• The reset link expires after a few hours — check the email for the exact time</p>
                <p>• Check your spam folder if you don't see it</p>
                <p>• Make sure to use the same email you registered with</p>
              </div>
              <button
                onClick={() => router.push('/auth/login')}
                className="btn-ghost w-full py-3 text-sm"
              >
                Back to Sign In
              </button>
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
