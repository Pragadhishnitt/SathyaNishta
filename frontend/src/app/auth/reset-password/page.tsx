"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Lock, Eye, EyeOff, CheckCircle, AlertCircle, Loader2, ArrowLeft, ArrowRight } from "lucide-react";

function ResetPasswordPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState("");
  const [tokenValid, setTokenValid] = useState<boolean | null>(null);

  useEffect(() => {
    const tokenParam = searchParams.get('token');
    if (tokenParam) {
      setToken(tokenParam);
      setTokenValid(true);
    } else {
      setTokenValid(false);
      setError("Invalid reset link");
    }
  }, [searchParams]);

  const calculatePasswordStrength = (password: string): number => {
    let strength = 0;
    if (password.length >= 8) strength += 1;
    if (password.length >= 12) strength += 1;
    if (/[a-z]/.test(password)) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^a-zA-Z0-9]/.test(password)) strength += 1;
    return Math.min(strength, 4);
  };

  const getPasswordStrengthColor = () => {
    const strength = calculatePasswordStrength(password);
    if (strength <= 1) return 'bg-red-500';
    if (strength === 2) return 'bg-orange-500';
    if (strength === 3) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getPasswordStrengthText = () => {
    const strength = calculatePasswordStrength(password);
    if (strength <= 1) return 'Weak';
    if (strength === 2) return 'Fair';
    if (strength === 3) return 'Good';
    return 'Strong';
  };

  const validateForm = (): boolean => {
    if (!password) {
      setError("Password is required");
      return false;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long");
      return false;
    }

    const strength = calculatePasswordStrength(password);
    if (strength < 3) {
      setError("Password is too weak. Include uppercase, lowercase, numbers, and special characters.");
      return false;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          token, 
          new_password: password 
        })
      });

      const data = await response.json();

      if (response.ok) {
        setIsSuccess(true);
      } else {
        setError(data.detail || 'Failed to reset password');
      }
    } catch (error) {
      console.error('Password reset error:', error);
      setError('Network error. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (tokenValid === null) {
    return (
      <div className="min-h-screen auth-bg flex items-center justify-center p-4">
        <div className="w-full max-w-md relative z-10">
          <div className="glass-card neon-border-indigo p-8 text-center">
            <Loader2 size={32} className="animate-spin text-neon-indigo mx-auto mb-4" />
            <p className="text-gray-400">Validating reset link...</p>
          </div>
        </div>
      </div>
    );
  }

  if (tokenValid === false) {
    return (
      <div className="min-h-screen auth-bg flex items-center justify-center p-4">
        <div className="w-full max-w-md relative z-10">
          <div className="glass-card neon-border-indigo p-8 text-center">
            <AlertCircle size={32} className="text-neon-red mx-auto mb-4" />
            <h2 className="text-lg font-semibold text-white mb-2">Invalid Reset Link</h2>
            <p className="text-gray-400 mb-4">{error}</p>
            <button
              onClick={() => router.push('/auth/forgot-password')}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              Request New Reset Link
              <ArrowRight size={15} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen auth-bg flex items-center justify-center p-4">
      {/* Background orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-neon-indigo/[0.07] rounded-full blur-[100px] animate-float" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-purple-600/[0.05] rounded-full blur-[100px] animate-float" style={{ animationDelay: '1.5s' }} />
        <div className="absolute top-1/2 left-1/2 w-[300px] h-[300px] bg-neon-cyan/[0.03] rounded-full blur-[80px]" />
      </div>

      <div className="w-full max-w-md relative z-10 animate-slide-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <button
            onClick={() => router.back()}
            className="mb-4 flex items-center gap-2 text-gray-500 hover:text-gray-300 transition-colors text-sm"
          >
            <ArrowLeft size={16} />
            Back
          </button>
          <div className="flex items-center justify-center gap-2.5 mb-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-neon-indigo/20 to-purple-600/20 flex items-center justify-center border border-neon-indigo/20 animate-pulse-glow">
              <Lock size={22} className="text-neon-indigo" />
            </div>
          </div>
          <h1 className="text-2xl font-bold gradient-text mb-1">Set New Password</h1>
          <p className="text-gray-500 text-sm">Choose a strong password</p>
        </div>

        {/* Reset Card */}
        <div className="glass-card neon-border-indigo p-6">
          {!isSuccess ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* New Password */}
              <div className="space-y-1">
                <div className="relative group">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-neon-indigo transition-colors" />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (error) setError("");
                    }}
                    placeholder="New password"
                    className={`w-full pl-10 pr-10 py-3 bg-white/[0.03] border rounded-xl text-white text-sm placeholder-gray-600 focus:outline-none focus:bg-white/[0.05] transition-all ${
                      error 
                        ? 'border-neon-red/40 focus:border-neon-red/60' 
                        : 'border-white/[0.06] focus:border-neon-indigo/40'
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                  >
                    {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
                
                {/* Password strength indicator */}
                {password && (
                  <div className="pt-1 px-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] text-gray-500">Password strength</span>
                      <span className={`text-[10px] font-medium ${
                        calculatePasswordStrength(password) <= 1 ? 'text-red-400' :
                        calculatePasswordStrength(password) === 2 ? 'text-orange-400' :
                        calculatePasswordStrength(password) === 3 ? 'text-yellow-400' :
                        'text-green-400'
                      }`}>
                        {getPasswordStrengthText()}
                      </span>
                    </div>
                    <div className="w-full bg-white/[0.1] rounded-full h-1">
                      <div 
                        className={`h-1 rounded-full transition-all duration-300 ${getPasswordStrengthColor()}`}
                        style={{ width: `${(calculatePasswordStrength(password) / 4) * 100}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Confirm Password */}
              <div className="space-y-1">
                <div className="relative group">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-neon-indigo transition-colors" />
                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                      if (error) setError("");
                    }}
                    placeholder="Confirm new password"
                    className={`w-full pl-10 pr-10 py-3 bg-white/[0.03] border rounded-xl text-white text-sm placeholder-gray-600 focus:outline-none focus:bg-white/[0.05] transition-all ${
                      error 
                        ? 'border-neon-red/40 focus:border-neon-red/60' 
                        : 'border-white/[0.06] focus:border-neon-indigo/40'
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                  >
                    {showConfirmPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="p-3 rounded-xl bg-neon-red/10 border border-neon-red/20 text-red-300 text-xs flex items-start gap-2 animate-slide-up">
                  <AlertCircle size={13} className="mt-0.5 flex-shrink-0" />
                  {error}
                </div>
              )}

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
                    Reset Password
                    <ArrowRight size={15} />
                  </>
                )}
              </button>
            </form>
          ) : (
            <div className="text-center space-y-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-neon-emerald/10 flex items-center justify-center animate-pulse-glow-emerald">
                <CheckCircle size={24} className="text-neon-emerald" />
              </div>
              <h2 className="text-lg font-semibold text-white">Password Reset Successful!</h2>
              <p className="text-gray-400 text-sm">
                Your password has been updated successfully. You can now sign in with your new password.
              </p>
              <button
                onClick={() => router.push('/auth/login')}
                className="btn-primary w-full flex items-center justify-center gap-2 py-3"
              >
                Sign In Now
                <ArrowRight size={15} />
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

export default function ResetPasswordPage() {
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
      <ResetPasswordPageContent />
    </Suspense>
  );
}
