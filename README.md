# AI Sign Language Interpreter

This project is a real-time Sign Language interpreter that uses a Convolutional Neural Network (CNN) to translate sign language gestures into text and voice. The system is built with a scalable architecture featuring a Streamlit web interface, a TensorFlow/Keras model for inference, and a TiDB Cloud database for robust data logging, user management, and analytics.

## Features

*   **Real-Time Sign-to-Voice:** Translates ASL letter signs from a live webcam feed into spoken words.
*   **Voice-to-Sign:** Converts spoken sentences into an animated avatar that performs the corresponding ASL signs.
*   **User Authentication:** Secure user registration and login system.
*   **Scalable Backend:** Powered by TiDB Cloud (a distributed SQL database) to log every prediction, manage user sessions, and collect feedback for model improvement.
*   **Interactive UI:** A user-friendly web interface built with Streamlit.
*   **Model Feedback Loop:** Allows users to correct misclassified signs, providing valuable data for future model retraining.

## System Architecture

The application follows a modern, scalable architecture designed for real-time AI services.

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Streamlit UI    │<---->│ Sign AI Backend  │<---->│   TiDB Cloud     │
│ (Webcam, Display)│      │  (Python, TF)    │      │ (Users, Logs)    │
└──────────────────┘      └──────────────────┘      └──────────────────┘
```

---

## 🚀 Getting Started

Follow these steps to set up and run the project on your local machine.

### 1. Prerequisites

*   Python
*   A webcam connected to your computer
*   A microphone for the Voice-to-Sign feature
*   A free [TiDB Cloud](https://tidbcloud.com/) account

### 2. Clone the Repository

Clone this project to your local machine:
```bash
git clone <your-repository-url>
cd <your-repository-folder>
```

### 3. Set Up the Python Environment

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 4. Install Dependencies

Install all the required Python libraries using the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 5. Set Up the TiDB Cloud Database

This application requires a TiDB Cloud cluster to function. The free Serverless Tier is perfect for this project.

1.  **Create a Cluster:**
    *   Log in to your [TiDB Cloud](https://tidbcloud.com/) account.
    *   Create a new **Serverless** cluster. Give it a name (e.g., `sign-ai-cluster`) and choose a region near you.

2.  **Get Credentials:**
    *   Once the cluster is "Available", click the **"Connect"** button.
    *   **Generate a password** and **copy it somewhere safe**.
    *   Under "Allow Access", click **"Allow Access from Anywhere"**. This adds `0.0.0.0/0` to your IP whitelist.
    *   From the "Connect with" -> "General" tab, download the **CA certificate** (`ca.pem`).

3.  **Configure Environment Variables:**
    *   Create a file named `.env` in the root of the project directory.
    *   Move the downloaded `ca.pem` file into a new folder named `certs`.
    *   Copy the contents of `.env.example` into your new `.env` file and fill it out with your cluster's details. It should look like this:

    ```ini
    # .env file
    TIDB_HOST="your-cluster-host.tidb.cloud"
    TIDB_PORT="4000"
    TIDB_USER="your-user.root"
    TIDB_PASSWORD="your-secret-password"
    TIDB_DB_NAME="sign_ai_db"
    TIDB_SSL_CA="certs/ca.pem"
    ```
    The application will automatically create the database and tables on the first run.

   To test the connection to the TiDB Cloud:
   Run this script:
   ```
   python test_tidb_connection.py
   ```

### 6. Prepare the AI Model

The application uses a pre-trained model named `sign_model.h5`.

*   **To use the existing model:** Ensure `sign_model.h5` is present in the root project directory.
*   **To train a new model:**
    1.  Organize your image dataset into `data/train` and `data/test` directories, with subdirectories for each letter (A-Z).
    2.  Run the training script:
        ```bash
        python train_model.py
        ```
    3.  This will generate a new, optimized `sign_model.h5` file in your project directory.

---

## 🏃‍♀️ Running the Application

Once the setup is complete, you can start the Streamlit web server.

1.  Make sure your virtual environment is activated.
2.  Run the following command in your terminal:
    ```bash
    streamlit run app.py
    ```
3.  Your web browser will automatically open with the application running.

## How to Use the App

1.  **Sign Up / Sign In:** Create a new user account or log in with existing credentials.
2.  **Select a Mode:**
    *   **Sign to Voice:** Your webcam will activate. Place your hand inside the green box and perform an ASL letter sign. The app will predict the letter, add it to the sentence, and speak it out loud.
    *   **Voice to Sign:** Click "Start Listening" and speak a word or sentence. An animated avatar will perform the signs for each letter in the sentence.

---

## Project Structure

```
.
├── .venv/                 # Virtual environment folder
├── avatars/               # GIFs for the Voice-to-Sign feature
├── certs/
│   └── ca.pem             # TiDB Cloud SSL certificate
├── data/                  # (Optional) Dataset for training
│   ├── train/
│   └── test/
├── .env                   # Environment variables (DB credentials)
├── .gitignore             # Files to be ignored by Git
├── app.py                 # Main Streamlit application file
├── model.py               # Model loading and image preprocessing
├── requirements.txt       # List of Python dependencies
├── sign_model.h5          # The trained CNN model
├── tidb_connector.py      # Handles all database interactions
├── train_model.py         # Script to train a new model
├── utils.py               # Utility functions (TTS, STT)
└── README.md              # This file
```
