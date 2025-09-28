from dotenv import load_dotenv
load_dotenv(".env")

from langchain.chat_models import init_chat_model
from schemas import State
from langgraph.types import Command
from typing_extensions import Literal
from utils import parse_email, format_email_markdown
from prompts import triage_system_prompt, default_background, triage_user_prompt, default_triage_instructions
from langgraph.graph import StateGraph, START, END



#Initialize the llm
llm = init_chat_model("openai:gpt-4.1", temperature=0)
llm_router = llm.with_structured_output(State)

def triage_router(state: State) -> Command[Literal["response_agent", "__end__"]]:
    
    #Get the email input
    email_input = state.get("email_input")
    
    #parse the email input in a structured format author, to, subject, email_thread
    parsed = parse_email(email_input)
    if not parsed: 
        raise ValueError("Could not parse email")
    author, to, subject, email_thread = parsed

    #Create the system prompt for triaging
    system_prompt = triage_system_prompt.format(
        background = default_background,
        triage_instructions = default_triage_instructions
    )
    
    #Create the user prompt for triaging
    user_prompt = triage_user_prompt.format(
        author=author, to=to, subject=subject, email_thread=email_thread
    )

    #Run the router LLM
    result = llm_router.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])
    
    #Add the returned classification to final classification variable
    classification = result.classification_decision

    #Format the email into a readable format
    email_markdown = format_email_markdown(subject, author, to, email_thread)

    #return message and perform actions based on the classification
    if classification == "respond":
            print("Classification: RESPOND - This email requires a response")
            goto = "response_agent"
            update = {
                "classification_decision": result.classification,
                "messages": [{"role": "user", "content": f"Respond to the email: {email_markdown}"}],
            }
    elif classification == "notify":
         print("Classification: NOTIFY - This email requires a response, but needs human intervention")
         return Command(
              goto="__end__",
              update={
                   "classification_decision": "notify",
                   "proposal": {
                        "to": author,
                        "subject": f"Re: {subject or 'Your Request'}",
                        "content": "Thanks for your message. We'll follow up with details shortly.",
                        "reason": "Requires human review."
                   }
              }
         )
    else:
         return Command(
              goto="__end__", 
              update={"classification_decision": "ignore"}
         )

def response_agent(state: State):
     #Build reply 
     last_msg = state["messages"][-1]["content"]
     return {"messages": [{"role": "assistant", "content": f"Auto-reply draft: {last_msg}"}]}

#Build graph
workflow = StateGraph(State)
workflow.add_node("triage_router", triage_router)
workflow.add_node("response_agent", response_agent)

workflow.add_edge(START, "triage_router")
workflow.add_edge("response_agent", END)

email_assistant = workflow.compile()








