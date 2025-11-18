from dotenv import load_dotenv
import os
from openai import OpenAI, AsyncOpenAI
from agents import Agent, Runner, trace, function_tool,OpenAIChatCompletionsModel, input_guardrail, GuardrailFunctionOutput
from openai.types.responses import ResponseTextDeltaEvent
from typing import Dict
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import asyncio
import brevo_python
from pydantic import BaseModel

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

class NameCheckOutput(BaseModel):
    is_name_in_message: bool
    name: str

async def main():

    load_dotenv(override=True)

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
    MODEL_NAME='gemini-2.5-flash-lite'

    gemini_client = AsyncOpenAI(base_url=BASE_URL, api_key=os.getenv("GEMINI_API_KEY"))

    custom_model = OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=gemini_client)
    
    instructions1 = "Eres un agente de ventas que trabaja para ComplAI, \
        una empresa que ofrece una herramienta SaaS para garantizar el cumplimiento de SOC2\
        y prepararse para auditorías, impulsada por IA. Redactas correos electrónicos en frío profesionales y serios."

    sales_agent1 = Agent(
            name="Agente de ventas profesional",
            instructions=instructions1,
            model=custom_model
    )

    description = "Escribe un correo electrónico de ventas en frío"

    tool1 = sales_agent1.as_tool(tool_name="sales_agent1", tool_description=description)

    toolTest = [tool1, send_html_email]



    guardrail_agent = Agent( 
        name="Revisión de nombre",
        instructions="Revisa si el usuario está incluyendo el nombre personal de alguien en lo que quiere que hagas.",
        output_type=NameCheckOutput,
        model=custom_model
    )

    @input_guardrail
    async def guardrail_against_name(ctx, agent, message):
        result = await Runner.run(guardrail_agent, message, context=ctx.context)
        is_name_in_message = result.final_output.is_name_in_message
        return GuardrailFunctionOutput(output_info={"found_name": result.final_output},tripwire_triggered=is_name_in_message)

    sales_manager_instructions = "Eres un gerente de ventas que trabaja para ComplAI. Utilizas las herramientas que se te proporcionan para generar correos electrónicos de ventas en frío. \
    Nunca generas correos electrónicos de ventas tú mismo; siempre utiliza la herramienta. \
    Después de usar la herramienta que genera el correo electrónico, Convierte un cuerpo de correo electrónico de texto a un cuerpo de correo electrónico HTML y Escribe un asunto para un correo electrónico de ventas en frío.\
     Finalmente, usas la herramienta send_html_email para enviar el correo electrónico con el asunto y el cuerpo HTML.   "
    
    sales_manager = Agent(
        name="Manager de ventas",
        instructions=sales_manager_instructions,
        tools=toolTest,
        model=custom_model,
        input_guardrails=[guardrail_against_name])
    
    message = "Envía un correo electrónico de ventas en frío dirigido a 'Estimado director ejecutivo' desde Alice"
    
    with trace("Automated SDR"):
        result = await Runner.run(sales_manager, message)
    
    print(result.final_output)

if __name__ == "__main__":
 

    asyncio.run(main())
