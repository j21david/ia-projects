# 🧠 ia-projects: Pequeños ejercicios para entender de agentes y LLMs

---

## 🎯 Descripción del Proyecto

Este repositorio contiene una colección de pequeños ejercicios y scripts de Python diseñados para explorar y comprender los fundamentos de los **Agentes de Inteligencia Artificial (IA)** y los **Large Language Models (LLMs)**.

El enfoque principal es la aplicación práctica de conceptos clave como el acceso a herramientas (Internet), la transferencia de tareas entre agentes (`handoff`), la implementación de mecanismos de seguridad (`guardrails`) y la integración de servicios de correo electrónico.

### 🔑 Conceptos Explorados

* **Agentes de IA:** Creación y configuración de entidades autónomas.
* **LLMs:** Uso de modelos de lenguaje para potenciar la lógica y conversación.
* **Guardrails:** Implementación de restricciones en las respuestas del agente.
* **Handoff:** Transferencia fluida de una tarea de un agente a otro.
* **Integración de Servicios:** Envío de correos electrónicos a través de **SendGrid** o **Brevo**.

---

## 📂 Contenido del Repositorio

El repositorio está organizado con archivos `.py` que representan ejercicios individuales y funcionales:

| Archivo | Descripción Breve | Concepto Principal |
| :--- | :--- | :--- |
| `hello_world_agent.py` | El script inicial para configurar y ejecutar un agente simple. | **Fundamentos de Agentes** |
| `agent_with_internet_access.py` | Un agente configurado con una herramienta de búsqueda para obtener información en tiempo real. | **Uso de Herramientas** |
| `agent_with_handoff.py` | Ejemplo de cómo dos o más agentes colaboran, transfiriéndose la conversación o tarea. | **Colaboración / Handoff** |
| `agent_with_guardrails.py` | Muestra cómo imponer reglas y límites en las respuestas del agente para asegurar la relevancia y seguridad. | **Guardrails / Seguridad** |
| `LICENSE` | La licencia bajo la cual se distribuye el código. | **Licencia (AGPL-3.0)** |

**Tecnología principal:** Python

---

## 💻 Requisitos y Configuración

Para ejecutar los proyectos, necesitarás **Python 3.x** y las librerías especificadas en el archivo `requirements.txt`.

### 🛠️ Instalación de Dependencias

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/j21david/ia-projects.git](https://github.com/j21david/ia-projects.git)
    cd ia-projects
    ```

2.  **Crear el archivo `requirements.txt`:**
    Asegúrate de que este archivo esté presente en la raíz del proyecto con el siguiente contenido:
    ```
    python-dotenv
    openai>=1.68.2
    openai-agents>=0.0.15
    sendgrid
    brevo_python
    ```

3.  **Instalar las librerías:**
    ```bash
    pip install -r requirements.txt
    ```

### ⚙️ Variables de Entorno

La librería `python-dotenv` se utiliza para gestionar las claves de API. Crea un archivo llamado **`.env`** en la raíz del repositorio y añade tus credenciales.

**Ejemplo de archivo `.env`:**

```dotenv
# Clave para el modelo de lenguaje (requerido por openai)
OPENAI_API_KEY="tu_clave_de_openai"

# Claves para servicios de correo (usados por algunos agentes)
SENDGRID_API_KEY="tu_clave_de_sendgrid"
BREVO_API_KEY="tu_clave_de_brevo"
