import { SignIn } from "@clerk/nextjs";

export default function Page() {
    return (
        <div className="flex items-center justify-center min-h-[calc(100vh-160px)]">
            <SignIn appearance={{ elements: { card: "bg-slate-900/70 border border-slate-800 backdrop-blur-xl", headerTitle: "text-slate-200", headerSubtitle: "text-slate-400" } }} />
        </div>
    );
}
