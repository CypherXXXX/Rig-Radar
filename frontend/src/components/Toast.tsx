"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, XCircle, Info, X } from "lucide-react";

type ToastType = "success" | "error" | "info";

interface Toast {
    id: number;
    message: string;
    type: ToastType;
}

interface ToastContextValue {
    toast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue>({
    toast: () => {},
});

export function useToast() {
    return useContext(ToastContext);
}

let _nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const addToast = useCallback((message: string, type: ToastType = "info") => {
        const id = ++_nextId;
        setToasts((prev) => [...prev, { id, message, type }]);
        setTimeout(() => {
            setToasts((prev) => prev.filter((t) => t.id !== id));
        }, 4000);
    }, []);

    const removeToast = useCallback((id: number) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);

    const icons = {
        success: <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0" />,
        error: <XCircle className="w-5 h-5 text-red-400 shrink-0" />,
        info: <Info className="w-5 h-5 text-cyan-400 shrink-0" />,
    };

    const glows = {
        success: "shadow-[0_0_20px_-5px_rgba(52,211,153,0.3)]",
        error: "shadow-[0_0_20px_-5px_rgba(248,113,113,0.3)]",
        info: "shadow-[0_0_20px_-5px_rgba(34,211,238,0.3)]",
    };

    const borders = {
        success: "border-emerald-400/20",
        error: "border-red-400/20",
        info: "border-cyan-400/20",
    };

    return (
        <ToastContext.Provider value={{ toast: addToast }}>
            {children}
            <div className="fixed bottom-6 right-6 z-100 flex flex-col gap-3 pointer-events-none">
                <AnimatePresence>
                    {toasts.map((t) => (
                        <motion.div
                            key={t.id}
                            initial={{ opacity: 0, y: 20, scale: 0.92, x: 40 }}
                            animate={{ opacity: 1, y: 0, scale: 1, x: 0 }}
                            exit={{ opacity: 0, x: 40, scale: 0.92 }}
                            transition={{ type: "spring", stiffness: 400, damping: 25 }}
                            className={`pointer-events-auto flex items-center gap-3 glass border ${borders[t.type]} rounded-2xl px-5 py-4 max-w-sm ${glows[t.type]}`}
                        >
                            {icons[t.type]}
                            <span className="text-sm text-slate-200 flex-1 font-medium">{t.message}</span>
                            <motion.button
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                                onClick={() => removeToast(t.id)}
                                className="text-slate-500 hover:text-slate-300 transition-colors p-0.5"
                            >
                                <X className="w-4 h-4" />
                            </motion.button>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </ToastContext.Provider>
    );
}
