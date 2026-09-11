
# PriceFlow

**Live Demo:** [http://priceflowsystem.duckdns.org](http://priceflowsystem.duckdns.org)

## About The Project
PriceFlow is a scalable, microservice-based SaaS platform designed for automated, real-time price monitoring and analytics. It empowers users to track product prices across various e-commerce platforms, offering detailed price history charts and notifications. 

The core data extraction engine is built to handle heavy WAF protections, utilizing anti-detect browsers to bypass modern anti-bot systems like Cloudflare and gather accurate pricing data seamlessly.

## Key Features
* **Automated Price Tracking:** Add product URLs and let the system track price fluctuations over time.
* **Advanced Web Scraping:** Bypasses complex anti-bot protections and JS-challenges using a custom stealth engine.
* **Interactive Analytics:** Visualizes historical price data using responsive charts.
* **Microservice Architecture:** Fully containerized environment ensuring high reliability and isolation.
* **Secure Authentication:** Robust user profile management with cryptographically hashed passwords.

## Tech Stack
* **Backend:** Python (FastAPI), SQLAlchemy, Pydantic
* **Data Extraction:** Playwright, Camoufox (Anti-detect engine)
* **Frontend:** React, Recharts, Tailwind CSS
* **Database & Cache:** PostgreSQL, Redis
* **Infrastructure & DevOps:** Docker, Docker Compose, AWS EC2

## Architecture Overview
The application runs on an AWS EC2 instance, orchestrated via Docker Compose. It features a decoupled architecture where the FastAPI backend securely communicates with a PostgreSQL database within an isolated Docker bridge network. The frontend is a React-based SPA that consumes the RESTful API to deliver a seamless user experience.
