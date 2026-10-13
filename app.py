import streamlit as st
import base64
from PIL import Image
import io
import openai

# Configuración de página
st.set_page_config(page_title="Validador & Tasador IA - Inmuebles Venezuela", page_icon="🏠", layout="wide")

st.title("🏠 Asistente de Tasación e Inspección Visual por IA")
st.write("Evalúa inmuebles, analiza fotos con Visión Artificial y calcula la banda de precios sugerida para el mercado venezolano.")

st.markdown("---")

# 1. Configuración de API Key en el menú lateral
st.sidebar.header("🔑 Configuración de IA")
api_key = st.sidebar.text_input("OpenAI API Key (para análisis de fotos)", type="password")

# 2. Base de Datos de Precios Referenciales (Actualizada Nueva Esparta y Caracas)
PRECIOS_BASE_M2 = {
    # --- Estado Nueva Esparta (Isla de Margarita / Coche) ---
    "Porlamar (Comercial / Residencial Principal)": 550,
    "Pampatar (Boca del Río / Costamar / El Morro)": 750,
    "La Asunción (Centro Histórico / Residencial)": 500,
    "Juan Griego (Zona Norte / Comercial)": 480,
    "Playa El Agua (Costa Turística / Vacacional)": 700,
    "La Mira (Costa Este / Residencial Turística)": 650,
    "El Valle / Guacuco": 600,
    
    # --- Otras Regiones Clave ---
    "Chacao / Altamira / Los Palos Grandes (Caracas)": 1100,
    "Baruta / Las Mercedes / Valle Arriba (Caracas)": 1250,
    "El Hatillo / La Lagunita (Caracas)": 850,
    "La Guaira (Zonas residenciales/playeras)": 650,
    "San Antonio de los Altos / Los Salias": 550,
    "Gran Caracas / Centro / Oeste": 450,
    "Otra Zona / Promedio General": 500
}

# 3. Formulario de Captura de Datos
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📋 Datos del Inmueble")
    
    tipo_propiedad = st.selectbox(
        "Tipo de Propiedad",
        ["Apartamento", "Casa / Townhouse", "Local Comercial", "Posada / Hotel", "Terreno / Galpón"]
    )
    
    zona = st.selectbox("Ubicación / Urbanización", list(PRECIOS_BASE_M2.keys()))
    metros_cuadrados = st.number_input("Superficie Total (m²)", min_value=10, max_value=5000, value=80, step=5)
    habitaciones = st.slider("Número de Habitaciones / Ambientes", 1, 20, 2)
    banos = st.slider("Número de Baños", 1, 20, 2)
    puestos = st.slider("Puestos de Estacionamiento", 0, 20, 1)

    st.subheader("⚡ Servicios Críticos e Infraestructura")
    tanque_agua = st.checkbox("¿Tanque de Agua de Gran Capacidad?", value=True)
    pozo_propio = st.checkbox("💧 ¿Pozo de Agua Propio (Casa o Edificio)?", value=False)
    planta_electrica = st.checkbox("⚡ ¿Planta Eléctrica (Total o Áreas Comunes)?", value=False)

with col_right:
    st.subheader("📸 Inspección Visual con IA (Opcional)")
    uploaded_file = st.file_uploader("Sube una foto representativa (Cocina, Baño o Sala)", type=["jpg", "jpeg", "png"])
    
    estado_conservacion = "Habitable / Estándar"
    analisis_ia_texto = ""

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Imagen cargada para análisis", use_container_width=True)

        if api_key:
            if st.button("🤖 Analizar Acabados con Visión Artificial"):
                with st.spinner("La IA está evaluando los materiales y el estado de conservación..."):
                    try:
                        buffered = io.BytesIO()
                        image.save(buffered, format="JPEG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()

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

# 4. Motor de Cálculo de Tasación (Incluyendo Pozo Profundo)
def calcular_tasacion(zona, m2, hab, banos, puestos, estado, tanque, pozo, planta, tipo_prop):
    base_m2 = PRECIOS_BASE_M2.get(zona, 500)
    
    # Coeficiente por estado
    coef_estado = 0.82 if estado == "Para remodelar" else (1.0 if estado == "Habitable / Estándar" else 1.28)
    
    # Coeficiente por servicios críticos ponderados para Venezuela
    coef_servicios = 1.0
    if tanque:
        coef_servicios += 0.04
    if pozo:
        coef_servicios += 0.12  # El pozo aporta un plus muy alto de valoración
    if planta:
        coef_servicios += 0.10

    # Coeficiente según tipo de propiedad
    factores_tipo = {
        "Apartamento": 1.0,
        "Casa / Townhouse": 0.95,
        "Local Comercial": 1.15,
        "Posada / Hotel": 1.25,
        "Terreno / Galpón": 0.60
    }
    coef_tipo = factores_tipo.get(tipo_prop, 1.0)

    precio_m2_ajustado = base_m2 * coef_estado * coef_servicios * coef_tipo
    valor_estimado = precio_m2_ajustado * m2
    
    # Rango de negociación (+/- 7%)
    precio_min = valor_estimado * 0.93
    precio_max = valor_estimado * 1.07
    
    return valor_estimado, precio_min, precio_max, precio_m2_ajustado

if st.button("🚀 Calcular Valoración de Mercado", use_container_width=True):
    estimado, p_min, p_max, m2_ajustado = calcular_tasacion(
        zona, metros_cuadrados, habitaciones, banos, puestos, estado_conservacion, tanque_agua, pozo_propio, planta_electrica, tipo_propiedad
    )
    
    st.subheader("📊 Resultados de la Tasación")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Precio Mínimo de Cierre", f"${p_min:,.0f} USD")
    c2.metric("Precio Sugerido de Lista", f"${estimado:,.0f} USD")
    c3.metric("Precio Máximo Esperado", f"${p_max:,.0f} USD")
    
    st.caption(f"Valor Promedio Ponderado: **${m2_ajustado:,.2f} USD / m²**")
    
    st.markdown("### 📋 Ficha para Publicar en Facebook / WhatsApp")
    
    # Detalle de servicios para la ficha
    servicios_lista = []
    if tanque_agua: servicios_lista.append("Tanque")
    if pozo_propio: servicios_lista.append("Pozo Propio 💧")
    if planta_electrica: servicios_lista.append("Planta Eléctrica ⚡")
    str_servicios = ", ".join(servicios_lista) if servicios_lista else "Servicios básicos estándar"

    texto_publicacion = f"""
✨ **EVALUACIÓN DE MERCADO - VALIDADOR IA** ✨

🏠 **Tipo:** {tipo_propiedad}
📍 **Ubicación:** {zona}
📐 **Superficie:** {metros_cuadrados} m²
🛏️ **Distribución:** {habitaciones} Hab/Ambientes | {banos} Baños | {puestos} Est.
🛠️ **Estado:** {estado_conservacion}
⚙️ **Servicios Críticos:** {str_servicios}

💰 **Banda Estimada de Publicación:** ${p_min:,.0f} - ${p_max:,.0f} USD
🎯 **Precio Base Sugerido:** ${estimado:,.0f} USD (${m2_ajustado:,.0f}/m²)

---
*Análisis generado mediante Modelo de Valoración Hedónica Ajustada.*
    """
    st.code(texto_publicacion, language="markdown")
                            
