# AIGolfCoach
**Step 1: Clone the Repository**
Open your terminal or command prompt and navigate to the directory where you want to store the project. Then, run the following command:
```bash
git clone <your-github-repository-url.git>
cd AIGOLFCOACH
```

**Step 2: Set Up the Python Backend**
This will create an isolated virtual environment for all the Python packages.

1.  Navigate into the `backend` directory:
    ```bash
    cd backend
    ```
    2.  Create a Python virtual environment:
    ```bash
    # On Windows
    python -m venv .venv

    # On macOS / Linux
    python3 -m venv .venv
    ```
3.  Activate the virtual environment:
    ```bash
    # On Windows
    .venv\Scripts\activate

    # On macOS / Linux
    source .venv/bin/activate
    ```
    *(Your terminal prompt should now start with `(.venv)`)*

4.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

**Step 3: Set Up the React Frontend**
This will install all the necessary Node.js packages.

1.  Navigate from the project root into the `frontend/app` directory. **Open a new, separate terminal for this step.**
    ```bash
    cd frontend/app
    ```
2.  Install the required Node packages:
    ```bash
    npm install
    ```
    *(This may take a few minutes as it downloads all the React dependencies.)*

---

#### **3. Running the Application (For Daily Development)**

To run the application, you will need **two separate terminals** running concurrently.

**Terminal 1: Start the Backend Server**

1.  Navigate to the `backend` directory.
2.  Activate the virtual environment if it's not already active:
    ```bash
    .venv\Scripts\activate
    ```
3.  Start the Uvicorn server:
    ```bash
    uvicorn main:app --reload
    ```
4.  You should see a confirmation that the server is running on **http://127.0.0.1:8000**. Leave this terminal running.

**Terminal 2: Start the Frontend Server**

1.  Navigate to the `frontend/app` directory.
2.  Start the React development server:
    ```bash
    npm start
    ```
3.  A new browser tab should automatically open to **http://localhost:3000**. If it doesn't, you can open it manually. You should see your application's UI.

You are now ready to use the application.

---

#### **4. Accessing the Application**

*   **Frontend UI:** Open your browser and go to **http://localhost:3000**. This is where you will interact with the application.
*   **Backend API Docs (Optional):** You can see the auto-generated API documentation by navigating to **http://localhost:8000/docs**. This is useful for testing the API directly.

---

#### **5. Common Troubleshooting**

*   **Error: `uvicorn: command not found`**
    *   **Cause:** The Python virtual environment is not active in your backend terminal.
    *   **Fix:** Run the activation command (`.venv\Scripts\activate` or `source .venv/bin/activate`).

*   **Error: `npm: command not found` or `npx: command not found`**
    *   **Cause:** Node.js is not installed correctly or was installed without adding it to your system's PATH.
    *   **Fix:** Reinstall the **LTS version of Node.js** from [nodejs.org](https://nodejs.org/) and ensure you restart your terminal and VS Code.

*   **Error in Browser Console: `CORS policy` error, `Failed to fetch`**
    *   **Cause:** The backend server is not running, or the `apiUrl` in your React code is pointing to the wrong address/port.
    *   **Fix:** Ensure the backend terminal is running and shows that Uvicorn is active on `http://127.0.0.1:8000`.

*   **Error: `ModuleNotFoundError` in the backend terminal**
    *   **Cause:** The Python packages were not installed correctly.
    *   **Fix:** Make sure your virtual environment is active and run `pip install -r requirements.txt` again in the `backend` directory.
