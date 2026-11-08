import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from mcp_server import list_tables, describe_table, run_query
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

print("Connecting to DB:", os.getenv("DB_NAME"))

@tool
def calculate(expression: str) -> str:
    """Useful for performing math calculations. Input should be a mathematical expression like '1984 / 59000000'."""
    try:
        return str(eval(expression))
    except Exception as e:
        return str(e)

tools = [list_tables, describe_table, run_query, calculate]

llm = ChatOpenAI(
    model= "gpt-4o",
    temperature=0.1
)

system_prompt = """You are an autonomous PostgreSQL Data Analyst expert in complex SQL joins and multi-table analysis.

CRITICAL RULES:
1. INTELLIGENT JOINS: Always run `list_tables` and `describe_table` first to verify the exact schema and foreign keys before attempting any queries. Never guess column names. If joining without a formal key, verify that both columns contain matching values before executing.
2. VERIFY COLUMN CONTEXT: Read the table schemas carefully before querying. If asked for a specific metric, ensure you are querying the correct table by analyzing the full schema context, rather than relying on a generic column name match.
3. EXACT STRING MATCHING (CASE SENSITIVITY): NEVER guess exact string values for filtering text. Text in PostgreSQL is case-sensitive. Before counting or filtering text columns, either use `get_unique_values` (or run a `SELECT DISTINCT column_name`), or use `ILIKE` for case-insensitive matching.
4. HANDLE MULTI-STEP QUESTIONS: If a question has multiple parts, or requires JOINs across multiple tables, break it down. Execute the necessary queries step-by-step, verify intermediate results, and synthesize the final answer carefully.
5. MISSING RECORDS (ANTI-JOIN): To find missing records (e.g., "sensors with no readings"), ALWAYS use a `LEFT JOIN` combined with a `WHERE ... IS NULL` clause. NEVER use `NOT IN` or subqueries for this, as they cause errors and infinite loops.
6. SELF-CORRECTION AND EMPTY RESULTS: If a SQL query fails with an ERROR, DO NOT run the exact same query again. Analyze the error, check relationships, change syntax, and retry. HOWEVER, if a query runs successfully but returns empty results (0 rows, None, or []), THIS IS NOT AN ERROR. Do not retry or change the query. Simply accept the empty result and formulate your final JSON response stating that no matching records were found.
7. VISUALIZATION: If the user asks for a chart, graph, or visualization, you MUST populate the "data" array with objects containing x_col and y_col, and fill the "visualization" object with type ("bar", "pie", or "line"), x, y, and title. If no chart is requested, set "data": [] and "visualization": null.

FINAL OUTPUT:
When you have the accurate answer, output a clear natural response answering the user. 
Then, output a valid JSON object (WITHOUT markdown code blocks) at the very end of your response containing exactly these keys:
- "step1_result": the direct numerical result or findings.
- "step2_result": null or additional metrics if relevant.
- "answer": your clear text answer to the user.
- "data": an array of objects with x_col and y_col or [].
- "visualization": an object with type, x, y, and title, or null.
"""
memory = MemorySaver()
agent_executor = create_react_agent(llm, tools, prompt=system_prompt, checkpointer=memory)
