"use client";

import { useState, useEffect } from "react";
import { Mail, X, Plus, Trash2, Send, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { useSession } from "next-auth/react";
import { createPortal } from "react-dom";

interface EmailReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  investigationData: any;
  reportType: "investigation" | "brief" | "compare";
  companyName?: string;
}

export function EmailReportModal({ 
  isOpen, 
  onClose, 
  investigationData, 
  reportType,
  companyName 
}: EmailReportModalProps) {
  const [recipients, setRecipients] = useState<string[]>([""]);
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState("");
  const { data: session } = useSession();

  // Auto-generate subject based on report type
  useEffect(() => {
    if (reportType === "investigation") {
      setSubject(`Sathya Nishta Investigation Report - ${companyName || "Analysis"}`);
    } else if (reportType === "brief") {
      setSubject("Sathya Nishta Market Intelligence Brief");
    } else if (reportType === "compare") {
      setSubject("Sathya Nishta Comparison Analysis");
    }
  }, [reportType, companyName]);

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const addRecipient = () => {
    setRecipients([...recipients, ""]);
  };

  const removeRecipient = (index: number) => {
    const newRecipients = recipients.filter((_, i) => i !== index);
    setRecipients(newRecipients.length > 0 ? newRecipients : [""]);
  };

  const updateRecipient = (index: number, value: string) => {
    const newRecipients = [...recipients];
    newRecipients[index] = value;
    setRecipients(newRecipients);
  };

  const getValidRecipients = (): string[] => {
    return recipients.filter(email => email.trim() && validateEmail(email.trim()));
  };

  const validateForm = (): boolean => {
    const validRecipients = getValidRecipients();
    if (validRecipients.length === 0) {
      setError("Please add at least one valid email address");
      return false;
    }
    if (validRecipients.length > 10) {
      setError("Maximum 10 recipients allowed");
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const token = (session?.user as any)?.accessToken || '';
      const validRecipients = getValidRecipients();

      const response = await fetch('/api/email/send-report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          recipients: validRecipients,
          subject: subject.trim() || undefined,
          message: message.trim() || undefined,
          investigation_data: investigationData,
          report_type: reportType
        })
      });

      const data = await response.json();

      if (response.ok) {
        setIsSuccess(true);
        // Reset form after 2 seconds
        setTimeout(() => {
          setIsSuccess(false);
          onClose();
          // Reset form state
          setRecipients([""]);
          setMessage("");
        }, 2000);
      } else {
        setError(data.detail || 'Failed to send email');
      }
    } catch (error) {
      console.error('Email send error:', error);
      setError('Network error. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      onClose();
      // Reset form state
      setRecipients([""]);
      setMessage("");
      setError("");
      setIsSuccess(false);
    }
  };

  if (!isOpen) return null;

  const modalContent = (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[60] animate-fade-in">
      <div className="glass-card neon-border-indigo p-6 max-w-lg w-full mx-4 animate-slide-up max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-neon-indigo/10 flex items-center justify-center">
              <Mail size={20} className="text-neon-indigo" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Share Report via Email</h2>
              <p className="text-xs text-gray-500">
                {reportType === "investigation" ? "Investigation Report" :
                 reportType === "brief" ? "Market Brief" : "Comparison Analysis"}
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-2 text-gray-500 hover:text-white transition-colors rounded-lg bg-white/[0.03] hover:bg-white/[0.08]"
          >
            <X size={18} />
          </button>
        </div>

        {!isSuccess ? (
          <form onSubmit={handleSubmit} className="flex flex-col min-h-0 flex-1">
            <div className="overflow-y-auto custom-scrollbar pr-2 space-y-4 mb-4">
              {/* Recipients */}
              <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Recipients <span className="text-neon-red">*</span>
              </label>
              <div className="space-y-2">
                {recipients.map((email, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => updateRecipient(idx, e.target.value)}
                      placeholder="Enter email address"
                      className="flex-1 px-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-lg text-white text-sm placeholder-gray-600 focus:outline-none focus:border-neon-indigo/40 focus:bg-white/[0.05] transition-all"
                      required
                    />
                    {recipients.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeRecipient(idx)}
                        className="p-2 text-gray-500 hover:text-neon-red transition-colors bg-white/[0.03] hover:bg-neon-red/10 rounded-lg"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                ))}
              </div>
              <div className="flex items-center justify-between mt-2">
                <button
                  type="button"
                  onClick={addRecipient}
                  disabled={recipients.length >= 10}
                  className="text-xs flex items-center gap-1 text-neon-indigo hover:text-neon-indigo/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Plus size={14} />
                  Add Recipient
                </button>
                <span className="text-[10px] text-gray-500">
                  {getValidRecipients().length} valid recipient(s) • Maximum 10
                </span>
              </div>
            </div>

            {/* Subject */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Subject
              </label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full px-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-lg text-white text-sm placeholder-gray-600 focus:outline-none focus:border-neon-indigo/40 focus:bg-white/[0.05] transition-all"
              />
            </div>

            {/* Message */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Personal Message (optional)
              </label>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Add a personal message to the recipients..."
                rows={4}
                className="w-full px-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-lg text-white text-sm placeholder-gray-600 focus:outline-none focus:border-neon-indigo/40 focus:bg-white/[0.05] transition-all resize-none"
              />
            </div>

            {/* Error */}
            {error && (
              <div className="p-3 rounded-xl bg-neon-red/10 border border-neon-red/20 text-red-300 text-xs flex items-start gap-2 animate-slide-up">
                <AlertCircle size={13} className="mt-0.5 flex-shrink-0" />
                {error}
              </div>
            )}

            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4 border-t border-white/[0.04] mt-auto flex-shrink-0">
              <button
                type="button"
                onClick={handleClose}
                disabled={isLoading}
                className="btn-ghost flex-1 py-2.5 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading || getValidRecipients().length === 0}
                className="btn-primary flex-1 flex items-center justify-center gap-2 py-2.5 disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send size={16} />
                    Send Report
                  </>
                )}
              </button>
            </div>
          </form>
        ) : (
          /* Success State */
          <div className="text-center space-y-4 py-8">
            <div className="w-16 h-16 mx-auto rounded-full bg-neon-emerald/10 flex items-center justify-center animate-pulse-glow-emerald">
              <CheckCircle size={24} className="text-neon-emerald" />
            </div>
            <h3 className="text-lg font-semibold text-white">Report Sent Successfully!</h3>
            <p className="text-gray-400 text-sm">
              The report has been sent to {getValidRecipients().length} recipient(s).
            </p>
          </div>
        )}
      </div>
    </div>
  );

  if (typeof document === 'undefined') return null;
  return createPortal(modalContent, document.body);
}
