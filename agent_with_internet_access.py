from dotenv import load_dotenv
import os
from openai import OpenAI, AsyncOpenAI
from agents import Agent, Runner, trace, function_tool,OpenAIChatCompletionsModel, input_guardrail, GuardrailFunctionOutput, WebSearchTool
from openai.types.responses import ResponseTextDeltaEvent
from agents.model_settings import ModelSettings
from typing import Dict
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import asyncio
import brevo_python
from pydantic import BaseModel, Field
import http.client
import json

@function_tool
def send_html_email( html_body: str) -> Dict[str, str]:
    """ Envía un correo electrónico con el asunto y el cuerpo HTML a todos los clientes potenciales de ventas """
    cfg = brevo_python.Configuration()
    cfg.api_key["api-key"] = os.getenv("BREVO_API_KEY")

    api = brevo_python.TransactionalEmailsApi(brevo_python.ApiClient(cfg))
    email = brevo_python.SendSmtpEmail(
        sender={"email": "test@gmail.com"},
        to=[{"email": "test@gmail.com"}],
        subject="subject: Informe de investigación",
        html_content=html_body,
    )
    api.send_transac_email(email)
    return {"status": "success"}


@function_tool
def search_serper(query: str) -> Dict[str, str]:
    """
    Performs a Google search using the Serper API.

    Args:
        query (str): The search query to send to Serper.

    Returns:
        Dict[str, str]: A dictionary with the search result as a JSON string.
    """
    conn = http.client.HTTPSConnection("google.serper.dev")
    api_key= os.getenv("SERPER_API_KEY")
    
    payload = json.dumps({
        "q": query
    })
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    conn.request("POST", "/search", payload, headers)
    res = conn.getresponse()
    data = res.read()
    
    return {"result": data.decode("utf-8")}

class NameCheckOutput(BaseModel):
    is_name_in_message: bool
    name: str

# Usamos Pydantic para definir el esquema de nuestra respuesta; esto se conoce como "Salidas Estructuradas".    
class WebSearchItem(BaseModel):
        reason: str = Field(description="Tu razonamiento de por qué esta búsqueda es importante para la consulta.")
    
        query: str = Field(description="El término de búsqueda para usar para la búsqueda web.")
    
class WebSearchPlan(BaseModel):
        searches: list[WebSearchItem] = Field(description="Una lista de búsquedas web a realizar para responder la consulta.")

class ReportData(BaseModel):
    short_summary: str = Field(description="Un resumen de 2-3 párrafos de los resultados.")

    markdown_report: str = Field(description="El informe final")

    follow_up_questions: list[str] = Field(description="Temas sugeridos para investigar más")        
        

async def main():
    INSTRUCTIONS = "Eres un asistente de investigación. Dado un término de búsqueda, buscas en la web ese término y \
    producí una descripción concisa de los resultados. La descripción debe tener 2-3 párrafos y menos de 300 \
    palabras. Captura los puntos principales. Escribe de manera concisa, no es necesario tener frases completas o buena \
    gramática. Esto será consumido por alguien que está sintetizando un informe, por lo que es vital que captures el \
    esencia y ignores cualquier fluff. No incluyas ningún comentario adicional más que la descripción en sí."
    
    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    google_api_key = os.getenv('GEMINI_API_KEY')
    
    gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)
    gemini_model = OpenAIChatCompletionsModel(model="gemini-2.5-flash-lite", openai_client=gemini_client)
    
    
    
    search_agent = Agent(
        name="Agente de búsqueda",
        instructions=INSTRUCTIONS,
        tools=[search_serper],
        model=gemini_model,
        model_settings=ModelSettings(tool_choice="required"),
    )

    ## Agente de Planificacion
    HOW_MANY_SEARCHES = 3

    INSTRUCTIONS = f"Eres un asistente de investigación útil. Dado un término de búsqueda, \
    produce un conjunto de búsquedas web para realizar para responder la consulta. \
    Salida: {HOW_MANY_SEARCHES} términos para consultar."


    planner_agent = Agent(
        name="Agente de planificación",
        instructions=INSTRUCTIONS,
        model=gemini_model,
        output_type=WebSearchPlan,
    )
    ## Agente de Correo Electrónico
    INSTRUCTIONS = """Eres capaz de enviar un correo electrónico HTML bien formateado basado en un informe detallado.
    Se te proporcionará un informe detallado. Debes usar tu herramienta para enviar un correo electrónico, proporcionando el 
    informe convertido en HTML limpio, bien presentado con un asunto adecuado."""

    email_agent = Agent(
        name="Agente de correo electrónico",
        instructions=INSTRUCTIONS,
        tools=[send_html_email],
        model=gemini_model,
    )  

    ## Agente de Informe Final
    INSTRUCTIONS = (
        "Eres un investigador senior encargado de escribir un informe coherente para una consulta de investigación. "
        "Se te proporcionará la consulta original y algunas investigaciones iniciales realizadas por un asistente de investigación.\n"
        "Primero, debes elaborar un esquema para el informe que describa la estructura y "
        "flujo del informe. Luego, genera el informe y devuelve ese como tu salida final.\n"
        "La salida final debe estar en formato markdown, y debe ser larga y detallada "
        "para 5-10 páginas de contenido, al menos 1000 palabras."
    )
    
    writer_agent = Agent(
        name="Agente de escritura",
        instructions=INSTRUCTIONS,
        model=gemini_model,
        output_type=ReportData,
    )  

    async def plan_searches(query: str):
        """ Utilice planner_agent para planificar qué búsquedas ejecutar para la consulta """
        print("Planificando búsquedas...")
        result = await Runner.run(planner_agent, f"Consulta: {query}")
        print(f"Se realizarán {len(result.final_output.searches)} búsquedas")
        return result.final_output

    async def perform_searches(search_plan: WebSearchPlan):
        """ Llama a search() para cada elemento en el plan de búsqueda """
        print("Buscando...")
        tasks = [asyncio.create_task(search(item)) for item in search_plan.searches]
        results = await asyncio.gather(*tasks)
        print("Búsqueda finalizada")
        return results

    async def search(item: WebSearchItem):
        """ Usa el agente de búsqueda para ejecutar una búsqueda web para cada elemento en el plan de búsqueda """
        input = f"Término de búsqueda: {item.query}\nRazón para buscar: {item.reason}"
        result = await Runner.run(search_agent, input)
        return result.final_output

    async def write_report(query: str, search_results: list[str]):
        """ Usa el agente de escritura para escribir un informe basado en los resultados de la búsqueda """
        print("Pensando sobre el informe...")
        input = f"Consulta original: {query}\nResultados de búsqueda resumidos: {search_results}"
        result = await Runner.run(writer_agent, input)
        print("Informe finalizado")
        return result.final_output

    async def send_email(report: ReportData):
        """ Usa el agente de correo electrónico para enviar un correo electrónico con el informe """
        print("Escribiendo correo electrónico...")
        result = await Runner.run(email_agent, report.markdown_report)
        print("Correo electrónico enviado")
        return report

    query = "Últimos frameworks de agentes de IA en 2025"
    
    with trace("Investigación"):
        print("Iniciando investigación...")
        search_plan = await plan_searches(query)
        #print(search_plan)
        search_results = await perform_searches(search_plan)
        #print(search_results)
        report = await write_report(query, search_results)
        #print(report)
        await send_email(report)  
        print("¡Felicidades!")


if __name__ == "__main__":
 

    asyncio.run(main())
