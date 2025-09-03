# AI Personal Assistant

AI Personal Assistant is a web application that integrates with Gmail and Google Calendar to help users manage their emails and events efficiently. It uses AI to categorize and summarize emails, identify important events, and provide options to add events to Google Calendar or ignore them.

## Features

- **User Authentication**: Secure user registration and login with token-based authentication.
- **Google Integration**: Connect your Google account to access Gmail and Calendar features.
- **Email Categorization**: AI-powered categorization of emails into events or general emails.
- **Email Summarization**: Summarize email content for quick understanding.
- **Event Management**: Add important events to Google Calendar or ignore them.
- **Dashboard**: View summarized emails and pending events in a user-friendly interface.

---

## Tech Stack

### Frontend
- **React**: Component-based UI development.
- **Tailwind CSS**: Utility-first CSS framework for styling.
- **Fetch API**: For making HTTP requests to the backend.
- **LocalStorage**: For managing user session data.

### Backend
- **FastAPI**: Python-based web framework for building APIs.
- **SQLite**: Lightweight database for storing user and Google credentials.
- **Google APIs**: Integration with Gmail and Google Calendar.
- **JWT**: Secure token-based authentication.
- **Passlib**: Password hashing for secure storage.

### AI Integration
- **Google Generative AI**: Used for categorizing and summarizing emails.

---

## Installation

### Prerequisites
- Node.js and npm installed
- Python 3.9+ installed
- Google Cloud project with Gmail and Calendar APIs enabled
- `.env` file with the following variables:
  - `GOOGLE_CLIENT_ID`
  - `GOOGLE_CLIENT_SECRET`
  - `SECRET_KEY`

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file and add your environment variables:
   ```env
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   SECRET_KEY=your-secret-key
   ```
5. Start the backend server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm start
   ```
4. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Usage

1. **Register**: Create an account using the registration form.
2. **Login**: Log in to access the dashboard.
3. **Connect Google Account**: Link your Google account to enable Gmail and Calendar features.
4. **Fetch Emails**: Fetch and process emails to view categorized and summarized content.
5. **Manage Events**: Add important events to your Google Calendar or ignore them.

---

## API Endpoints

### Authentication
- `POST /register`: Register a new user.
- `POST /login`: Log in and receive an access token.

### Google Integration
- `GET /auth/google`: Get Google OAuth URL.
- `GET /auth/google/callback`: Handle Google OAuth callback.
- `GET /google/status`: Check Google account connection status.
- `DELETE /auth/google/unlink`: Unlink Google account.

### Email and Event Management
- `POST /fetch-emails`: Fetch and process emails.
- `POST /add-to-calendar/{email_id}`: Add an event to Google Calendar.
- `DELETE /ignore-event/{email_id}`: Ignore an event.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
