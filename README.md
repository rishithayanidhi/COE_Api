# 🌱 Incubation Management System  

A **FastAPI-based REST API** to manage blogs, events, domains, and event registrations for an incubation program.  
It also provides **admin features** like blog approval/rejection for content moderation.  

---

## 📌 Features  

- ✅ Manage **Domains** (AI, ML, Blockchain, etc.)  
- 📝 Create & moderate **Blogs**  
- 🎯 Host and manage **Events**  
- 👥 Register users for events  
- 🛡️ Admin API for **approving/rejecting blogs**  
- ⚡ Built with **FastAPI** for high performance  

---

## 🚀 Tech Stack  

- **Backend:** FastAPI (Python)  
- **Database:** PostgreSQL (can adapt to others)  
- **ORM/Queries:** psycopg2 (direct queries)  
- **API Testing:** Postman  

---

## ⚡ Getting Started  

### 1️⃣ Clone the repo  
```bash
git clone https://github.com/your-username/incubation-management-system.git
cd incubation-management-system
```

### 2️⃣ Create and activate virtual environment  
```bash
python -m venv venv
source venv/bin/activate   # For Linux/Mac
venv\Scripts\activate      # For Windows
```

### 3️⃣ Install dependencies  
```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Database  
Update `app/db/connection.py` with your PostgreSQL credentials:  
```python
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="your_db",
    user="your_username",
    password="your_password"
)
```

### 5️⃣ Run the server  
```bash
uvicorn app.main:app --reload
```

Server runs on 👉 `http://localhost:8000`  

---

## 📖 API Documentation  

Detailed API docs are available here:  

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)  
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)  
- **Custom Docs:** [📑 API Documentation](./API_DOCUMENTATION.md)  

---

## 🧪 Testing  

- Use **Postman** for testing  
- Import the provided Postman collection  
- Set environment variable:  
  ```baseUrl = http://localhost:8000```

---

## 🤝 Contributing  

1. Fork the project  
2. Create your feature branch (`git checkout -b feature/my-feature`)  
3. Commit changes (`git commit -m "Add new feature"`)  
4. Push to branch (`git push origin feature/my-feature`)  
5. Open a Pull Request  

---

## 📜 License  

This project is licensed under the **MIT License**.  

---

✨ Built with love using **FastAPI**  
