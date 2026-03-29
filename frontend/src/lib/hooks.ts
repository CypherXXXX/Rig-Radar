"use client";

import { useState, useEffect, useCallback } from "react";
import type { TrackedItem, PriceHistoryEntry, TrendingDeal, AnalyticsData } from "@/types";
import { getUserItems, getHistory, getTrending, createTracker, deleteTracker, refreshItemPrice, getAnalytics } from "@/lib/api";

interface AsyncState<T> {
    data: T | null;
    loading: boolean;
    error: string | null;
    refetch: () => void;
}

function useAsync<T>(
    fetcher: () => Promise<{ data: T }>,
    deps: unknown[] = []
): AsyncState<T> {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const execute = useCallback(() => {
        setLoading(true);
        setError(null);
        fetcher()
            .then((res) => setData(res.data))
            .catch((err: Error) => setError(err.message))
            .finally(() => setLoading(false));
    }, deps);

    useEffect(() => {
        execute();
    }, [execute]);

    return { data, loading, error, refetch: execute };
}

export function useUserItems(userId: string | null | undefined): AsyncState<TrackedItem[]> {
    return useAsync<TrackedItem[]>(
        () => {
            if (!userId) return Promise.resolve({ data: [] as TrackedItem[], message: "", success: true });
            return getUserItems(userId);
        },
        [userId]
    );
}

export function usePriceHistory(itemId: string): AsyncState<PriceHistoryEntry[]> {
    return useAsync<PriceHistoryEntry[]>(
        () => getHistory(itemId),
        [itemId]
    );
}

export function useAnalytics(itemId: string, period?: string) {
    const [data, setData] = useState<AnalyticsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const execute = useCallback((p?: string) => {
        setLoading(true);
        setError(null);
        getAnalytics(itemId, p)
            .then((res) => setData(res.data))
            .catch((err: Error) => setError(err.message))
            .finally(() => setLoading(false));
    }, [itemId]);

    useEffect(() => {
        execute(period);
    }, [execute, period]);

    return { data, loading, error, refetch: execute };
}

export function useTrending(): AsyncState<TrendingDeal[]> {
    return useAsync<TrendingDeal[]>(() => getTrending(), []);
}

export function useCreateTracker() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const execute = useCallback(
        async (data: Parameters<typeof createTracker>[0]) => {
            setLoading(true);
            setError(null);
            try {
                const res = await createTracker(data);
                return res.data;
            } catch (err: unknown) {
                const msg = err instanceof Error ? err.message : "Failed to create tracker";
                setError(msg);
                throw err;
            } finally {
                setLoading(false);
            }
        },
        []
    );

    return { execute, loading, error };
}

export function useDeleteTracker() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const execute = useCallback(async (itemId: string) => {
        setLoading(true);
        setError(null);
        try {
            await deleteTracker(itemId);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : "Failed to delete tracker";
            setError(msg);
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    return { execute, loading, error };
}

export function useRefreshPrice() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const execute = useCallback(async (itemId: string) => {
        setLoading(true);
        setError(null);
        try {
            const res = await refreshItemPrice(itemId);
            return res.data;
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : "Failed to refresh price";
            setError(msg);
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    return { execute, loading, error };
}
