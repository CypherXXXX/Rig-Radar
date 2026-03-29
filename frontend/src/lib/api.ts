import type {
    TrackedItem,
    PriceHistoryEntry,
    TrendingDeal,
    TrackRequest,
    ApiResponse,
    AnalyticsData,
} from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchApi<T>(
    path: string,
    options: RequestInit = {}
): Promise<ApiResponse<T>> {
    const url = `${API_URL}${path}`;

    const res = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
    });

    if (!res.ok) {
        const body = await res.json().catch(() => null);
        const detail =
            body?.detail ?? body?.message ?? `API error ${res.status}`;
        throw new Error(detail);
    }

    return res.json() as Promise<ApiResponse<T>>;
}

export async function getUserItems(userId: string): Promise<ApiResponse<TrackedItem[]>> {
    return fetchApi<TrackedItem[]>(`/api/items/${encodeURIComponent(userId)}`);
}

export async function getHistory(itemId: string): Promise<ApiResponse<PriceHistoryEntry[]>> {
    return fetchApi<PriceHistoryEntry[]>(`/api/history/${encodeURIComponent(itemId)}`);
}

export async function getTrending(): Promise<ApiResponse<TrendingDeal[]>> {
    return fetchApi<TrendingDeal[]>("/api/trending");
}

export async function createTracker(data: TrackRequest): Promise<ApiResponse<TrackedItem>> {
    return fetchApi<TrackedItem>("/api/track", {
        method: "POST",
        body: JSON.stringify(data),
    });
}

export async function deleteTracker(itemId: string): Promise<ApiResponse<null>> {
    return fetchApi<null>(`/api/items/${encodeURIComponent(itemId)}`, {
        method: "DELETE",
    });
}

export async function refreshItemPrice(itemId: string): Promise<ApiResponse<TrackedItem>> {
    return fetchApi<TrackedItem>(`/api/refresh/${encodeURIComponent(itemId)}`, {
        method: "POST",
    });
}

export async function getAnalytics(itemId: string, period?: string): Promise<ApiResponse<AnalyticsData>> {
    const params = period ? `?period=${encodeURIComponent(period)}` : "";
    return fetchApi<AnalyticsData>(`/api/analytics/${encodeURIComponent(itemId)}${params}`);
}
