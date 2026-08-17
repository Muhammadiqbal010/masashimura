# 🚀 Capstone Project - Django + Vue

Fullstack web application using Django (Backend) and Vue.js (Frontend).

---

## 📦 Tech Stack

* **Backend:** Django + Django REST Framework
* **Frontend:** Vue 3 + Vite
* **Database:** SQLite (development)
* **API:** REST API (JSON)

---

## 📁 Project Structure

```
capstone_project/
│
├── backend/      # Django project
├── frontend/     # Vue project
├── .gitignore
└── README.md
```

---

## ⚙️ Backend Setup (Django)

1. Masuk ke folder backend

```
cd backend
```

2. Buat virtual environment

```
python -m venv venv
```

3. Aktifkan virtual environment

* Windows:

```
venv\Scripts\activate
```

* Mac/Linux:

```
source venv/bin/activate
```

4. Install dependencies

```
pip install -r requirements.txt
```

5. Jalankan migration

```
python manage.py migrate
```

6. Jalankan server

```
python manage.py runserver
```

📍 Backend berjalan di:
http://127.0.0.1:8000

---

## 🌐 Frontend Setup (Vue)

1. Masuk ke folder frontend

```
cd frontend
```

2. Install dependencies

```
npm install
```

3. Jalankan development server

```
npm run dev
```

📍 Frontend berjalan di:
http://localhost:5173

---

## 🔗 API Endpoint Example

* Menu API:
  http://127.0.0.1:8000/api/menus/

---

## 👤 Django Admin

Buat superuser:

```
cd backend
python manage.py createsuperuser
```

Login admin:
http://127.0.0.1:8000/admin

---


## 🚀 Run Full Project

Jalankan backend:

```
cd backend
python manage.py runserver
```

Jalankan frontend:

```
cd frontend
npm run dev
```

---

## 📌 Author

Irfan Setiawan
