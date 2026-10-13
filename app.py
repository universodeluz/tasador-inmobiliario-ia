import streamlit as st
import base64
from PIL import Image
import io
import openai  # O puedes usar la librería de google-generativeai

# Configuración de página
st.set_page_config(page_title="Validador & Tasador IA - Inmuebles Venezuela", page_icon="🏠", layout="wide")

st.title("🏠 Asistente de Tasación e Inspección Visual por IA")
st.write("Evalúa inmuebles, analiza fotos con Visión Artificial y calcula la banda de precios sugerida para el mercado venezolano.")

st.markdown("---")

# 1. Configuración de API Key en el menú lateral
st.sidebar.header("🔑 Configuración de IA")
api_key = st.sidebar.text_input("OpenAI API Key (para análisis de fotos)", type="password")

# 2. Base de Datos de Precios Referenciales (Ajustable a tu mercado local)
PRECIOS_BASE_M2 = {
    "Chacao / Altamira / Los Palos Grandes": 1100,
    "Baruta / Las Mercedes / Valle Arriba": 1250,
    "El Hatillo / La Lagunita": 850,
    "La Guaira (Zonas residenciales/playeras)": 650,
    "San Antonio de los Altos / Los Salias": 550,
    "Isla de Margarita (Porlamar / Pampatar)": 600,
    "Gran Caracas / Centro / Oeste": 450,
    "Otra Zona / Promedio General": 500
}

# 3. Formulario de Captura de Datos
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📋 Datos del Inmueble")
    zona = st.selectbox("Ubicación / Urbanización", list(PRECIOS_BASE_M2.keys()))
    metros_cuadrados = st.number_input("Superficie Total (m²)", min_value=20, max_value=2000, value=80, step=5)
    habitaciones = st.slider("Número de Habitaciones", 1, 6, 2)
    banos = st.slider("Número de Baños", 1, 6, 2)
    puestos = st.slider("Puestos de Estacionamiento", 0, 5, 1)

    st.subheader("⚡ Servicios Críticos")
    tanque_agua = st.checkbox("¿Edificio/Casa con Tanque de Agua de Gran Capacidad?", value=True)
    planta_electrica = st.checkbox("¿Planta Eléctrica en el Conjunto?", value=False)

with col_right:
    st.subheader("📸 Inspección Visual con IA (Opcional)")
    uploaded_file = st.file_uploader("Sube una foto representativa (Cocina, Baño o Sala)", type=["jpg", "jpeg", "png"])
    
    estado_conservacion = "Habitable / Estándar"  # Valor por defecto
    analisis_ia_texto = ""

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Imagen cargada para análisis", use_container_width=True)

        if api_key:
            if st.button("🤖 Analizar Acabados con Visión Artificial"):
                with st.spinner("La IA está evaluando los materiales y el estado de conservación..."):
                    try:
                        # Convertir imagen a base64
                        buffered = io.BytesIO()
                        image.save(buffered, format="JPEG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()

                        # Llamada a OpenAI GPT-4o con visión
                        client = openai.OpenAI(api_key=api_key)
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {
                                    "role": "system",
                                    "content": "Eres un perito tasador inmobiliario experto en el mercado venezolano. Analiza la imagen y clasifica el estado del inmueble estrictamente en una de estas 3 categorías: 'Para remodelar', 'Habitable / Estándar' o 'Totalmente Remodelado / Lujo'. Explica brevemente por qué (materiales, iluminación, conservación)."
                                },
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": "¿Cuál es la calidad de los acabados y estado de conservación de esta área?"},
                                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
                                    ]
                                }
                            ],
                            max_tokens=300
                        )

                        analisis_ia_texto = response.choices[0].message.content
                        st.success("Análisis completado por la IA:")
                        st.write(analisis_ia_texto)

                        # Auto-seleccionar categoría basada en la respuesta
                        if "Lujo" in analisis_ia_texto or "Remodelado" in analisis_ia_texto:
                            estado_conservacion = "Totalmente Remodelado / Lujo"
                        elif "remodelar" in analisis_ia_texto.lower():
                            estado_conservacion = "Para remodelar"
                        else:
                            estado_conservacion = "Habitable / Estándar"

                    except Exception as e:
                        st.error(f"Error al procesar la imagen: {e}")
        else:
            st.info("💡 Ingresa tu OpenAI API Key en la barra lateral para activar el análisis automático de fotos.")

    estado_conservacion = st.selectbox(
        "Estado de Conservación Confirmado", 
        ["Para remodelar", "Habitable / Estándar", "Totalmente Remodelado / Lujo"],
        index=["Para remodelar", "Habitable / Estándar", "Totalmente Remodelado / Lujo"].index(estado_conservacion)
    )

st.markdown("---")

# 4. Motor de Cálculo de Tasación
def calcular_tasacion(zona, m2, hab, banos, puestos, estado, tanque, planta):
    base_m2 = PRECIOS_BASE_M2[zona]
    
    # Coeficiente por estado
    coef_estado = 0.82 if estado == "Para remodelar" else (1.0 if estado == "Habitable / Estándar" else 1.28)
    
    # Coeficiente por servicios en Venezuela
    coef_servicios = 1.0
    if tanque:
        coef_servicios += 0.05
    if planta:
        coef_servicios += 0.12

    precio_m2_ajustado = base_m2 * coef_estado * coef_servicios
    valor_estimado = precio_m2_ajustado * m2
    
    # Rango de negociación (+/- 7%)
    precio_min = valor_estimado * 0.93
    precio_max = valor_estimado * 1.07
    
    return valor_estimado, precio_min, precio_max, precio_m2_ajustado

if st.button("🚀 Calcular Valoración de Mercado", use_container_width=True):
    estimado, p_min, p_max, m2_ajustado = calcular_tasacion(
        zona, metros_cuadrados, habitaciones, banos, puestos, estado_conservacion, tanque_agua, planta_electrica
    )
    
    st.subheader("📊 Resultados de la Tasación")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Precio Mínimo de Cierre", f"${p_min:,.0f} USD")
    c2.metric("Precio Sugerido de Lista", f"${estimado:,.0f} USD")
    c3.metric("Precio Máximo Esperado", f"${p_max:,.0f} USD")
    
    st.caption(f"Valor Promedio Ponderado: **${m2_ajustado:,.2f} USD / m²**")
    
    st.markdown("### 📋 Ficha para Publicar en Facebook / WhatsApp")
    
    texto_publicacion = f"""
✨ **EVALUACIÓN DE MERCADO - VALIDADOR IA** ✨

📍 **Ubicación:** {zona}
📐 **Superficie:** {metros_cuadrados} m²
🛏️ **Distribución:** {habitaciones} Hab | {banos} Baños | {puestos} Est.
🛠️ **Estado:** {estado_conservacion}
💧 **Agua / Luz:** {"Tanque Integrado" if tanque_agua else "Sin tanque principal"} | {"Planta Eléctrica" if planta_electrica else "Sin planta"}

💰 **Banda Estimada de Publicación:** ${p_min:,.0f} - ${p_max:,.0f} USD
🎯 **Precio Base Sugerido:** ${estimado:,.0f} USD (${m2_ajustado:,.0f}/m²)

---
*Análisis generado mediante Modelo de Valoración Hedónica Ajustada.*
    """
    st.code(texto_publicacion, language="markdown")
