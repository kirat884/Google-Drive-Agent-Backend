# import uvicorn
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from agent import get_agent_response
#
# app = FastAPI(title="Drive Search Agent")
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# class ChatRequest(BaseModel):
#     message: str
#     history: list = []
#
# @app.get("/")
# def root():
#     return {"status": "Drive Agent is running!"}
#
# @app.post("/chat")
# def chat(req: ChatRequest):
#     response = get_agent_response(req.message, req.history)
#     return {"reply": response}
#
#
# if __name__ == "__main__":
#     uvicorn.run(app, host="localhost", port=4000)
import uvicorn
# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import ask_agent


app = FastAPI(
    title="Google Drive File Assistant",
    description="FastAPI backend for Google Drive LangChain Agent",
    version="1.0.0"
)


# CORS middleware allows frontend to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # okay for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    # history: Optional[List[dict]] = []



class ChatResponse(BaseModel):
    response: str


@app.get("/")
def home():
    return {
        "message": "Google Drive Agent API is running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        answer = ask_agent(request.message)

        return ChatResponse(response=answer)

    except Exception as e:
        return ChatResponse(response=f"Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=4000)