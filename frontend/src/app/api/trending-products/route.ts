import { NextRequest, NextResponse } from "next/server";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

export async function GET(request: NextRequest) {
    try {
        const force = request.nextUrl.searchParams.get("force") === "true";
        const backendUrl = `${API_URL}/api/trending-products${force ? "?force=true" : ""}`;

        const res = await fetch(backendUrl, {
            headers: { "Content-Type": "application/json" },
            cache: "no-store",
            signal: AbortSignal.timeout(55000),
        });

        if (!res.ok) {
            throw new Error(`Backend returned ${res.status}`);
        }

        const json = await res.json();

        if (json.success && json.data && json.data.length > 0) {
            return NextResponse.json(json, {
                headers: {
                    "Cache-Control": "public, s-maxage=300, stale-while-revalidate=600",
                },
            });
        }

        const fallbackRes = await fetch(`${API_URL}/api/trending`, {
            headers: { "Content-Type": "application/json" },
            cache: "no-store",
            signal: AbortSignal.timeout(10000),
        });

        if (fallbackRes.ok) {
            const fallbackJson = await fallbackRes.json();
            if (fallbackJson.data && fallbackJson.data.length > 0) {
                const converted = fallbackJson.data.map((deal: Record<string, unknown>) => ({
                    id: deal.item_id || "",
                    name: deal.product_name || "Unknown",
                    image: deal.product_image_url || "",
                    url: deal.product_url || "",
                    store: typeof deal.store === "string" ? deal.store.charAt(0).toUpperCase() + deal.store.slice(1) : "Amazon",
                    price: deal.current_price || 0,
                    originalPrice: deal.previous_price || 0,
                    discount: deal.drop_percentage || 0,
                    rating: 0,
                    reviews: 0,
                    category: "Deal",
                }));
                return NextResponse.json(
                    { data: converted, message: "Trending from cache", success: true },
                    {
                        headers: {
                            "Cache-Control": "public, s-maxage=120, stale-while-revalidate=300",
                        },
                    }
                );
            }
        }

        return NextResponse.json(json);
    } catch {
        try {
            const fallbackRes = await fetch(`${API_URL}/api/trending`, {
                headers: { "Content-Type": "application/json" },
                cache: "no-store",
                signal: AbortSignal.timeout(10000),
            });

            if (fallbackRes.ok) {
                const fallbackJson = await fallbackRes.json();
                if (fallbackJson.data && fallbackJson.data.length > 0) {
                    const converted = fallbackJson.data.map((deal: Record<string, unknown>) => ({
                        id: deal.item_id || "",
                        name: deal.product_name || "Unknown",
                        image: deal.product_image_url || "",
                        url: deal.product_url || "",
                        store: typeof deal.store === "string" ? deal.store.charAt(0).toUpperCase() + deal.store.slice(1) : "Amazon",
                        price: deal.current_price || 0,
                        originalPrice: deal.previous_price || 0,
                        discount: deal.drop_percentage || 0,
                        rating: 0,
                        reviews: 0,
                        category: "Deal",
                    }));
                    return NextResponse.json(
                        { data: converted, message: "Trending from cache", success: true }
                    );
                }
            }
        } catch {}

        return NextResponse.json(
            { data: [], message: "Failed to fetch trending products", success: false },
            { status: 500 }
        );
    }
}
