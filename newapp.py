import streamlit as st
from google import genai
import os
import base64

# -------------------------------------------------------------
# CONFIGURACIÓN API KEY
# -------------------------------------------------------------
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    st.error("Falta configurar la variable de entorno API_KEY.")
    st.stop()

client = genai.Client(api_key=API_KEY)

# -------------------------------------------------------------
# PROMPT BASE (versión simplificada del servicio original)
# -------------------------------------------------------------
def build_prompt(question, personal_year):
    return f"""
Eres una consultora esotérica experta llamada 'Elara, la Observadora de Estrellas'.
Usa numerología y lectura de manos para ofrecer una guía sabia, empática y empoderadora.

Pregunta del usuario: "{question}"
Año personal: {personal_year}

Analiza también las imágenes de las manos del usuario siguiendo estos principios:
- Forma de la mano y dedos
- Líneas principales (vida, cabeza, corazón, destino)
- Líneas débiles, fuertes, rotas
- Símbolos presentes
- Montes de la palma

Entrega la lectura en formato **Markdown** y usa tablas cuando hables de ciclos o periodos.
No hagas predicciones absolutas, solo guía.
"""

# -------------------------------------------------------------
# STREAMLIT UI
# -------------------------------------------------------------
st.title("🔮 Domina Tu Destino — Lectura Épica con Gemini")
st.write("Servicio de lectura de manos + numerología generado con Gemini en Streamlit.")

# FORM
question = st.text_area("❓ Escribe tu pregunta")
personal_year = st.number_input("🔢 Año personal", min_value=1, max_value=9, step=1)
uploaded_images = st.file_uploader("🖐️ Sube imágenes de tus manos", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

generate_btn = st.button("✨ Generar lectura")

# -------------------------------------------------------------
# PROCESAMIENTO
# -------------------------------------------------------------
if generate_btn:

    if not question:
        st.error("Debes escribir una pregunta.")
        st.stop()

    with st.spinner("Consultando a Elara, la Observadora de Estrellas..."):

        # Construir prompt
        prompt = build_prompt(question, personal_year)

        # Construir partes de imagen
        image_parts = []
        for img in uploaded_images:
            base64_data = base64.b64encode(img.read()).decode("utf-8")
            mime_type = img.type

            image_parts.append({
                "inline_data": {
                    "data": base64_data,
                    "mime_type": mime_type
                }
            })

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    {"text": prompt},
                    *image_parts
                ]
            )

            st.success("Lectura generada con éxito ✨")
            st.markdown(response.text)

        except Exception as e:
            st.error(f"Error al generar la lectura: {e}")