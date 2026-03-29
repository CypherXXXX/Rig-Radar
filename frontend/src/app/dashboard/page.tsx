"use client";

import { useState } from "react";
import { Plus, AlertTriangle, RefreshCw, TrendingDown, LayoutDashboard, Search, SlidersHorizontal } from "lucide-react";
import { useUser } from "@clerk/nextjs";
import { motion, AnimatePresence } from "framer-motion";
import TrackerCard from "@/components/TrackerCard";
import AddTrackerModal from "@/components/AddTrackerModal";
import { useUserItems } from "@/lib/hooks";
import { useToast } from "@/components/Toast";
import type { TrackedItem } from "@/types";

function CardSkeleton() {
    return (
        <div className="glass rounded-2xl p-6 animate-pulse">
            <div className="flex items-center gap-3 mb-6">
                <div className="w-14 h-14 rounded-xl bg-slate-800/50" />
                <div className="flex-1 space-y-2">
                    <div className="h-4 bg-slate-800/50 rounded w-3/4" />
                    <div className="h-3 bg-slate-800/50 rounded w-1/4" />
                </div>
            </div>
            <div className="flex justify-between items-end">
                <div className="space-y-2">
                    <div className="h-3 bg-slate-800/50 rounded w-12" />
                    <div className="h-7 bg-slate-800/50 rounded w-24" />
                </div>
                <div className="space-y-2">
                    <div className="h-3 bg-slate-800/50 rounded w-12" />
                    <div className="h-5 bg-slate-800/50 rounded w-16" />
                </div>
            </div>
            <div className="h-1.5 bg-slate-800/50 rounded-full mt-5" />
        </div>
    );
}

export default function DashboardPage() {
    const { user } = useUser();
    const userId = user?.id ?? null;
    const { data: items, loading: itemsLoading, error: itemsError, refetch: refetchItems } = useUserItems(userId);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [sortBy, setSortBy] = useState<"name" | "price" | "date">("date");
    const { toast } = useToast();

    const handleTrackerCreated = (_newItem: TrackedItem) => {
        toast("Tracker created successfully!", "success");
        refetchItems();
        setIsModalOpen(false);
    };

    const handleItemDeleted = () => {
        toast("Tracker removed", "info");
        refetchItems();
    };

    const filteredItems = items
        ? items
            .filter((item) => {
                if (!searchQuery) return true;
                return item.product_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    item.store.toLowerCase().includes(searchQuery.toLowerCase());
            })
            .sort((a, b) => {
                if (sortBy === "name") return a.product_name.localeCompare(b.product_name);
                if (sortBy === "price") return a.current_price - b.current_price;
                return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
            })
        : [];

    const totalTrackers = items?.length ?? 0;
    const belowTarget = items?.filter((i) => i.current_price < i.target_price).length ?? 0;
    const totalSavings = items?.reduce((sum, i) => {
        const diff = i.target_price - i.current_price;
        return diff > 0 ? sum + diff : sum;
    }, 0) ?? 0;

    return (
        <div className="flex flex-col gap-8">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6">
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-center gap-4"
                >
                    <div className="w-14 h-14 rounded-2xl bg-linear-to-br from-cyan-400/20 to-purple-500/20 flex items-center justify-center border border-cyan-400/20">
                        <LayoutDashboard className="w-7 h-7 text-cyan-400" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
                        <p className="text-slate-400 text-sm mt-0.5">Manage your price trackers and alerts</p>
                    </div>
                </motion.div>

                <motion.button
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    whileHover={{ scale: 1.03, y: -2 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => setIsModalOpen(true)}
                    className="w-full sm:w-auto flex items-center justify-center gap-2 bg-linear-to-r from-cyan-400 to-cyan-500 text-slate-950 px-6 py-3 rounded-xl font-semibold shadow-lg shadow-cyan-400/20 hover:shadow-cyan-400/30 transition-shadow"
                >
                    <Plus className="w-5 h-5" />
                    Add Tracker
                </motion.button>
            </div>

            {!itemsLoading && !itemsError && items && items.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="grid grid-cols-1 md:grid-cols-3 gap-4"
                >
                    <div className="glass rounded-2xl p-5 flex items-center gap-4">
                        <div className="w-11 h-11 rounded-xl bg-cyan-400/10 flex items-center justify-center border border-cyan-400/20">
                            <LayoutDashboard className="w-5 h-5 text-cyan-400" />
                        </div>
                        <div>
                            <p className="text-2xl font-bold text-white font-mono">{totalTrackers}</p>
                            <p className="text-xs text-slate-500">Active Trackers</p>
                        </div>
                    </div>
                    <div className="glass rounded-2xl p-5 flex items-center gap-4">
                        <div className="w-11 h-11 rounded-xl bg-emerald-400/10 flex items-center justify-center border border-emerald-400/20">
                            <TrendingDown className="w-5 h-5 text-emerald-400" />
                        </div>
                        <div>
                            <p className="text-2xl font-bold text-emerald-400 font-mono">{belowTarget}</p>
                            <p className="text-xs text-slate-500">Below Target</p>
                        </div>
                    </div>
                    <div className="glass rounded-2xl p-5 flex items-center gap-4">
                        <div className="w-11 h-11 rounded-xl bg-purple-500/10 flex items-center justify-center border border-purple-500/20">
                            <TrendingDown className="w-5 h-5 text-purple-400" />
                        </div>
                        <div>
                            <p className="text-2xl font-bold text-purple-400 font-mono">₹{totalSavings.toLocaleString("en-IN", { maximumFractionDigits: 0 })}</p>
                            <p className="text-xs text-slate-500">Potential Savings</p>
                        </div>
                    </div>
                </motion.div>
            )}

            {!itemsLoading && !itemsError && items && items.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15 }}
                    className="flex flex-col sm:flex-row gap-3"
                >
                    <div className="relative flex-1">
                        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search trackers..."
                            className="w-full glass rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/30 focus:ring-1 focus:ring-cyan-400/20 transition-all border border-slate-800/50"
                        />
                    </div>
                    <div className="flex items-center gap-2">
                        <SlidersHorizontal className="w-4 h-4 text-slate-500" />
                        {(["date", "name", "price"] as const).map((s) => (
                            <button
                                key={s}
                                onClick={() => setSortBy(s)}
                                className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                                    sortBy === s
                                        ? "bg-cyan-400/10 text-cyan-400 border border-cyan-400/20"
                                        : "text-slate-500 hover:text-slate-300 border border-transparent"
                                }`}
                            >
                                {s.charAt(0).toUpperCase() + s.slice(1)}
                            </button>
                        ))}
                    </div>
                </motion.div>
            )}

            {itemsError && (
                <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center gap-4 bg-red-400/5 border border-red-400/20 rounded-2xl p-5"
                >
                    <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
                    <div className="flex-1">
                        <p className="text-red-400 text-sm font-medium">Failed to load trackers</p>
                        <p className="text-red-400/60 text-xs mt-0.5">{itemsError}</p>
                    </div>
                    <motion.button
                        whileHover={{ rotate: 180 }}
                        transition={{ duration: 0.3 }}
                        onClick={refetchItems}
                        className="text-red-400 hover:text-red-300 transition-colors"
                    >
                        <RefreshCw className="w-4 h-4" />
                    </motion.button>
                </motion.div>
            )}

            {itemsLoading && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {Array.from({ length: 6 }).map((_, i) => (
                        <CardSkeleton key={i} />
                    ))}
                </div>
            )}

            {!itemsLoading && !itemsError && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <AnimatePresence mode="popLayout">
                        {filteredItems.length > 0 ? (
                            filteredItems.map((item, i) => (
                                <motion.div
                                    key={item.item_id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, scale: 0.95 }}
                                    transition={{ delay: i * 0.05 }}
                                >
                                    <TrackerCard item={item} onDeleted={handleItemDeleted} />
                                </motion.div>
                            ))
                        ) : (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="col-span-1 md:col-span-2 lg:col-span-3 py-24 flex flex-col items-center justify-center glass rounded-2xl"
                            >
                                <motion.div
                                    animate={{ y: [0, -8, 0] }}
                                    transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
                                    className="w-20 h-20 rounded-3xl bg-linear-to-br from-cyan-400/10 to-purple-500/10 border border-slate-800 flex items-center justify-center mb-6"
                                >
                                    <Plus className="w-10 h-10 text-slate-600" />
                                </motion.div>
                                <p className="text-slate-400 mb-2 font-medium text-lg">No tracked items yet</p>
                                <p className="text-slate-600 text-sm mb-6 max-w-xs text-center">Start by adding a product URL from Amazon or Flipkart to track its price.</p>
                                <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={() => setIsModalOpen(true)}
                                    className="text-cyan-400 hover:text-cyan-300 font-medium transition-colors text-sm flex items-center gap-1"
                                >
                                    Add your first tracker
                                    <Plus className="w-4 h-4" />
                                </motion.button>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            )}

            <AddTrackerModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSuccess={handleTrackerCreated}
            />
        </div>
    );
}
