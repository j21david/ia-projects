from dotenv import load_dotenv
import os
from openai import OpenAI, AsyncOpenAI
from agents import Agent, Runner, trace, function_tool,OpenAIChatCompletionsModel
from openai.types.responses import ResponseTextDeltaEvent
from typing import Dict
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import asyncio
import brevo_python


@function_tool
def send_html_email(subject: str, html_body: str) -> Dict[str, str]:
    """ Envía un correo electrónico con el asunto y el cuerpo HTML a todos los clientes potenciales de ventas """
    cfg = brevo_python.Configuration()
    cfg.api_key["api-key"] = os.getenv("BREVO_API_KEY")

    api = brevo_python.TransactionalEmailsApi(brevo_python.ApiClient(cfg))
    email = brevo_python.SendSmtpEmail(
        sender={"email": "test@gmail.com"},
        to=[{"email": "test@gmail.com"}],
        subject=subject,
        html_content=html_body,
    )
    api.send_transac_email(email)
    return {"status": "success"}

async def main():

    load_dotenv(override=True)

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
    MODEL_NAME='gemini-2.5-flash-lite'

    gemini_client = AsyncOpenAI(base_url=BASE_URL, api_key=os.getenv("GEMINI_API_KEY"))

    custom_model = OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=gemini_client)
    
    instructions1 = "Eres un agente de ventas que trabaja para ComplAI, \
        una empresa que ofrece una herramienta SaaS para garantizar el cumplimiento de SOC2\
        y prepararse para auditorías, impulsada por IA. Redactas correos electrónicos en frío profesionales y serios."

    instructions2 = "Eres un agente de ventas con sentido del humor y atractivo \
        que trabaja para ComplAI, una empresa que ofrece una herramienta SaaS para \
        garantizar el cumplimiento de SOC2 y prepararse para auditorías, impulsada por IA. \
        Redactas correos electrónicos en frío ingeniosos y atractivos que probablemente obtengan respuesta."

    instructions3 = "Eres un agente de ventas muy activo que trabaja para ComplAI, \
        una empresa que ofrece una herramienta SaaS para garantizar el cumplimiento de SOC2\
        y prepararse para auditorías, impulsada por IA. Redactas correos electrónicos en frío concisos y directos."

    sales_agent1 = Agent(
            name="Agente de ventas profesional",
            instructions=instructions1,
            model=custom_model
    )
    sales_agent2 = Agent(
            name="Agente de ventas atractivo",
            instructions=instructions2,
            model=custom_model
    )

    sales_agent3 = Agent(
            name="Agente de ventas ocpado",
            instructions=instructions3,
            model=custom_model
    )
    sales_picker = Agent(
    name="sales_picker",
    instructions="Elige el mejor correo electrónico de ventas en frío entre las opciones disponibles. \
        Imagina que eres un cliente y elige el que probablemente te responda. \
        No des explicaciones; responde solo con el correo electrónico seleccionado.",
    model=custom_model
    )
    description = "Escribe un correo electrónico de ventas en frío"

    tool1 = sales_agent1.as_tool(tool_name="sales_agent1", tool_description=description)
    tool2 = sales_agent2.as_tool(tool_name="sales_agent2", tool_description=description)
    tool3 = sales_agent3.as_tool(tool_name="sales_agent3", tool_description=description)

    tools = [tool1, tool2, tool3]


    subject_instructions = "Puedes escribir un asunto para un correo electrónico de ventas en frío. \
    Se te proporciona un mensaje y necesitas escribir un asunto para un correo electrónico que probablemente obtenga respuesta."

    html_instructions = "Puedes convertir un cuerpo de correo electrónico de texto a un cuerpo de correo electrónico HTML. \
        Se te proporciona un cuerpo de correo electrónico de texto que puede tener algún markdown \
        y necesitas convertirlo a un cuerpo de correo electrónico HTML con un diseño simple, claro y atractivo."

    subject_writer = Agent(name="Escritor de asunto de correo electrónico", instructions=subject_instructions, model=custom_model)
    subject_tool = subject_writer.as_tool(tool_name="subject_writer", 
                                          tool_description="Escribe un asunto para un correo electrónico de ventas en frío")

    html_converter = Agent(name="Conversor de cuerpo de correo electrónico HTML", instructions=html_instructions, model=custom_model)
    html_tool = html_converter.as_tool(tool_name="html_converter",
                                       tool_description="Convierte un cuerpo de correo electrónico de texto a un cuerpo de correo electrónico HTML")

    tools_mail = [subject_tool, html_tool, send_html_email]

    instructions ="Eres un formateador y remitente de correos electrónicos. \
    Recibes el cuerpo de un correo electrónico para enviarlo. \
    Primero usas la herramienta subject_writer para escribir un asunto para el correo electrónico, \
    luego usas la herramienta html_converter para convertir el cuerpo a HTML. \
    Finalmente, usas la herramienta send_html_email para enviar el correo electrónico con el asunto y el cuerpo HTML."


    emailer_agent = Agent(
        name="Email Manager",
        instructions=instructions,
        tools=tools_mail,
        model=custom_model,
        handoff_description="Convierte un email a HTML y lo envía")

    # Aqui le pasamos el control al emailer_agent
    handoffs = [emailer_agent]

    sales_manager_instructions = "Eres un gerente de ventas que trabaja para ComplAI. Utilizas las herramientas que se te proporcionan para generar correos electrónicos de ventas en frío. \
    Nunca generas correos electrónicos de ventas tú mismo; siempre utilizas las herramientas. \
    Pruebas las 3 herramientas del agente de ventas al menos una vez antes de elegir la mejor. \
    Puedes usar las herramientas maximo 3 veces veces si no estás satisfecho con los resultados del primer intento. \
    Seleccionas el mejor correo electrónico usando tu propio criterio sobre cuál será más efectivo. \
    Después de elegir el correo electrónico, transfieres al agente Email Manager para formatear y enviar el correo."
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
    MODEL_NAME='gemini-2.5-flash'

    gemini_client = AsyncOpenAI(base_url=BASE_URL, api_key=os.getenv("GEMINI_API_KEY"))

    gemini_model = OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=gemini_client)

    sales_manager = Agent(
        name="Manager de ventas",
        instructions=sales_manager_instructions,
        tools=tools,
        handoffs=handoffs,
        model=gemini_model)
    
    message = "Envía un correo electrónico de ventas en frío dirigido a 'Estimado director ejecutivo'"
    
    with trace("Automated SDR"):
        result = await Runner.run(sales_manager, message)
    
    print(result.final_output)

if __name__ == "__main__":
 

    asyncio.run(main())
