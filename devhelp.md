# virtual environment 
  activate cmd 
    name venv 
    .\venv\Scripts\Activate.ps1


# BACKEND RUNNING CMD
 uvicorn app.main:app --host 127.0.0.1 --port 8000

# DATABASE 
 activate psql
 psql -U postgres
\c nutidelight 

