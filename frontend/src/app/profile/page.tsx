"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/Navbar";
import { SidebarNav } from "@/components/SidebarNav";
import { User, Mail, Building, Briefcase, Edit2, Save, X, CheckCircle, AlertCircle, Shield, Calendar } from "lucide-react";

export default function ProfilePage() {
  const router = useRouter();
  const { data: session } = useSession();
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState<"success" | "error" | "">("");
  
  const [profile, setProfile] = useState({
    name: "",
    email: "",
    company: "",
    role: "",
    bio: "",
    isVerified: false,
    isPremium: false,
    createdAt: "",
    lastLogin: ""
  });

  const [editForm, setEditForm] = useState({
    name: "",
    company: "",
    role: "",
    bio: ""
  });

  useEffect(() => {
    if (!session) {
      router.push("/auth/login?callbackUrl=/profile");
      return;
    }

    // Fetch user profile
    if (session) {
      fetchProfile();
    }
  }, [session]);

  const fetchProfile = async () => {
    try {
      const response = await fetch('/api/profile', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${(session as any)?.accessToken || ''}`,
        },
      });

      let data;
      try {
        data = await response.json();
      } catch (e) {
        console.error('Profile fetch error:', e);
        return;
      }

      if (response.ok) {
        setProfile({
          name: data.name || '',
          email: data.email || '',
          company: data.company || '',
          role: data.role || '',
          bio: data.bio || '',
          isVerified: data.is_verified || false,
          isPremium: data.is_premium || false,
          createdAt: data.created_at ? new Date(data.created_at).toLocaleDateString() : '',
          lastLogin: data.last_login ? new Date(data.last_login).toLocaleDateString() : ''
        });
      } else {
        console.error('Profile fetch failed:', data);
      }
    } catch (error) {
      console.error('Failed to load profile:', error);
    }
  };

  const handleEdit = () => {
    setIsEditing(true);
    setMessage("");
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditForm({
      name: profile.name,
      company: profile.company,
      role: profile.role,
      bio: profile.bio
    });
    setMessage("");
  };

  const handleSave = async () => {
    setIsLoading(true);
    setMessage("");
    setMessageType("");

    try {
      const response = await fetch('/api/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken || ''}`,
        },
        body: JSON.stringify(editForm),
      });

      if (response.ok) {
        const updatedUser = await response.json();
        setProfile({
          name: updatedUser.name || '',
          email: updatedUser.email || '',
          company: updatedUser.company || '',
          role: updatedUser.role || '',
          bio: updatedUser.bio || '',
          isVerified: updatedUser.is_verified || false,
          isPremium: updatedUser.is_premium || false,
          createdAt: updatedUser.created_at || '',
          lastLogin: updatedUser.last_login || ''
        });
        
        setIsEditing(false);
        setMessage("Profile updated successfully!");
        setMessageType("success");
        
        // Clear message after 3 seconds
        setTimeout(() => setMessage(""), 3000);
      } else {
        const error = await response.json();
        setMessage(error.detail || "Failed to update profile");
        setMessageType("error");
      }
    } catch (error) {
      console.error('Profile update error:', error);
      setMessage("Network error. Please try again.");
      setMessageType("error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setEditForm(prev => ({ ...prev, [field]: value }));
  };

  if (!session) {
    return <div className="h-screen bg-surface-0 flex items-center justify-center">Redirecting...</div>;
  }

  return (
    <div className="flex flex-col h-screen bg-surface-0 text-white">
      <Navbar />
      <div className="flex flex-1 overflow-hidden">
        <SidebarNav />
        <main className="flex-1 overflow-y-auto px-6 py-6">
          <div className="max-w-4xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              <h1 className="text-2xl font-bold gradient-text mb-2">Profile Settings</h1>
              <p className="text-gray-400">Manage your account information and preferences</p>
            </div>

            {/* Message */}
            {message && (
              <div className={`mb-6 p-4 rounded-xl flex items-center gap-3 animate-slide-up ${
                messageType === "success" 
                  ? "bg-neon-emerald/10 border border-neon-emerald/20 text-emerald-300" 
                  : "bg-neon-red/10 border border-neon-red/20 text-red-300"
              }`}>
                {messageType === "success" ? (
                  <CheckCircle size={20} className="flex-shrink-0" />
                ) : (
                  <AlertCircle size={20} className="flex-shrink-0" />
                )}
                <span className="text-sm">{message}</span>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Profile Card */}
              <div className="lg:col-span-2 space-y-6">
                {/* Basic Info */}
                <div className="glass-card neon-border-indigo p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                      <User size={18} className="text-neon-indigo" />
                      Basic Information
                    </h2>
                    {!isEditing ? (
                      <button
                        onClick={handleEdit}
                        className="btn-ghost flex items-center gap-2 py-2 px-4"
                      >
                        <Edit2 size={16} />
                        Edit Profile
                      </button>
                    ) : (
                      <div className="flex gap-2">
                        <button
                          onClick={handleCancel}
                          disabled={isLoading}
                          className="btn-ghost flex items-center gap-2 py-2 px-4 disabled:opacity-50"
                        >
                          <X size={16} />
                          Cancel
                        </button>
                        <button
                          onClick={handleSave}
                          disabled={isLoading}
                          className="btn-primary flex items-center gap-2 py-2 px-4 disabled:opacity-50"
                        >
                          {isLoading ? (
                            <>
                              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                              Saving...
                            </>
                          ) : (
                            <>
                              <Save size={16} />
                              Save Changes
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="space-y-4">
                    {/* Name */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Full Name</label>
                      {isEditing ? (
                        <input
                          type="text"
                          value={editForm.name}
                          onChange={(e) => handleInputChange('name', e.target.value)}
                          className="w-full px-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-lg text-white text-sm focus:outline-none focus:border-neon-indigo/40 focus:bg-white/[0.05] transition-all"
                        />
                      ) : (
                        <div className="flex items-center gap-3 text-gray-300">
                          <User size={16} className="text-gray-500" />
                          <span>{profile.name || "Not set"}</span>
                        </div>
                      )}
                    </div>

                    {/* Email */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Email Address</label>
                      <div className="flex items-center gap-3 text-gray-300">
                        <Mail size={16} className="text-gray-500" />
                        <span>{profile.email}</span>
                        {profile.isVerified && (
                          <span className="text-xs px-2 py-1 rounded-full bg-neon-emerald/10 text-neon-emerald border border-neon-emerald/20">
                            Verified
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Company */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Company</label>
                      {isEditing ? (
                        <input
                          type="text"
                          value={editForm.company}
                          onChange={(e) => handleInputChange('company', e.target.value)}
                          placeholder="Your company name"
                          className="w-full px-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-lg text-white text-sm placeholder-gray-600 focus:outline-none focus:border-neon-indigo/40 focus:bg-white/[0.05] transition-all"
                        />
                      ) : (
                        <div className="flex items-center gap-3 text-gray-300">
                          <Building size={16} className="text-gray-500" />
                          <span>{profile.company || "Not set"}</span>
                        </div>
                      )}
                    </div>

                    {/* Role */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Role</label>
                      {isEditing ? (
                        <input
                          type="text"
                          value={editForm.role}
                          onChange={(e) => handleInputChange('role', e.target.value)}
                          placeholder="Your job role"
                          className="w-full px-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-lg text-white text-sm placeholder-gray-600 focus:outline-none focus:border-neon-indigo/40 focus:bg-white/[0.05] transition-all"
                        />
                      ) : (
                        <div className="flex items-center gap-3 text-gray-300">
                          <Briefcase size={16} className="text-gray-500" />
                          <span>{profile.role || "Not set"}</span>
                        </div>
                      )}
                    </div>

                    {/* Bio */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Bio</label>
                      {isEditing ? (
                        <textarea
                          value={editForm.bio}
                          onChange={(e) => handleInputChange('bio', e.target.value)}
                          placeholder="Tell us about yourself..."
                          rows={4}
                          className="w-full px-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-lg text-white text-sm placeholder-gray-600 focus:outline-none focus:border-neon-indigo/40 focus:bg-white/[0.05] transition-all resize-none"
                        />
                      ) : (
                        <div className="text-gray-300 whitespace-pre-wrap">
                          {profile.bio || "No bio set"}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Status Card */}
              <div className="space-y-6">
                {/* Account Status */}
                <div className="glass-card neon-border-indigo p-6">
                  <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
                    <Shield size={18} className="text-neon-indigo" />
                    Account Status
                  </h2>
                  
                  <div className="space-y-4">
                    {/* Email Verification */}
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-300">Email Verification</p>
                        <p className="text-xs text-gray-500">
                          {profile.isVerified ? "Verified" : "Not verified"}
                        </p>
                      </div>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        profile.isVerified 
                          ? "bg-neon-emerald/20" 
                          : "bg-neon-red/20"
                      }`}>
                        {profile.isVerified ? (
                          <CheckCircle size={16} className="text-neon-emerald" />
                        ) : (
                          <AlertCircle size={16} className="text-neon-red" />
                        )}
                      </div>
                    </div>

                    {/* Premium Status */}
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-300">Premium Account</p>
                        <p className="text-xs text-gray-500">
                          {profile.isPremium ? "Active" : "Free tier"}
                        </p>
                      </div>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        profile.isPremium 
                          ? "bg-neon-emerald/20" 
                          : "bg-gray-600/20"
                      }`}>
                        {profile.isPremium ? (
                          <CheckCircle size={16} className="text-neon-emerald" />
                        ) : (
                          <Shield size={16} className="text-gray-500" />
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Account Info */}
                <div className="glass-card neon-border-indigo p-6">
                  <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
                    <Calendar size={18} className="text-neon-indigo" />
                    Account Information
                  </h2>
                  
                  <div className="space-y-3">
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Member Since</p>
                      <p className="text-sm text-gray-300">{profile.createdAt}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Last Login</p>
                      <p className="text-sm text-gray-300">{profile.lastLogin}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
