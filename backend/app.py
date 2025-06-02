import os
import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

import requests
from flask import Flask, send_from_directory, request, jsonify, abort
from dotenv import load_dotenv
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import psycopg2

# Make a change
# Load environment variables
try:
  DB_HOST=os.environ['DB_HOST']
  DB_PORT= int(os.environ['DB_PORT'])
  DB_NAME=os.environ['DB_NAME']
  DB_USER=os.environ['DB_USER']
  DB_PASSWORD=os.environ['DB_PASSWORD']
  API=os.getenv('DB_API')

except:
  logger = logging.getLogger(__name__)
  logger.warning("Using Local Variables")
  load_dotenv(dotenv_path=".env")
  API = os.getenv('DB_API')

# Global variable for the SPARQL endpoint
SEMOPENALEX_SPARQL_ENDPOINT = "https://semopenalex.org/sparql"
app= Flask(__name__, static_folder='build', static_url_path='/')
CORS(app)

def setup_logger():
    """Configure logging with rotating file handler for all levels"""
    # Create logs directory if it doesn't exist
    log_path = "/home/LogFiles" if os.environ.get("WEBSITE_SITE_NAME") else "logs"
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    # Configure logging format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create handlers for different log levels with different storage allocations
    handlers = {
        "debug": RotatingFileHandler(
            os.path.join(log_path, "debug.log"),
            maxBytes=15*1024*1024,  # 10MB
            backupCount=3
        ),
        "info": RotatingFileHandler(
            os.path.join(log_path, "info.log"),
            maxBytes=15*1024*1024,  # 10MB
            backupCount=3
        ),
        "warning": RotatingFileHandler(
            os.path.join(log_path, "warning.log"),
            maxBytes=10*1024*1024,   # 5MB
            backupCount=3
        ),
        "error": RotatingFileHandler(
            os.path.join(log_path, "error.log"),
            maxBytes=5*1024*1024,   # 2MB
            backupCount=3
        ),
        "critical": RotatingFileHandler(
            os.path.join(log_path, "critical.log"),
            maxBytes=2*1024*1024,   # 1MB
            backupCount=3
        )
    }

    # Set levels and formatters for handlers
    handlers["debug"].setLevel(logging.DEBUG)
    handlers["info"].setLevel(logging.INFO)
    handlers["warning"].setLevel(logging.WARNING)
    handlers["error"].setLevel(logging.ERROR)
    handlers["critical"].setLevel(logging.CRITICAL)

    for handler in handlers.values():
        handler.setFormatter(formatter)

    # Get Flask's logger
    logger = logging.getLogger("flask.app")
    logger.setLevel(logging.DEBUG)  # Capture all levels

    # Add handlers to logger
    for handler in handlers.values():
        logger.addHandler(handler)

    return logger

# Initialize logger
logger = setup_logger()

# Add this right after app initialization
app.logger.handlers = logger.handlers
app.logger.setLevel(logger.level)

def execute_query(query, params):
    """
    Utility function to execute a query and fetch results from the database.
    Handles connection and cursor management.
    """
    try:
        with psycopg2.connect(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),            
            database=os.getenv('DB_NAME'),
            sslmode='disable'       
        ) as connection:
            app.logger.debug(f"Executing query: {query} with params: {params}")
            with connection.cursor() as cursor:
                cursor.execute(query, params)                
                results = cursor.fetchall()
                app.logger.info(f"Query executed successfully, returned {len(results)} results")
                return results        
    except Exception as e:
        app.logger.error(f"Database error: {str(e)}")
        return None

def fetch_last_known_institutions(raw_id: str) -> list:
    """
    Make a request to the OpenAlex API to fetch the last known institutions for a given author id.
    The parameter raw_id is the id in the authors table, which has the format "https://openalex.org/author/1234",
    but we only need the last part of the id, i.e., "1234".
    """
    try:
        id = raw_id.split('/')[-1]
        response = requests.get(f"https://api.openalex.org/authors/{id}")
        data = response.json()
        return data.get("last_known_institutions", [])
    except Exception as e:
        logger.error(f"Error fetching last known institutions for id {id}: {str(e)}")
        return []

def get_author_ids(author_name):  
    app.logger.debug(f"Getting author IDs for: {author_name}")
    query = """SELECT get_author_ids(%s);"""
    results = execute_query(query, (author_name,))
    if results:
        app.logger.info(f"Found author IDs for {author_name}")
        return results[0][0]
    app.logger.warning(f"No author IDs found for {author_name}")
    return None

def get_institution_id(institution_name):
    app.logger.debug(f"Getting institution ID for: {institution_name}")
    query = """SELECT get_institution_id(%s);"""
    results = execute_query(query, (institution_name,))
    if results:
        if results[0][0] == {}:
            app.logger.warning(f"No institution ID found for {institution_name}")
            return None
        app.logger.info(f"Found institution ID for {institution_name}")
        return results[0][0]['institution_id']
    app.logger.warning(f"Query returned no results for institution {institution_name}")
    return None

def search_by_author_institution_topic(author_name, institution_name, topic_name):
    app.logger.debug(f"Searching by author, institution, and topic: {author_name}, {institution_name}, {topic_name}")
    author_ids = get_author_ids(author_name)
    if not author_ids:
        app.logger.warning(f"No author IDs found for {author_name}")
        return None
    
    author_id = author_ids[0]['author_id']
    app.logger.debug(f"Using author ID: {author_id}")

    institution_id = get_institution_id(institution_name)
    if institution_id is None:
        app.logger.warning(f"No institution ID found for {institution_name}")
        return None

    query = """SELECT search_by_author_institution_topic(%s, %s, %s);"""
    results = execute_query(query, (author_id, institution_id, topic_name))
    if results:
        app.logger.info("Found results for author-institution-topic search")
        return results[0][0]
    app.logger.warning("No results found for author-institution-topic search")
    return None

def search_by_author_institution(author_name, institution_name):
    app.logger.debug(f"Searching by author and institution: {author_name}, {institution_name}")
    author_ids = get_author_ids(author_name)
    if not author_ids:
        app.logger.warning(f"No author IDs found for {author_name}")
        return None
    
    author_id = author_ids[0]['author_id']
    app.logger.debug(f"Using author ID: {author_id}")

    institution_id = get_institution_id(institution_name)
    if institution_id is None:
        app.logger.warning(f"No institution ID found for {institution_name}")
        return None

    query = """SELECT search_by_author_institution(%s, %s);"""
    results = execute_query(query, (author_id, institution_id))
    if results:
        app.logger.info("Found results for author-institution search")
        return results[0][0]
    app.logger.warning("No results found for author-institution search")
    return None

def search_by_institution_topic(institution_name, topic_name):
    app.logger.debug(f"Searching by institution and topic: {institution_name}, {topic_name}")
    institution_id = get_institution_id(institution_name)
    if institution_id is None:
        app.logger.warning(f"No institution ID found for {institution_name}")
        return None

    query = """SELECT search_by_institution_topic(%s, %s);"""
    results = execute_query(query, (institution_id, topic_name))
    if results:
        app.logger.info("Found results for institution-topic search")
        return results[0][0]
    app.logger.warning("No results found for institution-topic search")
    return None

def search_by_author_topic(author_name, topic_name):
    app.logger.debug(f"Searching by author and topic: {author_name}, {topic_name}")
    author_ids = get_author_ids(author_name)
    if not author_ids:
        app.logger.warning(f"No author IDs found for {author_name}")
        return None
    
    author_id = author_ids[0]['author_id']
    app.logger.debug(f"Using author ID: {author_id}")

    query = """SELECT search_by_author_topic(%s, %s);"""
    results = execute_query(query, (author_id, topic_name))
    if results:
        app.logger.info("Found results for author-topic search")
        return results[0][0]
    app.logger.warning("No results found for author-topic search")
    return None

def search_by_topic(topic_name):
    app.logger.debug(f"Searching by topic: {topic_name}")
    query = """SELECT search_by_topic(%s);"""
    results = execute_query(query, (topic_name,))
    if results:
        app.logger.info(f"Found results for topic search: {topic_name}")
        return results[0][0]
    app.logger.warning(f"No results found for topic: {topic_name}")
    return None

def search_by_institution(institution_name, id=None):
    app.logger.debug(f"Searching by institution: {institution_name}")
    if not id:
        institution_id = get_institution_id(institution_name)
        if institution_id is None:
            app.logger.warning(f"No institution ID found for {institution_name}")
            return None
    else:
        institution_id = id
    query = """SELECT search_by_institution(%s);"""
    results = execute_query(query, (institution_id,))
    if results:
        app.logger.info(f"Found results for institution search: {institution_name}")
        return results[0][0]
    app.logger.warning(f"No results found for institution: {institution_name}")
    return None

def search_by_author(author_name):
    app.logger.debug(f"Searching by author: {author_name}")
    author_ids = get_author_ids(author_name)
    if not author_ids:
        app.logger.warning(f"No author IDs found for {author_name}")
        return None

    author_id = author_ids[0]['author_id']
    app.logger.debug(f"Using author ID: {author_id}")

    query = """SELECT search_by_author(%s);"""
    results = execute_query(query, (author_id,))
    if results:
        app.logger.info(f"Found results for author search: {author_name}")
        return results[0][0]
    app.logger.warning(f"No results found for author: {author_name}")
    return None


## Creates lists for autofill functionality from the institution and keyword csv files
# It's good practice to load autofill lists once at startup if they are static.
# These lists are crucial for guiding user input and for backend fuzzy matching.
with open('institutions.csv', 'r', encoding='UTF-8') as file:
    raw_autofill_inst_list = file.read().split('\n')
    autofill_inst_list = [name.replace('"', '').strip() for name in raw_autofill_inst_list if name.strip()]
    # This list serves as the ground truth for institutional name resolution.
with open('subfields.csv', 'r') as file:
    autofill_subfields_list = file.read().split('\n')
SUBFIELDS = True
if not SUBFIELDS:
  with open('keywords.csv', 'r') as fil:
      autofill_topics_list = fil.read().split('\n')


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
  return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(404)
def not_found(e):
    app.logger.warning(f"404 error: {request.url}")
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(500)
def server_error(e):
    app.logger.error(f"500 error: {str(e)}")
    return "Internal Server Error", 500

# Suggested helper function for sanitizing institution names
def sanitize_name(name):
    # This function prepares names for comparison, a foundational step for reliable matching.
    # By standardizing names, we increase the chances of finding accurate connections.
    if isinstance(name, str):
        return name.lower().strip().replace('.', '').replace(',', '')
    return ""

# Suggested helper for fuzzy matching (conceptual)
def fuzzy_match_institutions(institution_names_list, available_institutions_list, threshold=80):
    """
    Performs fuzzy matching for a list of institution names against a list of known institutions.
    This function aims to bridge the gap between user input and precise data identifiers.
    """
    matched_institutions = []
    # Ensuring the list of available institutions is clean for matching
    # This cultivates a reliable ground for comparison.
    clean_available_institutions = [sanitize_name(inst) for inst in available_institutions_list if inst]

    for name in institution_names_list:
        sanitized_input_name = sanitize_name(name)
        if not sanitized_input_name:
            continue
        
        # Here, you would use a fuzzy matching library e.g., fuzzywuzzy
        # For demonstration, this is a conceptual placeholder.
        # match = process.extractOne(sanitized_input_name, clean_available_institutions, score_cutoff=threshold)
        
        # Conceptual: find best match in clean_available_institutions
        # This is a simplified stand-in for a proper fuzzy match algorithm.
        # The pursuit of the right match is a journey of algorithmic refinement.
        best_match = None
        highest_similarity = 0 # Requires a similarity function, e.g., Levenshtein distance

        # This simplistic loop is for concept only; a real fuzzy match library is more efficient.
        for known_inst_name_sanitized in clean_available_institutions:
            # Replace with actual similarity score calculation
            # from a library like fuzzywuzzy:
            # current_similarity = fuzz.ratio(sanitized_input_name, known_inst_name_sanitized)
            
            # Placeholder similarity:
            if sanitized_input_name in known_inst_name_sanitized or known_inst_name_sanitized in sanitized_input_name:
                 current_similarity = 90 # Arbitrary high score for simple substring match
            else:
                 current_similarity = 0

            if current_similarity > highest_similarity and current_similarity >= threshold:
                highest_similarity = current_similarity
                # Find the original name corresponding to the sanitized best match
                original_index = -1
                for i, inst_s in enumerate(clean_available_institutions):
                    if inst_s == known_inst_name_sanitized:
                        original_index = available_institutions_list.index(available_institutions_list[i]) # find original casing
                        break
                if original_index != -1:
                    best_match = available_institutions_list[original_index]


        if best_match:
            # In a real scenario, you'd likely return an ID or a more structured object.
            # The goal is to transform raw input into actionable, recognized entities.
            app.logger.info(f"Fuzzy matched '{name}' to '{best_match}' with similarity {highest_similarity}")
            matched_institutions.append(best_match) # Or an ID associated with best_match
        else:
            app.logger.warning(f"Could not confidently fuzzy match institution: {name}")
            
    # Returning a list of recognized institution names (or ideally, their IDs/objects).
    # This list becomes the refined input for further data retrieval.
    return matched_institutions

@app.route('/initial-search', methods=['POST'])
def initial_search():
    request_data = request.get_json()
    page = request_data.get('page', 1)
    per_page = request_data.get('per_page', 25)

    # The primary institution name, potentially containing comma-separated values.
    # This field is the first port of call for institutional queries.
    institution_input = request_data.get('organization', "") 
    # 'extra_institutions' can be an array from multi-select (now handled by parsing institution_input or selectedInstitutions on frontend)
    # or a string from CSV upload. The frontend will now send primary/selected institutions via 'organization' (potentially comma-sep)
    # and CSV content via 'extra_institutions' if a file was uploaded.
    extra_institutions_input = request_data.get('extra_institutions') # This could be CSV string or array from multi-select on frontend

    researcher = request_data.get('researcher', "").title()
    institution_type = request_data.get('type', "") # e.g. HBCU, Carnegie R1
    topic = request_data.get('topic', "")
    
    app.logger.info(f"Search Request -- Primary Inst Input: {institution_input}, Extras: {extra_institutions_input}, Researcher: {researcher}, Topic: {topic}, Type: {institution_type}")

    all_institution_names = []
    
    # Handling the primary institution input which might be comma-separated for <=5 items
    # This embraces the flexibility of user input, a small step towards more natural interaction.
    if institution_input:
        potential_institutions = [name.strip() for name in institution_input.split(',') if name.strip()]
        all_institution_names.extend(potential_institutions)

    # Handling 'extra_institutions_input' which could be an array (from multi-select) or CSV string
    # This logic ensures that multiple avenues of input converge towards a unified list.
    is_csv_upload = False
    if isinstance(extra_institutions_input, str) and "-----BEGIN CSV-----" in extra_institutions_input: # Example CSV marker
        is_csv_upload = True
        # A more robust CSV parsing might be needed if not just names
        # Sanitize lines from CSV string
        csv_lines = extra_institutions_input.replace("-----BEGIN CSV-----", "").replace("-----END CSV-----", "").split('\n')
        csv_institution_names = [sanitize_name(line.strip()) for line in csv_lines if line.strip()]
        all_institution_names.extend(csv_institution_names)
        app.logger.info(f"Processed {len(csv_institution_names)} names from CSV input.")
    elif isinstance(extra_institutions_input, list):
        all_institution_names.extend([name.strip() for name in extra_institutions_input if name.strip()])

    # Deduplicate and sanitize all collected names
    # Ensuring uniqueness and consistency is a vital part of data preparation.
    unique_sanitized_names = sorted(list(set([sanitize_name(name) for name in all_institution_names if name])))
    
    # Perform fuzzy matching on the unique sanitized names
    # This step translates potentially imprecise user inputs into recognized entities.
    # `autofill_inst_list` should be loaded from your institutions.csv or database.
    final_institutions_to_search = fuzzy_match_institutions(unique_sanitized_names, autofill_inst_list)
    app.logger.info(f"Final institutions after fuzzy matching: {final_institutions_to_search}")


    results = None
    try:
        # The search logic now prioritizes based on the combination of inputs,
        # moving towards a more intuitive and powerful search experience.
        if final_institutions_to_search and len(final_institutions_to_search) > 0 and researcher and topic:
            # If multiple institutions came from fuzzy matching, pass them to a handler that expects a list.
            # For now, get_institution_researcher_subfield_results takes one institution.
            # This needs to be adapted or a new function created for multiple institutions.
            # Conceptual: results = get_MULTI_institution_researcher_subfield_results(final_institutions_to_search, researcher, topic, page, per_page)
            # Using the first matched institution for now, as existing function expects one:
            results = get_institution_researcher_subfield_results(final_institutions_to_search[0], researcher, topic, page, per_page)
            # To truly support all, the backend functions like get_institution_researcher_subfield_results
            # would need to accept a list of institutions and aggregate results.
        elif final_institutions_to_search and len(final_institutions_to_search) > 0 and researcher:
            results = get_institution_and_researcher_results(final_institutions_to_search[0], researcher, page, per_page) # Adapt for multi
        elif final_institutions_to_search and len(final_institutions_to_search) > 0 and topic:
            # If multiple institutions, decide if you want to pass all to get_institution_and_subfield_results
            # or adapt it like get_multiple_institution_results
            if len(final_institutions_to_search) > 1 :
                 # This function is designed for multiple institutions if topic is also a filter
                 results = get_multiple_institution_and_subfield_results(final_institutions_to_search, topic, page, per_page)
            else:
                 results = get_institution_and_subfield_results(final_institutions_to_search[0], topic, page, per_page)

        elif researcher and topic:
            results = get_researcher_and_subfield_results(researcher, topic, page, per_page)
        elif topic:
            results = get_subfield_results(topic, page, per_page)
        elif researcher:
            results = get_researcher_result(researcher, page, per_page)
        elif final_institutions_to_search and len(final_institutions_to_search) > 0:
            # This is the primary path for multi-institution searches (comma-separated or CSV)
            # The 'ids' flag might relate to whether inputs are names or pre-resolved IDs.
            # Assuming names for now, so ids=False.
            # The spirit of collaboration is reflected in searching across many institutions.
            results = get_multiple_institution_results(final_institutions_to_search, page, per_page, ids=is_csv_upload) # Pass CSV flag if needed
            # Adjust 'ids' if fuzzy_match_institutions returns IDs instead of names
        
        # Fallback: if only institution_type is provided (e.g., "HBCU")
        # This path requires a function that can search by type alone.
        elif institution_type and not topic and not researcher and not final_institutions_to_search:
             # Conceptual: You'd need a new function like get_institutions_by_type_results
             # app.logger.info(f"Searching for institutions of type: {institution_type}")
             # results = get_institutions_by_type_results(institution_type, page, per_page)
             # For now, this case might lead to no results if not handled.
             pass


        if not results:
            app.logger.warning("Search returned no results or unhandled search combination.")
            return {} # Return empty if no specific search path was taken or no results

        app.logger.info("Search completed successfully.")
        return results

    except Exception as e:
        app.logger.critical(f"Critical error during search: {str(e)}", exc_info=True)
        # Providing a clear error response is part of a robust system.
        return {"error": "An unexpected error occurred. The details have been logged."}

@app.route('/geo_info', methods=['POST'])
def get_geo_info():
    institution_id = request.json.get('institution_oa_link')
    app.logger.debug(f"Searching for geo data for institution link: {institution_id}")
    institution_id = institution_id.replace("openalex.org/institutions/", "")
    api_call = f"https://api.openalex.org/institutions/{institution_id}?select=geo"
    headers = {'Accept': 'application/json'}
    response = requests.get(api_call, headers=headers)
    if not response.status_code == 404:
        data = response.json()
        if data == None:
            app.logger.warning(f"No data found for institution {institution_id}")
        else:
            app.logger.info(f"Found geo data for institution id {institution_id}")
            geography_data = data['geo']
            return geography_data
    else:
        app.logger.warning(f"(404 Error) Institution not found for id {institution_id}")

def get_researcher_result(researcher, page=1, per_page=20):
    """
    Gets the results when user only inputs a researcher
    Uses database to get result, defaults to SPARQL if researcher is not in database
    """
    data = search_by_author(researcher)
    if data is None:
        app.logger.info("No database results, falling back to SPARQL...")
        data = get_author_metadata_sparql(researcher)
        if data == {}:
            app.logger.warning("No results found in SPARQL for researcher")
            return {}
        topic_list, graph = list_given_researcher_institution(data['oa_link'], data['name'], data['current_institution'])
        results = {"metadata": data, "graph": graph, "list": topic_list}
        app.logger.info(f"Successfully retrieved SPARQL results for researcher: {researcher}")
        return results

    app.logger.debug("Processing database results for researcher")
    list = []
    metadata = data['author_metadata']

    if metadata['orcid'] is None:
        metadata['orcid'] = ''
    metadata['work_count'] = metadata['num_of_works']
    metadata['current_institution'] = metadata['last_known_institution']
    metadata['cited_by_count'] = metadata['num_of_citations']
    metadata['oa_link'] = metadata['openalex_url']
    
    if metadata['last_known_institution'] is None:
        app.logger.debug("Fetching last known institutions from OpenAlex")
        institution_object = fetch_last_known_institutions(metadata['oa_link'])
        if institution_object == []:
            app.logger.warning("No last known institution found")
            last_known_institution = ""
        else:
            institution_object = institution_object[0]
            last_known_institution = institution_object['display_name']
            institution_url = institution_object['id']
    else:
        last_known_institution = metadata['last_known_institution']
    metadata['current_institution'] = last_known_institution
    metadata['institution_url'] = institution_url

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    # nodes.append({ 'id': last_known_institution, 'label': last_known_institution, 'type': 'INSTITUTION' })
    edges.append({ 'id': f"""{metadata['openalex_url']}-{last_known_institution}""", 'start': metadata['openalex_url'], 'end': last_known_institution, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
    # nodes.append({ 'id': metadata['openalex_url'], 'label': researcher, "type": "AUTHOR"})
    
    total_topics = len(data['data'])
    start = (page - 1) * per_page
    end = start + per_page

    for entry in data['data'][start:end]:
        subfield = entry['topic']
        num_works = entry['num_of_works']
        list.append((subfield, num_works))
        nodes.append({'id': subfield, 'label': subfield, 'type': "SUBFIELD", 'people': (num_works / metadata['work_count']) * 50 })
        subfield_metadata = data['subfield_metadata']
        for topic in subfield_metadata[subfield]:
            nodes.append({'id': topic['topic_display_name'], 'label': topic['topic_display_name'], 'type': "TOPIC"})
            edges.append({ 'id': f"""{subfield}-{topic['topic_display_name']}""", 'start': subfield, 'end': topic['topic_display_name'], "label": "has_topic", "start_type": "SUBFIELD", "end_type": "TOPIC"})

    graph = {"nodes": nodes, "edges": edges}
    app.logger.info(f"Successfully built result for researcher: {researcher}")
    return {"metadata": metadata,
            "metadata_pagination": {
            "total_pages": (total_topics + per_page - 1) // per_page,
            "current_page": page,
            "total_topics": total_topics,
        }, "graph": graph, "list": list}

def get_institution_results(institution, page=1, per_page=10):
    """
    Gets the results when user only inputs an institution
    Uses database to get result, defaults to SPARQL if institution is not in database
    """
    data = search_by_institution(institution)
    if data is None:
        app.logger.info("No database results, falling back to SPARQL...")
        data = get_institution_metadata_sparql(institution)
        if data == {}:
            app.logger.warning("No results found in SPARQL for institution")
            return {}
        topic_list, graph = list_given_institution(data['ror'], data['name'], data['oa_link'])
        results = {"metadata": data, "graph": graph, "list": topic_list}
        app.logger.info(f"Successfully retrieved SPARQL results for institution: {institution}")
        return results
    app.logger.debug("Processing database results for institution")
    metadata = data['institution_metadata']
    metadata['homepage'] = metadata['url']
    metadata['works_count'] = metadata['num_of_works']
    metadata['name'] = metadata['institution_name']
    metadata['cited_count'] = metadata['num_of_citations']
    metadata['oa_link'] = metadata['openalex_url']
    metadata['author_count'] = metadata['num_of_authors']

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    # institution_id = metadata['openalex_url']

    total_topics = len(data['data'])
    start = (page - 1) * per_page
    end = start + per_page

    list = []
    for entry in data['data'][start:end]:
        subfield = entry['topic_subfield']
        number = entry['num_of_authors']
        list.append((subfield, number))
        nodes.append({'id': subfield, 'label': subfield, 'type': "SUBFIELD", 'people': (number / metadata['author_count']) * 100 })
        subfield_metadata = data['subfield_metadata']
        for topic in subfield_metadata[subfield]:
            nodes.append({'id': topic['topic_display_name'], 'label': topic['topic_display_name'], 'type': "TOPIC"})
            edges.append({ 'id': f"""{subfield}-{topic['topic_display_name']}""", 'start': subfield, 'end': topic['topic_display_name'], "label": "has_topic", "start_type": "SUBFIELD", "end_type": "TOPIC"})
    
    graph = {"nodes": nodes, "edges": edges}
    app.logger.info(f"Successfully built result for institution: {institution}")
    return {
        "metadata": metadata,
        "metadata_pagination": {
            "total_pages": (total_topics + per_page - 1) // per_page,
            "current_page": page,
            "total_topics": total_topics,
        },
        "extra_metadata": {},
        "graph": graph,
        "list": list
    }

@app.route('/geo_info_batch', methods=['POST'])
def get_geo_info_batch():
    institutions = request.json.get('institutions', [])
    results = []
    if not institutions or not isinstance(institutions, list):
        return jsonify({'error': 'Invalid or missing "institutions" list'}), 400

    for entry in institutions:
        if not isinstance(entry, list) or len(entry) != 3:
            continue  

        oa_link, institution_name, authors = entry

        if not oa_link.startswith("https://openalex.org/"):
            continue  

        institution_id = oa_link.replace("https://openalex.org/", "")
        api_url = f"https://api.openalex.org/institutions/{institution_id}?select=geo"
        headers = {'Accept': 'application/json'}

        try:
            response = requests.get(api_url, headers=headers)
            if response.status_code != 404:
                data = response.json()
                geo = data.get("geo", {})
                if geo.get("latitude") and geo.get("longitude"):
                    results.append({
                        "lat": geo["latitude"],
                        "lng": geo["longitude"],
                        "name": institution_name,
                        "authors": int(authors)
                    })
        except Exception as e:
            app.logger.warning(f"Error fetching geo info for {institution_name}: {e}")
    return jsonify(results)

def get_subfield_results(topic, page=1, per_page=20, map_limit=100):
    """
    Gets the results when user only inputs a subfield
    Uses database to get result
    """
    data = search_by_topic(topic)
    if data is None:
        app.logger.warning(f"No results found for topic: {topic}")
        return {"metadata": None, "graph": None, "list": None}

    app.logger.debug("Processing database results for topic")
    list = []
    metadata = {}

    topic_clusters = []
    for entry in data['subfield_metadata']:
        topic_cluster = entry['topic']
        topic_clusters.append(topic_cluster)
        subfield_oa_link = entry['subfield_url']
    metadata['topic_clusters'] = topic_clusters
    metadata['work_count'] = data['totals']['total_num_of_works']
    metadata['cited_by_count'] = data['totals']['total_num_of_citations']
    metadata['researchers'] = data['totals']['total_num_of_authors']
    metadata['oa_link'] = subfield_oa_link
    metadata['name'] = topic.title()

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    coordinates_metadata = []

    topic_id = topic
    nodes.append({ 'id': topic_id, 'label': topic, 'type': 'TOPIC' })

    total_topics = len(data['data'])
    start = (page - 1) * per_page
    end = start + per_page
    
    for entry in data['data'][start:end]:
        institution = entry['institution_name']
        number = entry['num_of_authors']
        oa_link = entry['institution_id']
        list.append((institution, number))
        coordinates_metadata.append((oa_link, institution, number))
        nodes.append({ 'id': institution, 'label': institution, 'type': 'INSTITUTION' })
        nodes.append({'id': number, 'label': number, 'type': "NUMBER"})
        edges.append({ 'id': f"""{institution}-{topic_id}""", 'start': institution, 'end': topic_id, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
        edges.append({ 'id': f"""{institution}-{number}""", 'start': institution, 'end': number, "label": "number", "start_type": "INSTITUTION", "end_type": "NUMBER"})
    
    for entry in data['data'][:map_limit]:
        institution = entry['institution_name']
        number = entry['num_of_authors']
        oa_link = entry['institution_id']
        coordinates_metadata.append((oa_link, institution, number))

    graph = {"nodes": nodes, "edges": edges}
    app.logger.info(f"Successfully built result for topic: {topic}")
    return {"metadata": metadata, 
            "metadata_pagination": {
            "total_pages": (total_topics + per_page - 1) // per_page,
            "current_page": page,
            "total_topics": total_topics,
        }, "graph": graph, "list": list, "coordinates": coordinates_metadata}

# get_multiple_institution_results is to use the fuzzy matching conceptually
# The `ids` parameter might distinguish if `institutions` are names (needs fuzzy) or pre-matched IDs
def get_multiple_institution_results(institutions_input_list, page=1, per_page=19, ids=False):
    """
    Handles searches for multiple institutions, potentially using fuzzy matching for names.
    The journey from raw input to refined, relevant data is central here.
    """
    # If `ids` is True, it implies `institutions_input_list` contains pre-matched IDs or exact names
    # that don't need further fuzzy matching here.
    # If `ids` is False (default or from non-CSV multi-input), we assume names that might need fuzzy matching.
    # However, `initial_search` now pre-processes with fuzzy matching. So, `institutions_input_list`
    # should already be a list of *recognized* institution names (or their IDs if fuzzy_match_institutions returns that).

    # For this refactoring, we'll assume institutions_input_list contains names recognized by fuzzy_match_institutions.
    # The 'ids' flag here might now determine how search_by_institution is called if it can take names vs IDs.

    final_metadata_collection = {} # Using a more descriptive name.
    all_nodes = [] # Aggregating graph nodes from all processed institutions.
    all_edges = [] # Aggregating graph edges.
    
    # Pagination for the list of institutions themselves, if needed.
    # This is distinct from pagination of topics *within* an institution.
    total_institutions_to_process = len(institutions_input_list)
    # institutions_to_display_on_page = institutions_input_list[start_index:end_index] # If paginating institutions

    # We process all institutions provided, then the frontend handles displaying one or more.
    # The backend's role is to gather all necessary data.
    processed_institutions_count = 0

    for inst_name_or_id in institutions_input_list: # Iterate through the (potentially fuzzy-matched) list
        current_institution_topics = []
        # The fundamental act of searching, now potentially enhanced by better name resolution.
        # The 'ids' flag could tell search_by_institution if inst_name_or_id is an ID or a name.
        # Assuming search_by_institution can handle names now, or we use a get_institution_id helper.
        
        # If inst_name_or_id is an ID (e.g. "openalex.org/I12345"), search_by_institution might need adjustment
        # or a separate path. For now, assume it's a name that `search_by_institution` can handle
        # or that `get_institution_id` (used within `search_by_institution`) can resolve.
        
        # Clarification: If fuzzy_match_institutions returns IDs, then `ids` should be True.
        # If it returns recognized names, search_by_institution needs to handle names.
        # For this example, let's assume `search_by_institution` is robust enough for names.
        institution_data = search_by_institution(inst_name_or_id) # Removed id parameter if fuzzy matching handles resolution

        if institution_data:
            processed_institutions_count +=1
            # Storing metadata under the resolved institution name.
            # This ensures consistency in how data is keyed and accessed.
            resolved_inst_name = institution_data['institution_metadata'].get('institution_name', inst_name_or_id)
            
            inst_metadata_transformed = {
                "institution_name": institution_data['institution_metadata'].get('institution_name'),
                "is_hbcu": institution_data['institution_metadata'].get('hbcu', False), # Add is_hbcu if available
                "cited_count": str(institution_data['institution_metadata'].get('num_of_citations', '0')),
                "author_count": str(institution_data['institution_metadata'].get('num_of_authors', '0')),
                "works_count": str(institution_data['institution_metadata'].get('num_of_works', '0')),
                "institution_url": institution_data['institution_metadata'].get('url'),
                "open_alex_link": institution_data['institution_metadata'].get('openalex_url'),
                "ror_link": institution_data['institution_metadata'].get('ror'),
                "topics": [] # Placeholder, to be filled from data['data']
            }
            
            # Building a shared graph for visualization purposes.
            # The graph is a powerful representation of interconnectedness.
            all_nodes.append({'id': resolved_inst_name, 'label': resolved_inst_name, 'type': "INSTITUTION" })

            for entry in institution_data.get('data', []): # Paginate this internal list if necessary
                subfield = entry.get('topic_subfield', 'Unknown Topic')
                num_authors = entry.get('num_of_authors', 0)
                current_institution_topics.append([subfield, str(num_authors)])
                
                # Add subfield to graph if not already present (conceptual - ensure unique IDs for nodes)
                # This requires careful node ID management to avoid duplicates if subfields are shared.
                subfield_node_id = f"{resolved_inst_name}_{subfield}" # Example of unique ID
                if not any(n['id'] == subfield_node_id for n in all_nodes):
                     all_nodes.append({'id': subfield_node_id, 'label': subfield, 'type': "SUBFIELD" })
                all_edges.append({ 
                    'id': f"""{resolved_inst_name}-{subfield_node_id}""", 
                    'start': resolved_inst_name, 
                    'end': subfield_node_id, 
                    "label": "researches", 
                    "start_type": "INSTITUTION", "end_type": "SUBFIELD"
                })
            inst_metadata_transformed["topics"] = current_institution_topics
            final_metadata_collection[resolved_inst_name] = inst_metadata_transformed
            
            # If this is the first institution and it's a single primary search from UI,
            # its full metadata might be needed at the top 'metadata' level for compatibility.
            if processed_institutions_count == 1 and len(institutions_input_list) == 1 and not is_csv_upload :
                 # This structure is what single institution search returns in 'metadata'
                 # Ensuring a consistent path for single vs the first of multiple.
                 primary_metadata_for_response = {
                    "name": inst_metadata_transformed["institution_name"],
                    "hbcu": inst_metadata_transformed.get("is_hbcu", False),
                    "cited_count": inst_metadata_transformed["cited_count"],
                    "author_count": inst_metadata_transformed["author_count"],
                    "works_count": inst_metadata_transformed["works_count"],
                    "homepage": inst_metadata_transformed["institution_url"],
                    "oa_link": inst_metadata_transformed["open_alex_link"],
                    "ror": inst_metadata_transformed["ror_link"],
                 }


    # The combined graph representing all found institutions and their topics.
    # This offers a bird's-eye view of the collective research landscape.
    combined_graph = {"nodes": all_nodes, "edges": all_edges}

    # For pagination of the institutions themselves (if institutions_input_list is very long)
    # This is conceptual and depends on how frontend wants to receive paginated *institutions*
    # total_pages_for_institutions = (total_institutions_to_process + per_page - 1) // per_page

    # The primary 'metadata' field might be for the first institution,
    # or be a summary if multiple were explicitly queried as primary.
    # For now, if institutions_input_list has content, 'extra_metadata' holds all details.
    # 'metadata' could be the first one, or an aggregate, or empty if all are in 'extra_metadata'.
    # To maintain compatibility with how Search.tsx uses `data.metadata` for single inst.
    # And `data.all_institution_metadata` for multi-inst.
    
    final_response_metadata = {}
    if institutions_input_list and final_metadata_collection:
        first_institution_name = institutions_input_list[0] # The name used for query
        # Try to get the resolved name if it changed due to fuzzy matching / backend resolution
        # This part assumes final_metadata_collection keys are resolved names.
        # We need to map back the first *input* name to its resolved data if possible,
        # or just pick the first item in final_metadata_collection.
        
        # A simple way:
        if final_metadata_collection:
            resolved_first_key = list(final_metadata_collection.keys())[0]
            first_inst_data = final_metadata_collection[resolved_first_key]
            final_response_metadata = { # Mimicking single institution metadata structure
                "name": first_inst_data["institution_name"],
                "hbcu": first_inst_data.get("is_hbcu", False),
                "cited_count": first_inst_data["cited_count"],
                "author_count": first_inst_data["author_count"],
                "works_count": first_inst_data["works_count"],
                "homepage": first_inst_data["institution_url"],
                "oa_link": first_inst_data["open_alex_link"],
                "ror": first_inst_data["ror_link"],
            }


    return {
        # 'metadata' might represent the primary queried institution or the first from a list.
        # This choice depends on how Search.tsx is structured to handle single vs multi.
        # If 'initial_search' sends only one primary institution, this is its metadata.
        # If multiple, this could be the first, and all others in 'extra_metadata'.
        "metadata": final_response_metadata if final_response_metadata else (institutions_input_list[0] if institutions_input_list else {}), # Fallback for safety
        "extra_metadata": final_metadata_collection, # All detailed metadata keyed by institution name.
        "metadata_pagination": { # This pagination refers to topics *within* the primary institution if displayed that way
            "total_pages": 1, # Placeholder - pagination logic needs to be clear
            "current_page": page,
            "total_topics": 0, # Placeholder
        },
        "graph": combined_graph,
        "list": [] # Main list might be empty if all data is in extra_metadata
    }

def get_multiple_institution_and_subfield_results(institution, topic, page, per_page):
    new_list = []
    nodes = []
    edges = []
    first = True
    for inst in institution:
        nodes.append({ 'id': inst, 'label': inst, 'type': 'INSTITUTION' })
        res = get_institution_and_subfield_results(inst, topic, page, per_page)
        for t in res['metadata']['topic_clusters']:
            nodes.append({ 'id': t, 'label': t, 'type': 'TOPIC'})
            edges.append({ 'id': f"""{inst}-{t}""", 'start': inst, 'end': t, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
        new_list.append((inst, res['metadata']['people_count']))
        if first:
            results = res
            first = False
    results['graph'] = {"nodes": nodes, "edges": edges}
    results['list'] = new_list
    return results

def get_researcher_and_subfield_results(researcher, topic, page=1, per_page=20):
    """
    Gets the results when user inputs a researcher and subfield
    Uses database to get result, defaults to SPARQL if researcher is not in database
    """
    data = search_by_author_topic(researcher, topic)
    if data is None:
        app.logger.info("No database results, falling back to SPARQL...")
        data = get_topic_and_researcher_metadata_sparql(topic, researcher)
        if data == {}:
            app.logger.warning("No results found in SPARQL for researcher and topic")
            return {}
        work_list, graph, extra_metadata = list_given_researcher_topic(topic, researcher, data['current_institution'], data['topic_oa_link'], data['researcher_oa_link'], data['institution_oa_link'])
        data['work_count'] = extra_metadata['work_count']
        data['cited_by_count'] = extra_metadata['cited_by_count']
        results = {"metadata": data, "graph": graph, "list": work_list}
        app.logger.info(f"Successfully retrieved SPARQL results for researcher: {researcher} and topic: {topic}")
        return results

    app.logger.debug("Processing database results for researcher and topic")
    list = []
    metadata = {}
    
    topic_clusters = []
    for entry in data['subfield_metadata']:
        topic_cluster = entry['topic']
        topic_clusters.append(topic_cluster)
        subfield_oa_link = entry['subfield_url']
    metadata['topic_name'] = topic
    metadata['topic_clusters'] = topic_clusters
    metadata['work_count'] = data['totals']['total_num_of_works']
    metadata['cited_by_count'] = data['totals']['total_num_of_citations']
    metadata['topic_oa_link'] = subfield_oa_link

    if data['author_metadata']['orcid'] is None:
        metadata['orcid'] = ''
    else:
        metadata['orcid'] = data['author_metadata']['orcid']
    metadata['researcher_name'] = researcher
    metadata['researcher_oa_link'] = data['author_metadata']['openalex_url']
    if data['author_metadata']['last_known_institution'] is None:
        app.logger.debug("Fetching last known institutions from OpenAlex")
        institution_object = fetch_last_known_institutions(metadata['researcher_oa_link'])[0]
        metadata['current_institution'] = institution_object['display_name']
    else:
        metadata['current_institution'] = data['author_metadata']['last_known_institution']
    last_known_institution = metadata['current_institution']

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    researcher_id = metadata['researcher_oa_link']
    subfield_id = metadata['topic_oa_link']
    nodes.append({ 'id': last_known_institution, 'label': last_known_institution, 'type': 'INSTITUTION' })
    edges.append({ 'id': f"""{researcher_id}-{last_known_institution}""", 'start': researcher_id, 'end': last_known_institution, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
    nodes.append({ 'id': researcher_id, 'label': researcher, 'type': 'AUTHOR' })
    nodes.append({ 'id': subfield_id, 'label': topic, 'type': 'TOPIC' })
    edges.append({ 'id': f"""{researcher_id}-{subfield_id}""", 'start': researcher_id, 'end': subfield_id, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
    
    total_topics = len(data['data'])
    start = (page - 1) * per_page
    end = start + per_page

    for entry in data['data'][start:end]:
        work = entry['work_name']
        number = entry['num_of_citations']
        list.append((work, number))
        nodes.append({ 'id': work, 'label': work, 'type': 'WORK' })
        nodes.append({'id': number, 'label': number, 'type': "NUMBER"})
        edges.append({ 'id': f"""{researcher_id}-{work}""", 'start': researcher_id, 'end': work, "label": "authored", "start_type": "AUTHOR", "end_type": "WORK"})
        edges.append({ 'id': f"""{work}-{number}""", 'start': work, 'end': number, "label": "citedBy", "start_type": "WORK", "end_type": "NUMBER"})
    
    graph = {"nodes": nodes, "edges": edges}
    app.logger.info(f"Successfully built result for researcher: {researcher} and topic: {topic}")
    return {"metadata": metadata, 
            "metadata_pagination": {
            "total_pages": (total_topics + per_page - 1) // per_page,
            "current_page": page,
            "total_topics": total_topics,
        }, "graph": graph, "list": list}

def get_institution_and_subfield_results(institution, topic, page=1, per_page=20):
    """
    Gets the results when user inputs an institution and subfield
    Uses database to get result, defaults to SPARQL if institution is not in database
    """
    data = search_by_institution_topic(institution, topic)
    if data is None:
        app.logger.info("Using SPARQL for institution and topic search...")
        data = get_institution_and_topic_metadata_sparql(institution, topic)
        if data == {}:
            app.logger.warning("No results found in SPARQL for institution and topic")
            return {}
        topic_list, graph, extra_metadata = list_given_institution_topic(institution, data['institution_oa_link'], topic, data['topic_oa_link'])
        data['work_count'] = extra_metadata['work_count']
        data['people_count'] = extra_metadata['num_people']
        results = {"metadata": data, "graph": graph, "list": topic_list}
        app.logger.info(f"Successfully retrieved SPARQL results for institution: {institution} and topic: {topic}")
        return results

    app.logger.debug("Processing database results for institution and topic")
    list = []
    metadata = {}

    topic_clusters = []
    for entry in data['subfield_metadata']:
        topic_cluster = entry['topic']
        topic_clusters.append(topic_cluster)
        subfield_oa_link = entry['subfield_url']
    metadata['topic_name'] = topic
    metadata['topic_clusters'] = topic_clusters
    metadata['work_count'] = data['totals']['total_num_of_works']
    metadata['cited_by_count'] = data['totals']['total_num_of_citations']
    metadata['topic_oa_link'] = subfield_oa_link
    metadata['topic_name'] = topic

    metadata['homepage'] = data['institution_metadata']['url']
    metadata['institution_oa_link'] = data['institution_metadata']['openalex_url']
    metadata['ror'] = data['institution_metadata']['ror']
    metadata['institution_name'] = institution

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    subfield_id = metadata['topic_oa_link']
    institution_id = metadata['institution_oa_link']
    nodes.append({ 'id': subfield_id, 'label': topic, 'type': 'TOPIC' })
    nodes.append({ 'id': institution_id, 'label': institution, 'type': 'INSTITUTION' })
    edges.append({ 'id': f"""{institution_id}-{subfield_id}""", 'start': institution_id, 'end': subfield_id, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
    
    total_topics = len(data['data'])
    metadata['people_count'] = total_topics
    start = (page - 1) * per_page
    end = start + per_page

    for entry in data['data'][start:end]:
        author_id = entry['author_id']
        author_name = entry['author_name']
        number = entry['num_of_works']
        list.append((author_name, number))
        nodes.append({ 'id': author_id, 'label': author_name, 'type': 'AUTHOR' })
        nodes.append({ 'id': number, 'label': number, 'type': 'NUMBER' })
        edges.append({ 'id': f"""{author_id}-{number}""", 'start': author_id, 'end': number, "label": "numWorks", "start_type": "AUTHOR", "end_type": "NUMBER"})
        edges.append({ 'id': f"""{author_id}-{institution_id}""", 'start': author_id, 'end': institution_id, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
    
    graph = {"nodes": nodes, "edges": edges}
    app.logger.info(f"Successfully built result for institution: {institution} and topic: {topic}")
    return {
        "metadata": metadata,
        "metadata_pagination": {
            "total_pages": (total_topics + per_page - 1) // per_page,
            "current_page": page,
            "total_topics": total_topics,
        },
        "graph": graph,
        "list": list
    }

def get_institution_and_researcher_results(institution, researcher, page=1, per_page=20):
    """
    Gets the results when user inputs an institution and researcher
    Uses database to get result, defaults to SPARQL if institution or researcher is not in database
    """
    data = search_by_author_institution(researcher, institution)
    if data is None:
        app.logger.info("Using SPARQL for institution and researcher search...")
        data = get_researcher_and_institution_metadata_sparql(researcher, institution)
        if data == {}:
            app.logger.warning("No results found in SPARQL for institution and researcher")
            return {}
        topic_list, graph = list_given_researcher_institution(data['researcher_oa_link'], researcher, institution)
        results = {"metadata": data, "graph": graph, "list": topic_list}
        app.logger.info(f"Successfully retrieved SPARQL results for researcher: {researcher} and institution: {institution}")
        return results
    
    app.logger.debug("Processing database results for institution and researcher")
    list = []
    metadata = {}

    metadata['homepage'] = data['institution_metadata']['url']
    metadata['institution_oa_link'] = data['institution_metadata']['openalex_url']
    metadata['ror'] = data['institution_metadata']['ror']
    metadata['institution_name'] = institution

    if data['author_metadata']['orcid'] is None:
        metadata['orcid'] = ''
    else:
        metadata['orcid'] = data['author_metadata']['orcid']
    metadata['researcher_name'] = researcher
    metadata['researcher_oa_link'] = data['author_metadata']['openalex_url']
    metadata['current_institution'] = ""
    #last_known_institution = metadata['current_institution']
    metadata['work_count'] = data['author_metadata']['num_of_works']
    metadata['cited_by_count'] = data['author_metadata']['num_of_citations']

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    author_id = metadata['researcher_oa_link']
    # nodes.append({ 'id': institution, 'label': institution, 'type': 'INSTITUTION' })
    # edges.append({ 'id': f"""{author_id}-{institution}""", 'start': author_id, 'end': institution, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
    # nodes.append({ 'id': author_id, 'label': researcher, "type": "AUTHOR"})
    
    total_topics = len(data['data'])
    start = (page - 1) * per_page
    end = start + per_page

    for entry in data['data'][start:end]:
        subfield = entry['topic_name']
        num_works = entry["num_of_works"]
        list.append((subfield, num_works))
        nodes.append({'id': subfield, 'label': subfield, 'type': "SUBFIELD", 'people': (num_works / metadata['work_count']) * 100 })
        subfield_metadata = data['subfield_metadata']
        for topic in subfield_metadata[subfield]:
            nodes.append({'id': topic['topic_display_name'], 'label': topic['topic_display_name'], 'type': "TOPIC"})
            edges.append({ 'id': f"""{subfield}-{topic['topic_display_name']}""", 'start': subfield, 'end': topic['topic_display_name'], "label": "has_topic", "start_type": "SUBFIELD", "end_type": "TOPIC"})

    graph = {"nodes": nodes, "edges": edges}
    app.logger.info(f"Successfully built result for researcher: {researcher} and institution: {institution}")
    return {"metadata": metadata,
            "metadata_pagination": {
            "total_pages": (total_topics + per_page - 1) // per_page,
            "current_page": page,
            "total_topics": total_topics,
        }, "graph": graph, "list": list}

def get_institution_researcher_subfield_results(institution, researcher, 
                                                topic, page=1, per_page=20):
    """
    Gets the results when user inputs an institution, researcher, and subfield
    Uses database to get result, defaults to SPARQL if institution or researcher is not in database
    """
    data = search_by_author_institution_topic(researcher, institution, topic)
    if data is None:
        app.logger.info("Using SPARQL for institution, researcher, and topic search...")
        data = get_institution_and_topic_and_researcher_metadata_sparql(institution, topic, researcher)
        if data == {}:
            app.logger.warning("No results found in SPARQL for institution, researcher, and topic")
            return {}
        work_list, graph, extra_metadata = list_given_researcher_topic(topic, researcher, institution, data['topic_oa_link'], data['researcher_oa_link'], data['institution_oa_link'])
        data['work_count'] = extra_metadata['work_count']
        data['cited_by_count'] = extra_metadata['cited_by_count']
        results = {"metadata": data, "graph": graph, "list": work_list}
        app.logger.info(f"Successfully retrieved SPARQL results for researcher: {researcher}, institution: {institution}, and topic: {topic}")
        return results

    app.logger.debug("Processing database results for institution, researcher, and topic")
    list = []
    metadata = {}

    metadata['homepage'] = data['institution_metadata']['url']
    metadata['institution_oa_link'] = data['institution_metadata']['openalex_url']
    metadata['ror'] = data['institution_metadata']['ror']
    metadata['institution_name'] = institution

    if data['author_metadata']['orcid'] is None:
        metadata['orcid'] = ''
    else:
        metadata['orcid'] = data['author_metadata']['orcid']
    metadata['researcher_name'] = researcher
    metadata['researcher_oa_link'] = data['author_metadata']['openalex_url']
    metadata['current_institution'] = ""
    #last_known_institution = metadata['current_institution']

    topic_clusters = []
    for entry in data['subfield_metadata']:
        topic_cluster = entry['topic']
        topic_clusters.append(topic_cluster)
        subfield_oa_link = entry['subfield_url']
    metadata['topic_name'] = topic
    metadata['topic_clusters'] = topic_clusters
    metadata['work_count'] = data['totals']['total_num_of_works']
    metadata['cited_by_count'] = data['totals']['total_num_of_citations']
    metadata['topic_oa_link'] = subfield_oa_link

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    institution_id = metadata['institution_oa_link']
    researcher_id = metadata['researcher_oa_link']
    subfield_id = metadata['topic_oa_link']
    nodes.append({ 'id': institution_id, 'label': institution, 'type': 'INSTITUTION' })
    edges.append({ 'id': f"""{researcher_id}-{institution_id}""", 'start': researcher_id, 'end': institution_id, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
    nodes.append({ 'id': researcher_id, 'label': researcher, 'type': 'AUTHOR' })
    nodes.append({ 'id': subfield_id, 'label': topic, 'type': 'TOPIC' })
    edges.append({ 'id': f"""{researcher_id}-{subfield_id}""", 'start': researcher_id, 'end': subfield_id, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
    
    total_topics = len(data['data'])
    start = (page - 1) * per_page
    end = start + per_page

    for entry in data['data'][start:end]:
        work_name = entry['work_name']
        number = entry['cited_by_count']
        list.append((work_name, number))
        nodes.append({ 'id': work_name, 'label': work_name, 'type': 'WORK' })
        nodes.append({'id': number, 'label': number, 'type': "NUMBER"})
        edges.append({ 'id': f"""{researcher_id}-{work_name}""", 'start': researcher_id, 'end': work_name, "label": "authored", "start_type": "AUTHOR", "end_type": "WORK"})
        edges.append({ 'id': f"""{work_name}-{number}""", 'start': work_name, 'end': number, "label": "citedBy", "start_type": "WORK", "end_type": "NUMBER"})
    
    graph = {"nodes": nodes, "edges": edges}
    app.logger.info(f"Successfully built result for researcher: {researcher}, institution: {institution}, and topic: {topic}")

    return {"metadata": metadata, 
            "metadata_pagination": {
            "total_pages": (total_topics + per_page - 1) // per_page,
            "current_page": page,
            "total_topics": total_topics,
        }, "graph": graph, "list": list}

def query_SPARQL_endpoint(endpoint_url, query):
    """
    Queries the endpoint to execute the SPARQL query.
    """
    app.logger.debug(f"Executing SPARQL query: {query}")
    try:
        response = requests.post(endpoint_url, data={"query": query}, headers={'Accept': 'application/json'})
        response.raise_for_status()  # Raises an HTTPError for bad responses
        data = response.json()
        return_value = []
        for entry in data['results']['bindings']:
            my_dict = {}
            for e in entry:
                my_dict[e] = entry[e]['value']
            return_value.append(my_dict)
        app.logger.info(f"SPARQL query returned {len(return_value)} results")
        return return_value
    except requests.exceptions.RequestException as e:
        app.logger.error(f"SPARQL query failed: {str(e)}")
        return []

def get_institution_from_id_sparql(id):
    app.logger.debug(f"Finding Institution with id: {id}")
    query = f"""
    SELECT ?name
    WHERE {'{'}
    <https://semopenalex.org/institution/{id}> <http://xmlns.com/foaf/0.1/name> ?name .
    {'}'} GROUP BY ?name
    """
    results = query_SPARQL_endpoint(SEMOPENALEX_SPARQL_ENDPOINT, query)
    if not results:
        app.logger.warning(f"No SPARQL results found for institution: {id}")
        return {}
    return results[0]['name']

def get_institution_metadata_sparql(institution):
    """
    Given an institution, queries the SemOpenAlex endpoint to retrieve metadata on the institution
    """
    app.logger.debug(f"Fetching institution metadata from SPARQL for: {institution}")
    query = f"""
    SELECT ?ror ?workscount ?citedcount ?homepage ?institution (COUNT(distinct ?people) as ?peoplecount)
    WHERE {'{'}
    ?institution <http://xmlns.com/foaf/0.1/name> "{institution}" .
    ?institution <https://semopenalex.org/ontology/ror> ?ror .
    ?institution <https://semopenalex.org/ontology/worksCount> ?workscount .
    ?institution <https://semopenalex.org/ontology/citedByCount> ?citedcount .
    ?institution <http://xmlns.com/foaf/0.1/homepage> ?homepage .
    ?people <http://www.w3.org/ns/org#memberOf> ?institution .
    {'}'} GROUP BY ?ror ?workscount ?citedcount ?homepage ?institution
    """
    results = query_SPARQL_endpoint(SEMOPENALEX_SPARQL_ENDPOINT, query)
    if not results:
        app.logger.warning(f"No SPARQL results found for institution: {institution}")
        return {}

    app.logger.debug("Processing SPARQL results for institution")
    ror = results[0]['ror']
    works_count = results[0]['workscount']
    cited_count = results[0]['citedcount']
    homepage = results[0]['homepage']
    author_count = results[0]['peoplecount']
    oa_link = results[0]['institution']
    oa_link = oa_link.replace('semopenalex', 'openalex').replace('institution', 'institutions')
    hbcu = is_HBCU(oa_link)

    metadata = {
        "name": institution,
        "ror": ror,
        "works_count": works_count,
        "cited_count": cited_count,
        "homepage": homepage,
        "author_count": author_count,
        'oa_link': oa_link,
        "hbcu": hbcu
    }
    app.logger.info(f"Successfully retrieved metadata for institution: {institution}")
    return metadata

def list_given_institution(ror, name, id):
    """
    Uses OpenAlex to determine the subfields which a given institution study.
    Must iterate through all authors related to the institution and determine what topics OA attributes to them.
    """
    app.logger.debug(f"Fetching subfields for institution: {name} (ROR: {ror})")
    final_subfield_count = {}
    headers = {'Accept': 'application/json'}
    response = requests.get(f'https://api.openalex.org/authors?per-page=200&filter=last_known_institutions.ror:{ror}&cursor=*', headers=headers)
    data = response.json()
    authors = data['results']
    next_page = data['meta']['next_cursor']
    counter = 0
    
    app.logger.debug("Processing authors and their topics")
    while next_page is not None and counter < 10:
        for a in authors:
            topics = a['topics']
            for topic in topics:
                if topic['subfield']['display_name'] in final_subfield_count:
                    final_subfield_count[topic['subfield']['display_name']] += 1
                else:
                    final_subfield_count[topic['subfield']['display_name']] = 1
        response = requests.get(f'https://api.openalex.org/authors?per-page=200&filter=last_known_institutions.ror:{ror}&cursor=' + next_page, headers=headers)
        data = response.json()
        authors = data['results']
        next_page = data['meta']['next_cursor']
        counter += 1
    
    sorted_subfields = sorted([(k, v) for k, v in final_subfield_count.items() if v > 5], key=lambda x: x[1], reverse=True)
    app.logger.info(f"Found {len(sorted_subfields)} subfields with more than 5 authors")

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    nodes.append({ 'id': id, 'label': name, 'type': 'INSTITUTION' })
    for subfield, number in sorted_subfields:
        nodes.append({'id': subfield, 'label': subfield, 'type': "TOPIC"})
        number_id = subfield + ":" + str(number)
        nodes.append({'id': number_id, 'label': number, 'type': "NUMBER"})
        edges.append({ 'id': f"""{id}-{subfield}""", 'start': id, 'end': subfield, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
        edges.append({ 'id': f"""{subfield}-{number_id}""", 'start': subfield, 'end': number_id, "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})
    graph = {"nodes": nodes, "edges": edges}

    app.logger.info(f"Successfully built subfield list and graph for institution: {name}")
    return sorted_subfields, graph

def get_author_metadata_sparql(author):
  """
  Given an author, queries the SemOpenAlex endpoint to retrieve metadata on the author

  Returns:
  metadata : information on the author as a dictionary with the following keys:
    name, cited_by_count, orcid, work_count, current_institution, oa_link, institution_url
  """

  query = f"""
    SELECT ?cite_count ?orcid ?works_count ?current_institution_name ?author ?current_institution
    WHERE {'{'}
    ?author <http://xmlns.com/foaf/0.1/name> "{author}" .
    ?author <https://semopenalex.org/ontology/citedByCount> ?cite_count .
    OPTIONAL {"{"}?author <https://dbpedia.org/ontology/orcidId> ?orcid .{"}"}
    ?author <https://semopenalex.org/ontology/worksCount> ?works_count .
    ?author <http://www.w3.org/ns/org#memberOf> ?current_institution .
    ?current_institution <http://xmlns.com/foaf/0.1/name> ?current_institution_name .
    {'}'}
  """
  results = query_SPARQL_endpoint(SEMOPENALEX_SPARQL_ENDPOINT, query)
  if results == []:
    return {}
  cited_by_count = results[0]['cite_count']
  orcid = results[0]['orcid'] if 'orcid' in results[0] else ''
  work_count = results[0]['works_count']
  current_institution = results[0]['current_institution_name']
  oa_link = results[0]['author']
  oa_link = oa_link.replace('semopenalex', 'openalex').replace('author', 'authors')
  institution_link = results[0]['current_institution'].replace('semopenalex', 'openalex').replace('institution', 'institutions')

  return {"name": author, "cited_by_count": cited_by_count, "orcid": orcid, "work_count": work_count, "current_institution": current_institution, "oa_link": oa_link, "institution_url": institution_link}

def get_researcher_and_institution_metadata_sparql(researcher, institution):
  """
  Given an institution and researcher, collects the metadata for the 2 and returns as one dictionary.

  Returns:
  metadata : information on the institution and researcher as a dictionary with the following keys:
    institution_name, researcher_name, homepage, institution_oa_link, researcher_oa_link, orcid, work_count, cited_by_count, ror
  """

  researcher_data = get_author_metadata_sparql(researcher)
  institution_data = get_institution_metadata_sparql(institution)
  if researcher_data == {} or institution_data == {}:
    return {}

  institution_name = institution
  researcher_name = researcher
  institution_url = institution_data['homepage']
  institution_oa = institution_data['oa_link']
  researcher_oa = researcher_data['oa_link']
  orcid = researcher_data['orcid']
  work_count = researcher_data['work_count']
  cited_by_count = researcher_data['cited_by_count']
  ror = institution_data['ror']

  return {"institution_name": institution_name, "researcher_name": researcher_name, "homepage": institution_url, "institution_oa_link": institution_oa, "researcher_oa_link": researcher_oa, "orcid": orcid, "work_count": work_count, "cited_by_count": cited_by_count, "ror": ror}

def list_given_researcher_institution(id, name, institution):
    """
    When an user searches for a researcher only or a researcher and institution.
    Checks OpenAlex for what topics are attributed to the author.
    """
    app.logger.debug(f"Building list for researcher: {name} at institution: {institution}")
    final_subfield_count = {}
    headers = {'Accept': 'application/json'}
    search_id = id.replace('https://openalex.org/authors/', '')
    
    app.logger.debug(f"Fetching author data from OpenAlex for ID: {search_id}")
    response = requests.get(f'https://api.openalex.org/authors/{search_id}', headers=headers)
    data = response.json()
    topics = data['topics']
    
    for t in topics:
        subfield = t['subfield']['display_name']
        if subfield in final_subfield_count:
            final_subfield_count[subfield] = final_subfield_count[subfield] + t['count']
        else:
            final_subfield_count[subfield] = t['count']
    sorted_subfields = sorted(final_subfield_count.items(), key=lambda x: x[1], reverse=True)
    app.logger.debug(f"Found {len(sorted_subfields)} subfields for researcher")

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    nodes.append({ 'id': institution, 'label': institution, 'type': 'INSTITUTION' })
    edges.append({ 'id': f"""{id}-{institution}""", 'start': id, 'end': institution, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
    nodes.append({ 'id': id, 'label': name, "type": "AUTHOR"})
    
    for s, number in sorted_subfields:
        nodes.append({'id': s, 'label': s, 'type': "TOPIC"})
        number_id = s + ":" + str(number)
        nodes.append({'id': number_id, 'label': number, 'type': "NUMBER"})
        edges.append({ 'id': f"""{id}-{s}""", 'start': id, 'end': s, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
        edges.append({ 'id': f"""{s}-{number_id}""", 'start': s, 'end': number_id, "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})
    graph = {"nodes": nodes, "edges": edges}

    app.logger.info(f"Successfully built list and graph for researcher: {name} at institution: {institution}")
    return sorted_subfields, graph

def get_subfield_metadata_sparql(subfield):
  """
  Given a subfield, queries the OpenAlex endpoint to retrieve metadata on the subfield
  Doesn't query SemOpenAlex because the necessary data is faster to retrieve from OpenAlex, but this may change
  in the future.

  Researchers does not work as expected at the moment.

  Returns:
  metadata : information on the subfield as a dictionary with the following keys:
    name, topic_clusters, cited_by_count, work_count, researchers, oa_link
  """
  headers = {'Accept': 'application/json'}
  response = requests.get(f'https://api.openalex.org/subfields?filter=display_name.search:{subfield}', headers=headers) 
  data = response.json()['results'][0]
  oa_link = data['id']
  cited_by_count = data['cited_by_count']
  work_count = data['works_count']
  topic_clusters = []
  for topic in data['topics']:
    topic_clusters.append(topic['display_name'])
  researchers = 0
  return {"name": subfield, "topic_clusters": topic_clusters, "cited_by_count": cited_by_count, "work_count": work_count, "researchers": researchers, "oa_link": oa_link}

def list_given_topic(subfield, id):
  """
  When an user searches for a topic only.
  Searches through each HBCU and partner institution and returns which institutions research the subfield.

  Parameters:
  subfield : name of subfield searched
  id : id of the subfield

  Returns:
  subfield_list : the subfields which OpenAlex attributes to a given institution
  graph : a graphical representation of subfield_list.
  """
  headers = {'Accept': 'application/json'}
  subfield_list = []
  extra_metadata = {}
  total_work_count = 0

  for institution in autofill_inst_list:
    response = requests.get(f'https://api.openalex.org/institutions?select=display_name,topics&filter=display_name.search:{institution}', headers=headers)
    try:
      data = response.json()
      data = data['results'][0]
      inst_topics = data['topics']
      count = 0
      for t in inst_topics:
        if t['subfield']['display_name'] == subfield:
          count = count + t['count']
          total_work_count = total_work_count + t['count']
      if count > 0:
        subfield_list.append((institution, count))
    except:  # noqa: E722
      continue

  subfield_list.sort(key=lambda x: x[1], reverse=True)
  extra_metadata['work_count'] = total_work_count

  nodes = []
  edges = []
  nodes.append({ 'id': id, 'label': subfield, 'type': 'TOPIC' })
  for i, c in subfield_list:
    if not c == 0:
      nodes.append({ 'id': i, 'label': i, 'type': 'INSTITUTION' })
      nodes.append({'id': c, 'label': c, 'type': "NUMBER"})
      edges.append({ 'id': f"""{i}-{id}""", 'start': i, 'end': id, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
      edges.append({ 'id': f"""{i}-{c}""", 'start': i, 'end': c, "label": "number", "start_type": "INSTITUTION", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}
  return subfield_list, graph, extra_metadata

def get_institution_and_topic_metadata_sparql(institution, topic):
  """
  Given a topic and institution, collects the metadata for the 2 and returns as one dictionary.

  Returns:
  metadata : information on the topic and institution as a dictionary with the following keys:
    institution_name, topic_name, work_count, cited_by_count, ror, topic_clusters, people_count, topic_oa_link, institution_oa_link, homepage
  """
  institution_data = get_institution_metadata_sparql(institution)
  topic_data = get_subfield_metadata_sparql(topic)
  if topic_data == {} or institution_data == {}:
    return {}

  institution_name = institution
  subfield_name = topic
  ror = institution_data['ror']
  topic_cluster = topic_data['topic_clusters']
  topic_oa = topic_data['oa_link']
  institution_oa = institution_data['oa_link']
  institution_url = institution_data['homepage']
  work_count = institution_data['works_count']
  cited_by_count = institution_data['cited_count']
  people_count = institution_data['author_count']
  return {"institution_name": institution_name, "topic_name": subfield_name, "work_count": work_count, "cited_by_count": cited_by_count, "ror": ror, "topic_clusters": topic_cluster, "people_count": people_count, "topic_oa_link": topic_oa, "institution_oa_link": institution_oa, "homepage": institution_url}

def list_given_institution_topic(institution, institution_id, topic, topic_id):
    """
    When an user searches for an institution and topic
    Uses a SemOpenAlex query to retrieve authors who work at the given institution and have published
    papers relating to the provided subfield.
    """
    app.logger.debug(f"Building list for institution: {institution} and topic: {topic}")
    query = f"""
    SELECT DISTINCT ?author ?name (GROUP_CONCAT(DISTINCT ?work; SEPARATOR=", ") AS ?works) WHERE {"{"}
    ?institution <http://xmlns.com/foaf/0.1/name> "{institution}" .
    ?author <http://www.w3.org/ns/org#memberOf> ?institution .
    ?author <http://xmlns.com/foaf/0.1/name> ?name .
    ?work <http://purl.org/dc/terms/creator> ?author .
    ?subfield a <https://semopenalex.org/ontology/Subfield> .
    ?subfield <http://www.w3.org/2004/02/skos/core#prefLabel> "{topic}" .
    ?topic <http://www.w3.org/2004/02/skos/core#broader> ?subfield .
    ?work <https://semopenalex.org/ontology/hasTopic> ?topic .
    {"}"}
    GROUP BY ?author ?name
    """
    results = query_SPARQL_endpoint(SEMOPENALEX_SPARQL_ENDPOINT, query)
    works_list = []
    final_list = []
    work_count = 0
    app.logger.debug("Processing SPARQL results")
    for a in results:
        works_list.append((a['author'], a['name'], a['works'].count(",") + 1))
        final_list.append((a['name'], a['works'].count(",") + 1))
        work_count = work_count + a['works'].count(",") + 1

    final_list.sort(key=lambda x: x[1], reverse=True)
    num_people = len(final_list)

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    nodes.append({ 'id': topic_id, 'label': topic, 'type': 'TOPIC' })
    nodes.append({ 'id': institution_id, 'label': institution, 'type': 'INSTITUTION' })
    edges.append({ 'id': f"""{institution_id}-{topic_id}""", 'start': institution_id, 'end': topic_id, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
    
    for author, name, num_works in works_list:
        nodes.append({ 'id': author, 'label': name, 'type': 'AUTHOR' })
        nodes.append({ 'id': num_works, 'label': num_works, 'type': 'NUMBER' })
        edges.append({ 'id': f"""{author}-{institution_id}""", 'start': author, 'end': institution_id, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
        edges.append({ 'id': f"""{author}-{num_works}""", 'start': author, 'end': num_works, "label": "numWorks", "start_type": "AUTHOR", "end_type": "NUMBER"})
    
    graph = {"nodes": nodes, "edges": edges}
    extra_metadata = {"work_count": work_count, "num_people": num_people}
    
    app.logger.info(f"Successfully built list and graph for institution: {institution} and topic: {topic}")
    return final_list, graph, extra_metadata

def get_topic_and_researcher_metadata_sparql(topic, researcher):
  """
  Given a topic and researcher, collects the metadata for the 2 and returns as one dictionary.

  Returns:
  metadata : information on the topic and researcher as a dictionary with the following keys:
    researcher_name, topic_name, orcid, current_institution, work_count, cited_by_count, topic_clusters, researcher_oa_link, topic_oa_link
  """

  researcher_data = get_author_metadata_sparql(researcher)
  topic_data = get_subfield_metadata_sparql(topic)
  if researcher_data == {} or topic_data == {}:
    return {}

  researcher_name = researcher
  subfield_name = topic
  orcid = researcher_data['orcid']
  current_org = researcher_data['current_institution']
  work_count = researcher_data['work_count']
  cited_by_count = researcher_data['cited_by_count']
  topic_cluster = topic_data['topic_clusters']
  researcher_oa = researcher_data['oa_link']
  topic_oa = topic_data['oa_link']
  institution_oa = researcher_data['institution_url']
  return {"researcher_name": researcher_name, "topic_name": subfield_name, "orcid": orcid, "current_institution": current_org, "work_count": work_count, "cited_by_count": cited_by_count, "topic_clusters": topic_cluster, "researcher_oa_link": researcher_oa, "topic_oa_link": topic_oa, "institution_oa_link": institution_oa}

def list_given_researcher_topic(topic, researcher, institution, topic_id, researcher_id, institution_id):
    """
    When an user searches for a researcher and topic
    Uses a SemOpenAlex query to retrieve works by the author that are related to the topic.
    """
    app.logger.debug(f"Building list for researcher: {researcher} and topic: {topic}")
    query = f"""
    SELECT DISTINCT ?work ?title ?cited_by_count WHERE {"{"}
    ?author <http://xmlns.com/foaf/0.1/name> "{researcher}" .
    ?work <http://purl.org/dc/terms/creator> ?author .
    ?work <http://xmlns.com/foaf/0.1/name> ?title .
    ?work <https://semopenalex.org/ontology/citedByCount> ?cited_by_count .
    ?subfield a <https://semopenalex.org/ontology/Subfield> .
    ?subfield <http://www.w3.org/2004/02/skos/core#prefLabel> "{topic}" .
    ?topic <http://www.w3.org/2004/02/skos/core#broader> ?subfield .
    ?work <https://semopenalex.org/ontology/hasTopic> ?topic .
    {"}"}
    """
    results = query_SPARQL_endpoint(SEMOPENALEX_SPARQL_ENDPOINT, query)
    work_list = []
    total_citations = 0
    app.logger.debug("Processing SPARQL results")
    for r in results:
        work_list.append((r['title'], int(r['cited_by_count'])))
        total_citations = total_citations + int(r['cited_by_count'])
    work_list.sort(key=lambda x: x[1], reverse=True)

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    nodes.append({ 'id': institution_id, 'label': institution, 'type': 'INSTITUTION' })
    edges.append({ 'id': f"""{researcher_id}-{institution_id}""", 'start': researcher_id, 'end': institution_id, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
    nodes.append({ 'id': researcher_id, 'label': researcher, 'type': 'AUTHOR' })
    nodes.append({ 'id': topic_id, 'label': topic, 'type': 'TOPIC' })
    edges.append({ 'id': f"""{researcher_id}-{topic_id}""", 'start': researcher_id, 'end': topic_id, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
    
    for work, number in work_list:
        nodes.append({ 'id': work, 'label': work, 'type': 'WORK' })
        nodes.append({'id': number, 'label': number, 'type': "NUMBER"})
        edges.append({ 'id': f"""{researcher_id}-{work}""", 'start': researcher_id, 'end': work, "label": "authored", "start_type": "AUTHOR", "end_type": "WORK"})
        edges.append({ 'id': f"""{work}-{number}""", 'start': work, 'end': number, "label": "citedBy", "start_type": "WORK", "end_type": "NUMBER"})
    
    graph = {"nodes": nodes, "edges": edges}
    extra_metadata = {"work_count": len(work_list), "cited_by_count": total_citations}
    
    app.logger.info(f"Successfully built list and graph for researcher: {researcher} and topic: {topic}")
    return work_list, graph, extra_metadata

def get_institution_and_topic_and_researcher_metadata_sparql(institution, topic, researcher):
    """
    Given an institution, topic, and researcher, collects the metadata for the 3 and returns as one dictionary.
    """
    app.logger.debug(f"Fetching metadata for institution: {institution}, topic: {topic}, researcher: {researcher}")

    institution_data = get_institution_metadata_sparql(institution)
    topic_data = get_subfield_metadata_sparql(topic)
    researcher_data = get_author_metadata_sparql(researcher)
    
    if researcher_data == {} or institution_data == {} or topic_data == {}:
        app.logger.warning("Missing metadata from one or more entities")
        return {}

    app.logger.debug("Processing combined metadata")
    institution_url = institution_data['homepage']
    orcid = researcher_data['orcid']
    work_count = researcher_data['work_count']
    cited_by_count = researcher_data['cited_by_count']
    topic_cluster = topic_data['topic_clusters']
    topic_oa = topic_data['oa_link']
    institution_oa = institution_data['oa_link']
    researcher_oa = researcher_data['oa_link']
    ror = institution_data['ror']

    metadata = {
        "institution_name": institution, 
        "topic_name": topic, 
        "researcher_name": researcher, 
        "topic_oa_link": topic_oa, 
        "institution_oa_link": institution_oa, 
        "homepage": institution_url, 
        "orcid": orcid, 
        "topic_clusters": topic_cluster, 
        "researcher_oa_link": researcher_oa, 
        "work_count": work_count, 
        "cited_by_count": cited_by_count, 
        'ror': ror
    }

    app.logger.info(f"Successfully compiled metadata for {researcher} at {institution} researching {topic}")
    return metadata

def query_SQL_endpoint(connection, query):
    """
    Queries the endpoint to execute the SQL query.
    """
    app.logger.debug(f"Executing SQL query: {query}")
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        app.logger.info(f"SQL query returned {len(result)} results")
        return result
    except Error as e:
        app.logger.error(f"SQL query failed: {str(e)}")

@app.route('/autofill-institutions', methods=['POST'])
def autofill_institutions():
    """
    Handles autofill for institutions.
    """
    inst = request.json.get('institution')
    app.logger.debug(f"Processing institution autofill for: {inst}")
    
    possible_searches = []
    for i in autofill_inst_list:
        if inst.lower() in i.lower():
            possible_searches.append(i)
    
    app.logger.info(f"Found {len(possible_searches)} matching institutions for '{inst}'")
    return {"possible_searches": possible_searches}

@app.route('/autofill-topics', methods=['POST'])
def autofill_topics():
    """
    Handles autofill for topics.
    """
    topic = request.json.get('topic')
    app.logger.debug(f"Processing topic autofill for: {topic}")
    
    possible_searches = []
    if len(topic) > 0:
        if SUBFIELDS:
            for i in autofill_subfields_list:
                if topic.lower() in i.lower():
                    possible_searches.append(i)
        else:
            for i in autofill_topics_list:
                if topic.lower() in i.lower():
                    possible_searches.append(i)
    
    app.logger.info(f"Found {len(possible_searches)} matching topics for '{topic}'")
    return {"possible_searches": possible_searches}

@app.route('/get-default-graph', methods=['POST'])
def get_default_graph():
    """
    Returns the default graph.
    """
    app.logger.debug("Loading default graph from file")
    try:
        with open("default.json", "r") as file:
            graph = json.load(file)
    except Exception as e:
        app.logger.error(f"Failed to load default graph: {str(e)}")
        return {"error": "Failed to load default graph"}

    app.logger.debug("Processing default graph data")
    nodes = []
    edges = []
    cur_nodes = graph['nodes']
    cur_edges = graph['edges']
    most = {}
    needed_topics = set()
    
    # Process edges
    for edge in cur_edges:
        if edge['start'] in most:
            if edge['connecting_works'] > most[edge['start']]:
                most[edge['start']] = edge['connecting_works']
        else:
            most[edge['start']] = edge['connecting_works']
    
    for edge in cur_edges:
        if most[edge['start']] == edge['connecting_works']:
            edges.append(edge)
            needed_topics.add(edge['end'])
    
    # Process nodes
    for node in cur_nodes:
        if node['type'] == 'TOPIC':
            if node['id'] in needed_topics:
                nodes.append(node)
        else:
            nodes.append(node)
    
    final_graph = {"nodes": nodes, "edges": edges}
    #count = sum(1 for a in cur_nodes if a['type'] == "INSTITUTION")
    
    app.logger.info(f"Successfully processed default graph with {len(nodes)} nodes and {len(edges)} edges")
    return {"graph": final_graph}

@app.route('/get-topic-space-default-graph', methods=['POST'])
def get_topic_space():
    """
    Returns the default graph for the topic space.
    """
    app.logger.debug("Building topic space default graph")
    nodes = [
        { "id": 1, 'label': "Physical Sciences", 'type': 'DOMAIN'}, 
        { "id": 2, 'label': "Life Sciences", 'type': 'DOMAIN'}, 
        { "id": 3, 'label': "Social Sciences", 'type': 'DOMAIN'}, 
        { "id": 4, 'label': "Health Sciences", 'type': 'DOMAIN'}
    ]
    edges = []
    graph = {"nodes": nodes, "edges": edges}
    
    app.logger.info("Successfully built topic space default graph")
    return {"graph": graph}

@app.route('/search-topic-space', methods=['POST'])
def search_topic_space():
    """
    API call for searches from the user when searching the topic space.
    """
    search = request.json.get('topic')
    app.logger.debug(f"Searching topic space for: {search}")
    
    try:
        with open('topic_default.json', 'r') as file:
            graph = json.load(file)
    except Exception as e:
        app.logger.error(f"Failed to load topic space data: {str(e)}")
        return {"error": "Failed to load topic space data"}

    nodes = []
    edges = []
    matches_found = 0
    
    app.logger.debug("Processing topic space search results")
    for node in graph['nodes']:
        if (node['label'] == search or 
            node['subfield_name'] == search or 
            node['field_name'] == search or 
            node['domain_name'] == search or 
            search in node['keywords'].split("; ")):
            
            matches_found += 1
            node_additions = []
            edge_additions = []
            
            # Add topic node
            topic_node = {
                'id': node['id'],
                'label': node['label'],
                'type': 'TOPIC',
                "keywords": node['keywords'],
                "summary": node['summary'],
                "wikipedia_url": node['wikipedia_url']
            }
            node_additions.append(topic_node)
            
            # Add hierarchy nodes
            subfield_node = {
                "id": node["subfield_id"],
                'label': node['subfield_name'],
                'type': 'SUBFIELD'
            }
            node_additions.append(subfield_node)
            
            field_node = {
                "id": node["field_id"],
                'label': node['field_name'],
                'type': 'FIELD'
            }
            node_additions.append(field_node)
            
            domain_node = {
                "id": node["domain_id"],
                'label': node['domain_name'],
                'type': 'DOMAIN'
            }
            node_additions.append(domain_node)
            
            # Add hierarchy edges
            topic_subfield = {
                'id': f"""{node['id']}-{node['subfield_id']}""",
                'start': node['id'],
                'end': node['subfield_id'],
                "label": "hasSubfield",
                "start_type": "TOPIC",
                "end_type": "SUBFIELD"
            }
            edge_additions.append(topic_subfield)
            
            subfield_field = {
                'id': f"""{node['subfield_id']}-{node['field_id']}""",
                'start': node['subfield_id'],
                'end': node['field_id'],
                "label": "hasField",
                "start_type": "SUBFIELD",
                "end_type": "FIELD"
            }
            edge_additions.append(subfield_field)
            
            field_domain = {
                'id': f"""{node['field_id']}-{node['domain_id']}""",
                'start': node['field_id'],
                'end': node['domain_id'],
                "label": "hasDomain",
                "start_type": "FIELD",
                "end_type": "DOMAIN"
            }
            edge_additions.append(field_domain)
            
            # Add unique nodes and edges
            for a in node_additions:
                if a not in nodes:
                    nodes.append(a)
            for a in edge_additions:
                if a not in edges:
                    edges.append(a)

    final_graph = {"nodes": nodes, "edges": edges}
    app.logger.info(f"Found {matches_found} matches in topic space for '{search}'")
    return {'graph': final_graph}

def create_connection(host_name, user_name, user_password, db_name):
    """Create a sql database connection and return the connection object."""
    app.logger.debug(f"Attempting to connect to MySQL database: {db_name} at {host_name}")
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        app.logger.info("Successfully connected to MySQL database")
    except Error as e:
        app.logger.error(f"Failed to connect to MySQL database: {str(e)}")

    return connection

def is_HBCU(id):
    """
    Checks if an institution is an HBCU.
    """
    app.logger.debug(f"Checking HBCU status for institution ID: {id}")
    connection = create_connection('openalexalpha.mysql.database.azure.com', 'openalexreader', 'collabnext2024reader!', 'openalex')
    id = id.replace('https://openalex.org/institutions/', "")
    query = f"""SELECT HBCU FROM institutions_filtered WHERE id = "{id}";"""
    result = query_SQL_endpoint(connection, query)
    
    is_hbcu = result == [(1,)]
    app.logger.info(f"Institution {id} HBCU status: {is_hbcu}")
    return is_hbcu

def get_institution_mup_id(institution_name):
    app.logger.debug(f"Searching for MUP ID for institution: {institution_name}")
    institution_id = get_institution_id(institution_name)
    if not institution_id:
        app.logger.debug(f"No institution ID found for {institution_name}")
        return None
    
    query = """SELECT get_institution_mup_id(%s);"""
    results = execute_query(query, (institution_id,))
    if results:
        app.logger.info(f"Successfully fetched MUP ID for {institution_name}")
        return results[0][0]
    app.logger.info(f"No MUP ID found for {institution_name}")
    return None

def get_institution_sat_scores(institution_name):
    """Returns {institution_name: String, institution_id: String, data: a list of dictionaries containing 'sat', and 'year'}"""
    app.logger.debug(f"Searching for MUP SAT scores data for institution: {institution_name}")
    institution_id = get_institution_id(institution_name)
    if not institution_id:
        app.logger.debug(f"No institution ID found for {institution_name}")
        return None
    
    query = """SELECT get_institution_sat_scores(%s);"""
    results = execute_query(query, (institution_id,))
    if results:
        results[0][0]['institution_name'] = institution_name
        results[0][0]['institution_id'] = institution_id
        app.logger.info(f"Successfully fetched MUP SAT scores data for {institution_name}")
        return results[0][0]
    app.logger.info(f"No MUP SAT scores data found for {institution_name}")
    return None

def get_institution_endowments_and_givings(institution_name):
    """Returns {institution_name: String, institution_id: String, data: a list of dictionaries containing 'endowment', 'giving', and 'year'}"""
    app.logger.debug(f"Searching for MUP endowments and givings data for institution: {institution_name}")
    institution_id = get_institution_id(institution_name)
    if not institution_id:
        app.logger.debug(f"No institution ID found for {institution_name}")
        return None
    
    query = """SELECT get_institution_endowments_and_givings(%s);"""
    results = execute_query(query, (institution_id,))
    if results:
        results[0][0]['institution_name'] = institution_name
        results[0][0]['institution_id'] = institution_id
        app.logger.info(f"Successfully fetched MUP endowments and givings data for {institution_name}")
        return results[0][0]
    app.logger.info(f"No MUP endowments and givings data found for {institution_name}")
    return None

def get_institution_medical_expenses(institution_name):
    """Returns {institution_name: String, institution_mup_id: String, data: a list of dictionaries containing 'expenditure', and 'year'}"""
    app.logger.debug(f"Searching for MUP medical expenses data for institution: {institution_name}")
    institution_mup_id = get_institution_mup_id(institution_name)
    if not institution_mup_id:
        app.logger.debug(f"No institution MUP ID found for {institution_name}")
        return None
    
    institution_mup_id = institution_mup_id['institution_mup_id']
    query = """SELECT get_institution_medical_expenses(%s);"""
    results = execute_query(query, (institution_mup_id,))
    if results:
        results[0][0]['institution_name'] = institution_name
        results[0][0]['institution_mup_id'] = institution_mup_id
        app.logger.info(f"Successfully fetched MUP medical expenses data for {institution_name}")
        return results[0][0]
    app.logger.info(f"No MUP medical expenses data found for {institution_name}")
    return None

def get_institution_doctorates_and_postdocs(institution_name):
    """Returns {institution_name: String, institution_id: String, data: a list of dictionaries containing 'num_postdocs', 'num_doctorates', and 'year'}"""
    app.logger.debug(f"Searching for MUP doctorates and postdocs data for institution: {institution_name}")
    institution_id = get_institution_id(institution_name)
    if not institution_id:
        app.logger.debug(f"No institution ID found for {institution_name}")
        return None
    
    query = """SELECT get_institution_doctorates_and_postdocs(%s);"""
    results = execute_query(query, (institution_id,))
    if results:
        results[0][0]['institution_name'] = institution_name
        results[0][0]['institution_id'] = institution_id
        app.logger.info(f"Successfully fetched MUP doctorates and postdocs data for {institution_name}")
        return results[0][0]
    app.logger.info(f"No MUP doctorates and postdocs data found for {institution_name}")
    return None

def get_institution_num_of_researches(institution_name):
    """Returns {institution_name: String, institution_id: String, data: a list of dictionaries containing 'num_federal_research', 'num_nonfederal_research', 'total_research', and 'year'}"""
    app.logger.debug(f"Searching for MUP number of researches data for institution: {institution_name}")
    institution_id = get_institution_id(institution_name)
    if not institution_id:
        app.logger.debug(f"No institution ID found for {institution_name}")
        return None
    
    query = """SELECT get_institution_num_of_researches(%s);"""
    results = execute_query(query, (institution_id,))
    if results:
        results[0][0]['institution_name'] = institution_name
        results[0][0]['institution_id'] = institution_id
        app.logger.info(f"Successfully fetched MUP number of researchers data for {institution_name}")
        return results[0][0]
    app.logger.info(f"No MUP number of researchers data found for {institution_name}")
    return None

def get_institutions_faculty_awards(institution_name):
    """Returns {institution_name: String, institution_id: String, data: a list of dictionaries containing 'nae', 'nam', 'nas', 'num_fac_awards', and 'year'}"""
    app.logger.debug(f"Searching for MUP faculty awards data for institution: {institution_name}")
    institution_id = get_institution_id(institution_name)
    if not institution_id:
        app.logger.debug(f"No institution ID found for {institution_name}")
        return None

    query = """SELECT get_institutions_faculty_awards(%s);"""
    results = execute_query(query, (institution_id,))
    if results:
        results[0][0]['institution_name'] = institution_name
        results[0][0]['institution_id'] = institution_id
        app.logger.info(f"Successfully fetched MUP faculty awards data for {institution_name}")
        return results[0][0]
    app.logger.info(f"No MUP faculty awards data found for {institution_name}")
    return None

def get_institutions_r_and_d(institution_name):
    """Returns {institution_name: String, institution_id: String, data: a list of dictionaries containing 'category', 'federal', 'percent_federal', 'total', and 'percent_total'}"""
    app.logger.debug(f"Searching for MUP R&D data for institution: {institution_name}")
    institution_id = get_institution_id(institution_name)
    if not institution_id:
        app.logger.debug(f"No institution ID found for {institution_name}")
        return None

    query = """SELECT get_institutions_r_and_d(%s);"""
    results = execute_query(query, (institution_id,))
    if results:
        results[0][0]['institution_name'] = institution_name
        results[0][0]['institution_id'] = institution_id
        app.logger.info(f"Successfully fetched MUP R&D data for {institution_name}")
        return results[0][0]
    app.logger.info(f"No MUP R&D datafound for {institution_name}")
    return None

def combine_graphs(graph1, graph2):
  dup_nodes = graph1['nodes'] + graph2['nodes']
  dup_edges = graph1['edges'] + graph2['edges']
  final_nodes = list({tuple(d.items()): d for d in dup_nodes}.values())
  final_edges = list({tuple(d.items()): d for d in dup_edges}.values())
  return {"nodes": final_nodes, "edges": final_edges}

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve static files and handle frontend routing."""
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        app.logger.debug(f"Serving static file: {path}")
        return send_from_directory(app.static_folder, path)
    
    app.logger.debug("Serving index.html for frontend routing")
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/get-institutions', methods=['GET'])
def get_institutions():
    """
    Returns the contents of the institutions.csv file as JSON.
    """
    try:
        with open('institutions.csv', 'r') as file:
            institutions = file.read().split(',\n')
        return jsonify(institutions=institutions)
    except Exception as e:
        return jsonify(error=str(e)), 500

# MUP ENDPOINTS
@app.route('/get-mup-id', methods=['POST'])
def get_mup_id():
    data = request.json
    if not data or 'institution_name' not in data:
        abort(400, description="Missing 'institution_name' in request data")

    institution_name = data['institution_name']
    result = get_institution_mup_id(institution_name)
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "No MUP ID found"}), 404

@app.route('/mup-sat-scores', methods=['POST'])
def get_sat_scores():
    data = request.json
    if not data or 'institution_name' not in data:
        abort(400, description="Missing 'institution_name' in request data")

    institution_name = data['institution_name']
    result = get_institution_sat_scores(institution_name)
    if result:
        return jsonify(result)
    else:
        abort(404, description=f"No SAT scores found for {institution_name}")

@app.route('/endowments-and-givings', methods=['POST'])
def get_endowments_and_givings():
    data = request.json
    if not data or 'institution_name' not in data:
        abort(400, description="Missing 'institution_name' in request data")
    
    institution_name = data['institution_name']
    result = get_institution_endowments_and_givings(institution_name)
    if result:
        return jsonify(result)
    else:
        abort(404, description=f"No data found for {institution_name}")

@app.route('/institution_num_of_researches', methods=['POST'])
def institution_num_of_researches():
    data = request.get_json()
    institution_name = data.get('institution_name')
    result = get_institution_num_of_researches(institution_name)
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "No data found"}), 404

@app.route('/institution_medical_expenses', methods=['POST'])
def institution_medical_expenses():
    data = request.get_json()
    institution_name = data.get('institution_name')
    result = get_institution_medical_expenses(institution_name)
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "No data found"}), 404

@app.route('/institution_doctorates_and_postdocs', methods=['POST'])
def institution_doctorates_and_postdocs():
    data = request.get_json()
    institution_name = data.get('institution_name')
    result = get_institution_doctorates_and_postdocs(institution_name)
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "No data found"}), 404

@app.route('/mup-faculty-awards', methods=['POST'])
def get_faculty_awards():
    data = request.json
    if not data or 'institution_name' not in data:
        abort(400, description="Missing 'institution_name' in request data")

    institution_name = data['institution_name']
    result = get_institutions_faculty_awards(institution_name)
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "No faculty awards found"}), 404

@app.route('/mup-r-and-d', methods=['POST'])
def get_r_and_d():
    data = request.json
    if not data or 'institution_name' not in data:
        abort(400, description="Missing 'institution_name' in request data")

    institution_name = data['institution_name']
    result = get_institutions_r_and_d(institution_name)
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "No R&D numbers found"}), 404

## Main 
if __name__ =='__main__':
  app.logger.info("Starting Flask application")
  app.run()