<div align="center">

  <h1>🚀 RigRadar</h1>
  <p><strong>The Ultimate Real-Time Hardware Price Tracker for the Indian Market</strong></p>
  <p>
    <a href="https://nextjs.org/"><img src="https://img.shields.io/badge/Next.js-black?style=for-the-badge&logo=next.js&logoColor=white" alt="Next JS"></a>
    <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"></a>
    <a href="https://aws.amazon.com/dynamodb/"><img src="https://img.shields.io/badge/DynamoDB-4053D6?style=for-the-badge&logo=amazon-dynamodb&logoColor=white" alt="DynamoDB"></a>
    <a href="https://clerk.com/"><img src="https://img.shields.io/badge/Clerk-6C47FF?style=for-the-badge&logo=clerk&logoColor=white" alt="Clerk"></a>
  </p>
</div>

<hr />

## 🎯 Why RigRadar? (The Main Purpose)
Building a custom PC or hunting for the lowest prices on electronics is a frustrating experience. Prices on e-commerce sites like Amazon and Flipkart fluctuate daily, and manually checking them leads to missed deals and wasted money. 

**RigRadar** was built to solve this. Its main purpose is to automate hardware price tracking across major Indian online retailers. By simply bringing a product URL to the dashboard, RigRadar instantly visualizes the product's 6-month historical pricing analytics and watches the live price for you. If the price ever drops below your custom threshold, the system immediately shoots you an alert so you can snag the deal.

## ✨ Key Features
- **🌐 Dual-Platform Tracking:** Flawlessly parses and tracks links directly from Amazon India (`amazon.in`) and Flipkart (`flipkart.com`).
- **📊 Interactive Analytics:** Automatically extracts and plots up to a 6-month historical price curve for items so you instantly know if the current price is a good deal.
- **⚡ Real-Time Price Drops:** Sets up rigorous background workers to watch your targeted price thresholds continuously.
- **🔔 Instant Notifications:** Hooks into email (or Discord via webhooks) to notify you within milliseconds of a detected price drop.
- **🔐 Secure Authentication:** Seamless, robust login flow powered by Clerk.
- **🔥 Trending Deals Hub:** Aggregates and displays curated live-drop deals happening currently in the market.

## 🛠️ Tech Stack & Tools Used
RigRadar uses a highly scalable, decoupled architecture split between a Next.js frontend and a Python FastAPI backend.
- **Frontend `(React / Next.js 15)`**: Drives the entire user interface interface with smooth transitions, server-side rendering, and dynamic routing.
- **Styling & UI `(TailwindCSS + Framer Motion)`**: Provides the slick, glassmorphic dark-mode aesthetic alongside ultra-fluid micro-animations.
- **Authentication `(Clerk)`**: Secures user accounts effortlessly, managing sessions and OAuth flows natively.
- **Backend API `(FastAPI / Python)`**: Acts as the rapid engine powering the scraper coordination, data sanitization, and DB interactions.
- **Scraping Engine `(Curl-Cffi + BeautifulSoup4)`**: Bypasses anti-bot mechanisms to fetch true product metadata and pricing without getting blocked.
- **Database `(AWS DynamoDB)`**: A NoSQL cloud database chosen for its lightning-fast read/write capacities during heavy simultaneous price polling.

## 📂 Folder Structure
```text
RigRadar/
├── backend/                   # 🐍 FastAPI Backend Engine
│   ├── routers/               # API endpoints (trackers, analytics, trending)
│   ├── services/              # Core Scraping & DynamoDB handlers
│   ├── main.py                # FastAPI ASGI Application Entrypoint
│   └── requirements.txt       # Python Dependencies
├── frontend/                  # ⚛️ Next.js Application
│   ├── src/
│   │   ├── app/               # Landing, Dashboard, Analytics, Auth Routes
│   │   ├── components/        # Reusable UI (Modals, Charts, Trackers)
│   │   ├── lib/               # Custom hooks and API fetch wrappers
│   │   └── types/             # Typescript data models
│   ├── next.config.ts         # Next.js configurations
│   ├── package.json           # Node Dependencies
│   └── tailwind.config.ts     # Tailwind & Custom UI definitions
├── worker/                    # ⚙️ Background Jobs
│   ├── scraper.py             # Scheduled massive price scraper tasks
│   └── notifier.py            # Alert dispatcher for users
└── README.md                  # Project Documentation
```

## 🔄 The Architectural Workflow
How does RigRadar perform under the hood?

1. **User Action:** You paste an Amazon or Flipkart link into the Add Tracker Modal and set your target price (e.g., ₹25,000 for a GPU).
2. **Metadata Extraction:** The Next.js frontend calls the FastAPI backend. The API extracts the Store ID, Image, Title, and fetches the `current_price` using optimized TLS fingerprint bypassing via `curl_cffi`.
3. **Database Injection:** The newly parsed data and your user ID are encrypted and stored in an AWS DynamoDB Table.
4. **Historical Generation:** The backend concurrently scrapes historical indexers associated with that product up to 6 months back, feeding the exact lowest/highest bounds straight to your frontend charting component.
5. **Background Polling:** A detached worker module actively sweeps DynamoDB, running background checks against the active retail links.
6. **Trigger Match:** If a background check returns a live price (e.g., ₹24,800) that is lower than your ₹25,000 target, it flags the row.
7. **Notification Dispatch:** The system triggers an instant asynchronous alert dispatching straight to your provided email address.

<br />

<div align="center">
  <p>Built with ❤️ for gamers, builders, and absolute deal hunters.</p>
</div>
