from flask import Flask, request, jsonify
from google import genai
import os

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("Falta configurar la variable de entorno API_KEY")

client = genai.Client(api_key=API_KEY)

personal_year_meanings = {
    "es": {
        1: "Nuevos comienzos, independencia y siembra de semillas para el futuro.",
        2: "Paciencia, cooperación, relaciones y diplomacia.",
        3: "Creatividad, autoexpresión, comunicación y actividades sociales.",
        4: "Trabajo duro, disciplina, construcción de cimientos y organización.",
        5: "Cambio, libertad, aventura y oportunidades inesperadas.",
        6: "Responsabilidad, hogar, familia y asuntos del corazón.",
        7: "Introspección, crecimiento espiritual, análisis y búsqueda de conocimiento.",
        8: "Abundancia, poder, carrera y asuntos financieros.",
        9: "Finalización, finales, dejar ir y humanitarismo.",
    }
}

def build_prompt_es(data, personal_year):
    meanings = personal_year_meanings["es"][personal_year]
    question = data["question"]

    return f"""
Eres una consultora esotérica experta llamada 'Elara, la Observadora de Estrellas'...

Pregunta del usuario: "{question}"
Año personal: {personal_year} ({meanings})
"""


@app.route("/generate-reading", methods=["POST"])
def generate_reading():
    try:
        data = request.get_json()
        lang = data.get("language", "es")
        personal_year = data["personalYear"]
        images = data.get("handImages", [])

        if lang == "es":
            prompt_text = build_prompt_es(data, personal_year)
        else:
            return jsonify({"success": False, "error": "Solo versión español incluida."})

        image_parts = []
        for img in images:
            image_parts.append({
                "inline_data": {
                    "data": img["base64"],
                    "mime_type": img["mimeType"]
                }
            })

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                {"text": prompt_text},
                *image_parts
            ]
        )

        return jsonify({"success": True, "analysis": response.text})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
