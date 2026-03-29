import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
    try {
        const force = request.nextUrl.searchParams.get("force") === "true";
        const backendUrl = `${API_URL}/api/trending-products${force ? "?force=true" : ""}`;

        const res = await fetch(backendUrl, {
            headers: { "Content-Type": "application/json" },
            cache: "no-store",
        });

        if (!res.ok) {
            throw new Error(`Backend returned ${res.status}`);
        }

        const json = await res.json();

        return NextResponse.json(json, {
            headers: {
                "Cache-Control": "public, s-maxage=300, stale-while-revalidate=600",
            },
        });
    } catch {
        return NextResponse.json(
            { data: [], message: "Failed to fetch trending products", success: false },
            { status: 500 }
        );
    }
}
