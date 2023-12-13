import fastapi
import sqlite3
import hashlib
import uuid  # Módulo para generar UUIDs
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import HTTPException, Depends
from datetime import datetime, timedelta
from fastapi import HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

conn = sqlite3.connect("contactos.db")

app = fastapi.FastAPI()
# Token
security = HTTPBearer()
security_basic = HTTPBasic()

class Contacto(BaseModel):
    email : str
    nombre : str
    telefono : str

class Contacto(BaseModel):
    email: str
    nombre: str
    telefono: str

origins = [
    "http://localhost:8080",
    "http://localhost:8000",
"https://mysql-front-b9df0f2dcfae.herokuapp.com"
"https://autentification-front-739523386c7c.herokuapp.com/"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)   


@app.post("/register/")
def register(credentials: HTTPBasicCredentials = Depends(security_basic)):
    if not credentials.username or not credentials.password:
        raise HTTPException(status_code=401, detail="Acceso denegado: Credenciales faltantes")

    username = credentials.username
    password = credentials.password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    with sqlite3.connect("contactos.db") as conn:
        c = conn.cursor()
        c.execute('SELECT username FROM usuarios WHERE username=?', (username,))
        existing_user = c.fetchone()

        if existing_user:
            return {"error": "El usuario ya existe"}

        c.execute(
            'INSERT INTO usuarios (username, password) VALUES (?, ?)',
            (username, hashed_password)
        )
        conn.commit()

    return {"status": "Usuario registrado con éxito"}


@app.post("/")
def root(credentials: HTTPBearer = Depends(security)):
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Acceso denegado: Token faltante")

    token = credentials.credentials

    current_timestamp = datetime.utcnow().timestamp()

    with sqlite3.connect("contactos.db") as conn:
        c = conn.cursor()
        c.execute('SELECT username, expiration_timestamp FROM usuarios WHERE token=?', (token,))
        user_data = c.fetchone()

        if user_data and current_timestamp < user_data[1]:  # Verificar si el token está dentro del tiempo de expiración
            return {"mensaje": "Acceso permitido"}
        else:
            raise HTTPException(status_code=401, detail="Acceso denegado: Token inválido o expirado")

@app.get("/token")
def generate_token(credentials: HTTPBasicCredentials = Depends(security_basic)):
    if not credentials.username or not credentials.password:
        raise HTTPException(status_code=401, detail="Acceso denegado: Credenciales faltantes")

    username = credentials.username
    password = credentials.password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    with sqlite3.connect("contactos.db") as conn:
        c = conn.cursor()
        c.execute('SELECT username, password FROM usuarios WHERE username=?', (username,))
        user = c.fetchone()

        if user and user[1] == hashed_password:
            timestamp = conn.execute('SELECT strftime("%s", "now")').fetchone()[0]
            token = hashlib.sha256((username + str(uuid.uuid4())).encode()).hexdigest()
            expiration_time = timedelta(minutes=20)  # Cambiar la duración a 1 minuto
            expiration_timestamp = (datetime.utcnow() + expiration_time).timestamp()
            c.execute(
                'UPDATE usuarios SET token=?, timestamp=?, expiration_timestamp=? WHERE username=?',
                (token, timestamp, expiration_timestamp, username)
            )
            conn.commit()
            return {"token": token, "timestamp": timestamp, "expiration_timestamp": expiration_timestamp}
        else:
            raise HTTPException(status_code=401, detail="Acceso denegado: Credenciales inválidas")


@app.post("/contactos")
async def crear_contacto(contacto: Contacto, credentials: HTTPBearer = Depends(security)):
    """Inserta un contactos """
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Acceso denegado: Token faltante")
    token = credentials.credentials

    current_timestamp = datetime.utcnow().timestamp()
    with sqlite3.connect("contactos.db") as conn:
        c = conn.cursor()
        c.execute('SELECT username, expiration_timestamp FROM usuarios WHERE token=?', (token,))
        user_data = c.fetchone()

        if user_data and current_timestamp < user_data[1]:  # Verificar si el token está dentro del tiempo de expiración
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM contactos WHERE email = ?', (contacto.email,))
            count = c.fetchone()[0]
            if count > 0:
                raise HTTPException(status_code=400, detail="El contacto ya existe")
            c.execute('INSERT INTO contactos (email, nombre, telefono) VALUES (?, ?, ?)',
                        (contacto.email, contacto.nombre, contacto.telefono))
            conn.commit()
            return contacto
        else:
            raise HTTPException(status_code=401, detail="Acceso denegado: Token inválido o expirado")

    


@app.get("/contactos")
async def obtener_contactos(credentials: HTTPBearer = Depends(security)):
    """Obtiene todos los contactos."""  
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Acceso denegado: Token faltante")

    token = credentials.credentials

    current_timestamp = datetime.utcnow().timestamp()

    with sqlite3.connect("contactos.db") as conn:
        c = conn.cursor()
        c.execute('SELECT username, expiration_timestamp FROM usuarios WHERE token=?', (token,))
        user_data = c.fetchone()

        if user_data and current_timestamp < user_data[1]:  # Verificar si el token está dentro del tiempo de expiración
            c = conn.cursor()
            c.execute('SELECT * FROM contactos;')
            response = []
            for row in c:
                contacto = {"email":row[0],"nombre":row[1], "telefono":row[2]}
                response.append(contacto)
            return response
        else:
            raise HTTPException(status_code=401, detail="Acceso denegado: Token inválido o expirado")
   


@app.get("/contactos/{email}")
async def obtener_contacto(email: str, credentials: HTTPBearer = Depends(security)):
    """Obtiene un contacto por su email."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Acceso denegado: Token faltante")

    token = credentials.credentials

    current_timestamp = datetime.utcnow().timestamp()

    with sqlite3.connect("contactos.db") as conn:
        c = conn.cursor()
        c.execute('SELECT username, expiration_timestamp FROM usuarios WHERE token=?', (token,))
        user_data = c.fetchone()

        if user_data and current_timestamp < user_data[1]:  # Verificar si el token está dentro del tiempo de expiración
            c = conn.cursor()
            c.execute('SELECT * FROM contactos WHERE email = ?', (email,))
            contacto = None
            for row in c:
                contacto = {"email":row[0],"nombre":row[1],"telefono":row[2]}
            return contacto
        else:
            raise HTTPException(status_code=401, detail="Acceso denegado: Token inválido o expirado")

    

@app.put("/contactos/{email}")
async def actualizar_contacto(email: str, contacto: Contacto, credentials: HTTPBearer = Depends(security)):
    """Actualiza un contacto."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Acceso denegado: Token faltante")

    token = credentials.credentials

    current_timestamp = datetime.utcnow().timestamp()

    with sqlite3.connect("contactos.db") as conn:
        c = conn.cursor()
        c.execute('SELECT username, expiration_timestamp FROM usuarios WHERE token=?', (token,))
        user_data = c.fetchone()

        if user_data and current_timestamp < user_data[1]:  # Verificar si el token está dentro del tiempo de expiración
                c = conn.cursor()
                c.execute('UPDATE contactos SET nombre = ?, telefono = ? WHERE email = ?',
                        (contacto.nombre, contacto.telefono, email))
                conn.commit()
                return contacto
        else:
            raise HTTPException(status_code=401, detail="Acceso denegado: Token inválido o expirado")



@app.delete("/contactos/{email}")
async def eliminar_contacto(email: str, credentials: HTTPBearer = Depends(security)):
    """Elimina un contacto."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Acceso denegado: Token faltante")

    token = credentials.credentials

    current_timestamp = datetime.utcnow().timestamp()

    with sqlite3.connect("contactos.db") as conn:
        c = conn.cursor()
        c.execute('SELECT username, expiration_timestamp FROM usuarios WHERE token=?', (token,))
        user_data = c.fetchone()

        if user_data and current_timestamp < user_data[1]:  # Verificar si el token está dentro del tiempo de expiración
                c = conn.cursor()
                c.execute('DELETE FROM contactos WHERE email = ?', (email,))
                conn.commit()
                return {"mensaje":"Contacto eliminado"}
        else:
            raise HTTPException(status_code=401, detail="Acceso denegado: Token inválido o expirado")

