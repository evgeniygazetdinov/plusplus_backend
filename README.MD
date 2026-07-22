# Chat Application


- **FastAPI**: A modern web framework for building APIs with Python.
- **SQLAlchemy**: A SQL toolkit and Object-Relational Mapping (ORM) system for Python.
- **Pydantic**: Data validation and settings management using Python type annotations.
- **SQLite**: A lightweight database for development and testing. in next release will be changed to Postgres

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/evgeniygazetdinov/chat_volc.git
   cd chat_volc

2.python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt

3. Run the application:
   ```bash
   uvicorn main:app --reload
    or you could use run.sh
    ```
base migration flow to create db
```
alembic init alembic
alembic revision --autogenerate -m "your migration message"
alembic upgrade head```

