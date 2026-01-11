import os
import streamlit as st
import random
import time
import pandas as pd
from sqlalchemy import create_engine, inspect
from langchain_community.utilities import SQLDatabase
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from typing_extensions import TypedDict
from typing_extensions import Annotated
from dotenv import load_dotenv
import shared_funcs as sf

load_dotenv()


class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str


class QueryOutput(TypedDict):
    """Generated SQL query."""

    query: Annotated[str, ..., "Syntactically valid SQL query."]


def write_query(state: State):
    """Generate SQL query to fetch information."""
    prompt = query_prompt_template.invoke(
        {
            "dialect": db.dialect,
            "top_k": 100,
            "table_info": db.get_table_info(),
            "input": state["question"],
        }
    )
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)
    return {"query": result["query"]}


def execute_query(state: State):
    """Execute SQL query."""
    execute_query_tool = QuerySQLDatabaseTool(db=db)
    return {"result": execute_query_tool.invoke(state["query"])}


def generate_answer(state: State):
    """Answer question using retrieved information as context."""
    prompt = (
        "Given the following user question, corresponding SQL query, "
        "and SQL result, answer the user question.\n\n"
        f"Question: {state['question']}\n"
        f"SQL Query: {state['query']}\n"
        f"SQL Result: {state['result']}"
    )
    response = llm.invoke(prompt)
    return {"answer": response.content}


system_message = """
Given an input question, create a syntactically correct {dialect} query to
run to help find the answer. Unless the user specifies in his question a
specific number of examples they wish to obtain, always limit your query to
at most {top_k} results. You can order the results by a relevant column to
return the most interesting examples in the database.

Never query for all the columns from a specific table, only ask for a the
few relevant columns given the question.

Pay attention to use only the column names that you can see in the schema
description. Be careful to not query for columns that do not exist. Also,
pay attention to which column is in which table.

Only use the following tables:
{table_info}
"""

db_select = "apple_weatherkit"
llm_select = "gemini-3-pro-preview"
model_provider = "google_genai"
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
db_path = sf.database_path(db_select)
db = SQLDatabase.from_uri(f"{db_path}")
llm = init_chat_model(llm_select, model_provider=model_provider)

engine = create_engine(db_path)

@st.cache_resource
def get_db_connection():
    """Establish and cache the database connection."""
    return engine

conn = get_db_connection()

st.set_page_config(page_title="NL to SQL Web App", layout="wide")
st.write("A Web Application that integrates a Google Gemini Large Language Model with a SQL Relational Database")
st.caption(f"This Web App is connected to the {llm_select} latest version LLMs. Enjoy!!")
st.sidebar.header(f"Database Information:")
st.sidebar.markdown(f"- {db_select}")

try:
    inspector = inspect(conn)
    table_names = inspector.get_table_names()
    
    st.sidebar.subheader("Available Tables:")
    for table in table_names:
        st.sidebar.markdown(f"- {table}")

    if table_names:
        selected_table = st.sidebar.selectbox("Select a table to view schema:", table_names)
    else:
        st.sidebar.info("No tables found in the database.")

except Exception as e:
    st.sidebar.error(f"Error connecting to DB: {e}")
    table_names = []
    selected_table = None

st.sidebar.markdown("**Connection Status:** Connected")
st.sidebar.write(f"**Database Dialect:** {conn.dialect.name}")

if selected_table:
    st.subheader(f"Schema for Table: `{selected_table}`")
    # Query the table schema
    columns = inspector.get_columns(selected_table)
    schema_df = pd.DataFrame(columns)
    st.dataframe(schema_df)

    st.subheader(f"First 10 Rows of `{selected_table}`")
    # Query data and display
    data_df = pd.read_sql_query(f"SELECT * FROM {selected_table} LIMIT 10", conn)
    st.dataframe(data_df)
elif table_names:
    st.info("Select a table from the sidebar to view its details.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Let's start chatting! 👇"}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What would you like to discover about the Database?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        user_prompt = "Question: {input}"
        query_prompt_template = ChatPromptTemplate(
            [("system", system_message), ("user", user_prompt)]
            )
        question = {"question": prompt}
        query = write_query({"question": question})
        result = execute_query({"query": query})
        answer = generate_answer({"question": question, "query": query, "result": result})
        full_query = query['query']
        full_response = answer['answer'][0]['text']
        message_placeholder.markdown(full_response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_query})
    st.session_state.messages.append({"role": "assistant", "content": full_response})
