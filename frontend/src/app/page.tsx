"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import Link from "next/link";
import { Radar, TrendingDown, Bell, LineChart, ArrowRight, Sparkles, Shield, Zap, ChevronRight, Clock, Info, ExternalLink } from "lucide-react";
import { useRef } from "react";

const stats = [
    { value: "2", label: "Supported Platforms", sub: "Amazon & Flipkart" },
    { value: "30m", label: "Poll Interval", sub: "Automatic re-check" },
    { value: "6 Mo", label: "Price History", sub: "Per product tracked" },
    { value: "100%", label: "Free to Use", sub: "No credit card needed" },
];

const features = [
    {
        icon: TrendingDown,
        title: "Smart Price Tracking",
        description: "Monitor prices across Amazon India & Flipkart with automated scraping. Track GPUs, CPUs, SSDs, RAM, monitors, and all PC components.",
        gradient: "from-cyan-400 to-cyan-500",
        glow: "group-hover:shadow-[0_0_40px_-10px_rgba(34,211,238,0.4)]",
        iconBg: "bg-cyan-400/10 border-cyan-400/20",
        iconColor: "text-cyan-400",
    },
    {
        icon: Bell,
        title: "Discord & Email Alerts",
        description: "Set your target price and receive instant notifications via Discord webhook or Email the moment the price falls below your threshold.",
        gradient: "from-purple-400 to-purple-500",
        glow: "group-hover:shadow-[0_0_40px_-10px_rgba(168,85,247,0.4)]",
        iconBg: "bg-purple-500/10 border-purple-500/20",
        iconColor: "text-purple-400",
    },
    {
        icon: LineChart,
        title: "Historical Analytics",
        description: "Visualize up to 6 months of price trend data with interactive charts. See lowest, highest, and average prices at a glance to time your purchase perfectly.",
        gradient: "from-emerald-400 to-emerald-500",
        glow: "group-hover:shadow-[0_0_40px_-10px_rgba(52,211,153,0.4)]",
        iconBg: "bg-emerald-400/10 border-emerald-400/20",
        iconColor: "text-emerald-400",
    },
];

const steps = [
    { num: "01", title: "Paste Product URL", desc: "Drop any Amazon.in or Flipkart.com product link into the tracker to begin monitoring.", icon: Sparkles },
    { num: "02", title: "Set Target Price (₹)", desc: "Define the exact INR price point you are waiting for. We watch the rest 24/7.", icon: Shield },
    { num: "03", title: "Get Alerted Instantly", desc: "Receive a Discord or Email notification the moment the price drops below your target.", icon: Zap },
];

const tips = [
    {
        icon: ExternalLink,
        iconColor: "text-cyan-400",
        iconBg: "bg-cyan-400/10 border-cyan-400/20",
        title: "Paste a Clean Product URL",
        text: "Copy the product URL directly from your browser on Amazon.in or Flipkart.com. The best format is a direct /dp/ link for Amazon (e.g. amazon.in/dp/B09XJ3JJDD) or a /p/ link for Flipkart.",
    },
    {
        icon: Clock,
        iconColor: "text-purple-400",
        iconBg: "bg-purple-500/10 border-purple-500/20",
        title: "Price History Explained",
        text: "When you track a product, RigRadar fetches up to 6 months of historical data from external indexers. A flat graph means the product is too new or no external history is available yet.",
    },
    {
        icon: Info,
        iconColor: "text-emerald-400",
        iconBg: "bg-emerald-400/10 border-emerald-400/20",
        title: "How to Get Discord Alerts",
        text: "In your Discord server, go to Edit Channel → Integrations → Webhooks → New Webhook. Copy the webhook URL and paste it when selecting Discord as your notification method.",
    },
];

export default function Home() {
    const heroRef = useRef(null);
    const { scrollYProgress } = useScroll({ target: heroRef, offset: ["start start", "end start"] });
    const heroY = useTransform(scrollYProgress, [0, 1], [0, 100]);
    const heroOpacity = useTransform(scrollYProgress, [0, 0.8], [1, 0]);

    return (
        <div className="flex flex-col pb-24">
            <section ref={heroRef} className="relative pt-16 md:pt-28 pb-20 md:pb-32 flex flex-col items-center text-center overflow-hidden">
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-cyan-400/8 rounded-full blur-[120px] animate-pulse-glow" />
                    <div className="absolute top-1/3 left-1/3 w-[400px] h-[400px] bg-purple-500/6 rounded-full blur-[100px] animate-pulse-glow" style={{ animationDelay: "1.5s" }} />
                </div>

                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                    style={{ y: heroY, opacity: heroOpacity }}
                    className="max-w-4xl mx-auto flex flex-col items-center gap-6 relative z-10"
                >
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.15, duration: 0.4 }}
                        className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-linear-to-r from-cyan-400/10 to-purple-500/10 border border-cyan-400/20 text-cyan-400 text-sm font-medium"
                    >
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Real-time price intelligence for India</span>
                    </motion.div>

                    <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tight text-white leading-[1.05]">
                        Track Prices.
                        <br />
                        <span className="text-gradient">
                            Save Thousands.
                        </span>
                    </h1>

                    <p className="text-lg md:text-xl text-slate-400 max-w-2xl leading-relaxed">
                        Monitor tech hardware prices across Amazon India & Flipkart. Get instant Discord or Email alerts when prices drop below your target — never overpay again.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-4 mt-4 w-full sm:w-auto">
                        <Link href="/dashboard">
                            <motion.div
                                whileHover={{ scale: 1.03, y: -2 }}
                                whileTap={{ scale: 0.97 }}
                                className="px-8 py-4 rounded-2xl bg-linear-to-r from-cyan-400 to-cyan-500 text-slate-950 font-semibold flex items-center justify-center gap-2 min-w-[220px] shadow-lg shadow-cyan-400/20 transition-shadow hover:shadow-cyan-400/30"
                            >
                                Start Tracking Free
                                <ArrowRight className="w-4 h-4" />
                            </motion.div>
                        </Link>
                        <Link href="/trending">
                            <motion.div
                                whileHover={{ scale: 1.03, y: -2 }}
                                whileTap={{ scale: 0.97 }}
                                className="px-8 py-4 rounded-2xl glass border border-slate-700/50 text-white font-medium flex items-center justify-center gap-2 min-w-[220px] hover:border-cyan-400/30 transition-all"
                            >
                                View Trending Deals
                                <ChevronRight className="w-4 h-4" />
                            </motion.div>
                        </Link>
                    </div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 60 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
                    className="mt-20 w-full max-w-5xl mx-auto relative"
                >
                    <div className="absolute inset-x-0 -top-20 -bottom-20 bg-linear-to-b from-cyan-400/5 via-transparent to-transparent blur-2xl -z-10" />
                    <div className="glass rounded-3xl overflow-hidden shadow-2xl shadow-slate-950/50 border border-slate-700/30">
                        <div className="p-3 border-b border-slate-800/50 flex items-center gap-6 bg-slate-900/30">
                            <div className="flex items-center gap-1.5">
                                <div className="w-3 h-3 rounded-full bg-red-400/60" />
                                <div className="w-3 h-3 rounded-full bg-amber-400/60" />
                                <div className="w-3 h-3 rounded-full bg-emerald-400/60" />
                            </div>
                            <div className="flex-1 flex justify-center">
                                <div className="bg-slate-800/50 rounded-lg px-16 py-1.5 text-xs text-slate-500 font-mono">rigradar.vercel.app/dashboard</div>
                            </div>
                        </div>
                        <div className="p-8 grid grid-cols-3 gap-6">
                            {[
                                { title: "RTX 4070 Super", price: "₹52,999", drop: "-12%", color: "emerald" },
                                { title: "Ryzen 7 7800X3D", price: "₹27,490", drop: "-8%", color: "cyan" },
                                { title: "Samsung 990 Pro 2TB", price: "₹11,999", drop: "-15%", color: "purple" },
                            ].map((item, i) => (
                                <motion.div
                                    key={item.title}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.5 + i * 0.15 }}
                                    className="bg-slate-800/30 rounded-2xl p-5 border border-slate-700/30"
                                >
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="w-10 h-10 rounded-xl bg-slate-700/50 flex items-center justify-center">
                                            <Radar className="w-5 h-5 text-slate-500" />
                                        </div>
                                        <span className={`text-xs font-semibold px-2 py-1 rounded-lg ${i === 0 ? "text-emerald-400 bg-emerald-400/10" : i === 1 ? "text-cyan-400 bg-cyan-400/10" : "text-purple-400 bg-purple-400/10"}`}>
                                            {item.drop}
                                        </span>
                                    </div>
                                    <p className="text-sm text-slate-300 font-medium mb-1">{item.title}</p>
                                    <p className="text-lg font-mono font-bold text-emerald-400">{item.price}</p>
                                    <div className="mt-3 h-10 overflow-hidden rounded-lg">
                                        <svg viewBox="0 0 200 40" className="w-full h-full" preserveAspectRatio="none">
                                            <defs>
                                                <linearGradient id={`grad-${i}`} x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="0%" stopColor={i === 0 ? "#34d399" : i === 1 ? "#22d3ee" : "#c084fc"} stopOpacity="0.3" />
                                                    <stop offset="100%" stopColor={i === 0 ? "#34d399" : i === 1 ? "#22d3ee" : "#c084fc"} stopOpacity="0" />
                                                </linearGradient>
                                            </defs>
                                            <path d={`M0,${25 + i * 3} C40,${20 - i * 2} 60,${30 + i} 100,${22 - i * 2} C140,${15 + i * 3} 160,${28 - i} 200,${18 + i * 2}`} fill="none" stroke={i === 0 ? "#34d399" : i === 1 ? "#22d3ee" : "#c084fc"} strokeWidth="2" />
                                            <path d={`M0,${25 + i * 3} C40,${20 - i * 2} 60,${30 + i} 100,${22 - i * 2} C140,${15 + i * 3} 160,${28 - i} 200,${18 + i * 2} V40 H0 Z`} fill={`url(#grad-${i})`} />
                                        </svg>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </div>
                </motion.div>
            </section>

            <motion.section
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                className="py-16 border-y border-slate-800/30"
            >
                <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                    {stats.map((stat, i) => (
                        <motion.div
                            key={stat.label}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: i * 0.1 }}
                            className="text-center"
                        >
                            <p className="text-3xl md:text-4xl font-bold text-white font-mono">{stat.value}</p>
                            <p className="text-sm text-slate-400 mt-1 font-medium">{stat.label}</p>
                            <p className="text-xs text-slate-600 mt-0.5">{stat.sub}</p>
                        </motion.div>
                    ))}
                </div>
            </motion.section>

            <section className="py-24">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="text-center mb-16"
                >
                    <p className="text-sm font-medium text-cyan-400 mb-3 tracking-wider uppercase">Features</p>
                    <h2 className="text-3xl md:text-5xl font-bold text-white mb-4">Everything You Need to<br /><span className="text-gradient">Save Smarter</span></h2>
                    <p className="text-slate-400 max-w-2xl mx-auto text-lg">Powerful tools designed for the Indian tech market. Track, analyze, and buy at the perfect moment.</p>
                </motion.div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {features.map((feature, i) => (
                        <motion.div
                            key={feature.title}
                            initial={{ opacity: 0, y: 30 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: i * 0.12 }}
                            whileHover={{ y: -6 }}
                            className={`group glass rounded-2xl p-8 flex flex-col gap-5 transition-all duration-300 ${feature.glow} card-shine`}
                        >
                            <div className={`w-14 h-14 rounded-2xl ${feature.iconBg} flex items-center justify-center border transition-transform duration-300 group-hover:scale-110`}>
                                <feature.icon className={`w-7 h-7 ${feature.iconColor}`} />
                            </div>
                            <h3 className="text-xl font-semibold text-slate-200">{feature.title}</h3>
                            <p className="text-slate-400 leading-relaxed">{feature.description}</p>
                        </motion.div>
                    ))}
                </div>
            </section>

            <section className="py-24">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="text-center mb-16"
                >
                    <p className="text-sm font-medium text-purple-400 mb-3 tracking-wider uppercase">How It Works</p>
                    <h2 className="text-3xl md:text-5xl font-bold text-white mb-4">Three Steps to<br /><span className="text-gradient">Your Best Deal</span></h2>
                </motion.div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto relative">
                    <div className="hidden md:block absolute top-16 left-[20%] right-[20%] h-px bg-linear-to-r from-cyan-400/0 via-cyan-400/30 to-purple-500/0" />

                    {steps.map((step, i) => (
                        <motion.div
                            key={step.num}
                            initial={{ opacity: 0, y: 30 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: i * 0.15 }}
                            className="flex flex-col items-center text-center gap-5 relative z-10"
                        >
                            <motion.div
                                whileHover={{ scale: 1.1, rotate: 5 }}
                                className="w-28 h-28 rounded-3xl glass flex items-center justify-center relative overflow-hidden"
                            >
                                <div className="absolute inset-0 bg-linear-to-br from-cyan-400/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                                <span className="text-3xl font-bold font-mono text-gradient relative z-10">{step.num}</span>
                            </motion.div>
                            <h3 className="text-xl font-semibold text-slate-200">{step.title}</h3>
                            <p className="text-slate-400 max-w-xs">{step.desc}</p>
                        </motion.div>
                    ))}
                </div>
            </section>

            <section className="py-24">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="text-center mb-16"
                >
                    <p className="text-sm font-medium text-emerald-400 mb-3 tracking-wider uppercase">Guides & Tips</p>
                    <h2 className="text-3xl md:text-5xl font-bold text-white mb-4">How to Use <span className="text-gradient">RigRadar</span></h2>
                    <p className="text-slate-400 max-w-2xl mx-auto text-lg">Everything you need to know to get the most out of your price trackers.</p>
                </motion.div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {tips.map((tip, i) => (
                        <motion.div
                            key={tip.title}
                            initial={{ opacity: 0, y: 30 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: i * 0.12 }}
                            whileHover={{ y: -4 }}
                            className="glass rounded-2xl p-7 flex flex-col gap-4 card-shine"
                        >
                            <div className={`w-12 h-12 rounded-2xl ${tip.iconBg} flex items-center justify-center border`}>
                                <tip.icon className={`w-6 h-6 ${tip.iconColor}`} />
                            </div>
                            <h3 className="text-lg font-semibold text-slate-200">{tip.title}</h3>
                            <p className="text-slate-400 leading-relaxed text-sm">{tip.text}</p>
                        </motion.div>
                    ))}
                </div>
            </section>

            <motion.section
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="py-16"
            >
                <div className="relative glass rounded-3xl p-12 md:p-16 text-center overflow-hidden">
                    <div className="absolute inset-0 bg-linear-to-br from-cyan-400/5 to-purple-500/5" />
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 bg-cyan-400/10 rounded-full blur-[100px] -z-10" />
                    <div className="relative z-10">
                        <h2 className="text-3xl md:text-5xl font-bold text-white mb-4">Ready to Save on Your Next Build?</h2>
                        <p className="text-slate-400 max-w-xl mx-auto text-lg mb-8">Track Amazon India & Flipkart tech prices in real-time. Start for free — no credit card required.</p>
                        <Link href="/dashboard">
                            <motion.div
                                whileHover={{ scale: 1.03, y: -2 }}
                                whileTap={{ scale: 0.97 }}
                                className="inline-flex items-center gap-2 px-10 py-4 rounded-2xl bg-linear-to-r from-cyan-400 to-cyan-500 text-slate-950 font-semibold shadow-lg shadow-cyan-400/20"
                            >
                                Get Started — It&apos;s Free
                                <ArrowRight className="w-4 h-4" />
                            </motion.div>
                        </Link>
                    </div>
                </div>
            </motion.section>
        </div>
    );
}
