import math
import os
from typing import Any

import requests
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "").strip().rstrip("/")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "").strip()
DATABRICKS_ENDPOINT = os.getenv("DATABRICKS_ENDPOINT", "mlops-course-income").strip()

REQUIRED_FIELDS = [
    "age",
    "education_num",
    "hours_per_week",
    "capital_gain",
    "capital_loss",
    "fnlwgt",
]


def validate_config() -> None:
    if not DATABRICKS_HOST or not DATABRICKS_TOKEN:
        raise RuntimeError(
            "Faltan DATABRICKS_HOST y/o DATABRICKS_TOKEN en el archivo .env."
        )


def as_finite_number(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"'{field}' debe ser numérico.")

    if not math.isfinite(number):
        raise ValueError(f"'{field}' debe ser un número finito.")
    return number


def normalize_record(data: dict[str, Any]) -> dict[str, float]:
    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        raise ValueError("Faltan campos: " + ", ".join(missing))

    record = {
        field: as_finite_number(data[field], field)
        for field in REQUIRED_FIELDS
    }

    # Mantener enteros donde conceptualmente corresponden.
    record["age"] = int(record["age"])
    record["education_num"] = int(record["education_num"])
    record["hours_per_week"] = int(record["hours_per_week"])

    # Feature derivada EXACTAMENTE como en el proyecto.
    record["capital_net_ratio"] = (
        record["capital_gain"] - record["capital_loss"]
    ) / (record["hours_per_week"] + 1)

    return record


def interpret_prediction(prediction: Any) -> tuple[int, str]:
    # El notebook muestra predictions[0]/predictions[1]. Normalizamos tanto
    # int como float/bool por tolerancia a pequeñas variaciones de respuesta.
    value = int(float(prediction))
    if value == 1:
        return 1, "califica"
    return 0, "no califica"


def extract_first_prediction(payload: Any) -> Any:
    if isinstance(payload, dict) and "predictions" in payload:
        predictions = payload["predictions"]
    else:
        predictions = payload

    if isinstance(predictions, list) and predictions:
        return predictions[0]

    raise RuntimeError(
        "Databricks respondió en un formato inesperado: no se encontró 'predictions'."
    )


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    configured = bool(DATABRICKS_HOST and DATABRICKS_TOKEN)
    return jsonify(
        {
            "status": "ok",
            "databricks_configured": configured,
            "endpoint": DATABRICKS_ENDPOINT,
        }
    )


@app.post("/predict")
def predict():
    try:
        validate_config()
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "El body debe ser JSON."}), 400

        record = normalize_record(data)
        payload = {"dataframe_records": [record]}

        url = (
            f"{DATABRICKS_HOST}/serving-endpoints/"
            f"{DATABRICKS_ENDPOINT}/invocations"
        )
        headers = {
            "Authorization": f"Bearer {DATABRICKS_TOKEN}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=45,
        )

        if not response.ok:
            # No devolvemos el token ni headers sensibles.
            return (
                jsonify(
                    {
                        "error": "Databricks rechazó la solicitud.",
                        "status_code": response.status_code,
                        "details": response.text[:1000],
                    }
                ),
                502,
            )

        try:
            response_json = response.json()
        except ValueError:
            return (
                jsonify(
                    {
                        "error": "Databricks devolvió una respuesta no-JSON.",
                        "details": response.text[:1000],
                    }
                ),
                502,
            )

        raw_prediction = extract_first_prediction(response_json)
        prediction, interpretation = interpret_prediction(raw_prediction)

        return jsonify(
            {
                "prediction": prediction,
                "interpretation": interpretation,
                "features": record,
                "serving_endpoint": DATABRICKS_ENDPOINT,
            }
        )

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except requests.RequestException as exc:
        return (
            jsonify(
                {
                    "error": "No fue posible conectar con Databricks.",
                    "details": str(exc),
                }
            ),
            502,
        )
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:  # pragma: no cover
        return (
            jsonify({"error": "Error interno del servidor.", "details": str(exc)}),
            500,
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
