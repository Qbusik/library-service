# 📚 Library Service API 📚

Library Service API is a Django application for managing library resources, books, borrowings, payments, and notifications. It provides a REST API with JWT authentication, asynchronous task processing with Celery, and Telegram bot integration.

---
## 📃 Features
- **Admin Panel** – located at /admin/
- Custom user management
- Books and borrowings management
- Automatic daily checking of overdue borrowings
- Stripe integration for payment processing
- Telegram notifications about overdue borrowings and successful payments
- Asynchronous tasks with Celery + Redis
- API documentation available via Swagger

---
## 🛠️ Prerequisites

**To run this project, you will need:**

- Docker – for an easy and consistent setup across environments
- A Telegram bot (created via @BotFather) and a chat to receive notifications
> Add your bot token and chat ID to the `.env` file
- A Stripe test account for payment processing
> Add your Stripe secret key to the `.env` file

---
## 🚀 Run with DOCKER

This is the fastest method to get the project running in an isolated environment.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Qbusik/library-service.git
    ```

2.  **Configure Environment Variables:**

    ```bash
    cp .env.sample .env
    # then fill in your credentials
    ```

3.  **Build and Run Containers:**
    ```bash
    docker-compose up --build
    ```
    The application will be available at: `http://localhost:8000/`

---
## ⚠️ Production Notes
- For Stripe payments, webhooks should be used instead of polling.  
  The scheduled task checking Stripe sessions is implemented only to meet project requirements.