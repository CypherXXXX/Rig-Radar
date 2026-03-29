export interface TrackedItem {
    item_id: string;
    user_id: string;
    product_url: string;
    product_name: string;
    product_image_url: string;
    store: string;
    current_price: number;
    target_price: number;
    notification_type: "discord" | "email";
    contact_info: string;
    created_at: string;
    updated_at: string;
}

export interface PriceHistoryEntry {
    item_id: string;
    timestamp: string;
    price: number;
}

export interface AnalyticsStats {
    current: number;
    lowest: number | null;
    highest: number | null;
    average: number | null;
    data_points: number;
}

export interface AnalyticsData {
    item: TrackedItem;
    history: PriceHistoryEntry[];
    stats: AnalyticsStats;
    external_history: boolean;
    period: string | null;
}

export interface TrendingDeal {
    item_id: string;
    product_name: string;
    product_image_url: string;
    product_url: string;
    store: string;
    previous_price: number;
    current_price: number;
    drop_percentage: number;
}

export interface TrendingProduct {
    id: string;
    name: string;
    image: string;
    url: string;
    store: string;
    price: number;
    originalPrice: number;
    discount: number;
    rating: number;
    reviews: number;
    category: string;
}

export interface TrackRequest {
    product_url: string;
    target_price: number;
    notification_type: "discord" | "email";
    contact_info: string;
    user_id: string;
}

export interface ApiResponse<T = unknown> {
    data: T;
    message: string;
    success: boolean;
}
