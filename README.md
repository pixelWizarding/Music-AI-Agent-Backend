# SHIFT SCALL Backend

## Overview

SHIFT SCALL Backend is a backend service built with **FastAPI**, integrating **Firestore** as the primary database and **Redis** for caching. The project handles contact management and provides APIs for creating, retrieving, and caching contact information.

### Technologies Used

- **FastAPI**: High-performance Python web framework for building APIs.
- **Firestore**: NoSQL cloud database from Google Firebase.
- **Redis**: In-memory data structure store, used as a cache for fast data access.
- **Google Cloud Memorystore**: Managed Redis instance for scalable caching.

## Features

- Create, retrieve, and manage contact information.
- Cache frequently accessed data in Redis to improve performance.
- Automatically generated API documentation with **Swagger UI** and **ReDoc**.

## Installation

### Prerequisites

- **Python 3.10+**
- **Pip** (Python package manager)
- **Google Cloud Firestore** and **Google Cloud Memorystore** instances (if using GCP services)

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/SHIFT-JP/shift-scall-backend.git
   cd shift-scall-backend
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Set up the environment variables by creating a .env file at the project root:

   ```bash
   FIREBASE_CREDENTIALS=path/to/firebase_credentials.json
   REDIS_HOST=your_redis_host
   REDIS_PORT=6379
   ```

4. RUN:

   ```bash
   npm start
   ```

   OR

   ```bash
   docker compose up --build
   ```

5. Format & Lint:

   ```bash
   npm run format
   ```

   ```bash
   npm run lint
   ```

6. Access the API documentation:

   ```bash
   Swagger UI: http://127.0.0.1:8000/docs
   ReDoc: http://127.0.0.1:8000/redoc
   ```
