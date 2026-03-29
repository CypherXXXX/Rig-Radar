"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Flame, Star, ExternalLink, TrendingDown, RefreshCw, Loader2, ShoppingCart, Cpu, HardDrive, Monitor, MemoryStick, Zap, AlertTriangle } from "lucide-react";
import type { TrendingProduct } from "@/types";

const categoryIcons: Record<string, React.ElementType> = {
    "GPU": Cpu,
    "CPU": Cpu,
    "RAM": MemoryStick,
    "SSD": HardDrive,
    "Monitor": Monitor,
    "Keyboard": Zap,
    "Mouse": Monitor,
    "Motherboard": Cpu,
    "Cooling": Zap,
    "PSU": Zap,
    "Headset": Monitor,
    "Laptop": Monitor,
    "Graphics Cards": Cpu,
    "Processors": Cpu,
    "Storage": HardDrive,
    "Memory": MemoryStick,
    "Monitors": Monitor,
    "Computers": Cpu,
    "Electronics": Zap,
};

function ProductImage({ src, alt, fallbackIcon: FallbackIcon }: { src: string; alt: string; fallbackIcon: React.ElementType }) {
    const [error, setError] = useState(false);
    const [loaded, setLoaded] = useState(false);

    if (!src || error) {
        return <FallbackIcon className="w-10 h-10 text-slate-600" />;
    }

    return (
        <>
            {!loaded && <div className="absolute inset-0 bg-slate-800/30 animate-pulse rounded-xl" />}
            <img
                src={src}
                alt={alt}
                referrerPolicy="no-referrer"
                crossOrigin="anonymous"
                className={`w-full h-full object-contain transition-all duration-300 group-hover:scale-110 ${loaded ? "opacity-100" : "opacity-0"}`}
                onLoad={() => setLoaded(true)}
                onError={() => setError(true)}
            />
        </>
    );
}

export default function TrendingPage() {
    const [products, setProducts] = useState<TrendingProduct[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [filter, setFilter] = useState<string>("All");
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
    const [fetchError, setFetchError] = useState<string | null>(null);

    const fetchProducts = useCallback(async (isRefresh = false) => {
        if (isRefresh) setRefreshing(true);
        else setLoading(true);
        setFetchError(null);

        try {
            const res = await fetch(`/api/trending-products?force=${isRefresh ? "true" : "true"}`);
            const json = await res.json();
            if (json.success && json.data && json.data.length > 0) {
                setProducts(json.data);
                setLastUpdated(new Date());
                setFetchError(null);
            } else {
                setFetchError(json.message || "No products found");
            }
        } catch {
            setFetchError("Failed to connect to the server");
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, []);

    useEffect(() => {
        fetchProducts();

        const interval = setInterval(() => fetchProducts(true), 3600000);
        return () => clearInterval(interval);
    }, [fetchProducts]);

    const categories = ["All", ...Array.from(new Set(products.map((p) => p.category)))];
    const filtered = filter === "All" ? products : products.filter((p) => p.category === filter);

    return (
        <div className="flex flex-col gap-8 pb-12">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6">
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-center gap-4"
                >
                    <div className="w-14 h-14 rounded-2xl bg-linear-to-br from-orange-400/20 to-red-500/20 flex items-center justify-center border border-orange-400/20">
                        <Flame className="w-7 h-7 text-orange-400" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-white">Trending Tech</h1>
                        <p className="text-slate-400 text-sm mt-0.5">
                            Top 10 tech products trending on Amazon &amp; Flipkart
                            {lastUpdated && (
                                <span className="text-slate-600"> · Updated {lastUpdated.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}</span>
                            )}
                        </p>
                    </div>
                </motion.div>

                <motion.button
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => fetchProducts(true)}
                    disabled={refreshing}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl glass border border-slate-700/50 text-sm font-medium text-slate-300 hover:border-cyan-400/30 hover:text-cyan-400 transition-all disabled:opacity-50"
                >
                    {refreshing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                    Refresh
                </motion.button>
            </div>

            {products.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="flex gap-2 overflow-x-auto pb-2 scrollbar-none"
                >
                    {categories.map((cat) => (
                        <button
                            key={cat}
                            onClick={() => setFilter(cat)}
                            className={`px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all duration-200 ${
                                filter === cat
                                    ? "bg-linear-to-r from-cyan-400/15 to-purple-500/15 border border-cyan-400/30 text-cyan-400"
                                    : "glass border border-slate-800/50 text-slate-400 hover:text-slate-200 hover:border-slate-700"
                            }`}
                        >
                            {cat}
                        </button>
                    ))}
                </motion.div>
            )}

            {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {Array.from({ length: 10 }).map((_, i) => (
                        <div key={i} className="glass rounded-2xl p-6 animate-pulse">
                            <div className="flex gap-4">
                                <div className="w-24 h-24 rounded-xl bg-slate-800/50 shrink-0" />
                                <div className="flex-1 space-y-3">
                                    <div className="h-4 bg-slate-800/50 rounded w-3/4" />
                                    <div className="h-3 bg-slate-800/50 rounded w-1/3" />
                                    <div className="flex gap-3">
                                        <div className="h-6 bg-slate-800/50 rounded w-20" />
                                        <div className="h-6 bg-slate-800/50 rounded w-16" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            ) : fetchError && products.length === 0 ? (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="py-24 flex flex-col items-center justify-center glass rounded-2xl"
                >
                    <AlertTriangle className="w-12 h-12 text-amber-400 mb-4" />
                    <p className="text-slate-300 font-medium mb-1">Could not load trending products</p>
                    <p className="text-slate-500 text-sm mb-4 max-w-sm text-center">{fetchError}</p>
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => fetchProducts()}
                        className="text-sm text-cyan-400 hover:text-cyan-300 transition-colors flex items-center gap-1"
                    >
                        <RefreshCw className="w-3.5 h-3.5" />
                        Try Again
                    </motion.button>
                </motion.div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <AnimatePresence mode="popLayout">
                        {filtered.map((product, i) => {
                            const CategoryIcon = categoryIcons[product.category] || Cpu;
                            return (
                                <motion.a
                                    key={product.id}
                                    href={product.url}
                                    target="_blank"
                                    rel="noreferrer"
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, scale: 0.95 }}
                                    transition={{ delay: i * 0.06 }}
                                    whileHover={{ y: -4 }}
                                    className="group glass rounded-2xl p-6 overflow-hidden transition-all duration-300 hover:border-orange-400/30 hover:shadow-[0_0_40px_-10px_rgba(249,115,22,0.2)] card-shine flex flex-col"
                                >
                                    <div className="flex gap-5">
                                        <div className="w-24 h-24 rounded-xl bg-white/5 border border-slate-700/30 overflow-hidden flex items-center justify-center shrink-0 p-2 group-hover:border-orange-400/20 transition-colors relative">
                                            <ProductImage src={product.image} alt={product.name} fallbackIcon={CategoryIcon} />
                                        </div>

                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-start justify-between gap-2 mb-2">
                                                <h3 className="text-sm font-medium text-slate-200 line-clamp-2 leading-snug group-hover:text-white transition-colors">{product.name}</h3>
                                            </div>

                                            <div className="flex items-center gap-2 mb-3">
                                                <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${product.store === "Amazon" ? "bg-orange-400/10 text-orange-400 border border-orange-400/20" : "bg-blue-400/10 text-blue-400 border border-blue-400/20"}`}>
                                                    {product.store}
                                                </span>
                                                <span className="text-xs text-slate-500">{product.category}</span>
                                            </div>

                                            <div className="flex items-end gap-3">
                                                <p className="text-2xl font-mono font-bold text-emerald-400">₹{product.price.toLocaleString("en-IN")}</p>
                                                {product.originalPrice > product.price && (
                                                    <p className="text-sm font-mono text-slate-600 line-through mb-0.5">₹{product.originalPrice.toLocaleString("en-IN")}</p>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-800/40">
                                        <div className="flex items-center gap-4">
                                            {product.discount > 0 && (
                                                <div className="flex items-center gap-1 text-emerald-400 bg-emerald-400/10 px-2.5 py-1 rounded-lg text-xs font-semibold">
                                                    <TrendingDown className="w-3 h-3" />
                                                    {product.discount}% off
                                                </div>
                                            )}
                                            {product.rating > 0 && (
                                                <div className="flex items-center gap-1">
                                                    <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                                                    <span className="text-xs text-slate-400 font-medium">{product.rating.toFixed(1)}</span>
                                                    {product.reviews > 0 && (
                                                        <span className="text-xs text-slate-600">({product.reviews.toLocaleString("en-IN")})</span>
                                                    )}
                                                </div>
                                            )}
                                        </div>

                                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <span className="text-xs text-orange-400 font-medium flex items-center gap-1">
                                                <ShoppingCart className="w-3 h-3" />
                                                Buy Now
                                            </span>
                                            <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
                                        </div>
                                    </div>
                                </motion.a>
                            );
                        })}
                    </AnimatePresence>
                </div>
            )}

            {!loading && !fetchError && filtered.length === 0 && products.length > 0 && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="py-24 flex flex-col items-center justify-center glass rounded-2xl"
                >
                    <Flame className="w-12 h-12 text-slate-700 mb-4" />
                    <p className="text-slate-500 font-medium mb-1">No products in this category</p>
                    <button onClick={() => setFilter("All")} className="text-sm text-cyan-400 hover:text-cyan-300 transition-colors mt-2">
                        Show all products
                    </button>
                </motion.div>
            )}
        </div>
    );
}
