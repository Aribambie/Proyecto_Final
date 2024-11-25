import streamlit as st
import json
from dotenv import load_dotenv
from langchain import hub
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_experimental.tools import PythonREPLTool
from langchain_experimental.agents.agent_toolkits import create_csv_agent

load_dotenv()


def inicializar_agents():
    base_prompt = hub.pull("langchain-ai/react-agent-template")
    instrucciones = """
    - Eres un agente especializado en la obra y vida de franz kafka que puede escribir y ejecutar código Python
    - Utiliza siempre las herramientas proporcionadas para responder preguntasy calculos
    - Si no puedes responder una pregunta, responde con "No tengo las herramientas para aclarar tu duda"
    - Proporciona explicaciones claras 
    - Siempre usa Python para realizar los cálculos
    """
    prompt = base_prompt.partial(instructions=instrucciones)

    llm = ChatOpenAI(temperature=0, model="gpt-4")
    tools = [PythonREPLTool()]

    python_agent = create_react_agent(
        prompt=prompt,
        llm=llm,
        tools=tools,
    )

    return AgentExecutor(agent=python_agent, tools=tools, verbose=True)


def creacion_de_agentes_csv():
    llm = ChatOpenAI(temperature=0, model="gpt-4")

    return {
        "Cuentos de Kafka": create_csv_agent(
            llm=llm,
            path="kafka_csv_files/eternacadencia_com_ar.csv",
            verbose=True,
            allow_dangerous_code=True,
            handle_parsing_errors=True  # Habilitar manejo de errores
        ),
        "Sobre la vida de Kafka": create_csv_agent(
            llm=llm,
            path="kafka_csv_files/historia_nationalgeographic_com_es.csv",
            verbose=True,
            allow_dangerous_code=True,
            handle_parsing_errors=True  # Habilitar manejo de errores
        ),
        "Cartas a Milena": create_csv_agent(
            llm=llm,
            path="kafka_csv_files/palabrayverso_com.csv",
            verbose=True,
            allow_dangerous_code=True,
            handle_parsing_errors=True  # Habilitar manejo de errores
        ),
        "Obras fundamentales de Kafka": create_csv_agent(
            llm=llm,
            path="kafka_csv_files/www_cultura_gob_ar.csv",
            verbose=True,
            allow_dangerous_code=True,
            handle_parsing_errors=True  # Habilitar manejo de errores
        )
    }


def save_history(history, archivo="history.json"):
    try:
        with open(archivo, "w") as f:
            json.dump(history, f, indent=4)
        st.success(f"Historial guardado en {archivo}")
    except Exception as e:
        st.error(f"No se pudo guardar el historial: {str(e)}")


def update_history(archivo="history.json"):
    try:
        with open(archivo, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception as e:
        st.error(f"No se pudo cargar el historial: {str(e)}")
        return []


def main():
    st.set_page_config(
        page_title="Agente de programación y obra literaria de Franz Kafka",
        page_icon="🪳",
        layout="wide"
    )

    st.title("🪳 Agente de programación y obra literaria de Franz Kafka")
    st.markdown("### Acerca de este Agente")
    st.markdown("""
    Este agente hace uso de la capacidad de análisis de datos de Python con datos la vida y trabajo de Kafka.
    Puede hacer cálculos por medio de la creación de programas de Python.
    Para hacer sus preguntas, use la casilla de preguntas.
    """)

    # Inicialización de agentes
    python_agent_executor = inicializar_agents()
    agentes_csv = creacion_de_agentes_csv()

    # Inicializar historial desde archivo
    if "history" not in st.session_state:
        st.session_state.historial = update_history()

    # Selección del agente
    st.sidebar.title("Configuración")
    opcion_agente = st.sidebar.selectbox(
        "Seleccione el agente de análisis:",
        ["Seleccione un agente...", "Cuentos de Kafka", "Sobre la vida de Kafka", "Cartas a Milena",
         "Obras fundamentales de Kafka"]
    )

    # Sección de ejemplos Python
    st.markdown("## Ejemplos de Python")
    ejemplos_python = [
        "Dibuja un patito.",
        "Multiplica 20 veces 20.",
        "Realiza una lista de multiplos de 2 en un rango de 0 a 30.",
    ]
    ejemplo_seleccionado = st.selectbox(
        "Seleccione un ejemplo:",
        ejemplos_python,
        key="ejemplo_python"
    )

    if st.button("Ejecutar Ejemplo", key="ejecutar_python"):
        with st.spinner("Procesando su solicitud..."):
            try:
                respuesta = python_agent_executor.invoke({"input": ejemplo_seleccionado})
                if 'output' in respuesta:
                    st.markdown("### Respuesta del Agente:")
                    st.code(respuesta['output'], language="python")
                else:
                    st.error("No se recibió respuesta del agente.")
            except Exception as e:
                st.error(f"Error al ejecutar el agente: {str(e)}")

    agente_a_usar = agentes_csv.get(opcion_agente) if opcion_agente != "Seleccione un agente..." else None

    # Campo de texto para pregunta personalizada
    pregunta_personalizada = st.text_input(
        "Escribe tu pregunta:",
        value="",
        key="pregunta_personalizada"
    )

    # Botón de análisis con historial
    if st.button("Analizar Datos", key="ejecutar_analisis"):
        pregunta_final = pregunta_personalizada

        if pregunta_final:
            with st.spinner("Analizando datos..."):
                try:
                    if agente_a_usar:
                        pregunta_con_contexto = f"""
                        Analiza los datos para responder: {pregunta_final}
                        Por favor, incluye:
                        1. Un resumen claro sobra la información pedida
                        2. Cualquier dato relevante
                        3. Sugerencias basadas en el análisis literario
                        """

                        respuesta = agente_a_usar.invoke({"input": pregunta_con_contexto})

                        # Guardar en el historial
                        st.session_state.historial.append({
                            "pregunta": pregunta_final,
                            "respuesta": respuesta['output']
                        })

                        # Guardar el historial en el archivo
                        save_history(st.session_state.historial)

                        # Mostrar resultados
                        st.markdown("### Resultados del Análisis")
                        st.write(respuesta['output'])

                        st.info("Análisis completado con éxito")
                    else:
                        st.error(
                            "No se pudo determinar el agente apropiado para esta categoría. Seleccione un agente válido.")
                except Exception as e:
                    st.error(f"Error durante el análisis: {str(e)}")
        else:
            st.error("Por favor, escribe una pregunta válida.")

    # Mostrar historial de preguntas y respuestas
    st.markdown("## Historial de Preguntas y Respuestas")
    for idx, item in enumerate(st.session_state.historial):
        with st.expander(f"Pregunta {idx + 1}: {item['pregunta']}"):
            st.write(f"*Respuesta:* {item['respuesta']}")


if __name__ == "__main__":
    main()

