"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Bell, Loader2, CheckCircle, Link2 } from "lucide-react";
import { useUser } from "@clerk/nextjs";
import { useCreateTracker } from "@/lib/hooks";
import { useToast } from "@/components/Toast";
import type { TrackedItem } from "@/types";

interface AddTrackerModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (item: TrackedItem) => void;
}

export default function AddTrackerModal({ isOpen, onClose, onSuccess }: AddTrackerModalProps) {
    const { user } = useUser();
    const { execute, loading, error } = useCreateTracker();
    const { toast } = useToast();

    const [url, setUrl] = useState("");
    const [price, setPrice] = useState("");
    const [method, setMethod] = useState<"email" | "discord">("email");
    const [contactInfo, setContactInfo] = useState("");
    const [success, setSuccess] = useState(false);

    const resetForm = () => {
        setUrl("");
        setPrice("");
        setMethod("email");
        setContactInfo("");
        setSuccess(false);
    };

    const handleClose = () => {
        if (loading) return;
        resetForm();
        onClose();
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!url.trim() || !price || !user?.id) return;

        const sanitizedUrl = url.trim();
        const parsedPrice = parseFloat(price);
        if (parsedPrice <= 0 || !Number.isFinite(parsedPrice)) return;

        try {
            const newItem = await execute({
                product_url: sanitizedUrl,
                target_price: parsedPrice,
                notification_type: method,
                contact_info: contactInfo.trim() || user.primaryEmailAddress?.emailAddress || "",
                user_id: user.id,
            });

            setSuccess(true);
            toast("Tracker created successfully!", "success");

            setTimeout(() => {
                resetForm();
                if (newItem) onSuccess(newItem);
            }, 1200);
        } catch {
            toast("Failed to create tracker", "error");
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={handleClose}
                    className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                >
                    <motion.div
                        initial={{ scale: 0.92, opacity: 0, y: 30 }}
                        animate={{ scale: 1, opacity: 1, y: 0 }}
                        exit={{ scale: 0.92, opacity: 0, y: 30 }}
                        transition={{ type: "spring", stiffness: 400, damping: 30 }}
                        onClick={(e) => e.stopPropagation()}
                        className="glass border border-slate-700/40 p-7 rounded-3xl w-full max-w-md shadow-2xl shadow-slate-950/70 relative overflow-hidden"
                    >
                        <div className="absolute top-0 left-0 right-0 h-1 bg-linear-to-r from-cyan-400 via-purple-500 to-cyan-400 animate-gradient" />

                        <motion.button
                            whileHover={{ scale: 1.1, rotate: 90 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={handleClose}
                            disabled={loading}
                            className="absolute top-5 right-5 text-slate-500 hover:text-slate-300 transition-colors disabled:opacity-50 p-1 rounded-lg hover:bg-slate-800/50"
                        >
                            <X className="w-5 h-5" />
                        </motion.button>

                        <div className="flex items-center gap-3 mb-7">
                            <motion.div
                                animate={success ? { scale: [1, 1.2, 1], backgroundColor: "rgba(52, 211, 153, 0.1)" } : {}}
                                className="w-12 h-12 rounded-2xl bg-cyan-400/10 flex items-center justify-center border border-cyan-400/20"
                            >
                                {success ? (
                                    <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring" }}>
                                        <CheckCircle className="w-6 h-6 text-emerald-400" />
                                    </motion.div>
                                ) : (
                                    <Bell className="w-6 h-6 text-cyan-400" />
                                )}
                            </motion.div>
                            <div>
                                <h2 className="text-xl font-bold text-slate-200">
                                    {success ? "Tracker Created!" : "New Price Tracker"}
                                </h2>
                                <p className="text-xs text-slate-500 mt-0.5">{success ? "Monitoring has begun" : "Track any Amazon or Flipkart product"}</p>
                            </div>
                        </div>

                        {success ? (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="text-center py-8"
                            >
                                <motion.div
                                    initial={{ scale: 0 }}
                                    animate={{ scale: 1 }}
                                    transition={{ type: "spring", delay: 0.1 }}
                                >
                                    <CheckCircle className="w-20 h-20 text-emerald-400 mx-auto mb-5" />
                                </motion.div>
                                <p className="text-slate-300 font-medium">Your price tracker is now active.</p>
                                <p className="text-slate-500 text-sm mt-1">We&apos;ll notify you when the price drops.</p>
                            </motion.div>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-5">
                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">Product URL</label>
                                    <div className="relative">
                                        <Link2 className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                                        <input
                                            type="url"
                                            value={url}
                                            onChange={(e) => setUrl(e.target.value)}
                                            placeholder="https://amazon.in/..."
                                            className="w-full bg-slate-900/50 border border-slate-700/50 rounded-xl pl-10 pr-4 py-3 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/40 focus:ring-1 focus:ring-cyan-400/20 transition-all"
                                            required
                                            disabled={loading}
                                        />
                                    </div>
                                    <p className="text-xs text-slate-500 mt-1.5 text-left pl-1">
                                        Paste a valid Amazon or Flipkart product URL to begin tracking.
                                    </p>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">Target Price (₹)</label>
                                    <input
                                        type="number"
                                        value={price}
                                        onChange={(e) => setPrice(e.target.value)}
                                        placeholder="49999"
                                        step="0.01"
                                        min="0.01"
                                        className="w-full bg-slate-900/50 border border-slate-700/50 rounded-xl px-4 py-3 font-mono text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/40 focus:ring-1 focus:ring-cyan-400/20 transition-all"
                                        required
                                        disabled={loading}
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">Notification Method</label>
                                    <div className="grid grid-cols-2 gap-3">
                                        <motion.button
                                            type="button"
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                            onClick={() => setMethod("email")}
                                            disabled={loading}
                                            className={`text-sm py-3 rounded-xl border transition-all font-medium ${method === "email" ? "bg-cyan-400/10 border-cyan-400/30 text-cyan-400 shadow-[0_0_15px_-5px_rgba(34,211,238,0.2)]" : "bg-slate-900/50 border-slate-700/50 text-slate-500 hover:border-slate-600"}`}
                                        >
                                            📧 Email
                                        </motion.button>
                                        <motion.button
                                            type="button"
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                            onClick={() => setMethod("discord")}
                                            disabled={loading}
                                            className={`text-sm py-3 rounded-xl border transition-all font-medium ${method === "discord" ? "bg-purple-500/10 border-purple-500/30 text-purple-400 shadow-[0_0_15px_-5px_rgba(168,85,247,0.2)]" : "bg-slate-900/50 border-slate-700/50 text-slate-500 hover:border-slate-600"}`}
                                        >
                                            💬 Discord
                                        </motion.button>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">
                                        {method === "email" ? "Email Address" : "Discord Webhook URL"}
                                    </label>
                                    <input
                                        type={method === "email" ? "email" : "url"}
                                        value={contactInfo}
                                        onChange={(e) => setContactInfo(e.target.value)}
                                        placeholder={method === "email" ? "you@example.com" : "https://discord.com/api/webhooks/..."}
                                        className="w-full bg-slate-900/50 border border-slate-700/50 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/40 focus:ring-1 focus:ring-cyan-400/20 transition-all"
                                        disabled={loading}
                                        required={method === "discord"}
                                    />
                                    <p className="text-xs text-slate-600 mt-1.5">
                                        {method === "email"
                                            ? "Leave blank to use your account email."
                                            : "In Discord: Edit Channel → Integrations → Webhooks → New Webhook → Copy URL."}
                                    </p>
                                </div>

                                {error && (
                                    <motion.div
                                        initial={{ opacity: 0, height: 0 }}
                                        animate={{ opacity: 1, height: "auto" }}
                                        className="bg-red-400/5 border border-red-400/20 rounded-xl px-4 py-3"
                                    >
                                        <p className="text-red-400 text-sm">{error}</p>
                                    </motion.div>
                                )}

                                <div className="pt-2">
                                    <motion.button
                                        type="submit"
                                        disabled={loading}
                                        whileHover={!loading ? { scale: 1.02, y: -1 } : {}}
                                        whileTap={!loading ? { scale: 0.98 } : {}}
                                        className="w-full bg-linear-to-r from-cyan-400 to-cyan-500 text-slate-900 font-semibold py-3.5 rounded-xl transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-400/20 hover:shadow-cyan-400/30"
                                    >
                                        {loading ? (
                                            <>
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                                Creating Tracker...
                                            </>
                                        ) : (
                                            "Start Tracking"
                                        )}
                                    </motion.button>
                                </div>
                            </form>
                        )}
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
