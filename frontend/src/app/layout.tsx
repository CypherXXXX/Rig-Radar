import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import { ClerkProvider } from '@clerk/nextjs';
import './globals.css';
import Navbar from '@/components/Navbar';
import { ToastProvider } from '@/components/Toast';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' });

export const metadata: Metadata = {
    title: 'RigRadar | Real-Time Price Intelligence for Tech Hardware',
    description: 'Track GPU, CPU, SSD, and tech component prices across Amazon & Flipkart. Get instant alerts, historical analytics, and trending deals — all in real-time.',
    keywords: 'price tracker, GPU prices, CPU prices, tech deals, Amazon price tracker, Flipkart price tracker, hardware deals',
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <ClerkProvider>
            <html lang="en" className="dark">
                <body className={`${inter.variable} ${jetbrainsMono.variable} antialiased font-sans bg-slate-950 text-slate-400 min-h-screen relative overflow-x-hidden`}>
                    <div className="fixed inset-0 -z-10">
                        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,var(--tw-gradient-stops))] from-slate-900/50 via-slate-950 to-slate-950" />
                        <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-400/5 rounded-full blur-3xl" />
                        <div className="absolute top-1/3 right-1/4 w-72 h-72 bg-purple-500/5 rounded-full blur-3xl" />
                    </div>
                    <ToastProvider>
                        <Navbar />
                        <main className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24 py-8">
                            {children}
                        </main>
                        <footer className="border-t border-slate-800/50 mt-24">
                            <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24 py-10 flex flex-col md:flex-row items-center justify-between gap-4">
                                <p className="text-sm text-slate-600">© 2026 RigRadar. Built for smart shoppers.</p>
                                <div className="flex items-center gap-6">
                                    <a href="https://github.com" target="_blank" rel="noreferrer" className="text-sm text-slate-600 hover:text-slate-400 transition-colors">GitHub</a>
                                    <a href="#" className="text-sm text-slate-600 hover:text-slate-400 transition-colors">Privacy</a>
                                    <a href="#" className="text-sm text-slate-600 hover:text-slate-400 transition-colors">Terms</a>
                                </div>
                            </div>
                        </footer>
                    </ToastProvider>
                </body>
            </html>
        </ClerkProvider>
    );
}
