"use client";

import { use, useMemo, useState, useCallback } from "react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, ReferenceLine } from "recharts";
import { ArrowLeft, AlertTriangle, RefreshCw, ExternalLink, BarChart3, TrendingDown, TrendingUp, Minus, Clock, Calendar, Loader2, Package } from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { useAnalytics, useRefreshPrice } from "@/lib/hooks";
import { useToast } from "@/components/Toast";

type Period = "1m" | "3m" | "6m" | "1y";

function StatSkeleton() {
    return (
        <div className="glass rounded-2xl p-6 flex flex-col items-center animate-pulse">
            <div className="w-10 h-10 rounded-xl bg-slate-800/50 mb-3" />
            <div className="h-3 bg-slate-800/50 rounded w-20 mb-3" />
            <div className="h-7 bg-slate-800/50 rounded w-24" />
        </div>
    );
}

export default function AnalyticsPage({ params }: { params: Promise<{ itemId: string }> }) {
    const resolvedParams = use(params);
    const { toast } = useToast();
    const [selectedPeriod, setSelectedPeriod] = useState<Period | undefined>(undefined);
    const [imgError, setImgError] = useState(false);

    const { data: analyticsData, loading: analyticsLoading, error: analyticsError, refetch: refetchAnalytics } = useAnalytics(resolvedParams.itemId, selectedPeriod);
    const { execute: refreshPrice, loading: refreshing } = useRefreshPrice();

    const item = analyticsData?.item ?? null;
    const history = analyticsData?.history ?? [];
    const serverStats = analyticsData?.stats ?? null;
    const hasExternalHistory = analyticsData?.external_history ?? false;

    const handleRefresh = useCallback(async () => {
        try {
            await refreshPrice(resolvedParams.itemId);
            refetchAnalytics(selectedPeriod);
            toast("Price refreshed successfully!", "success");
        } catch {
            toast("Failed to refresh price", "error");
        }
    }, [resolvedParams.itemId, refreshPrice, refetchAnalytics, selectedPeriod, toast]);

    const handlePeriodSelect = useCallback((period: Period) => {
        if (selectedPeriod === period) {
            setSelectedPeriod(undefined);
        } else {
            setSelectedPeriod(period);
        }
    }, [selectedPeriod]);

    const chartData = useMemo(() => {
        if (!history || history.length === 0) return [];
        return history.map((h) => ({
            timestamp: new Date(h.timestamp).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "2-digit" }),
            price: h.price,
            fullDate: new Date(h.timestamp).toLocaleDateString("en-IN", { day: "2-digit", month: "long", year: "numeric" }),
        }));
    }, [history]);

    const yDomain = useMemo(() => {
        if (chartData.length === 0) return [0, 100];
        const prices = chartData.map((d) => d.price);
        const minP = Math.min(...prices);
        const maxP = Math.max(...prices);
        if (minP === maxP) {
            const pad = Math.max(minP * 0.05, 500);
            return [Math.max(0, minP - pad), maxP + pad];
        }
        const range = maxP - minP;
        const pad = range * 0.15;
        return [Math.max(0, minP - pad), maxP + pad];
    }, [chartData]);

    const priceChange = useMemo(() => {
        if (!item) return null;
        const diff = item.current_price - item.target_price;
        return { diff };
    }, [item]);

    const periodLabels: { key: Period; label: string; desc: string }[] = [
        { key: "1m", label: "1 Month", desc: "Last 30 days" },
        { key: "3m", label: "3 Months", desc: "Last 90 days" },
        { key: "6m", label: "6 Months", desc: "Last 180 days" },
        { key: "1y", label: "1 Year", desc: "Last 365 days" },
    ];

    if (analyticsLoading && !analyticsData) {
        return (
            <div className="flex flex-col gap-8">
                <div className="h-4 bg-slate-800/50 rounded w-40 animate-pulse" />
                <div className="flex flex-col md:flex-row justify-between gap-6">
                    <div className="flex gap-6">
                        <div className="w-32 h-32 bg-slate-800/50 rounded-2xl animate-pulse shrink-0" />
                        <div className="space-y-3">
                            <div className="h-8 bg-slate-800/50 rounded w-72 animate-pulse" />
                            <div className="h-4 bg-slate-800/50 rounded w-40 animate-pulse" />
                        </div>
                    </div>
                    <div className="space-y-2">
                        <div className="h-3 bg-slate-800/50 rounded w-20 animate-pulse" />
                        <div className="h-9 bg-slate-800/50 rounded w-28 animate-pulse" />
                    </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <StatSkeleton />
                    <StatSkeleton />
                    <StatSkeleton />
                    <StatSkeleton />
                </div>
                <div className="glass rounded-2xl p-6 h-[500px] animate-pulse" />
            </div>
        );
    }

    if (analyticsError || !item) {
        return (
            <div className="flex flex-col items-center justify-center py-32 gap-4">
                <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="w-20 h-20 rounded-3xl bg-red-400/10 flex items-center justify-center border border-red-400/20"
                >
                    <AlertTriangle className="w-10 h-10 text-red-400" />
                </motion.div>
                <p className="text-red-400 font-medium text-lg">{analyticsError ?? "Item not found"}</p>
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => refetchAnalytics()}
                    className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors glass px-4 py-2 rounded-xl"
                >
                    <RefreshCw className="w-4 h-4" /> Retry
                </motion.button>
            </div>
        );
    }

    const showStats = selectedPeriod && serverStats && serverStats.lowest !== null;

    return (
        <div className="flex flex-col gap-8">
            <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
            >
                <Link href="/dashboard" className="inline-flex items-center gap-2 text-slate-400 hover:text-white transition-colors w-fit group">
                    <motion.div whileHover={{ x: -3 }} transition={{ duration: 0.15 }}>
                        <ArrowLeft className="w-4 h-4" />
                    </motion.div>
                    <span className="text-sm">Back to Dashboard</span>
                </Link>
            </motion.div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col md:flex-row justify-between items-start gap-6"
            >
                <div className="flex gap-5 items-start">
                    <motion.div
                        whileHover={{ scale: 1.05 }}
                        className="w-28 h-28 md:w-32 md:h-32 rounded-2xl glass overflow-hidden shrink-0 flex items-center justify-center"
                    >
                        {item.product_image_url && !imgError ? (
                            <img
                                src={item.product_image_url}
                                alt={item.product_name}
                                referrerPolicy="no-referrer"
                                crossOrigin="anonymous"
                                className="w-full h-full object-contain p-3"
                                onError={() => setImgError(true)}
                            />
                        ) : (
                            <Package className="w-12 h-12 text-slate-600" />
                        )}
                    </motion.div>
                    <div className="flex-1 min-w-0">
                        <h1 className="text-xl md:text-2xl lg:text-3xl font-bold text-white mb-3 leading-tight">{item.product_name}</h1>
                        <div className="flex flex-wrap items-center gap-3">
                            <span className="inline-flex items-center gap-1.5 bg-slate-800/50 text-slate-300 px-3 py-1.5 rounded-full text-xs font-medium capitalize border border-slate-700/30">
                                {item.store}
                            </span>
                            <a
                                href={item.product_url}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1.5 text-cyan-400 hover:text-cyan-300 text-sm transition-colors group"
                            >
                                View on {item.store}
                                <ExternalLink className="w-3 h-3 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                            </a>
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={handleRefresh}
                                disabled={refreshing}
                                className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-emerald-400 transition-colors px-3 py-1.5 rounded-full glass border border-slate-700/30 hover:border-emerald-400/30 disabled:opacity-50"
                            >
                                {refreshing ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                                Refresh Price
                            </motion.button>
                        </div>
                    </div>
                </div>
                <div className="text-left md:text-right shrink-0">
                    <p className="text-sm text-slate-500 mb-1">Current Price</p>
                    <motion.p
                        key={serverStats?.current}
                        initial={{ scale: 1.05, color: "#22d3ee" }}
                        animate={{ scale: 1, color: "#34d399" }}
                        className="text-3xl md:text-4xl font-mono font-bold text-emerald-400"
                    >
                        ₹{(serverStats?.current ?? item.current_price)?.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </motion.p>
                    {priceChange && (
                        <motion.div
                            initial={{ opacity: 0, y: 5 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={`mt-2 inline-flex items-center gap-1 text-sm font-medium px-3 py-1.5 rounded-xl ${priceChange.diff <= 0 ? "text-emerald-400 bg-emerald-400/10 border border-emerald-400/20" : "text-red-400 bg-red-400/10 border border-red-400/20"}`}
                        >
                            {priceChange.diff < 0 ? <TrendingDown className="w-3.5 h-3.5" /> : priceChange.diff > 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <Minus className="w-3.5 h-3.5" />}
                            {priceChange.diff <= 0 ? `₹${Math.abs(priceChange.diff).toLocaleString("en-IN")} below target` : `₹${priceChange.diff.toLocaleString("en-IN")} above target`}
                        </motion.div>
                    )}
                    <div className="mt-2">
                        <p className="text-xs text-slate-600">Target: <span className="text-slate-400 font-mono">₹{item.target_price?.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span></p>
                    </div>
                </div>
            </motion.div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="glass rounded-2xl p-6"
            >
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-cyan-400/10 flex items-center justify-center border border-cyan-400/20">
                            <Calendar className="w-5 h-5 text-cyan-400" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-slate-200">Price History</h3>
                            <p className="text-xs text-slate-500">Select a time period to fetch historical pricing data</p>
                        </div>
                    </div>
                    {analyticsLoading && analyticsData && (
                        <div className="flex items-center gap-2 text-cyan-400 text-sm">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Fetching data...
                        </div>
                    )}
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {periodLabels.map((p) => (
                        <motion.button
                            key={p.key}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => handlePeriodSelect(p.key)}
                            disabled={analyticsLoading}
                            className={`relative p-4 rounded-xl text-left transition-all duration-300 border disabled:opacity-60 ${
                                selectedPeriod === p.key
                                    ? "bg-cyan-400/10 border-cyan-400/30 shadow-[0_0_20px_-5px_rgba(34,211,238,0.3)]"
                                    : "glass border-slate-700/30 hover:border-slate-600/50"
                            }`}
                        >
                            <p className={`text-sm font-semibold mb-0.5 ${selectedPeriod === p.key ? "text-cyan-400" : "text-slate-300"}`}>{p.label}</p>
                            <p className="text-xs text-slate-500">{p.desc}</p>
                            {selectedPeriod === p.key && (
                                <motion.div
                                    layoutId="periodIndicator"
                                    className="absolute top-2 right-2 w-2 h-2 rounded-full bg-cyan-400"
                                    transition={{ duration: 0.2 }}
                                />
                            )}
                        </motion.button>
                    ))}
                </div>
            </motion.div>

            <AnimatePresence mode="wait">
                {showStats && (
                    <motion.div
                        key="stats"
                        initial={{ opacity: 0, y: 20, height: 0 }}
                        animate={{ opacity: 1, y: 0, height: "auto" }}
                        exit={{ opacity: 0, y: -10, height: 0 }}
                        transition={{ duration: 0.3 }}
                        className="grid grid-cols-2 md:grid-cols-4 gap-4"
                    >
                        <div className="glass rounded-2xl p-5 flex flex-col items-center text-center group hover:border-emerald-400/20 transition-all duration-300 hover:shadow-[0_0_30px_-10px_rgba(52,211,153,0.2)]">
                            <motion.div
                                whileHover={{ scale: 1.1, rotate: -10 }}
                                className="w-10 h-10 rounded-xl bg-emerald-400/10 flex items-center justify-center mb-3 border border-emerald-400/20"
                            >
                                <TrendingDown className="w-5 h-5 text-emerald-400" />
                            </motion.div>
                            <p className="text-slate-500 text-xs mb-1.5 uppercase tracking-wider">Lowest</p>
                            <p className="text-xl font-mono text-emerald-400 font-bold">
                                ₹{serverStats!.lowest!.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </p>
                        </div>
                        <div className="glass rounded-2xl p-5 flex flex-col items-center text-center group hover:border-red-400/20 transition-all duration-300 hover:shadow-[0_0_30px_-10px_rgba(248,113,113,0.2)]">
                            <motion.div
                                whileHover={{ scale: 1.1, rotate: 10 }}
                                className="w-10 h-10 rounded-xl bg-red-400/10 flex items-center justify-center mb-3 border border-red-400/20"
                            >
                                <TrendingUp className="w-5 h-5 text-red-400" />
                            </motion.div>
                            <p className="text-slate-500 text-xs mb-1.5 uppercase tracking-wider">Highest</p>
                            <p className="text-xl font-mono text-red-400 font-bold">
                                ₹{serverStats!.highest!.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </p>
                        </div>
                        <div className="glass rounded-2xl p-5 flex flex-col items-center text-center group hover:border-cyan-400/20 transition-all duration-300 hover:shadow-[0_0_30px_-10px_rgba(34,211,238,0.2)]">
                            <motion.div
                                whileHover={{ scale: 1.1, rotate: -5 }}
                                className="w-10 h-10 rounded-xl bg-cyan-400/10 flex items-center justify-center mb-3 border border-cyan-400/20"
                            >
                                <BarChart3 className="w-5 h-5 text-cyan-400" />
                            </motion.div>
                            <p className="text-slate-500 text-xs mb-1.5 uppercase tracking-wider">Average</p>
                            <p className="text-xl font-mono text-cyan-400 font-bold">
                                ₹{serverStats!.average!.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </p>
                        </div>
                        <div className="glass rounded-2xl p-5 flex flex-col items-center text-center group hover:border-purple-400/20 transition-all duration-300 hover:shadow-[0_0_30px_-10px_rgba(168,85,247,0.2)]">
                            <motion.div
                                whileHover={{ scale: 1.1, rotate: 5 }}
                                className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center mb-3 border border-purple-500/20"
                            >
                                <Clock className="w-5 h-5 text-purple-400" />
                            </motion.div>
                            <p className="text-slate-500 text-xs mb-1.5 uppercase tracking-wider">Data Points</p>
                            <p className="text-xl font-mono text-purple-400 font-bold">
                                {serverStats!.data_points}
                            </p>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <AnimatePresence mode="wait">
                {selectedPeriod && (
                    <motion.div
                        key="chart"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ delay: 0.1 }}
                        className="glass rounded-2xl p-6 min-h-[500px] flex flex-col"
                    >
                        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-xl bg-cyan-400/10 flex items-center justify-center border border-cyan-400/20">
                                    <LineChart className="w-5 h-5 text-cyan-400" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-semibold text-slate-200">Price Timeline</h3>
                                    <p className="text-xs text-slate-500 flex items-center gap-1">
                                        <Calendar className="w-3 h-3" />
                                        {periodLabels.find((p) => p.key === selectedPeriod)?.desc}
                                        {chartData.length > 0 && ` · ${chartData.length} data points`}
                                        {hasExternalHistory && (
                                            <span className="ml-1 text-emerald-400">· Historical data available</span>
                                        )}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {analyticsLoading ? (
                            <div className="flex flex-col items-center justify-center flex-1 gap-4">
                                <Loader2 className="w-10 h-10 text-cyan-400 animate-spin" />
                                <p className="text-slate-400 font-medium">Fetching price history...</p>
                                <p className="text-slate-600 text-sm">Scraping real-time data from the web</p>
                            </div>
                        ) : chartData.length > 0 ? (
                            <div style={{ width: "100%", height: 400, position: "relative" }}>
                                <ResponsiveContainer width="100%" height={400}>
                                    <AreaChart key={selectedPeriod || 'default'} data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                                        <defs>
                                            <linearGradient id="colorPriceMain" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.25} />
                                                <stop offset="50%" stopColor="#22d3ee" stopOpacity={0.08} />
                                                <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                                        <XAxis
                                            dataKey="timestamp"
                                            stroke="#64748b"
                                            fontSize={11}
                                            tickLine={false}
                                            axisLine={false}
                                            dy={10}
                                            interval="preserveStartEnd"
                                            minTickGap={20}
                                        />
                                        <YAxis
                                            stroke="#64748b"
                                            fontSize={11}
                                            tickLine={false}
                                            axisLine={false}
                                            tickFormatter={(value: number) => value >= 1000 ? `₹${(value / 1000).toFixed(1)}k` : `₹${value}`}
                                            domain={yDomain}
                                            width={70}
                                        />
                                        {item.target_price && (
                                            <ReferenceLine
                                                y={item.target_price}
                                                stroke="#a855f7"
                                                strokeDasharray="6 4"
                                                strokeWidth={1.5}
                                                label={{
                                                    value: `Target: ₹${item.target_price.toLocaleString("en-IN")}`,
                                                    position: "insideTopRight",
                                                    style: { fill: "#a855f7", fontSize: 11, fontWeight: 500 },
                                                }}
                                            />
                                        )}
                                        <Tooltip
                                            contentStyle={{
                                                backgroundColor: "rgba(15, 23, 42, 0.95)",
                                                borderColor: "#1e293b",
                                                borderRadius: "16px",
                                                color: "#f8fafc",
                                                padding: "14px 18px",
                                                backdropFilter: "blur(12px)",
                                                boxShadow: "0 20px 40px -10px rgba(0,0,0,0.5)",
                                            }}
                                            itemStyle={{ color: "#22d3ee", fontWeight: "bold", fontFamily: "var(--font-mono)" }}
                                            labelStyle={{ color: "#94a3b8", fontSize: "12px", marginBottom: "6px" }}
                                            formatter={((value: unknown) => [`₹${Number(value || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`, "Price"]) as never}
                                        />
                                        <Area
                                            type="monotoneX"
                                            dataKey="price"
                                            stroke="#22d3ee"
                                            fillOpacity={1}
                                            fill="url(#colorPriceMain)"
                                            strokeWidth={2.5}
                                            dot={chartData.length <= 30 ? { fill: "#22d3ee", strokeWidth: 0, r: 4 } : false}
                                            activeDot={{ fill: "#22d3ee", strokeWidth: 3, stroke: "#0f172a", r: 7 }}
                                            animationDuration={800}
                                            animationEasing="ease-out"
                                        />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center flex-1 gap-4">
                                <motion.div
                                    animate={{ y: [0, -6, 0] }}
                                    transition={{ repeat: Infinity, duration: 3 }}
                                    className="w-16 h-16 rounded-3xl bg-slate-800/50 flex items-center justify-center border border-slate-700/30"
                                >
                                    <BarChart3 className="w-8 h-8 text-slate-600" />
                                </motion.div>
                                <p className="text-slate-400 font-medium">No historical data found for this period</p>
                                <p className="text-slate-600 text-sm text-center max-w-md">
                                    Price history will build up automatically as the product is tracked over time. Each visit and refresh adds real data points.
                                </p>
                                <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={handleRefresh}
                                    disabled={refreshing}
                                    className="inline-flex items-center gap-2 text-sm text-cyan-400 hover:text-cyan-300 transition-colors glass px-4 py-2 rounded-xl border border-cyan-400/20 disabled:opacity-50"
                                >
                                    {refreshing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                                    Add Data Point
                                </motion.button>
                            </div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>

            {!selectedPeriod && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="glass rounded-2xl p-8 flex flex-col items-center justify-center gap-4 min-h-[300px]"
                >
                    <motion.div
                        animate={{ y: [0, -8, 0] }}
                        transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
                        className="w-20 h-20 rounded-3xl bg-linear-to-br from-cyan-400/10 to-purple-400/10 flex items-center justify-center border border-cyan-400/20"
                    >
                        <BarChart3 className="w-10 h-10 text-cyan-400" />
                    </motion.div>
                    <h3 className="text-xl font-semibold text-slate-200">Select a time period above</h3>
                    <p className="text-slate-500 text-sm text-center max-w-md">
                        Choose a time range to fetch and display accurate historical pricing data, including lowest, highest, and average prices for that period.
                    </p>
                </motion.div>
            )}

            {item.created_at && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                    className="flex items-center justify-center gap-2 text-xs text-slate-600"
                >
                    <Clock className="w-3 h-3" />
                    Tracking since {new Date(item.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "long", year: "numeric" })}
                    {item.updated_at && ` · Last updated ${new Date(item.updated_at).toLocaleDateString("en-IN", { day: "2-digit", month: "long", year: "numeric" })}`}
                </motion.div>
            )}
        </div>
    );
}

function LineChart(props: React.SVGProps<SVGSVGElement>) {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
            <path d="M3 3v18h18" />
            <path d="m19 9-5 5-4-4-3 3" />
        </svg>
    );
}
