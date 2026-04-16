# AI Golf Coach

The AI Golf Coach is a full-stack web application designed to provide amateur golfers with detailed biomechanical analysis of their swing using advanced computer vision and deep learning techniques.

---

## Local Development Setup

This project utilizes Docker to manage its backend services (PostgreSQL and Redis) to ensure a consistent and reliable development environment.

### Prerequisites

-   [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
-   Python 3.11+ and `pip`.
-   Node.js 18+ and `npm`.

### Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/michaelw221/AIGolfCoach.git
    cd AIGolfCoach
    ```

2.  **Configure Environment Variables**
    Navigate to the `backend` directory, copy the example environment file, and update it with your database password.

    ```bash
    cd backend
    cp .env.example .env
    ```
    Open the newly created `.env` file and ensure the `DATABASE_URL` password matches the `POSTGRES_PASSWORD` you set in the `docker-compose.yml` file.

3.  **Launch Backend Services**
    From the **root directory** of the project, run the following command to start the PostgreSQL and Redis containers in the background:

    ```bash
    docker compose up -d
    ```
    This will download the necessary images and start the services. You can verify they are running in Docker Desktop.

4.  **Setup the Backend (Python)**
    Navigate into the `backend` folder, create a virtual environment, and install the required Python packages.

    ```bash
    # From the /backend directory
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use: .\.venv\Scripts\activate
    pip install -r requirements.txt
    ```

5.  **Setup the Frontend (React)**
    In a separate terminal, navigate into the `frontend` folder and install the Node.js packages.

    ```bash
    cd frontend
    npm install
    ```

### Running the Application

To run the full application, you need to start three separate processes in three different terminals:

1.  **Start the FastAPI Backend API** (Terminal 1, in `/backend`)
    ```bash
    uvicorn main:app --reload
    ```

2.  **Start the Celery Worker** (Terminal 2, in `/backend`)
    ```bash
    celery -A worker.celery_config worker --loglevel=info --pool=solo
    ```

3.  **Start the React Frontend** (Terminal 3, in `/frontend`)
    ```bash
    npm start
    ```

You can now access the web application at **http://localhost:3000**.