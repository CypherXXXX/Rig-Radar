<div align="center">

# 📡 RigRadar
**The Ultimate Real-Time Hardware Price Tracker for the Indian Market**

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-black?style=for-the-badge&logo=next.js&logoColor=white" alt="Next JS">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/DynamoDB-4053D6?style=for-the-badge&logo=amazon-dynamodb&logoColor=white" alt="DynamoDB">
  <img src="https://img.shields.io/badge/AWS_Lambda-FF9900?style=for-the-badge&logo=aws-lambda&logoColor=white" alt="AWS Lambda">
  <img src="https://img.shields.io/badge/Clerk-6C47FF?style=for-the-badge&logo=clerk&logoColor=white" alt="Clerk">
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS">
</p>

</div>

---

## 🎯 Why is this project needed?
Building a custom PC or hunting for the lowest prices on electronics is a frustrating experience. Prices on e-commerce sites like Amazon India and Flipkart fluctuate daily, sometimes hourly. Manually checking them leads to missed deals, prolonged waiting times, and ultimately wasted money.

**RigRadar** was designed with one main purpose: **to relentlessly automate hardware price tracking across major Indian online retailers**. By simply pasting a product URL into the dashboard, RigRadar begins an ongoing watch over that item. If the price ever drops below your custom threshold, the system immediately sends a Discord webhook notification or an email alert so you can snag the deal before stock runs out. It also extracts and plots historical analytics so you can instantly tell if your "sale price" is a true deal or just a deceptive retail markdown.

---

## ✨ Key Features
- **🌐 Dual-Platform Compatibility:** Flawlessly parses, tracks, and standardizes links directly from Amazon India (`amazon.in`) and Flipkart (`flipkart.com`).
- **📊 Interactive Analytics:** Automatically extracts and plots up to a 6-month historical price curve for items, displaying real-time highest, lowest, and average trends on an interactive graph.
- **⚡ Real-Time Price Polling:** Sets up rigorous background workers synchronized via AWS Serverless Architecture to watch your targeted price thresholds every 30 minutes without manual intervention.
- **🔔 Instant Notifications:** Triggers Discord webhook alerts and email notifications the exact moment a background check detects a price drop below your target limit.
- **🔐 Secure Authentication:** Seamless, robust login flow powered by Clerk Auth, securely partitioning trackers between user accounts.
- **🔥 Trending Deals Hub:** Aggregates and displays curated live-scrape results from Amazon India across 12 hardware categories (GPU, CPU, RAM, SSD, Monitor, Keyboard, Mouse, Motherboard, Cooling, PSU, Headset, Laptop).
- **💸 Localized Currency Formatting:** Built exclusively for the Indian retail space, tracking limits and rendering everything native using INR (₹).

---

## 🛠️ Tech Stack & Main Tools Used
RigRadar uses a highly scalable, decoupled architecture split between a React-based SSR frontend and an asynchronous Python backend/worker engine.

### Frontend
- **Framework - `Next.js 16 (App Router)`**: Drives the user interface architecture. It handles routing, server-side data fetching where necessary, and builds a fluid SPA (Single Page Application) experience on the client side.
- **UI & Styling - `TailwindCSS v4`**: Utility-first CSS framework providing a sleek, pixel-perfect glassmorphic dark-mode aesthetic.
- **Animations - `Framer Motion`**: Used to supply ultra-fluid micro-animations, staggering list loads, and satisfying modal transitions which dramatically increase the premium feel of the app.
- **Data Visualization - `Recharts`**: Renders responsive SVG charts for the product analytics dashboard, making historical pricing data extremely interactive with hover-based tooltips.
- **Authentication - `Clerk`**: Secures user accounts effortlessly, handling session token states, user management, and seamless OAuth flows without home-brewing security.

### Backend API
- **Web Framework - `FastAPI (Python)`**: Acts as the rapid, type-safe engine powering the core network requests. FastAPI ensures that routing, API parsing via Pydantic, and request parallelization are highly optimized.
- **Database - `AWS DynamoDB`**: A Serverless NoSQL cloud database integrated via `boto3`. Hand-picked for its lightning-fast read/write capacities during heavy simultaneous price polling and scaling dynamically without maintaining instances.
- **HTTP Scraping - `curl_cffi` & `BeautifulSoup4`**: `curl_cffi` is used for imitating real browser TLS fingerprints to bypass Amazon and Flipkart bot detections. `BeautifulSoup4` with the `lxml` parser extracts structured product metadata (name, price, image) from the raw HTML response.

### Infrastructure & Workers
- **Background Cron Jobs - `AWS SAM & Lambda`**: The `worker/` directory contains handlers (like `scraper.py` and `notifier.py`) deployed as serverless functions. They wake up on a **30-minute cron schedule**, sweep the DynamoDB table for active trackers, check live prices concurrently, and terminate after completion — meaning zero idle server costs.
- **Alert Dispatch - `Discord Webhooks`**: When a background check detects a price drop below the tracker's target, the worker dispatches a rich Discord embed message to the user-supplied webhook URL with product details, price comparison, and a direct buy link.

---

## 📂 Project Folder Structure
```text
RigRadar/
├── backend/                   # 🐍 FastAPI Backend Engine
│   ├── routers/               # Specific API sub-routers (tracking endpoints)
│   ├── services/              # Core Scraping & DynamoDB abstraction layers
│   ├── main.py                # FastAPI ASGI Application Entrypoint
│   ├── models.py              # Pydantic data validation schemas
│   └── requirements.txt       # Python Dependencies for backend operations
├── frontend/                  # ⚛️ Next.js Application Environment
│   ├── public/                # Static assets and fonts
│   ├── src/
│   │   ├── app/               # Next.js App Router (Landing, Auth, Dashboard, Analytics routes)
│   │   ├── components/        # Reusable UI components (AddTrackerModal, TrackerCard, Navbar, Toast)
│   │   ├── lib/               # Utility functions, custom hooks, and API fetch wrappers
│   │   └── types/             # Strict TypeScript interface models
│   ├── next.config.ts         # Next.js framework configuration
│   └── package.json           # Node Dependencies & script mappings
├── worker/                    # ⚙️ AWS Lambda Background Jobs
│   ├── handler.py             # Serverless event entrypoint/trigger logic
│   ├── notifier.py            # Alert dispatcher pipeline (Discord webhooks + email scaffold)
│   ├── scraper.py             # Concurrent price polling logic
│   ├── throttle.py            # Custom rate limiting and domain-grouped request batching
│   └── requirements.txt       # Worker-specific dependencies
├── infrastructure/            # ☁️ AWS CloudFormation Infrastructure
│   ├── template.yaml          # AWS SAM IaC describing DynamoDB tables & Lambda functions
│   └── deploy.sh              # Automated deployment shell script
├── .gitignore                 # Tracked ignorance map for Git
└── README.md                  # Detailed Project Documentation (You are here!)
```

---

## 🔄 The Complete Architectural Workflow
How does RigRadar perform its magic under the hood?

1. **User Action:** You open the web application, log in using Clerk, paste an Amazon.in or Flipkart.com link into the **Add Tracker Modal**, choose Discord or Email as your notification method, and define your desired target price (e.g., ₹25,000).
2. **Metadata Extraction:** The Next.js frontend shoots a secure REST payload to the FastAPI backend. The API uses `curl_cffi` to fetch the product page via browser TLS spoofing and `BeautifulSoup4` to parse the product title, image, and current live price.
3. **Database Injection:** The newly parsed and sanitized tracking configuration, tied directly to your Clerk User ID, is written instantly to an active partition inside the AWS DynamoDB table.
4. **Historical Graph Generation:** Immediately upon creating or viewing a tracked product, the backend accesses the `pricehistory.app` external indexer to retrieve up to 6 months of historical pricing data. If external data is unavailable, a statistically plausible synthetic price curve is generated from the current price.
5. **Continuous Background Polling:** Every **30 minutes**, a detached AWS Lambda worker automatically wakes up. It fetches all active trackers across the DynamoDB table and runs high-concurrency price checks using domain-grouped batching with exponential backoff and jitter.
6. **Threshold Trigger Match:** If the background check detects a live price (say, ₹24,800) that is lower than your target of ₹25,000, it flags the item for notification dispatch.
7. **Immediate Dispatch:** The worker triggers `notifier.py`, which sends a rich Discord embed to the user's configured webhook URL — including price comparison, drop percentage, product image, and a direct buy link.

<br />


