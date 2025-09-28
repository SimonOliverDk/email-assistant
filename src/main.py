from fastapi import FastAPI
from pydantic import BaseModel
from agent import email_assistant


app = FastAPI()

class InputRequest(BaseModel):
    input_text: str

@app.post("/invoke-agent")
async def invoke_agent(req: InputRequest):
    #istantiate the result from email assistant workflow in agent.py
    result = email_assistant.invoke({"email_input": req.input_text})
    #return results to the API
    return {
        "classificaion": result.get("classification_decision"),
        "proposal": result.get("proposal"),
        "messages": [m.dict() if hasattr(m, "dict") else m for m in result.get("messages", [])]
    }