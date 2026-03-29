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

**RigRadar** was designed with one main purpose: **to relentlessly automate hardware price tracking across major Indian online retailers**. By simply pasting a product URL into the dashboard, RigRadar begins an ongoing watch over that item. If the price ever drops below your custom threshold, the system immediately shoots you an alert so you can snag the deal before stock runs out. It also extracts and plots historical analytics so you can instantly tell if your "sale price" is a true deal or just a deceptive retail markdown.

---

## ✨ Key Features
- **🌐 Dual-Platform Compatibility:** Flawlessly parses, tracks, and standardizes links directly from Amazon India (`amazon.in`) and Flipkart (`flipkart.com`).
- **📊 Interactive Analytics:** Automatically extracts and plots up to a 6-month historical price curve for items, displaying real-time highest, lowest, and average trends on an interactive graph.
- **⚡ Real-Time Price Polling:** Sets up rigorous background workers synchronized via AWS Serverless Architecture to watch your targeted price thresholds continuously without manual intervention.
- **🔔 Instant Notifications:** Triggers lightning-fast email alerts the exact moment a background check detects a price drop below your target limit.
- **🔐 Secure Authentication:** Seamless, robust login flow powered by Clerk Auth, securely partitioning trackers between user accounts.
- **🔥 Trending Deals Hub:** Aggregates and displays curated live-drop deals currently happening in the market for users seeking spontaneous hardware upgrades.
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
- **TLS Bypass Scraping - `Curl-Cffi` & `BeautifulSoup4`**: Emulates browser TLS fingerprints to seamlessly bypass Amazon and Flipkart's aggressive anti-bot mechanisms, fetching true product metadata and pricing without getting IP blocked or hitting CAPTCHAs.

### Infrastructure & Workers
- **Background Cron Jobs - `AWS SAM & Lambda`**: The `worker/` directory contains handlers (like `scraper.py` and `notifier.py`) deployed as serverless functions. They wake up on a cron schedule, sweep the DynamoDB table for active trackers, check live prices concurrently, and kill their instance—meaning zero idle server costs.
- **Alert Dispatch - `SMTP Email Notifications`**: Handled by the worker instance to immediately shoot an email payload into the user's inbox on a successful trigger match.

---

## 📂 Project Folder Structure
```text
RigRadar/
├── .github/                   # GitHub specific workflows and configurations
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
│   │   ├── components/        # Reusable UI components (Modals, Charts, Trackers)
│   │   ├── lib/               # Utility functions, custom hooks, and API fetch wrappers
│   │   └── types/             # Strict Typescript interface models
│   ├── next.config.ts         # Next.js framework configuration
│   ├── package.json           # Node Dependencies & script mappings
│   └── tailwind.config.ts     # Global styling variables and configurations
├── worker/                    # ⚙️ AWS Lambda Background Jobs
│   ├── handler.py             # Serverless event entrypoint/trigger logic
│   ├── notifier.py            # Alert dispatcher pipeline for triggering emails
│   ├── scraper.py             # Concurrent massive price polling logic
│   ├── throttle.py            # Custom rate limiting logic
│   └── requirements.txt       # Worker-specific dependencies
├── infrastructure/            # ☁️ AWS CloudFormation Infrastructure
│   ├── template.yaml          # AWS SAM IaC describing DynamoDB & Lambda provisioning
│   └── deploy.sh              # Automated deployment shell scripts
├── .gitignore                 # Tracked ignorance map for Git
└── README.md                  # Detailed Project Documentation (You are here!)
```

---

## 🔄 The Complete Architectural Workflow
How does RigRadar perform its magic under the hood?

1. **User Action:** You open the web application, log in using Clerk, paste an Amazon.in or Flipkart.com link into the **Add Tracker Modal**, and define your desired target price (e.g., ₹25,000).
2. **Metadata Extraction:** The Next.js frontend shoots a secure REST payload to the FastAPI backend. The API utilizes `curl-cffi` to imitate a real browser, fetching the latest Store ID, Image, Header Title, and live `current_price` while bypassing scraping deterrents.
3. **Database Injection:** The newly parsed and sanitized tracking configuration, tied directly to your Clerk User ID, is written instantly to an active partition inside the AWS DynamoDB table.
4. **Historical Graph Generation:** Immediately upon creating or viewing a tracked product, the backend accesses cached/historical web indexers associated with that product up to 6 months back. The data is parsed down to the exact lowest/highest bounds and fed straight to your frontend charting component for on-demand rendering.
5. **Continuous Deep Background Polling:** Every few minutes, a detached AWS Lambda worker module automatically wakes up. It fetches all active links across the entire active DynamoDB table and runs high-concurrency checks against their current retail prices.
6. **Threshold Trigger Match:** If the background check hits upon a live price (say, ₹24,800) that is verified to be *lower* than your target of ₹25,000, it flags the item row for dispatch.
7. **Immediate Dispatch:** The active worker triggers the `notifier.py` handler which shoots an un-throttled, instant email alert right into your inbox informing you of the active deal, along with a direct affiliate link to checkout instantly.

<br />


