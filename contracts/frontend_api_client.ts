/**
 * Sathya Nishta — Frontend API Client
 * ====================================
 * TEAM B OWNS THIS FILE.
 *
 * Handles all API communication with the backend:
 * - POST /api/v1/investigate (start investigation)
 * - GET /api/v1/investigate/:id (get report)
 * - SSE /api/v1/investigate/:id/stream (real-time updates)
 *
 * Version: 1.0.0
 * Last Updated: Sprint 1
 */

import {
    InvestigationRequest,
    InvestigationResponse,
    InvestigationReport,
    SSEEventData,
    SathyaNishtaAPIError
} from './types';

export class SathyaNishtaClient {
    private baseUrl: string;
    private apiKey?: string;

    /**
     * Initialize the API client
     * @param baseUrl Backend API base URL (default: http://127.0.0.1:8000)
     * @param apiKey Optional API key for authentication
     */
    constructor(baseUrl: string = "http://127.0.0.1:8000", apiKey?: string) {
        this.baseUrl = baseUrl.replace(/\/$/, "");  // Remove trailing slash
        this.apiKey = apiKey;
    }

    /**
     * Internal request wrapper with error handling
     */
    private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;
        const headers: HeadersInit = {
            "Content-Type": "application/json",
            ...(this.apiKey ? { "X-API-Key": this.apiKey } : {}),
            ...options.headers,
        };

        try {
            const response = await fetch(url, { ...options, headers });

            if (!response.ok) {
                // Handle rate limiting
                if (response.status === 429) {
                    throw new SathyaNishtaAPIError(
                        "Rate limit exceeded (100 requests/min). Please try again later.",
                        429,
                        "RATE_LIMIT_EXCEEDED"
                    );
                }

                // Handle authentication errors
                if (response.status === 401) {
                    throw new SathyaNishtaAPIError(
                        "Authentication failed. Please check your API key.",
                        401,
                        "UNAUTHORIZED"
                    );
                }

                // Generic error
                const errorText = await response.text();
                throw new SathyaNishtaAPIError(
                    errorText || `HTTP ${response.status}`,
                    response.status
                );
            }

            return response.json() as Promise<T>;
        } catch (error) {
            if (error instanceof SathyaNishtaAPIError) {
                throw error;
            }
            // Network error or JSON parse error
            throw new SathyaNishtaAPIError(
                error instanceof Error ? error.message : "Network error",
                0,
                "NETWORK_ERROR"
            );
        }
    }

    /**
     * Start a new investigation
     * @param request Investigation query and optional context
     * @returns Investigation ID and stream URL
     * @example
     * const response = await client.startInvestigation({
     *   query: "Investigate Adani for circular trading in Q3 2024"
     * });
     * console.log(response.investigation_id);
     */
    async startInvestigation(request: InvestigationRequest): Promise<InvestigationResponse> {
        return this.request<InvestigationResponse>("/api/v1/investigate", {
            method: "POST",
            body: JSON.stringify(request),
        });
    }

    /**
     * Get the final report for a completed investigation
     * @param investigationId UUID of the investigation
     * @returns Complete investigation report with findings and verdict
     * @example
     * const report = await client.getReport("123e4567-e89b-12d3-a456-426614174000");
     * console.log(report.fraud_risk_score, report.verdict);
     */
    async getReport(investigationId: string): Promise<InvestigationReport> {
        return this.request<InvestigationReport>(`/api/v1/investigate/${investigationId}`);
    }

    /**
     * Get the EventSource URL for real-time SSE streaming
     * @param investigationId UUID of the investigation
     * @returns Full URL to the SSE endpoint
     * @example
     * const eventSource = new EventSource(client.getStreamUrl(investigationId));
     * eventSource.addEventListener("agent_started", (e) => {
     *   const data = JSON.parse(e.data);
     *   console.log("Agent started:", data.agent);
     * });
     */
    getStreamUrl(investigationId: string): string {
        const url = `${this.baseUrl}/api/v1/investigate/${investigationId}/stream`;
        // Add API key as query param for SSE (EventSource doesn't support headers)
        if (this.apiKey) {
            return `${url}?api_key=${encodeURIComponent(this.apiKey)}`;
        }
        return url;
    }

    /**
     * Create and configure an EventSource for real-time updates
     * @param investigationId UUID of the investigation
     * @param handlers Event handlers for different event types
     * @returns Configured EventSource instance
     * @example
     * const eventSource = client.createEventSource(investigationId, {
     *   onAgentStarted: (data) => console.log("Agent started:", data.agent),
     *   onAgentCompleted: (data) => console.log("Agent completed:", data.agent, data.status),
     *   onInvestigationComplete: (data) => console.log("Investigation done:", data.fraud_risk_score),
     *   onError: (error) => console.error("SSE error:", error)
     * });
     */
    createEventSource(
        investigationId: string,
        handlers: {
            onAgentStarted?: (data: SSEEventData) => void;
            onAgentCompleted?: (data: SSEEventData) => void;
            onInvestigationComplete?: (data: SSEEventData) => void;
            onError?: (error: Event) => void;
        }
    ): EventSource {
        const url = this.getStreamUrl(investigationId);
        const eventSource = new EventSource(url);

        // Register event handlers
        if (handlers.onAgentStarted) {
            eventSource.addEventListener("agent_started", (e) => {
                const data = JSON.parse((e as MessageEvent).data);
                handlers.onAgentStarted!(data);
            });
        }

        if (handlers.onAgentCompleted) {
            eventSource.addEventListener("agent_completed", (e) => {
                const data = JSON.parse((e as MessageEvent).data);
                handlers.onAgentCompleted!(data);
            });
        }

        if (handlers.onInvestigationComplete) {
            eventSource.addEventListener("investigation_complete", (e) => {
                const data = JSON.parse((e as MessageEvent).data);
                handlers.onInvestigationComplete!(data);
                // Auto-close connection on completion
                eventSource.close();
            });
        }

        if (handlers.onError) {
            eventSource.onerror = handlers.onError;
        }

        return eventSource;
    }

    /**
     * Helper: Start investigation and return both response and EventSource
     * @param request Investigation query
     * @param handlers SSE event handlers
     * @returns Object with investigation response and configured EventSource
     * @example
     * const { response, eventSource } = await client.startInvestigationWithStream({
     *   query: "Investigate company X"
     * }, {
     *   onAgentStarted: (data) => updateUI(data)
     * });
     */
    async startInvestigationWithStream(
        request: InvestigationRequest,
        handlers: Parameters<typeof this.createEventSource>[1]
    ): Promise<{ response: InvestigationResponse; eventSource: EventSource }> {
        const response = await this.startInvestigation(request);
        const eventSource = this.createEventSource(response.investigation_id, handlers);
        return { response, eventSource };
    }
}

/**
 * Default client instance for convenience
 * Usage: import { apiClient } from './api';
 */
export const apiClient = new SathyaNishtaClient(
    process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"
);
