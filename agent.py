
from dotenv import load_dotenv

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq

from drive_tool import search_drive_files


load_dotenv()


SYSTEM_PROMPT = """You are a helpful Google Drive file assistant. 
Your job is to help users find files in their Google Drive.

When a user asks to find a file, you MUST use the search_drive_files tool.
Translate the user's natural language request into a proper Google Drive query string.

Google Drive query examples:
- Find PDF files → mimeType = 'application/pdf'
- Find files named report → name contains 'report'
- Find files with word invoice → fullText contains 'invoice'
- Find Google Sheets → mimeType = 'application/vnd.google-apps.spreadsheet'
- Find recent files → modifiedTime > '2024-01-01T00:00:00'
- Find all files → mimeType != 'application/vnd.google-apps.folder'
- List all files → mimeType != 'application/vnd.google-apps.folder'
- Name all files → mimeType != 'application/vnd.google-apps.folder'
- Show everything in Drive → mimeType != 'application/vnd.google-apps.folder'
- Combine: name contains 'budget' and mimeType = 'application/vnd.google-apps.spreadsheet'

IMPORTANT RULES:
Never call the tool with an empty contains query like:
name contains ''

That is invalid.

If the user asks for all files, list files, name all files, or show everything, use:
mimeType != 'application/vnd.google-apps.folder'

When the search_drive_files tool returns results, you MUST show the exact file names, file types, modified dates, and links to the user.
Do not only say "I found the files".
Always include the actual search results from the tool response.

Always be conversational and friendly. After showing results, ask if they need anything else.
If no files are found, suggest trying different keywords.
"""
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

tools = [search_drive_files]

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

agent = create_tool_calling_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    return_intermediate_steps=True,
    handle_parsing_errors=True
)


def ask_agent(user_input: str):
    response = agent_executor.invoke(
        {
            "input": user_input
        }
    )

    # This is the final LLM message
    final_answer = response.get("output", "")

    # These are the actual tool calls + tool outputs
    intermediate_steps = response.get("intermediate_steps", [])

    # If tool was used, return actual Google Drive search result
    if intermediate_steps:
        tool_output = intermediate_steps[-1][1]

        return str(tool_output)

    # If no tool was used, return normal answer
    return final_answer


if __name__ == "__main__":
    print("Google Drive Agent started. Type 'exit' to stop.\n")

    while True:
        user_question = input("You: ")

        if user_question.lower() in ["exit", "quit", "q"]:
            print("Agent stopped.")
            break

        answer = ask_agent(user_question)

        print("\nAgent:")
        print(answer)
        print("-" * 50)