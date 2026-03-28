import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";

interface User {
  id: string;
  email: string;
  name: string;
  is_verified: boolean;
  is_premium: boolean;
}

export function usePremiumAuth() {
  const { data: session, status } = useSession();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (status === "loading") return;

    if (session?.user) {
      // For OAuth users, assume they're verified and premium for now
      const userData: User = {
        id: (session.user as any).id || session.user.email,
        email: session.user.email || "",
        name: session.user.name || "",
        is_verified: true, // OAuth users are considered verified
        is_premium: true,  // Allow access to Sathyanishta mode
      };
      setUser(userData);
    } else {
      setUser(null);
    }
    setIsLoading(false);
  }, [session, status]);

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
  };
}