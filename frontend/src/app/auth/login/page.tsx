"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Mail, Lock, ArrowRight, Shield, Eye, EyeOff, Info, User, Building, Briefcase, Check, X, AlertCircle } from "lucide-react";

interface FormErrors {
  email?: string;
  password?: string;
  name?: string;
  confirmPassword?: string;
  general?: string;
}

interface FormData {
  email: string;
  password: string;
  name: string;
  confirmPassword: string;
  company: string;
  role: string;
}

export default function LoginPage() {
  const router = useRouter();
  const [isSignUp, setIsSignUp] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSuccess, setIsSuccess] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);
  
  const [formData, setFormData] = useState<FormData>({
    email: "",
    password: "",
    name: "",
    confirmPassword: "",
    company: "",
    role: ""
  });

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

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

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!validateEmail(formData.email)) {
      newErrors.email = "Please enter a valid email address";
    }

    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters long";
    } else if (passwordStrength < 3) {
      newErrors.password = "Password is too weak. Include uppercase, lowercase, numbers, and special characters.";
    }

    if (isSignUp) {
      if (!formData.name) {
        newErrors.name = "Full name is required";
      } else if (formData.name.length < 2) {
        newErrors.name = "Name must be at least 2 characters long";
      }

      if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = "Passwords do not match";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear specific field error when user starts typing
    if (errors[field as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
    
    // Update password strength
    if (field === 'password') {
      setPasswordStrength(calculatePasswordStrength(value));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsLoading(true);
    setErrors({});

    try {
      if (isSignUp) {
        // Sign up logic
        const response = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: formData.email,
            password: formData.password,
            name: formData.name,
            company: formData.company || undefined,
            role: formData.role || undefined
          })
        });

        let data;
        try {
          data = await response.json();
        } catch (e) {
          data = { detail: 'Server error. Please try again.' };
        }

        if (!response.ok) {
          if (response.status === 400 && data.detail === 'Email already registered') {
            setErrors({ email: 'This email is already registered. Try signing in instead.' });
          } else {
            setErrors({ general: data.detail || 'Registration failed. Please try again.' });
          }
        } else {
          setIsSuccess(true);
          // Reset form
          setFormData({
            email: '',
            password: '',
            name: '',
            confirmPassword: '',
            company: '',
            role: ''
          });
        }
      } else {
        // Sign in logic
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: formData.email,
            password: formData.password
          })
        });

        let data;
        try {
          data = await response.json();
        } catch (e) {
          data = { detail: 'Server error. Please try again.' };
        }

        if (!response.ok) {
          if (response.status === 401) {
            setErrors({ general: 'Invalid email or password' });
          } else if (response.status === 400 && data.detail === 'Please verify your email before logging in') {
            setErrors({ general: 'Please verify your email before logging in. Check your inbox for the verification link.' });
          } else {
            setErrors({ general: data.detail || 'Login failed. Please try again.' });
          }
        } else {
          // Store token and user info
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('user', JSON.stringify(data.user));
          router.push('/');
        }
      }
    } catch (error) {
      console.error('Authentication error:', error);
      setErrors({ general: 'Network error. Please check your connection and try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    signIn("google", { callbackUrl: "/" });
  };

  const getPasswordStrengthColor = () => {
    if (passwordStrength <= 1) return 'bg-red-500';
    if (passwordStrength === 2) return 'bg-orange-500';
    if (passwordStrength === 3) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getPasswordStrengthText = () => {
    if (passwordStrength <= 1) return 'Weak';
    if (passwordStrength === 2) return 'Fair';
    if (passwordStrength === 3) return 'Good';
    return 'Strong';
  };

  return (
    <div className="min-h-screen auth-bg flex flex-col items-center justify-center py-12 px-4 relative overflow-y-auto">
      {/* Background orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-neon-indigo/[0.07] rounded-full blur-[100px] animate-float" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-purple-600/[0.05] rounded-full blur-[100px] animate-float" style={{ animationDelay: '1.5s' }} />
        <div className="absolute top-1/2 left-1/2 w-[300px] h-[300px] bg-neon-cyan/[0.03] rounded-full blur-[80px]" />
      </div>

      <div className="w-full max-w-md relative z-10 animate-slide-up my-8">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2.5 mb-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-neon-indigo/20 to-purple-600/20 flex items-center justify-center border border-neon-indigo/20 animate-pulse-glow">
              <Shield size={22} className="text-neon-indigo" />
            </div>
          </div>
          <h1 className="text-2xl font-bold gradient-text mb-1">Sathya Nishta</h1>
          <p className="text-gray-500 text-sm">AI-Powered Forensic Investigation Platform</p>
        </div>

        {/* Auth Card */}
        <div className="glass-card neon-border-indigo p-6">
          {/* Tabs */}
          <div className="flex gap-1 mb-6 p-1 bg-white/[0.02] rounded-xl">
            <button
              onClick={() => { setIsSignUp(false); setErrors({}); setIsSuccess(false); }}
              className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-all duration-300 ${
                !isSignUp
                  ? "bg-neon-indigo/15 text-neon-indigo border border-neon-indigo/20 shadow-neon-indigo"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => { setIsSignUp(true); setErrors({}); setIsSuccess(false); }}
              className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-all duration-300 ${
                isSignUp
                  ? "bg-neon-indigo/15 text-neon-indigo border border-neon-indigo/20 shadow-neon-indigo"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              Sign Up
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name field for sign up */}
            {isSignUp && (
              <div className="space-y-1">
                <div className="relative group">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-neon-indigo transition-colors" />
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    placeholder="Full name"
                    className={`w-full pl-10 pr-4 py-3 bg-white/[0.03] border rounded-xl text-white text-sm placeholder-gray-600 focus:outline-none focus:bg-white/[0.05] transition-all ${
                      errors.name 
                        ? 'border-neon-red/40 focus:border-neon-red/60' 
                        : 'border-white/[0.06] focus:border-neon-indigo/40'
                    }`}
                  />
                </div>
                {errors.name && (
                  <p className="text-xs text-neon-red flex items-center gap-1 px-1">
                    <AlertCircle size={10} />
                    {errors.name}
                  </p>
                )}
              </div>
            )}

            {/* Email */}
            <div className="space-y-1">
              <div className="relative group">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-neon-indigo transition-colors" />
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  placeholder="Email address"
                  className={`w-full pl-10 pr-4 py-3 bg-white/[0.03] border rounded-xl text-white text-sm placeholder-gray-600 focus:outline-none focus:bg-white/[0.05] transition-all ${
                    errors.email 
                      ? 'border-neon-red/40 focus:border-neon-red/60' 
                      : 'border-white/[0.06] focus:border-neon-indigo/40'
                  }`}
                />
              </div>
              {errors.email && (
                <p className="text-xs text-neon-red flex items-center gap-1 px-1">
                  <AlertCircle size={10} />
                  {errors.email}
                </p>
              )}
            </div>

            {/* Password */}
            <div className="space-y-1">
              <div className="relative group">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-neon-indigo transition-colors" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  placeholder="Password"
                  className={`w-full pl-10 pr-10 py-3 bg-white/[0.03] border rounded-xl text-white text-sm placeholder-gray-600 focus:outline-none focus:bg-white/[0.05] transition-all ${
                    errors.password 
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
              
              {errors.password && (
                <p className="text-xs text-neon-red flex items-center gap-1 px-1">
                  <AlertCircle size={10} />
                  {errors.password}
                </p>
              )}
              
              {/* Password strength indicator for sign up */}
              {isSignUp && formData.password && (
                <div className="pt-1 px-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] text-gray-500">Password strength</span>
                    <span className={`text-[10px] font-medium ${
                      passwordStrength <= 1 ? 'text-red-400' :
                      passwordStrength === 2 ? 'text-orange-400' :
                      passwordStrength === 3 ? 'text-yellow-400' :
                      'text-green-400'
                    }`}>
                      {getPasswordStrengthText()}
                    </span>
                  </div>
                  <div className="w-full bg-white/[0.1] rounded-full h-1">
                    <div 
                      className={`h-1 rounded-full transition-all duration-300 ${getPasswordStrengthColor()}`}
                      style={{ width: `${(passwordStrength / 4) * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Confirm Password for sign up */}
            {isSignUp && (
              <div className="space-y-1">
                <div className="relative group">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-neon-indigo transition-colors" />
                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    value={formData.confirmPassword}
                    onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                    placeholder="Confirm password"
                    className={`w-full pl-10 pr-10 py-3 bg-white/[0.03] border rounded-xl text-white text-sm placeholder-gray-600 focus:outline-none focus:bg-white/[0.05] transition-all ${
                      errors.confirmPassword 
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
                {errors.confirmPassword && (
                  <p className="text-xs text-neon-red flex items-center gap-1 px-1">
                    <AlertCircle size={10} />
                    {errors.confirmPassword}
                  </p>
                )}
              </div>
            )}

            {/* Optional fields for sign up */}
            {isSignUp && (
              <div className="grid grid-cols-2 gap-3">
                <div className="relative group">
                  <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-neon-indigo transition-colors" />
                  <input
                    type="text"
                    value={formData.company}
                    onChange={(e) => handleInputChange('company', e.target.value)}
                    placeholder="Company (optional)"
                    className="w-full pl-10 pr-4 py-3 bg-white/[0.03] border border-white/[0.06] rounded-xl text-white text-sm placeholder-gray-600 focus:outline-none focus:border-neon-indigo/40 focus:bg-white/[0.05] transition-all"
                  />
                </div>
                <div className="relative group">
                  <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-neon-indigo transition-colors" />
                  <input
                    type="text"
                    value={formData.role}
                    onChange={(e) => handleInputChange('role', e.target.value)}
                    placeholder="Role (optional)"
                    className="w-full pl-10 pr-4 py-3 bg-white/[0.03] border border-white/[0.06] rounded-xl text-white text-sm placeholder-gray-600 focus:outline-none focus:border-neon-indigo/40 focus:bg-white/[0.05] transition-all"
                  />
                </div>
              </div>
            )}

            {/* General Error */}
            {errors.general && (
              <div className="p-3 rounded-xl bg-neon-red/10 border border-neon-red/20 text-red-300 text-xs flex items-start gap-2 animate-slide-up">
                <AlertCircle size={13} className="mt-0.5 flex-shrink-0" />
                {errors.general}
              </div>
            )}

            {/* Success Message */}
            {isSuccess && (
              <div className="p-3 rounded-xl bg-neon-emerald/10 border border-neon-emerald/20 text-emerald-300 text-xs flex items-start gap-2 animate-slide-up">
                <Check size={13} className="mt-0.5 flex-shrink-0" />
                <div>
                  <strong>Registration successful!</strong> Please check your email to verify your account.
                </div>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading || isSuccess}
              className="btn-primary w-full flex items-center justify-center gap-2 py-3 disabled:opacity-50"
            >
              {isLoading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : isSuccess ? (
                <>
                  <Check size={15} />
                  Check Your Email
                </>
              ) : (
                <>
                  {isSignUp ? "Create Account" : "Sign In"}
                  <ArrowRight size={15} />
                </>
              )}
            </button>

            {/* Forgot Password Link */}
            {!isSignUp && (
              <div className="text-center">
                <button
                  type="button"
                  onClick={() => router.push('/auth/forgot-password')}
                  className="text-neon-indigo hover:text-neon-indigo/80 text-sm transition-colors"
                >
                  Forgot your password?
                </button>
              </div>
            )}
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/[0.06]" />
            </div>
            <div className="relative flex justify-center text-[11px]">
              <span className="px-3 bg-surface-2 text-gray-600">or continue with</span>
            </div>
          </div>

          {/* Google OAuth */}
          <button
            onClick={handleGoogleSignIn}
            className="btn-ghost w-full flex items-center justify-center gap-2.5 py-3"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            Google
          </button>
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
