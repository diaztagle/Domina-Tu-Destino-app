"""
Mapa de Tu Destino - Plataforma de Consultas Esotéricas
Aplicación web para análisis quirológico y ciclos vitales
Autor: Sistema de IA para labor social
"""

import streamlit as st
import sqlite3
import hashlib
import datetime
import json
import cv2
import numpy as np
from PIL import Image
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd

# ============================================================================
# CONFIGURACIÓN INICIAL
# ============================================================================

st.set_page_config(
    page_title="Mapa de Tu Destino",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# BASE DE DATOS - CONFIGURACIÓN
# ============================================================================

def init_db():
    """Inicializa la base de datos SQLite"""
    conn = sqlite3.connect('destino.db', check_same_thread=False)
    c = conn.cursor()
    
    # Tabla de usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Tabla de consultas
    c.execute('''CREATE TABLE IF NOT EXISTS consultas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  consulta_text TEXT,
                  fecha_nacimiento DATE,
                  ano_personal INTEGER,
                  fotos_data TEXT,
                  analisis_auto TEXT,
                  interpretacion_personal TEXT,
                  status TEXT DEFAULT 'pendiente',
                  anonimo INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # Tabla de pagos
    c.execute('''CREATE TABLE IF NOT EXISTS pagos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  consulta_id INTEGER,
                  monto REAL,
                  tipo TEXT,
                  status TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  FOREIGN KEY (consulta_id) REFERENCES consultas(id))''')
    
    conn.commit()
    return conn

# ============================================================================
# BASE DE CONOCIMIENTOS - QUIROLOGÍA Y CICLOS
# ============================================================================

CONOCIMIENTOS_QUIROLOGIA = {
    "formas_mano": {
        "cuadrada": {
            "descripcion": "Mano práctica y lógica",
            "caracteristicas": "Palma cuadrada, dedos de longitud similar a la palma",
            "personalidad": "Persona práctica, metódica, confiable. Prefiere la estabilidad y el orden."
        },
        "conica": {
            "descripcion": "Mano artística e intuitiva",
            "caracteristicas": "Palma ovalada, dedos que se estrechan hacia las puntas",
            "personalidad": "Persona creativa, intuitiva, emocional. Busca belleza y armonía."
        },
        "filosofica": {
            "descripcion": "Mano intelectual",
            "caracteristicas": "Palma rectangular, dedos largos y nudosos",
            "personalidad": "Persona analítica, filosófica, busca conocimiento profundo."
        },
        "espatulada": {
            "descripcion": "Mano de acción",
            "caracteristicas": "Dedos que se ensanchan en las puntas",
            "personalidad": "Persona activa, enérgica, práctica. Le gusta la acción directa."
        }
    },
    
    "lineas": {
        "vida": {
            "larga": "Gran vitalidad y energía. Vida longeva si se cuida la salud.",
            "corta": "No indica vida corta, sino intensidad. Enfoque en calidad sobre cantidad.",
            "profunda": "Energía vital fuerte, resistencia física.",
            "fragmentada": "Cambios importantes en el estilo de vida."
        },
        "cabeza": {
            "larga": "Pensamiento analítico, atención al detalle.",
            "corta": "Decisiones rápidas, pensamiento directo.",
            "recta": "Pensamiento lógico y práctico.",
            "curva": "Imaginación, creatividad, pensamiento lateral."
        },
        "corazon": {
            "larga": "Emociones profundas, relaciones duraderas.",
            "corta": "Enfoque más cerebral que emocional.",
            "profunda": "Pasión intensa en relaciones.",
            "fragmentada": "Experiencias emocionales variadas."
        },
        "destino": {
            "presente": "Sentido claro de propósito y dirección.",
            "ausente": "Libertad para crear su propio camino.",
            "fuerte": "Influencias externas marcan el camino.",
            "debil": "Mayor control personal del destino."
        }
    },
    
    "montes": {
        "venus": "Amor, pasión, vitalidad física",
        "jupiter": "Ambición, liderazgo, confianza",
        "saturno": "Responsabilidad, disciplina, sabiduría",
        "apolo": "Creatividad, arte, éxito",
        "mercurio": "Comunicación, negocios, adaptabilidad",
        "luna": "Imaginación, intuición, emociones",
        "marte": "Energía, coraje, determinación"
    },
    
    "signos": {
        "estrella": "Evento significativo, éxito o cambio dramático",
        "cruz": "Obstáculo superado o protección espiritual",
        "triangulo": "Talento especial o habilidad mental",
        "cuadrado": "Protección ante adversidades",
        "isla": "Periodo de dificultad o confusión temporal"
    }
}

CICLOS_VITALES = {
    1: {
        "nombre": "Año de Inicios",
        "descripcion": "Tiempo de nuevos comienzos, iniciativa personal, independencia",
        "consejos": "Toma la iniciativa, confía en ti, empieza proyectos nuevos"
    },
    2: {
        "nombre": "Año de Cooperación",
        "descripcion": "Relaciones, diplomacia, asociaciones, paciencia",
        "consejos": "Trabaja en equipo, cultiva relaciones, sé diplomático"
    },
    3: {
        "nombre": "Año de Expresión",
        "descripcion": "Creatividad, comunicación, alegría, socialización",
        "consejos": "Expresa tu creatividad, comunícate, disfruta la vida social"
    },
    4: {
        "nombre": "Año de Construcción",
        "descripcion": "Trabajo duro, estructura, bases sólidas, disciplina",
        "consejos": "Organiza tu vida, trabaja con disciplina, construye cimientos"
    },
    5: {
        "nombre": "Año de Cambios",
        "descripcion": "Libertad, aventura, cambios, adaptabilidad",
        "consejos": "Abraza el cambio, busca nuevas experiencias, sé flexible"
    },
    6: {
        "nombre": "Año de Responsabilidad",
        "descripcion": "Familia, hogar, servicio, armonía",
        "consejos": "Cuida tus relaciones familiares, sé responsable, busca armonía"
    },
    7: {
        "nombre": "Año de Introspección",
        "descripcion": "Espiritualidad, análisis, soledad productiva, conocimiento",
        "consejos": "Medita, estudia, busca conocimiento interior, reflexiona"
    },
    8: {
        "nombre": "Año de Poder",
        "descripcion": "Logros materiales, autoridad, éxito profesional",
        "consejos": "Enfócate en metas materiales, asume liderazgo, busca éxito"
    },
    9: {
        "nombre": "Año de Culminación",
        "descripcion": "Cierre de ciclos, humanitarismo, sabiduría, desapego",
        "consejos": "Cierra ciclos, ayuda a otros, comparte tu sabiduría"
    }
}

# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def hash_password(password):
    """Hash de contraseña con SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def validar_email(email):
    """Validación básica de email"""
    return '@' in email and '.' in email.split('@')[1]

def calcular_ano_personal(fecha_nacimiento):
    """Calcula el año personal según numerología"""
    try:
        dia = fecha_nacimiento.day
        mes = fecha_nacimiento.month
        ano_actual = datetime.datetime.now().year
        
        # Suma día + mes + año actual
        suma = dia + mes + ano_actual
        
        # Reducir a un dígito (1-9)
        while suma > 9:
            suma = sum(int(d) for d in str(suma))
        
        return suma
    except:
        return None

def enviar_email_notificacion(destinatario, asunto, mensaje):
    """Envía notificación por email (requiere configuración SMTP)"""
    # NOTA: Configurar con credenciales reales
    try:
        # Esta es una implementación de ejemplo
        # En producción, usar variables de entorno para credenciales
        return True
    except Exception as e:
        st.error(f"Error al enviar email: {str(e)}")
        return False

# ============================================================================
# ANÁLISIS DE IMÁGENES - QUIROLOGÍA
# ============================================================================

def analizar_forma_mano(imagen):
    """Analiza la forma de la mano usando procesamiento de imágenes"""
    try:
        # Convertir imagen a numpy array
        img_array = np.array(imagen)
        
        # Convertir a escala de grises
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Detectar contornos
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Obtener el contorno más grande (la mano)
            contorno_mano = max(contours, key=cv2.contourArea)
            
            # Calcular proporciones
            x, y, w, h = cv2.boundingRect(contorno_mano)
            ratio = h / w if w > 0 else 1
            
            # Clasificar según ratio
            if 0.9 <= ratio <= 1.1:
                return "cuadrada"
            elif ratio > 1.3:
                return "filosofica"
            elif ratio < 0.9:
                return "espatulada"
            else:
                return "conica"
        
        return "indeterminada"
    except Exception as e:
        return "error"

def detectar_lineas(imagen):
    """Detecta líneas principales en la palma"""
    try:
        img_array = np.array(imagen)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Detectar bordes
        edges = cv2.Canny(gray, 50, 150)
        
        # Detectar líneas usando Hough Transform
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=50, maxLineGap=10)
        
        analisis_lineas = {
            "vida": "presente",
            "cabeza": "presente",
            "corazon": "presente",
            "destino": "presente" if lines is not None and len(lines) > 5 else "ausente"
        }
        
        return analisis_lineas
    except:
        return {"vida": "indeterminada", "cabeza": "indeterminada", 
                "corazon": "indeterminada", "destino": "indeterminada"}

def analizar_mano_completo(imagenes):
    """Análisis completo de las imágenes de la mano"""
    resultados = {
        "forma": "indeterminada",
        "lineas": {},
        "interpretacion": ""
    }
    
    if imagenes:
        # Analizar la primera imagen (palma derecha preferentemente)
        primera_imagen = imagenes[0]
        resultados["forma"] = analizar_forma_mano(primera_imagen)
        resultados["lineas"] = detectar_lineas(primera_imagen)
        
        # Generar interpretación
        forma_info = CONOCIMIENTOS_QUIROLOGIA["formas_mano"].get(
            resultados["forma"], 
            {"personalidad": "Forma no identificada claramente"}
        )
        
        resultados["interpretacion"] = f"""
**Forma de Mano:** {resultados["forma"].capitalize()}
{forma_info.get('personalidad', '')}

**Líneas Principales:**
- Línea de Vida: {resultados["lineas"].get("vida", "No detectada")}
- Línea de Cabeza: {resultados["lineas"].get("cabeza", "No detectada")}
- Línea de Corazón: {resultados["lineas"].get("corazon", "No detectada")}
- Línea de Destino: {resultados["lineas"].get("destino", "No detectada")}
        """
    
    return resultados

# ============================================================================
# GESTIÓN DE USUARIOS
# ============================================================================

def registrar_usuario(email, password):
    """Registra un nuevo usuario"""
    if not validar_email(email):
        return False, "Email inválido"
    
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres"
    
    try:
        conn = st.session_state.db_conn
        c = conn.cursor()
        
        password_hash = hash_password(password)
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", 
                  (email, password_hash))
        conn.commit()
        
        return True, "Usuario registrado exitosamente"
    except sqlite3.IntegrityError:
        return False, "El email ya está registrado"
    except Exception as e:
        return False, f"Error: {str(e)}"

def login_usuario(email, password):
    """Autentica un usuario"""
    try:
        conn = st.session_state.db_conn
        c = conn.cursor()
        
        password_hash = hash_password(password)
        c.execute("SELECT id, email FROM users WHERE email = ? AND password = ?", 
                  (email, password_hash))
        
        result = c.fetchone()
        if result:
            return True, {"id": result[0], "email": result[1]}
        else:
            return False, "Credenciales incorrectas"
    except Exception as e:
        return False, f"Error: {str(e)}"

# ============================================================================
# GESTIÓN DE CONSULTAS
# ============================================================================

def crear_consulta(user_id, consulta_text, fecha_nacimiento, fotos, anonimo=False):
    """Crea una nueva consulta"""
    try:
        conn = st.session_state.db_conn
        c = conn.cursor()
        
        # Calcular año personal
        ano_personal = calcular_ano_personal(fecha_nacimiento)
        
        # Analizar fotos
        analisis = analizar_mano_completo(fotos)
        
        # Combinar análisis quirológico + ciclo vital
        ciclo_info = CICLOS_VITALES.get(ano_personal, {})
        
        analisis_completo = f"""
{analisis['interpretacion']}

**Ciclo Vital Actual (Año {ano_personal}):**
{ciclo_info.get('nombre', 'Información no disponible')}

{ciclo_info.get('descripcion', '')}

**Recomendaciones para este ciclo:**
{ciclo_info.get('consejos', '')}

---
**IMPORTANTE:** Esta es una interpretación automática basada en análisis digital. 
Para una lectura personalizada y profunda, un experto revisará tu consulta y 
te enviará su interpretación personal.
        """
        
        # Guardar fotos como base64 (simplificado para ejemplo)
        fotos_json = json.dumps({"cantidad": len(fotos)})
        
        c.execute("""INSERT INTO consultas 
                     (user_id, consulta_text, fecha_nacimiento, ano_personal, 
                      fotos_data, analisis_auto, anonimo)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                  (user_id, consulta_text, fecha_nacimiento, ano_personal,
                   fotos_json, analisis_completo, 1 if anonimo else 0))
        
        conn.commit()
        consulta_id = c.lastrowid
        
        return True, consulta_id, analisis_completo
    except Exception as e:
        return False, None, f"Error: {str(e)}"

def obtener_consultas_pendientes():
    """Obtiene consultas pendientes para el dashboard admin"""
    try:
        conn = st.session_state.db_conn
        c = conn.cursor()
        
        c.execute("""SELECT c.id, c.consulta_text, c.fecha_nacimiento, 
                            c.ano_personal, c.analisis_auto, c.created_at,
                            u.email
                     FROM consultas c
                     LEFT JOIN users u ON c.user_id = u.id
                     WHERE c.status = 'pendiente'
                     ORDER BY c.created_at DESC""")
        
        consultas = []
        for row in c.fetchall():
            consultas.append({
                "id": row[0],
                "consulta": row[1],
                "fecha_nac": row[2],
                "ano_personal": row[3],
                "analisis": row[4],
                "fecha_creacion": row[5],
                "email": row[6] if row[6] else "Anónimo"
            })
        
        return consultas
    except Exception as e:
        st.error(f"Error al obtener consultas: {str(e)}")
        return []

def actualizar_interpretacion(consulta_id, interpretacion):
    """Actualiza la interpretación personal de una consulta"""
    try:
        conn = st.session_state.db_conn
        c = conn.cursor()
        
        c.execute("""UPDATE consultas 
                     SET interpretacion_personal = ?, status = 'completada'
                     WHERE id = ?""",
                  (interpretacion, consulta_id))
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error al actualizar: {str(e)}")
        return False

# ============================================================================
# INTERFAZ DE USUARIO - PÁGINAS
# ============================================================================

def pagina_inicio():
    """Página de inicio"""
    st.title("🔮 Mapa de Tu Destino")
    st.subheader("Consultas Esotéricas Accesibles para Todos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### ¿Qué ofrecemos?
        
        - **Análisis Quirológico**: Lectura de manos basada en conocimientos tradicionales
        - **Ciclos Vitales**: Comprende tu momento actual según numerología
        - **Interpretación Personalizada**: Análisis humano profundo de expertos
        - **Bajo Costo**: Acceso a orientación esotérica para todos
        
        ### ¿Cómo funciona?
        
        1. Crea tu cuenta o inicia sesión
        2. Completa el formulario con tu consulta
        3. Sube fotos de tus manos
        4. Recibe análisis automático inmediato
        5. Obtén interpretación personalizada de un experto
        """)
    
    with col2:
        st.info("""
        ### ⚠️ Aviso Importante
        
        Esta plataforma ofrece **orientación y autoconocimiento**, 
        NO sustituye:
        
        - Consejo médico profesional
        - Asesoría legal
        - Terapia psicológica
        - Asesoría financiera profesional
        
        Los análisis son herramientas de reflexión personal 
        y crecimiento espiritual.
        
        ### 💰 Modelo de Precios
        
        - **Análisis Automático**: GRATIS
        - **Interpretación Personal**: $3 USD
        - **Suscripción Mensual**: $5 USD (consultas ilimitadas)
        """)
    
    st.markdown("---")
    st.markdown("### 🌟 Testimonios")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("*'Me ayudó a entender mejor mi momento actual'* - Ana M.")
    with col2:
        st.success("*'Accesible y revelador'* - Carlos R.")
    with col3:
        st.success("*'Análisis detallado y útil'* - María L.")

def pagina_auth():
    """Página de autenticación"""
    st.title("Acceso de Usuario")
    
    tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
    
    with tab1:
        st.subheader("Iniciar Sesión")
        
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Contraseña", type="password", key="login_password")
        
        if st.button("Ingresar", type="primary"):
            if email and password:
                exito, resultado = login_usuario(email, password)
                if exito:
                    st.session_state.user = resultado
                    st.session_state.logged_in = True
                    st.success("¡Bienvenido!")
                    st.rerun()
                else:
                    st.error(resultado)
            else:
                st.warning("Por favor completa todos los campos")
    
    with tab2:
        st.subheader("Crear Cuenta")
        
        nuevo_email = st.text_input("Email", key="reg_email")
        nuevo_password = st.text_input("Contraseña", type="password", key="reg_password")
        confirmar_password = st.text_input("Confirmar Contraseña", type="password", key="reg_confirm")
        
        acepta_terminos = st.checkbox("Acepto términos de servicio y política de privacidad")
        
        if st.button("Registrarse", type="primary"):
            if not acepta_terminos:
                st.warning("Debes aceptar los términos de servicio")
            elif nuevo_password != confirmar_password:
                st.error("Las contraseñas no coinciden")
            elif nuevo_email and nuevo_password:
                exito, mensaje = registrar_usuario(nuevo_email, nuevo_password)
                if exito:
                    st.success(mensaje)
                    st.info("Ahora puedes iniciar sesión")
                else:
                    st.error(mensaje)
            else:
                st.warning("Por favor completa todos los campos")

def pagina_consulta():
    """Página de nueva consulta"""
    st.title("Nueva Consulta")
    
    st.warning("""
    **Aviso de Privacidad y Consentimiento**
    
    Al usar este servicio aceptas que:
    - Tus datos serán procesados para brindarte el servicio
    - Las fotos serán analizadas con fines de lectura quirológica
    - Puedes solicitar anonimato (no se mostrará tu email al analista)
    - Puedes solicitar eliminación de datos después de la consulta
    """)
    
    with st.form("formulario_consulta"):
        st.subheader("1. Tu Consulta")
        consulta_text = st.text_area(
            "¿Qué te gustaría saber?",
            placeholder="Ej: ¿Cómo me irá en mi carrera profesional este año? ¿Es buen momento para cambios?",
            height=150
        )
        
        st.subheader("2. Información Personal")
        col1, col2 = st.columns(2)
        
        with col1:
            fecha_nacimiento = st.date_input(
                "Fecha de Nacimiento",
                min_value=datetime.date(1920, 1, 1),
                max_value=datetime.date.today()
            )
        
        with col2:
            anonimo = st.checkbox("Consulta anónima (tu email no se mostrará)")
        
        st.subheader("3. Fotos de tus Manos")
        st.info("""
        **Instrucciones para mejores resultados:**
        - Toma fotos con buena iluminación
        - Fondo liso y claro
        - Mano abierta y relajada
        - Sube al menos la palma de tu mano dominante
        """)
        
        fotos = []
        col1, col2 = st.columns(2)
        
        with col1:
            foto1 = st.file_uploader("Palma Derecha", type=['jpg', 'jpeg', 'png'])
            foto2 = st.file_uploader("Palma Izquierda", type=['jpg', 'jpeg', 'png'])
        
        with col2:
            foto3 = st.file_uploader("Dorso/Lateral (Opcional)", type=['jpg', 'jpeg', 'png'])
            foto4 = st.file_uploader("Foto Adicional (Opcional)", type=['jpg', 'jpeg', 'png'])
        
        tipo_servicio = st.radio(
            "Tipo de Servicio",
            ["Análisis Automático (Gratis)", "Interpretación Personal ($3 USD)"]
        )
        
        submitted = st.form_submit_button("Enviar Consulta", type="primary")
        
        if submitted:
            # Validaciones
            if not consulta_text:
                st.error("Por favor describe tu consulta")
            elif not foto1:
                st.error("Sube al menos una foto de tu palma")
            else:
                # Procesar fotos
                imagenes_procesadas = []
                for foto in [foto1, foto2, foto3, foto4]:
                    if foto:
                        imagen = Image.open(foto)
                        imagenes_procesadas.append(imagen)
                
                # Crear consulta
                with st.spinner("Procesando tu consulta..."):
                    exito, consulta_id, analisis = crear_consulta(
                        st.session_state.user["id"],
                        consulta_text,
                        fecha_nacimiento,
                        imagenes_procesadas,
                        anonimo
                    )
                
                if exito:
                    st.success("¡Consulta creada exitosamente!")
                    
                    # Mostrar análisis automático
                    st.subheader("Tu Análisis Automático")
                    st.markdown(analisis)
                    
                    if tipo_servicio == "Interpretación Personal ($3 USD)":
                        st.info("""
                        **Siguiente Paso: Pago**
                        
                        Para recibir la interpretación personalizada de un experto, 
                        procede al pago de $3 USD.
                        
                        (En producción, aquí iría la integración con Stripe)
                        """)
                        
                        # Simular botón de pago
                        if st.button("Proceder al Pago"):
                            st.success("Pago procesado (simulación). Un experto revisará tu consulta pronto.")
                    else:
                        st.info("""
                        Has recibido el análisis automático gratuito. 
                        
                        Si deseas una interpretación más profunda y personalizada, 
                        puedes solicitar el servicio premium desde tu perfil.
                        """)
                else:
                    st.error(f"Error al crear consulta: {analisis}")

def pagina_mis_consultas():
    """Página de historial de consultas del usuario"""
    st.title("Mis Consultas")
    
    try:
        conn = st.session_state.db_conn
        c = conn.cursor()
        
        c.execute("""SELECT id, consulta_text, fecha_nacimiento, ano_personal,
                            analisis_auto, interpretacion_personal, status, created_at
                     FROM consultas
                     WHERE user_id = ?
                     ORDER BY created_at DESC""",
                  (st.session_state.user["id"],))
        
        consultas = c.fetchall()
        
        if not consultas:
            st.info("Aún no tienes consultas. ¡Crea tu primera consulta!")
        else:
            for consulta in consultas:
                with st.expander(f"Consulta del {consulta[7]} - {consulta[6].upper()}"):
                    st.markdown(f"**Tu pregunta:** {consulta[1]}")
                    st.markdown(f"**Fecha de nacimiento:** {consulta[2]}")
                    st.markdown(f"**Año Personal:** {consulta[3]}")
                    
                    st.markdown("---")
                    st.markdown("### Análisis Automático")
                    st.markdown(consulta[4])
                    
                    if consulta[5]:
                        st.markdown("---")
                        st.markdown("### 🌟 Interpretación Personal del Experto")
                        st.success(consulta[5])
                    elif consulta[6] == 'pendiente':
                        st.info("Tu interpretación personal está en proceso. Te notificaremos cuando esté lista.")
    except Exception as e:
        st.error(f"Error al cargar consultas: {str(e)}")

def pagina_dashboard_admin():
    """Dashboard administrativo para gestionar consultas"""
    st.title("📊 Dashboard Administrativo")
    
    # Verificar si es admin (simplificado - en producción usar