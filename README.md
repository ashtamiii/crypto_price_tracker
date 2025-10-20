# Cryptocurrency Price Tracker

A **Selenium-powered Python tool** that dynamically scrapes real-time cryptocurrency data from [CoinMarketCap](https://coinmarketcap.com/).  
Developed as part of my **Project Internship at Cybernaut Edutech LLP**.

---

## Project Overview
This tool automates a browser using Selenium WebDriver to extract the **top 10 cryptocurrencies** and their key metrics:
- Name  
- Current Price  
- 24-hour Change  
- Market Cap  

The collected data is **saved to CSV** for analysis, dashboard integration, or trend tracking.

---

## Features
Real-time price scraping  
Handles JavaScript-rendered pages dynamically  
Exports data to CSV  
Headless browser option for background execution  
Historical logging with timestamps  
Filtering by price or percentage change (optional)  

---

## Tech Stack
- **Language:** Python  
- **Libraries:** Selenium, pandas, webdriver_manager, time  
- **Browser:** Google Chrome + ChromeDriver  
- **Storage:** CSV files  

---

## How to Run
1. Clone the repository:
   ```bash
   git clone https://github.com/ashtamiii/Cryptocurrency-Price-Tracker.git
   cd Cryptocurrency_Price_Tracker
