# 🏥 MedDetect - Clinical Data Management System

## 📌 Overview

MedDetect is a lightweight healthcare management system designed to manage patient records and clinical visit data efficiently. It provides a structured way to store, retrieve, and analyze medical information such as symptoms, diagnosis, and medications.

The project focuses on backend data handling, demonstrating how real-world healthcare data can be managed using Python and SQLite.

---

## ⚙️ Tech Stack

* Python
* SQLite (Database)
* JSON (for flexible data storage)
* Flask (for application layer, if applicable)

---

## 🧠 Key Features

* Patient registration with unique identification
* Visit history tracking for each patient
* Structured storage of symptoms, diagnosis, and medications
* JSON-based handling for flexible medical data
* Automatic database initialization and schema handling
* Data retrieval and transformation for application use

---

## 🏗️ Project Structure

```
MedDetect/
│
├── app.py        # Main application entry point
├── db.py         # Database management (core data layer)
├── logic.py      # Business logic / processing
├── clinical.db   # SQLite database (auto-generated)
└── ...
```

---

## 🔄 System Flow

1. Initialize database using `init_db()`
2. Register or fetch patient using phone number
3. Store visit details including symptoms and diagnosis
4. Convert structured data into JSON for storage
5. Retrieve and convert data back into usable format

---

## 🗄️ Database Design

### Patients Table

* patient_id (Primary Key)
* name
* phone (Unique)

### Visits Table

* patient_id (Foreign Key)
* visit_number
* visit_date
* doctor_name
* symptoms (JSON)
* diagnosis
* medication (JSON)
* notes

---

## ▶️ How to Run

### Step 1: Clone Repository

```bash
git clone <your-repo-link>
cd MedDetect
```

### Step 2: Install Dependencies

```bash
pip install flask numpy pandas scikit-learn
```

### Step 3: Run Application

```bash
python app.py
```

### Step 4: Access

Open browser:

```
http://127.0.0.1:5000/
```

---

## ⚠️ Limitations

* Uses JSON instead of normalized relational tables
* No authentication or role-based access
* No indexing for large-scale performance
* Uses delete-and-insert instead of update operations

---

## 🚀 Future Improvements

* Migrate to PostgreSQL for scalability
* Normalize database schema
* Add authentication and security layers
* Implement REST APIs
* Use ORM like SQLAlchemy

---

## 💡 Key Learning Outcomes

* Database design using SQLite
* Data serialization using JSON
* Backend data flow management
* Handling real-world structured and semi-structured data
* Understanding trade-offs in system design

---

## 📌 Conclusion

MedDetect demonstrates how a simple yet functional healthcare data system can be built with efficient backend logic, making it a strong foundation for scaling into a full-fledged clinical application.
