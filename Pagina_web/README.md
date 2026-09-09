# Web demo — MLOps Adult Income

Aplicación local para reemplazar Postman durante la demo del proyecto final. El navegador llama a `POST /predict`; Flask calcula `capital_net_ratio`, construye el payload `dataframe_records` y consulta el endpoint `mlops-course-income` de Databricks.

## Arquitectura

`index.html → Flask /predict → Databricks Model Serving → respuesta → index.html`

El token de Databricks solo existe en `.env` del backend y nunca se envía al navegador.

## 1. Requisitos

- Python 3.10+ recomendado.
- Acceso al workspace de Databricks.
- Endpoint `mlops-course-income` en estado READY.
- Token de acceso con permisos para invocar Model Serving.

## 2. Crear entorno virtual

### Windows PowerShell

```powershell
cd ruta\a\esan-mlops-web
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Windows CMD

```bat
cd ruta\a\esan-mlops-web
py -m venv .venv
.\.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS/Linux

```bash
cd /ruta/a/esan-mlops-web
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Configurar Databricks

Copia `.env.example` a `.env` y completa:

```text
DATABRICKS_HOST=https://TU-WORKSPACE.cloud.databricks.com
DATABRICKS_TOKEN=TU_TOKEN
DATABRICKS_ENDPOINT=mlops-course-income
PORT=5000
```

No uses comillas si no son necesarias.

## 4. Ejecutar

```bash
python app.py
```

Abre:

`http://127.0.0.1:5000`

## 5. Probar

Primero pulsa `Cargar ejemplo` en el caso que quieras mostrar y luego `Predecir prospecto`.

Caso 1:

- age=45
- education_num=13
- hours_per_week=55
- capital_gain=15000
- capital_loss=0
- fnlwgt=190000
- capital_net_ratio = 15000 / 56 ≈ 267.86

Caso 2:

- age=22
- education_num=9
- hours_per_week=20
- capital_gain=0
- capital_loss=0
- fnlwgt=210000
- capital_net_ratio = 0

## 6. Verificación rápida

Con el servidor levantado, abre:

`http://127.0.0.1:5000/health`

Debe aparecer `status=ok` y `databricks_configured=true`.

Luego prueba la página principal. Si Databricks responde correctamente, el caso 1 debería devolver clase 1 y el caso 2 clase 0, tal como está validado en el notebook del proyecto.

## 7. Qué NO debes subir a GitHub

Nunca subas `.env`. El repositorio solo debe contener `.env.example`. El `.gitignore` ya bloquea `.env`.

## 8. Contrato enviado a Databricks

El backend construye exactamente:

```json
{
  "dataframe_records": [
    {
      "age": 45,
      "education_num": 13,
      "hours_per_week": 55,
      "capital_gain": 15000,
      "capital_loss": 0,
      "fnlwgt": 190000,
      "capital_net_ratio": 267.8571428571
    }
  ]
}
```

POST:

`https://<host>/serving-endpoints/mlops-course-income/invocations`

Headers:

```text
Authorization: Bearer <token>
Content-Type: application/json
```
