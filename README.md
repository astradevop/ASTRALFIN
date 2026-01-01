# ASTRALFIN

ASTRALFIN is a comprehensive neo-banking platform built with Django, designed to simulate core banking operations including account management, funds transfer, loans, and investment portfolio tracking.

## Features

- **Digital Banking**: Create accounts with generated customer IDs and account numbers (IFSC: NEOBANKX).
- **Funds Transfer**: Secure money transfer via mobile number or account details (NEFT/IMPS simulation).
- **Transaction History**: Detailed tabular statements with debit/credit tracking and PDF export.
- **Loan Management**: End-to-end loan application workflow with automated EMI scheduling, manual payments, and pre-closure options.
- **Investments**: Portfolio management for tracking assets like Mutual Funds, Stocks, and Fixed Deposits.
- **Security**: 
    - Custom User model with phone verification.
    - Transaction atomicity to ensure data integrity.
    - Role-based access control.

## Tech Stack

- **Backend**: Python 3.12, Django 5.2
- **Database**: PostgreSQL
- **Frontend**: HTML5, Tailwind CSS
- **Authentication**: Custom Auth & Auth0 integration
- **Reporting**: ReportLab for PDF generation

## Local Setup

1. **Clone the repository**
   ```bash
   git clone <repository_url>
   cd ASTRALFIN
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Unix
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your_secret_key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   
   # Database
   DB_NAME=your_db_name
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=5432
   
   # Auth0 (Optional for local dev if disabled)
   AUTH0_DOMAIN=...
   AUTH0_CLIENT_ID=...
   AUTH0_CLIENT_SECRET=...
   ```

5. **Run Migrations & Server**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py runserver
   ```

   Access the application at `http://localhost:8000`.

## License

MIT License.
