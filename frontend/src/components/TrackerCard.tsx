"use client";

import { memo, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { TrendingDown, Package, Trash2, Loader2, ExternalLink } from "lucide-react";
import type { TrackedItem } from "@/types";
import { useDeleteTracker } from "@/lib/hooks";
import { useToast } from "@/components/Toast";

interface TrackerCardProps {
    item: TrackedItem;
    onDeleted?: () => void;
}

const TrackerCard = memo(function TrackerCard({ item, onDeleted }: TrackerCardProps) {
    const isDrop = item.current_price < item.target_price;
    const dropAmount = item.target_price - item.current_price;
    const progressPct = Math.min(100, Math.max(5, (item.current_price / item.target_price) * 100));
    const { execute: remove, loading: deleting } = useDeleteTracker();
    const { toast } = useToast();
    const [showConfirm, setShowConfirm] = useState(false);
    const [imgError, setImgError] = useState(false);

    const handleDelete = async (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (!showConfirm) {
            setShowConfirm(true);
            return;
        }
        try {
            await remove(item.item_id);
            onDeleted?.();
        } catch {
            toast("Failed to delete tracker", "error");
        }
    };

    const handleCancelDelete = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setShowConfirm(false);
    };

    return (
        <Link href={`/analytics/${item.item_id}`}>
            <motion.div
                whileHover={{ y: -4 }}
                transition={{ duration: 0.2 }}
                className="relative group glass rounded-2xl p-6 overflow-hidden transition-all duration-300 hover:border-cyan-400/30 hover:shadow-[0_0_40px_-10px_rgba(34,211,238,0.2)] card-shine h-full flex flex-col"
            >
                <div className="absolute inset-0 bg-linear-to-br from-cyan-400/3 to-purple-500/3 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                <div className="relative z-10 flex justify-between items-start">
                    <div className="flex items-center gap-3.5 min-w-0 flex-1">
                        <motion.div
                            whileHover={{ scale: 1.05 }}
                            className="w-14 h-14 rounded-xl bg-white/5 flex items-center justify-center border border-slate-700/30 overflow-hidden shrink-0"
                        >
                            {item.product_image_url && !imgError ? (
                                <img
                                    src={item.product_image_url}
                                    alt={item.product_name}
                                    referrerPolicy="no-referrer"
                                    crossOrigin="anonymous"
                                    className="w-full h-full object-contain p-1.5"
                                    onError={() => setImgError(true)}
                                />
                            ) : (
                                <Package className="text-slate-500 w-6 h-6" />
                            )}
                        </motion.div>
                        <div className="min-w-0 flex-1">
                            <h3 className="font-medium text-slate-200 line-clamp-2 text-sm leading-snug group-hover:text-white transition-colors">{item.product_name}</h3>
                            <div className="flex items-center gap-2 mt-1.5">
                                <span className="text-xs text-slate-500 capitalize px-2 py-0.5 rounded-full bg-slate-800/50 border border-slate-700/30">{item.store}</span>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 ml-3">
                        {isDrop && (
                            <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                className="flex items-center gap-1 text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded-lg text-xs font-semibold border border-emerald-400/20"
                            >
                                <TrendingDown className="w-3 h-3" />
                                -₹{dropAmount.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                            </motion.div>
                        )}
                    </div>
                </div>

                <div className="relative z-10 mt-5 flex items-end justify-between flex-1">
                    <div>
                        <p className="text-xs text-slate-500 mb-1">Current</p>
                        <p className="text-xl font-mono text-emerald-400 font-bold">₹{item.current_price?.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                    </div>
                    <div className="text-right">
                        <p className="text-xs text-slate-500 mb-1">Target</p>
                        <p className="text-base font-mono text-slate-300 font-medium">₹{item.target_price?.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                    </div>
                </div>

                <div className="relative z-10 mt-4 w-full bg-slate-800/30 rounded-full h-2 overflow-hidden">
                    <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${progressPct}%` }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                        className={`h-full rounded-full ${isDrop ? "bg-linear-to-r from-emerald-400 to-emerald-500" : "bg-linear-to-r from-amber-400 to-amber-500"}`}
                    />
                </div>

                <div className="relative z-10 mt-4 flex items-center justify-between">
                    <div className="flex items-center gap-1 text-slate-600 text-xs opacity-0 group-hover:opacity-100 transition-opacity">
                        <ExternalLink className="w-3 h-3" />
                        View analytics
                    </div>

                    {showConfirm ? (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="flex items-center gap-2"
                        >
                            <span className="text-xs text-red-400">Delete?</span>
                            <button
                                onClick={handleDelete}
                                disabled={deleting}
                                className="text-xs bg-red-500/15 text-red-400 px-2.5 py-1 rounded-lg hover:bg-red-500/25 transition-colors disabled:opacity-50 flex items-center gap-1 border border-red-500/20"
                            >
                                {deleting ? <Loader2 className="w-3 h-3 animate-spin" /> : "Yes"}
                            </button>
                            <button
                                onClick={handleCancelDelete}
                                className="text-xs bg-slate-800/50 text-slate-400 px-2.5 py-1 rounded-lg hover:bg-slate-700/50 transition-colors"
                            >
                                No
                            </button>
                        </motion.div>
                    ) : (
                        <motion.button
                            whileHover={{ scale: 1.15 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={handleDelete}
                            className="opacity-0 group-hover:opacity-100 text-slate-600 hover:text-red-400 transition-all p-1.5 rounded-lg hover:bg-red-400/10"
                        >
                            <Trash2 className="w-4 h-4" />
                        </motion.button>
                    )}
                </div>
            </motion.div>
        </Link>
    );
});

export default TrackerCard;
