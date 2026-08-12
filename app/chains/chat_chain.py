from app.services.llm import llm_with_tools
from app.prompts.chat_prompt import chat_prompt


def get_llm_response(message: str):

    prompt_value = chat_prompt.invoke(
        {
            "message": message
        }
    )

    response = llm_with_tools.invoke(
        prompt_value
    )

    return response

def stream_llm_response(message: str):

    prompt_value = chat_prompt.invoke(
        {
            "message": message
        }
    )

    for chunk in llm_with_tools.stream(
        prompt_value
    ):
        yield chunk