import streamlit as st
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from google import genai

# ---- Load environment variables ----
load_dotenv()
client = genai.Client()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

# ---- Neo4j connection helper ----
def run_cypher(cypher_query):
    with GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD)) as driver:
        with driver.session() as session:
            result = session.run(cypher_query)
            data = result.data()

            # If the query returns only one column, extract the values
            if data and len(data[0].keys()) == 1:
                key = list(data[0].keys())[0]
                values = [row[key] for row in data]
            else:
                values = data
    return values

# ---- LLM helper: Generate Cypher ----
def generate_cypher(user_question):
    prompt = f"""
    You are an AI that converts natural language questions into Cypher queries.

    IMPORTANT RULES:
    - Output ONLY the Cypher query.
    - Follow the schema, relationships, and properties.
    - No explanation, no markdown, no code blocks, no extra text, no backticks.
    - The query must return only string values.
    - The last line MUST be a RETURN <string property> expression.

    Schema:
    (:Movie)-[:IN_GENRE]->(:Genre)
    (:Person)-[:DIRECTED]->(:Movie)
    (:Person)-[:ACTED_IN]->(:Movie)

    Relationships:
    "ACTED_IN"
    "DIRECTED"
    "PRODUCED"
    "WROTE"
    "FOLLOWS"
    "REVIEWED"

    Properties:
    "Movie.title"
    "Movie.released"
    "Movie.tagline"
    "Person.name"
    "Person.born"

    User question: "{user_question}"
    Return ONLY the Cypher query.
    """
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    cypher_query = response.text.strip("```").strip()
    return cypher_query

# ---- LLM helper: Summarize results ----
def summarize_results(user_question, values):
    prompt = f"""
You are an AI assistant. Summarize database results concisely.
User question: "{user_question}"
Database result: "{values}"
Write all the values with a short, clear explanation (1-2 lines).
"""
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text.strip("```").strip()

# ---- Streamlit UI ----
st.title("🎬 Movie Graph Assistant")
st.write("Ask questions about the movies. The system generates Cypher, queries Neo4j, and gives concise answer.")

user_question = st.text_area("Ask your question:")

if st.button("Submit"):
    if not user_question.strip():
        st.warning("Please enter a question.")
    else:
        # Step 1: Generate Cypher
        cypher_query = generate_cypher(user_question)
        st.code(cypher_query, language="cypher")

        # Step 2: Run query on Neo4j
        try:
            values = run_cypher(cypher_query)
            st.success("Query executed successfully!")
            st.write("Raw Output:", values)
        except Exception as e:
            st.error(f"Query execution failed: {e}")
            values = None

        summary = summarize_results(user_question, values)
        st.markdown(f"**Answer:** {summary}")
