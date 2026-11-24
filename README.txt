MITHUN RESTAURANT POS — REACT + DJANGO + MYSQL

Your uploaded project was reviewed. The React UI and existing MySQL tables are retained. PHP API endpoints have been replaced by Django REST-style JSON endpoints. The old orders, order_items, products, categories and settings tables are accessed directly (unmanaged Django models / SQL), so do NOT import the SQL again if your current database already exists.

TECH STACK
- React + Vite frontend
- Python Django backend + Django session authentication
- MySQL database: mithun_restaurant
- Cash / manual UPI / manual card confirmation workflow
- GST calculation and 80mm browser receipt printing

WINDOWS 10 SETUP
1. Install Python 3.11+ and Node.js LTS.
2. Keep your existing XAMPP MySQL service running. Apache is not needed for Django.
3. Extract this project, for example C:\\MithunRestaurantPOS.
4. Open Command Prompt:
   cd C:\\MithunRestaurantPOS\\backend
   py -m venv venv
   venv\\Scripts\\activate
   pip install -r requirements.txt
5. Configure MySQL if required before running the server. Defaults are DB_NAME=mithun_restaurant, DB_USER=root, DB_PASSWORD blank, DB_HOST=127.0.0.1. If your MySQL password differs, set DB_PASSWORD in the command prompt:
   set DB_PASSWORD=YOUR_MYSQL_PASSWORD
6. Run Django database migrations (creates Django's auth/session tables; does not recreate your restaurant tables):
   py manage.py migrate
7. Create a secure administrator account:
   py manage.py createsuperuser
   Use a strong unique password (10+ characters). Only active staff/admin accounts can log into the POS.
8. Build React:
   cd ..\\frontend
   npm install
   npm run build
   The Vite build output is written to backend\\static_build. Copy its generated index.html to backend\\templates\\index.html (the included build_frontend.bat performs this copy).
   Easier: run build_frontend.bat from project root.
9. Start Django:
   cd ..\\backend
   py manage.py runserver 127.0.0.1:8000
10. Open http://127.0.0.1:8000/

QUICK BUILD (after dependencies installed)
Run build_frontend.bat from the project root. Then run the Django server from backend.

SECURITY
- Django handles password hashing, login sessions, CSRF checks, authentication-required API endpoints, HttpOnly session cookies and password validators.
- Create accounts with createsuperuser or Django admin; POS login requires is_staff=True. Do not use old PHP setup_admin.php or expose it.
- Change DJANGO_SECRET_KEY before deployment. For local-only testing the bundled development fallback is present; do not use that fallback in production.
- DEBUG must be 0, DJANGO_SECRET_KEY must be a long random secret, ALLOWED_HOSTS must be configured, HTTPS must be enabled for public deployment. Do not expose XAMPP/phpMyAdmin or Django runserver to the public internet.
- Keep backups of mithun_restaurant. Never share admin passwords, MySQL passwords, or payment credentials.

PAYMENTS
The current project supports Cash and manual UPI/Card confirmation only. It does NOT connect to a UPI payment gateway or card terminal. The operator must verify payment in the UPI app/bank or card terminal before clicking Payment received. Automatic verification requires a payment provider integration and server-side signature/webhook verification.

GST / RECEIPT
Existing configurable single GST rate is retained. Confirm the applicable GST rate and invoice requirements (including CGST/SGST/IGST) with your accountant. Set the thermal printer driver to 80mm, margins minimum, scale 100%, headers/footers off. Browser print dialog is used; test the printer before live service.

DATABASE COMPATIBILITY
Expected tables and columns are the same as in your uploaded project database/restaurant.sql. If your database schema differs, share the MySQL error or a schema export (without credentials) for adjustment. Existing PHP admin password hashes are not imported into Django users; create a Django superuser once. Restaurant transaction data remains in the existing MySQL tables.
