"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Radar, Menu, X } from "lucide-react";
import { UserButton, useUser, SignInButton } from "@clerk/nextjs";
import { motion, AnimatePresence } from "framer-motion";

export default function Navbar() {
    const { isSignedIn } = useUser();
    const pathname = usePathname();
    const [scrolled, setScrolled] = useState(false);
    const [mobileOpen, setMobileOpen] = useState(false);
    const navRef = useRef<HTMLElement>(null);

    useEffect(() => {
        const handler = () => setScrolled(window.scrollY > 10);
        window.addEventListener("scroll", handler, { passive: true });
        return () => window.removeEventListener("scroll", handler);
    }, []);

    useEffect(() => {
        setMobileOpen(false);
    }, [pathname]);

    const links = [
        { href: "/dashboard", label: "Dashboard" },
        { href: "/trending", label: "Trending" },
    ];

    const isActive = (href: string) => pathname === href;

    return (
        <nav
            ref={navRef}
            className={`sticky top-0 z-50 transition-all duration-300 ${
                scrolled
                    ? "bg-slate-950/90 backdrop-blur-2xl border-b border-slate-800/60 shadow-lg shadow-slate-950/50"
                    : "bg-transparent border-b border-transparent"
            }`}
        >
            <div className="max-w-7xl mx-auto px-6 h-[72px] flex items-center justify-between">
                <Link href="/" className="flex items-center gap-2.5 group">
                    <motion.div
                        whileHover={{ rotate: 180 }}
                        transition={{ duration: 0.5, ease: "easeInOut" }}
                    >
                        <Radar className="w-8 h-8 text-cyan-400" />
                    </motion.div>
                    <span className="text-xl font-bold tracking-tight text-gradient">
                        RigRadar
                    </span>
                </Link>

                <div className="hidden md:flex items-center gap-1">
                    {links.map((link) => (
                        <Link
                            key={link.href}
                            href={link.href}
                            className={`relative px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                                isActive(link.href)
                                    ? "text-cyan-400"
                                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
                            }`}
                        >
                            {link.label}
                            {isActive(link.href) && (
                                <motion.div
                                    layoutId="navbar-indicator"
                                    className="absolute -bottom-px left-3 right-3 h-0.5 bg-linear-to-r from-cyan-400 to-purple-500 rounded-full"
                                    transition={{ type: "spring", stiffness: 400, damping: 30 }}
                                />
                            )}
                        </Link>
                    ))}
                </div>

                <div className="flex items-center gap-3">
                    {isSignedIn ? (
                        <UserButton />
                    ) : (
                        <SignInButton mode="modal">
                            <motion.button
                                whileHover={{ scale: 1.03 }}
                                whileTap={{ scale: 0.97 }}
                                className="text-sm font-medium px-5 py-2.5 rounded-xl bg-linear-to-r from-cyan-400/10 to-purple-500/10 border border-cyan-400/20 text-cyan-400 hover:border-cyan-400/40 transition-all duration-200"
                            >
                                Sign In
                            </motion.button>
                        </SignInButton>
                    )}

                    <button
                        onClick={() => setMobileOpen(!mobileOpen)}
                        className="md:hidden text-slate-400 hover:text-white transition-colors p-2"
                    >
                        {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                    </button>
                </div>
            </div>

            <AnimatePresence>
                {mobileOpen && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="md:hidden border-t border-slate-800/40 bg-slate-950/95 backdrop-blur-2xl"
                    >
                        <div className="px-6 py-4 flex flex-col gap-1">
                            {links.map((link) => (
                                <Link
                                    key={link.href}
                                    href={link.href}
                                    className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                                        isActive(link.href)
                                            ? "text-cyan-400 bg-cyan-400/5"
                                            : "text-slate-400 hover:text-white hover:bg-slate-800/30"
                                    }`}
                                >
                                    {link.label}
                                </Link>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </nav>
    );
}
