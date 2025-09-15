# AI Sign Language Interpreter

This project is a real-time American Sign Language (ASL) interpreter that uses a state-of-the-art AI pipeline to translate sign language gestures into text and voice. It leverages MediaPipe for robust hand tracking, a custom neural network for intelligent feature extraction, and a TiDB Cloud database with vector search for scalable and accurate sign recognition.

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

### Key Features

*   **Real-Time Interpretation:** Translates signs from a live webcam feed by finding the most similar gesture in its knowledge base.
*   **AI Pipeline:** Uses MediaPipe to extract hand landmarks, which are then converted into powerful 128-dimensional "embedding" vectors by a custom CNN.
*   **Scalable Vector Database:** Powered by TiDB Cloud, which stores and searches through thousands of sign embeddings in milliseconds using approximate nearest neighbor (ANN) search.
*   **Teachable AI:** An "Admin Mode" allows users to easily teach the system new signs, continuously expanding its vocabulary.
*   **Secure User Authentication:** Features a full registration and login system to manage user sessions.

### System Architecture

The application is built on a modern, decoupled architecture designed for real-time AI inference and data management.

```
┌───────────┐      ┌────────────────┐      ┌──────────────────┐      ┌────────────────┐
│  Webcam   │----->│   MediaPipe    │----->│    Custom NN     │----->│  TiDB Cloud    │
│ (Input)   │      │(Landmark Extr.)│      │(Embedding Model) │      │(Vector Search) │
└───────────┘      └────────────────┘      └──────────────────┘      └───────┬────────┘
                                                                            │
                                                                            ▼
                                                                     ┌───────────┐
                                                                     │ Streamlit │
                                                                     │ (UI)      │
                                                                     └───────────┘
```

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

## Getting Started (Local Setup)

Follow these steps to set up and run the project on your local machine.

### 1. Prerequisites

*   Python 3.9 - 3.11
*   A webcam and microphone
*   A free [TiDB Cloud](https://tidbcloud.com/) account for the database backend

### 2. Clone the Repository

```bash
git clone <your-repository-url>
cd sign-ai-project
```

### 3. Set Up a Virtual Environment

It is strongly recommended to use a virtual environment.

```bash
# Create a virtual environment
python -m venv .venv

# Activate it
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 4. Install Dependencies

Install all required Python libraries from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 5. Configure the TiDB Cloud Database

The application's "memory" is a TiDB Cloud cluster. The free Serverless Tier is perfect for this.

1.  **Create a Cluster:** Log in to [TiDB Cloud](https://tidbcloud.com/) and create a free **Serverless** cluster.
2.  **Get Credentials:**
    *   Click the **"Connect"** button on your cluster's dashboard.
    *   **Generate a password** and copy it securely.
    *   Under "Allow Access", click **"Allow Access from Anywhere"**.
    *   Download the **CA certificate** (`ca.pem`).
3.  **Configure Environment Variables:**
    *   Create a folder named `certs` in your project and move `ca.pem` into it.
    *   Create a file named `.env` in the root of the project.
    *   Copy the following template into your `.env` file and fill it with your credentials:

    ```ini
    # .env file
    TIDB_HOST="your-cluster-host.tidb.cloud"
    TIDB_PORT="4000"
    TIDB_USER="your-user.root"
    TIDB_PASSWORD="your-secret-password-you-copied"
    TIDB_DB_NAME="sign_ai_db"
    TIDB_SSL_CA="certs/ca.pem"
    ```

### 6. Train the AI Model

The application requires a model file named `landmark_model.h5` to function. You must train this model on a dataset of sign language images.

1.  **Download the Dataset:** The [Kaggle ASL Alphabet dataset](https://www.kaggle.com/datasets/grassknoted/asl-alphabet) is highly recommended. Download and unzip it.
2.  **Structure the Data:** Create a `data/` folder in your project, and inside it, a `train/` folder. Move all the letter folders (A, B, C, del, space, etc.) from the unzipped dataset into `data/train/`.
3.  **Run the Training Script:** Execute the training script from your terminal. This will process all the images, train the neural network, and save the `landmark_model.h5` file.
    ```bash
    python train_model.py
    ```

### 💡 Tip: Training on Google Colab
> Training the model can be slow on a laptop. For a massive speed boost, you can use Google Colab's free T4 GPUs. The workflow is simple: ZIP your `data` folder, upload it to a Colab notebook, copy the contents of `train_model.py` into a cell, and run it there. Then, download the resulting `landmark_model.h5` file back to your local project.

---

## Running the Application

Once setup is complete, launch the Streamlit app.

```bash
streamlit run app.py
```

Your web browser will open with the application.

### How to Use the App

1.  **Sign Up / Sign In:** Create a new user account.
2.  **Teach the AI:** Switch to **"Admin: Teach AI New Signs"** mode.
    *   For each sign you trained on (A, B, C, etc.), type its label, perform the sign for the camera, and click "Generate and Save Embedding". This populates your TiDB knowledge base.
3.  **Interpret Signs:** Switch to **"Interpreter (Sign to Voice)"** mode to get real-time predictions.
