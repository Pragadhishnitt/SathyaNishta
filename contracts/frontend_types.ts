/**
 * Sathya Nishta — Frontend Contracts (TypeScript Types)
 * ======================================================
 * TEAM B OWNS THIS FILE (but must match backend schemas).
 *
 * All types used for:
 * - API requests/responses
 * - UI state management
 * - SSE event handling
 *
 * Version: 1.0.0
 * Last Updated: Sprint 1
 */

// ==========================================
// ENUMS
// ==========================================

export enum InvestigationStatus {
    QUEUED = "queued",
    RUNNING = "running",
    COMPLETED = "completed",
    FAILED = "failed",
    STOPPED = "stopped"
}

export enum AgentType {
    FINANCIAL = "financial",
    GRAPH = "graph",
    AUDIO = "audio",
    COMPLIANCE = "compliance"
}

export enum AgentStatus {
    PENDING = "pending",
    RUNNING = "running",
    APPROVED = "approved",
    REJECTED = "rejected",
    FAILED = "failed"
}

export enum Severity {
    CRITICAL = "critical",
    HIGH = "high",
    MEDIUM = "medium",
    LOW = "low",
    INFO = "info"
}

export enum Verdict {
    CRITICAL = "critical",  // Score 8-10
    HIGH = "high",          // Score 6-7.9
    MEDIUM = "medium",      // Score 4-5.9
    LOW = "low",            // Score 2-3.9
    SAFE = "safe"           // Score 0-1.9
}

// ==========================================
// SHARED MODELS
// ==========================================

export interface Finding {
    type: string;
    severity: Severity;
    detail: string;
    evidence: string;
    confidence: number;  // 0.0 to 1.0
    metadata?: Record<string, any>;
}

// ==========================================
// API REQUESTS & RESPONSES
// ==========================================

export interface InvestigationRequest {
    query: string;
    context?: Record<string, any>;
}

export interface InvestigationResponse {
    investigation_id: string;  // UUID
    status: InvestigationStatus;
    stream_url: string;
    estimated_completion_time?: string;  // ISO 8601
}

export interface DomainFindings {
    agent_type: AgentType;
    findings: Finding[];
    confidence: number;
    status: AgentStatus;
}

export interface InvestigationReport {
    investigation_id: string;  // UUID
    query: string;
    status: InvestigationStatus;
    fraud_risk_score: number;  // 0.0 to 10.0
    verdict: Verdict;
    summary: string;
    domains: Record<AgentType, DomainFindings>;
    cross_domain_insights: string[];
    evidence_chain: string[];
    audit_trail_id: string;
    created_at: string;  // ISO 8601
    updated_at: string;  // ISO 8601
}

// ==========================================
// SSE EVENTS
// ==========================================

export interface SSEEventData {
    agent?: AgentType;
    status?: AgentStatus;
    message?: string;
    progress?: number;  // 0-100
    [key: string]: any;
}

export interface AgentStartedEvent extends SSEEventData {
    agent: AgentType;
    status: "running";
}

export interface AgentCompletedEvent extends SSEEventData {
    agent: AgentType;
    status: "approved" | "rejected" | "failed";
    findings_count?: number;
}

export interface InvestigationCompleteEvent extends SSEEventData {
    investigation_id: string;
    fraud_risk_score: number;
    verdict: Verdict;
}

export interface ErrorEvent extends SSEEventData {
    error: string;
    error_code?: string;
}

// ==========================================
// UI STATE MODELS
// ==========================================

export interface AgentCardState {
    agent_type: AgentType;
    status: AgentStatus;
    findings_count: number;
    confidence?: number;
    start_time?: Date;
    end_time?: Date;
}

export interface InvestigationProgress {
    investigation_id: string;
    status: InvestigationStatus;
    agents: AgentCardState[];
    current_step: string;
    progress_percent: number;  // 0-100
}

// ==========================================
// API CLIENT ERROR
// ==========================================

export class SathyaNishtaAPIError extends Error {
    constructor(
        message: string,
        public status: number,
        public code?: string
    ) {
        super(message);
        this.name = "SathyaNishtaAPIError";
    }
}

// ==========================================
// HELPER TYPES
// ==========================================

/**
 * Type guard to check if event is an agent event
 */
export function isAgentEvent(event: SSEEventData): event is AgentStartedEvent | AgentCompletedEvent {
    return "agent" in event && typeof event.agent === "string";
}

/**
 * Type guard to check if event is investigation complete
 */
export function isInvestigationCompleteEvent(event: SSEEventData): event is InvestigationCompleteEvent {
    return "investigation_id" in event && "fraud_risk_score" in event;
}

/**
 * Convert verdict enum to display color
 */
export function getVerdictColor(verdict: Verdict): string {
    switch (verdict) {
        case Verdict.CRITICAL: return "#dc2626";  // red-600
        case Verdict.HIGH: return "#ea580c";      // orange-600
        case Verdict.MEDIUM: return "#f59e0b";    // amber-500
        case Verdict.LOW: return "#eab308";       // yellow-500
        case Verdict.SAFE: return "#10b981";      // emerald-500
    }
}

/**
 * Convert severity enum to display color
 */
export function getSeverityColor(severity: Severity): string {
    switch (severity) {
        case Severity.CRITICAL: return "#dc2626";
        case Severity.HIGH: return "#ea580c";
        case Severity.MEDIUM: return "#f59e0b";
        case Severity.LOW: return "#3b82f6";
        case Severity.INFO: return "#6b7280";
    }
}

/**
 * Format fraud risk score with color coding
 */
export function formatFraudScore(score: number): { formatted: string; color: string } {
    const formatted = score.toFixed(1);
    let color: string;
    if (score >= 8) color = "#dc2626";
    else if (score >= 6) color = "#ea580c";
    else if (score >= 4) color = "#f59e0b";
    else if (score >= 2) color = "#eab308";
    else color = "#10b981";
    return { formatted, color };
}
