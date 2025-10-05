# CathPed - Patient Management System 🩺

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?style=for-the-badge&logo=flask)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?style=for-the-badge&logo=postgresql)
![Google Cloud](https://img.shields.io/badge/Google_Cloud-API-4285F4?style=for-the-badge&logo=google-cloud)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6-yellow?style=for-the-badge&logo=javascript)

**CathPed** is a full-stack web application, developed as a complete, individual solution to optimize the patient management workflow in the medical field. The system automates data entry via **Google Forms/Sheets** and organizes the entire patient lifecycle in an intuitive and secure web interface.

***

## 🎯 The Problem It Solves

In medical routines, referring patients between specialists often results in decentralized data, manual spreadsheets, and difficulty in tracking the status of each case. This manual process is prone to errors, consumes valuable time, and complicates the overall workflow overview.

**CathPed** was created to solve this exact problem by offering a centralized platform that automates data collection and structures care into clear stages, from initial assessment to post-procedure follow-up.

***

## ✨ Key Features

-   ✅ **Automatic Sync with Google Sheets**: New patients filled out in a Google Form are automatically imported into the application, serving as the single source of truth for new entries.
-   ✅ **Structured Workflow**: The system guides the user through 4 essential care stages: **Assessment**, **Authorization**, **Procedure Execution**, and **Post-Procedure Follow-Up**. The interface dynamically adapts, showing only the next required action for each patient.
-   ✅ **Full CRUD Operations**:
    -   **Create**: New patients are created via the Google Sheets API.
    -   **Read**: View and search for patients in an organized list.
    -   **Update**: The patient's status is updated by filling out the forms for each stage.
    -   **Delete**: Deleting a patient is synchronized, removing the record from both the **PostgreSQL** database and the original **Google Sheets** spreadsheet, ensuring data consistency.
-   ✅ **Secure Authentication**: Restricted access to the application through a login and session system.
-   ✅ **Patient Summary and PDF Generation**: A consolidated view of all patient information, which can be exported as a PDF file directly from the browser using `jsPDF` and `html2canvas`.
-   ✅ **Search and Filtering**: Search functionality to quickly locate patients by name.
-   ✅ **Responsive Interface**: The design adapts to different screen sizes, allowing for use on desktops and mobile devices.

***

## 🏛️ Architecture and Data Flow

This project was conceived as an end-to-end solution, where I was responsible for all stages, from architectural design to back-end and front-end implementation.

The data flow works as follows:

1.  **Data Entry**: Partner physicians fill out a **Google Form** with a new patient's data.
2.  **Initial Storage**: The response is automatically saved to a **Google Sheets** spreadsheet.
3.  **Application Sync**: When accessing the patient list, the **Flask** application uses the **Google Sheets API** to fetch new entries.
4.  **Data Persistence**: The application checks for new patients and saves them to the **PostgreSQL** database (hosted on Neon), avoiding duplicates.
5.  **User Interaction**: The physician uses the web interface to manage each stage of the process. Each form filled out in the application saves the data to relational tables in the database.
6.  **Deletion Sync**: If a patient is deleted in the application, an API call is made to remove the corresponding row in Google Sheets, maintaining integrity across platforms.

***

## 🛠️ Tech Stack

The choice of technologies was focused on robustness, scalability, and productivity.

-   **Back-end**:
    -   **Python**: Main language for the application.
    -   **Flask**: Web micro-framework to build routes, business logic, and the internal API.
    -   **SQLAlchemy**: ORM for object-relational mapping and interacting with the database securely and efficiently.
    -   **Google API Client Library for Python**: For robust integration with the Google Sheets API.

-   **Front-end**:
    -   **HTML5**: Semantic structure of the pages.
    -   **CSS3**: Custom styling and responsiveness (with Flexbox and Media Queries).
    -   **JavaScript (Vanilla)**: For client-side interactivity, such as the asynchronous login system and PDF generation.

-   **Database**:
    -   **PostgreSQL (Neon)**: Serverless relational database to securely and persistently store patient data and their respective stages.

-   **APIs and Libraries**:
    -   `Google Sheets API v4`
    -   `jsPDF` & `html2canvas` for the export functionality.

***

## 🗃️ Database Structure

The database was modeled relationally to ensure data integrity and organization.

-   **`FormResponse`**: The central table that stores the initial patient data imported from Google Sheets.
-   **Stage Tables**: `CaseEvaluation`, `Authorization`, `ProcedureExecution`, `FollowUp`.
    -   Each of these tables has a **one-to-one** relationship with the `FormResponse` table.
    -   The `cascade="all, delete-orphan"` configuration ensures that when a patient is deleted, all their associated stage records are automatically removed, maintaining database consistency.

***

## 🚀 How to Run Locally

Follow the steps below to set up and run the project in your local environment.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/cathped.git](https://github.com/your-username/cathped.git)
    cd cathped
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure the environment variables:**
    Create a `.env` file in the project root and add the following variables:

    ```env
    # Key for the Flask session (can be any random string)
    secret_key='YOUR_SECRET_KEY_HERE'

    # Connection URI for your PostgreSQL database
    SQLALCHEMY_DATABASE_URI='postgresql://user:password@host:port/database'

    # Application login credentials
    APP_USERNAME='your_login_username'
    APP_PASSWORD='your_login_password'

    # Google API Settings
    SPREADSHEET_ID='YOUR_GOOGLE_SPREADSHEET_ID'
    # The full content of your service account credentials JSON file, as a single-line string.
    CREDENTIALS_FILE='{"type": "service_account", "project_id": "...", ...}'
    ```
    > **Note**: To get the `CREDENTIALS_FILE`, you need to create a project on the Google Cloud Platform, enable the Google Sheets API, and create a service account. Download the credentials JSON file and share your spreadsheet with the service account's email.

5.  **Run the application:**
    ```bash
    flask run
    ```
    Access `http://127.0.0.1:5000` in your browser.
