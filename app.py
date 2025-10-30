import streamlit as st
from neo4j import GraphDatabase
import pandas as pd

# --- NEO4J CONNECTION DETAILS ---
# IMPORTANT: Replace with your credentials
URI = st.secrets["NEO4J_URI"]
USER = "neo4j"
PASSWORD = st.secrets["NEO4J_PASSWORD"]

# --- HELPER FUNCTIONS ---

@st.cache_resource
def get_driver():
    """Establishes connection to Neo4j and returns the driver object."""
    try:
        driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
        driver.verify_connectivity()
        print("Connected to Neo4j")
        return driver
    except Exception as e:
        st.error(f"Failed to connect to Neo4j: {e}")
        return None

def run_query(driver, query, params={}):
    """Runs a Cypher query and returns the results as a Pandas DataFrame."""
    with driver.session() as session:
        result = session.run(query, params)
        return pd.DataFrame([r.data() for r in result])

@st.cache_data
def get_all_movie_titles(_driver):
    """Fetches all movie titles from Neo4j, caches the result."""
    print("Caching all movie titles...")
    query = "MATCH (m:Movie) RETURN m.title AS title ORDER BY title"
    df = run_query(_driver, query)
    return df['title'].tolist()

# --- DEFINE THE QUERIES ---

# Basic Semantic Query (Shared Actors & Genres)
basic_rec_query = """
MATCH (m:Movie) WHERE toLower(m.title) = toLower($title)
MATCH (m)-[:HAS_GENRE]->(g:Genre)
MATCH (rec:Movie)-[:HAS_GENRE]->(g)
WHERE m <> rec
WITH m, rec, count(g) AS sharedGenres
MATCH (m)<-[:ACTED_IN]-(a:Actor)-[:ACTED_IN]->(rec)
WITH rec, sharedGenres, count(a) AS sharedActors
RETURN rec.title AS Recommendation, sharedGenres, sharedActors
ORDER BY sharedActors DESC, sharedGenres DESC
LIMIT 10
"""

# --- BUILD THE STREAMLIT APP ---

st.title("🎬 Movie Recommendation Engine")
st.write("Powered by Neo4j Knowledge Graph")

# Get the Neo4j driver
driver = get_driver()

if driver:
    # 1. Fetch the full list of movies
    movie_list = get_all_movie_titles(driver)
    
    # 2. Add a "placeholder" at the top of the list
    movie_list.insert(0, "--- Type or select a movie ---")

    # 3. Create the selectbox (this replaces st.text_input)
    movie_title = st.selectbox(
        "Enter a movie title you like (e.g., Inception, The Matrix, Avatar):",
        options=movie_list
    )

    # Check if a real movie was selected 
    if movie_title != "--- Type or select a movie ---":
        # --- Basic Recommendations ---
        st.subheader("Basic Recommendations (Shared Actors & Genres)")
        with st.spinner("Finding recommendations based on actors and genres..."):
            basic_df = run_query(driver, basic_rec_query, {'title': movie_title})
            if basic_df.empty:
                st.write("No basic recommendations found.")
            else:
                basic_df.index += 1 # Start index from 1
                st.dataframe(basic_df, use_container_width=True)
         

    # Clean up the driver connection when the app closes
    # This part might not be strictly necessary for Streamlit, but it's good practice.
    # driver.close() # Caching handles this