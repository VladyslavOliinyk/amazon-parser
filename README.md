# amazon-parser
A Python web scraping application that fetches Amazon's Best Sellers, serves the data via a FastAPI REST API, and displays it on a dynamic web interface.


### Amazon Best Sellers Parser & API

This project is a comprehensive web scraping application. It automatically scrapes product data from Amazon's Best Sellers pages, serves this data through a RESTful API built with FastAPI, and presents it on an interactive web front-end.

#### Key Features:

* **Automated Daily Scraping:** A background scheduler (APScheduler) runs once every 24 hours to automatically update the list of product categories and their top 5 best-selling items.
* **Dynamic API:** The FastAPI backend provides several endpoints to:
    * Serve the complete snapshot of all scraped data.
    * Provide status updates on the parser (last run time).
    * Allow manual triggering of the scraping process.
* **Interactive Frontend:** A vanilla HTML, CSS, and JavaScript interface allows users to:
    * Select a product category from a dynamically populated dropdown list.
    * Instantly view the top 5 products for the selected category.
    * Manually trigger a full data refresh via a confirmation dialog.
* **Robust Scraping:** The scraping module, built with `Selenium` and `BeautifulSoup`, incorporates techniques to mimic human behavior (e.g., User-Agent rotation, random delays) to minimize the risk of being blocked.
* **Containerized for Deployment:** The application is configured with a `Dockerfile` to ensure it can be easily built and deployed on cloud services like Render.com.
