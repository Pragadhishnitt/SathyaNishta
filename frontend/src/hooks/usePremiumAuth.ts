import { useState, useEffect } from "react";

interface User {
  id: string;
  email: string;
  name: string;
  is_verified: boolean;
  is_premium: boolean;
}

export function usePremiumAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = () => {
    try {
      const token = localStorage.getItem('access_token');
      const userStr = localStorage.getItem('user');
      
      if (!token || !userStr) {
        setUser(null);
        setIsLoading(false);
        return;
      }

      const userData = JSON.parse(userStr);
      setUser(userData);
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to check auth status:', error);
      setUser(null);
      setIsLoading(false);
    }
  };

  const requireAuth = (): boolean => {
    return !!user && user.is_verified;
  };

  const requirePremium = (): boolean => {
    return !!user && user.is_verified && user.is_premium;
  };

  const redirectToLogin = () => {
    window.location.href = '/auth/login';
  };

  const redirectToProfile = () => {
    window.location.href = '/profile';
  };

  return {
    user,
    isLoading,
    requireAuth,
    requirePremium,
    redirectToLogin,
    redirectToProfile,
    checkAuthStatus
  };
}
