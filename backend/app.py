import os
import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

import requests
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import psycopg2

# -----------------------------------------------------------------------------
# As per my usage I have an absolute base directory for data files to put
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Load up the environment variables in the loop
try:
    DB_HOST = os.environ["DB_HOST"]
    DB_PORT = int(os.environ["DB_PORT"])
    DB_NAME = os.environ["DB_NAME"]
    DB_USER = os.environ["DB_USER"]
    DB_PASSWORD = os.environ["DB_PASSWORD"]
    API = os.getenv("DB_API")
except:
    logger = logging.getLogger(__name__)
    logger.warning("Using Local Variables")
    load_dotenv(dotenv_path=".env")
    API = os.getenv("DB_API")
# Global variable needs to be kept for the SPARQL endpoint
SEMOPENALEX_SPARQL_ENDPOINT = "https://semopenalex.org/sparql"
app = Flask(__name__, static_folder="build", static_url_path="/")
CORS(app)


def setup_logger():
    """Configure logging with rotating file handler for all levels"""
    log_path = "/home/LogFiles" if os.environ.get(
        "WEBSITE_SITE_NAME") else "logs"
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handlers = {
        "debug": RotatingFileHandler(
            os.path.join(log_path, "debug.log"), maxBytes=15 * 1024 * 1024, backupCount=3
        ),
        "info": RotatingFileHandler(
            os.path.join(log_path, "info.log"), maxBytes=15 * 1024 * 1024, backupCount=3
        ),
        "warning": RotatingFileHandler(
            os.path.join(log_path, "warning.log"), maxBytes=10 * 1024 * 1024, backupCount=3
        ),
        "error": RotatingFileHandler(
            os.path.join(log_path, "error.log"), maxBytes=5 * 1024 * 1024, backupCount=3
        ),
        "critical": RotatingFileHandler(
            os.path.join(log_path, "critical.log"), maxBytes=2 * 1024 * 1024, backupCount=3
        ),
    }
    handlers["debug"].setLevel(logging.DEBUG)
    handlers["info"].setLevel(logging.INFO)
    handlers["warning"].setLevel(logging.WARNING)
    handlers["error"].setLevel(logging.ERROR)
    handlers["critical"].setLevel(logging.CRITICAL)
    for h in handlers.values():
        h.setFormatter(formatter)
    logger_ = logging.getLogger("flask.app")
    logger_.setLevel(logging.DEBUG)
    for h in handlers.values():
        logger_.addHandler(h)
    return logger_


# Watch and initialize the logger
logger = setup_logger()
app.logger.handlers = logger.handlers
app.logger.setLevel(logger.level)


def execute_query(query, params):
    """
    We definitely know more about the utility function than we do about executing a query and fetching the results from the database. That's why we need to handle the connection and the management of the cursor.
    """
    try:
        with psycopg2.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            sslmode="disable",
        ) as connection:
            app.logger.debug(f"Executing query: {query} with params: {params}")
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                app.logger.info(
                    f"Query executed successfully, returned {len(results)} results"
                )
                return results
    except Exception as e:
        app.logger.error(f"Database error: {str(e)}")
        return None


def fetch_last_known_institutions(raw_id: str) -> list:
    """
    Makes a question in my opinion, to send a request to the OpenAlex Application Programming Interface which is the way forward to "fetch" the last known institutions for a given author ID.
    """
    try:
        just_id = raw_id.split("/")[-1]
        response = requests.get(f"https://api.openalex.org/authors/{just_id}")
        data = response.json()
        return data.get("last_known_institutions", [])
    except Exception as e:
        logger.error(
            f"Error fetching last known institutions for id {just_id}: {str(e)}")
        return []


def get_author_ids(author_name):
    app.logger.debug(f"Getting author IDs for: {author_name}")
    query = """SELECT get_author_id(%s);"""
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
            app.logger.warning(
                f"No institution ID found for {institution_name}")
            return None
        app.logger.info(f"Found institution ID for {institution_name}")
        return results[0][0]["institution_id"]
    app.logger.warning(
        f"Query returned no results for institution {institution_name}")
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


def search_by_author_institution_topic(author_name, institution_name, topic_name):
    app.logger.debug(
        f"Searching by author, institution, and topic: "
        f"{author_name}, {institution_name}, {topic_name}"
    )
    author_ids = get_author_ids(author_name)
    if not author_ids:
        app.logger.warning(f"No author IDs found for {author_name}")
        return None

    author_id = author_ids[0]["author_id"]
    app.logger.debug(f"Using author ID: {author_id}")

    institution_id = get_institution_id(institution_name)
    if institution_id is None:
        app.logger.warning(f"No institution ID found for {institution_name}")
        return None

    query = """SELECT search_by_author_institution_topic(%s, %s, %s);"""
    results = execute_query(query, (author_id, institution_id, topic_name))
    if results:
        app.logger.info(
            "Found results for local testing for author-institution-topic search")
        return results[0][0]
    app.logger.warning("No results found for author-institution-topic search")
    return None


def search_by_author_institution(author_name, institution_name):
    app.logger.debug(
        f"Searching by author and institution: {author_name}, {institution_name}"
    )
    author_ids = get_author_ids(author_name)
    if not author_ids:
        app.logger.warning(f"No author IDs found for {author_name}")
        return None

    author_id = author_ids[0]["author_id"]
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
    app.logger.debug(
        f"Searching by institution and topic: {institution_name}, {topic_name}"
    )
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
    app.logger.debug(
        f"Searching by author and topic: {author_name}, {topic_name}")
    author_ids = get_author_ids(author_name)
    if not author_ids:
        app.logger.warning(f"No author IDs found for {author_name}")
        return None

    author_id = author_ids[0]["author_id"]
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


def search_by_institution(institution_name):
    app.logger.debug(f"Searching by institution: {institution_name}")
    institution_id = get_institution_id(institution_name)
    if institution_id is None:
        app.logger.warning(f"No institution ID found for {institution_name}")
        return None

    query = """SELECT search_by_institution(%s);"""
    results = execute_query(query, (institution_id,))
    if results:
        app.logger.info(
            f"Found results for institution search: {institution_name}")
        return results[0][0]
    app.logger.warning(f"No results found for institution: {institution_name}")
    return None


# -----------------------------------------------------------------------------
# While Flask has inbuilt logging with 5 levels of severity, we don't have any such thing for CSV files so we load them with absolute paths
# -----------------------------------------------------------------------------
institutions_csv_path = os.path.join(BASE_DIR, "institutions.csv")
subfields_csv_path = os.path.join(BASE_DIR, "subfields.csv")
with open(institutions_csv_path, "r") as file:
    autofill_inst_list = file.read().split(",\n")
with open(subfields_csv_path, "r") as file:
    autofill_subfields_list = file.read().split("\n")
SUBFIELDS = True
if not SUBFIELDS:
    keywords_csv_path = os.path.join(BASE_DIR, "keywords.csv")
    with open(keywords_csv_path, "r") as fil:
        autofill_topics_list = fil.read().split("\n")


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def index(path):
    return send_from_directory(app.static_folder, "index.html")


@app.errorhandler(404)
def not_found(e):
    app.logger.warning(f"404 error: {request.url}")
    return send_from_directory(app.static_folder, "index.html")


@app.errorhandler(500)
def server_error(e):
    app.logger.error(f"500 error: {str(e)}")
    return "Internal Server Error", 500


@app.route("/initial-search", methods=["POST"])
def initial_search():
    """
    The API call is what we do for the searches we make from the user. Once the user makes a search we delete it and call "other" methods depending on what the user inputted.

    I am not the person to expect this, that the frontend passes this in:
      organization (string)
      researcher   (string)
      topic        (string)
      type         (string) (for now, always HBCU)

    Returns a dictionary with the following:
      metadata : ...
      graph    : { nodes: [], edges: [] }
      list     : ...
    """
    institution = request.json.get("organization", "")
    researcher = request.json.get("researcher", "")
    researcher = researcher.title()
    type_ = request.json.get("type", "")
    topic = request.json.get("topic", "")
    app.logger.info(
        f"Received search request - Institution: {institution}, "
        f"Researcher: {researcher}, Topic: {topic}, Type: {type_}"
    )
    try:
        if institution and researcher and topic:
            results = get_institution_researcher_subfield_results(
                institution, researcher, topic
            )
        elif institution and researcher:
            results = get_institution_and_researcher_results(
                institution, researcher)
        elif institution and topic:
            results = get_institution_and_subfield_results(institution, topic)
        elif researcher and topic:
            results = get_researcher_and_subfield_results(researcher, topic)
        elif topic:
            results = get_subfield_results(topic)
        elif institution:
            results = get_institution_results(institution)
        elif researcher:
            results = get_researcher_result(researcher)
        else:
            results = None
        if not results:
            app.logger.warning("Search returned no results")
            return {}
        app.logger.info("Search completed successfully")
        return results
    except Exception as e:
        app.logger.critical(f"Critical error during search: {str(e)}")
        return {"error": "An unexpected error occurred"}
# -----------------------------------------------------------------------------
# The rest of the `get_institution_results`, `get_subfield_results`, etc.
# they do remain unchanged except for, we might add absolute path logic for the
# JSON loads which means that we have to integrate the GET functions with our tests.
# What we have to do is look at the `get_default_graph` as well as the `search_topic_space`
# below and when we do we will see that our Dockerized application is functioning
# correctly in accordance with the application of the database.
# -----------------------------------------------------------------------------
# Thus follows the identical functions, we're not modifying the wrappers we're modifying
# what we expect which is to see that we just need to change the test results in
# each test function platform variable to mock get_researcher_result, etc.


def get_researcher_result(researcher):
    """
    Response comes faster to a direct query of one paragraph than 13 long messages.
    That's correct that the user only inputs a researcher, it's just the only
    question that we have is is the user going to only input one researcher and then
    how is our test function utilizing the existing database to get the result? If we're using the database then
    We should be able to default to SPARQL and write a test case for when the user..
    the researcher is not in the database.
    """
    data = search_by_author(researcher)
    if data is None:
        app.logger.info("No database results, falling back to SPARQL...")
        data = get_author_metadata_sparql(researcher)
        if data == {}:
            app.logger.warning("No results found in SPARQL for researcher")
            return {}
        topic_list, graph = list_given_researcher_institution(
            data['oa_link'], data['name'], data['current_institution'])
        results = {"metadata": data, "graph": graph, "list": topic_list}
        app.logger.info(
            f"Successfully retrieved SPARQL results for researcher: {researcher}")
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
    nodes.append({'id': last_known_institution,
                 'label': last_known_institution, 'type': 'INSTITUTION'})
    edges.append({'id': f"""{metadata['openalex_url']}-{last_known_institution}""", 'start': metadata['openalex_url'],
                 'end': last_known_institution, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
    nodes.append({'id': metadata['openalex_url'],
                 'label': researcher, "type": "AUTHOR"})

    for entry in data['data']:
        topic = entry['topic']
        num_works = entry['num_of_works']
        list.append((topic, num_works))
        nodes.append({'id': topic, 'label': topic, 'type': "TOPIC"})
        number_id = topic + ":" + str(num_works)
        nodes.append({'id': number_id, 'label': num_works, 'type': "NUMBER"})
        edges.append({'id': f"""{metadata['openalex_url']}-{topic}""", 'start': metadata['openalex_url'],
                     'end': topic, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
        edges.append({'id': f"""{metadata['openalex_url']}-{number_id}""", 'start': topic,
                     'end': number_id, "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})

    graph = {"nodes": nodes, "edges": edges}
    app.logger.info(f"Successfully built result for researcher: {researcher}")
    return {"metadata": metadata, "graph": graph, "list": list}


def get_institution_results(institution):
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
        topic_list, graph = list_given_institution(
            data['ror'], data['name'], data['oa_link'])
        results = {"metadata": data, "graph": graph, "list": topic_list}
        app.logger.info(
            f"Successfully retrieved SPARQL results for institution: {institution}")
        return results

    app.logger.debug("Processing database results for institution")
    list = []
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
    institution_id = metadata['openalex_url']
    nodes.append(
        {'id': institution_id, 'label': institution, 'type': 'INSTITUTION'})

    for entry in data['data']:
        subfield = entry['topic_subfield']
        number = entry['num_of_authors']
        list.append((subfield, number))
        nodes.append({'id': subfield, 'label': subfield, 'type': "TOPIC"})
        number_id = subfield + ":" + str(number)
        nodes.append({'id': number_id, 'label': number, 'type': "NUMBER"})
        edges.append({'id': f"""{institution_id}-{subfield}""", 'start': institution_id,
                     'end': subfield, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
        edges.append({'id': f"""{subfield}-{number_id}""", 'start': subfield,
                     'end': number_id, "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})

    graph = {"nodes": nodes, "edges": edges}
    app.logger.info(
        f"Successfully built result for institution: {institution}")
    return {"metadata": metadata, "graph": graph, "list": list}


def get_subfield_results(topic):
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
    topic_id = topic
    nodes.append({'id': topic_id, 'label': topic, 'type': 'TOPIC'})

    for entry in data['data']:
        institution = entry['institution_name']
        number = entry['num_of_authors']
        list.append((institution, number))
        nodes.append(
            {'id': institution, 'label': institution, 'type': 'INSTITUTION'})
        nodes.append({'id': number, 'label': number, 'type': "NUMBER"})
        edges.append({'id': f"""{institution}-{topic_id}""", 'start': institution, 'end': topic_id,
                     "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
        edges.append({'id': f"""{institution}-{number}""", 'start': institution, 'end': number,
                     "label": "number", "start_type": "INSTITUTION", "end_type": "NUMBER"})

    graph = {"nodes": nodes, "edges": edges}
    app.logger.info(f"Successfully built result for topic: {topic}")
    return {"metadata": metadata, "graph": graph, "list": list}


def get_researcher_and_subfield_results(researcher, topic):
    """
    These are all correlated, we could do something like denormalization for our
    test cases. Here we have to get the results when the user inputs a research
    object as well as a subfield..thus we use the database to get the result and then
    we default to SPARQL if the researcher is not in the database.
    """
    data = search_by_author_topic(researcher, topic)
    if data is None:
        app.logger.info("No database results, falling back to SPARQL...")
        data = get_topic_and_researcher_metadata_sparql(topic, researcher)
        if data == {}:
            app.logger.warning(
                "No results found in SPARQL for researcher and topic")
            return {}
        work_list, graph, extra_metadata = list_given_researcher_topic(
            topic, researcher, data['current_institution'], data['topic_oa_link'], data['researcher_oa_link'], data['institution_oa_link'])
        data['work_count'] = extra_metadata['work_count']
        data['cited_by_count'] = extra_metadata['cited_by_count']
        results = {"metadata": data, "graph": graph, "list": work_list}
        app.logger.info(
            f"Successfully retrieved SPARQL results for researcher: {researcher} and topic: {topic}")
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
        institution_object = fetch_last_known_institutions(
            metadata['researcher_oa_link'])[0]
        metadata['current_institution'] = institution_object['display_name']
    else:
        metadata['current_institution'] = data['author_metadata']['last_known_institution']
    last_known_institution = metadata['current_institution']

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    researcher_id = metadata['researcher_oa_link']
    subfield_id = metadata['topic_oa_link']
    nodes.append({'id': last_known_institution,
                 'label': last_known_institution, 'type': 'INSTITUTION'})
    edges.append({'id': f"""{researcher_id}-{last_known_institution}""", 'start': researcher_id,
                 'end': last_known_institution, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
    nodes.append({'id': researcher_id, 'label': researcher, 'type': 'AUTHOR'})
    nodes.append({'id': subfield_id, 'label': topic, 'type': 'TOPIC'})
    edges.append({'id': f"""{researcher_id}-{subfield_id}""", 'start': researcher_id,
                 'end': subfield_id, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})

    for entry in data['data']:
        work = entry['work_name']
        number = entry['num_of_citations']
        list.append((work, number))
        nodes.append({'id': work, 'label': work, 'type': 'WORK'})
        nodes.append({'id': number, 'label': number, 'type': "NUMBER"})
        edges.append({'id': f"""{researcher_id}-{work}""", 'start': researcher_id,
                     'end': work, "label": "authored", "start_type": "AUTHOR", "end_type": "WORK"})
        edges.append({'id': f"""{work}-{number}""", 'start': work, 'end': number,
                     "label": "citedBy", "start_type": "WORK", "end_type": "NUMBER"})

    graph = {"nodes": nodes, "edges": edges}
    app.logger.info(
        f"Successfully built result for researcher: {researcher} and topic: {topic}")
    return {"metadata": metadata, "graph": graph, "list": list}


def get_institution_and_subfield_results(institution, topic):
    """
    Main get institution function. Every get function seems to be bundled with,
    what happens when the user inputs an institution and subfield. Then we do,
    we use the database to get the result and then default to SPARQL if the
    institution is not in the database.
    """
    data = search_by_institution_topic(institution, topic)
    if data is None:
        app.logger.info("Using SPARQL for institution and topic search...")
        data = get_institution_and_topic_metadata_sparql(institution, topic)
        if data == {}:
            app.logger.warning(
                "No results found in SPARQL for institution and topic")
            return {}
        topic_list, graph, extra_metadata = list_given_institution_topic(
            institution, data['institution_oa_link'], topic, data['topic_oa_link'])
        data['work_count'] = extra_metadata['work_count']
        data['people_count'] = extra_metadata['num_people']
        results = {"metadata": data, "graph": graph, "list": topic_list}
        app.logger.info(
            f"Successfully retrieved SPARQL results for institution: {institution} and topic: {topic}")
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
    metadata['people_count'] = data['totals']['total_num_of_authors']
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
    nodes.append({'id': subfield_id, 'label': topic, 'type': 'TOPIC'})
    nodes.append(
        {'id': institution_id, 'label': institution, 'type': 'INSTITUTION'})
    edges.append({'id': f"""{institution_id}-{subfield_id}""", 'start': institution_id,
                 'end': subfield_id, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})

    for entry in data['data']:
        author_id = entry['author_id']
        author_name = entry['author_name']
        number = entry['num_of_works']
        list.append((author_name, number))
        nodes.append({'id': author_id, 'label': author_name, 'type': 'AUTHOR'})
        nodes.append({'id': number, 'label': number, 'type': 'NUMBER'})
        edges.append({'id': f"""{author_id}-{number}""", 'start': author_id, 'end': number,
                     "label": "numWorks", "start_type": "AUTHOR", "end_type": "NUMBER"})
        edges.append({'id': f"""{author_id}-{institution_id}""", 'start': author_id, 'end': institution_id,
                     "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})

    graph = {"nodes": nodes, "edges": edges}
    metadata['people_count'] = len(list)
    app.logger.info(
        f"Successfully built result for institution: {institution} and topic: {topic}")
    return {"metadata": metadata, "graph": graph, "list": list}


def get_institution_and_researcher_results(institution, researcher):
    """
    I was wonder if we can test this by getting the results with the mock cases..
    how can we mock the experience of what happens when the user inputs an institution
    and researcher? Well, we can use the database to get the result and then default
    to SPARQL if the institution or researcher is not in the database.
    """
    data = search_by_author_institution(researcher, institution)
    if data is None:
        app.logger.info(
            "Using SPARQL for institution and researcher search...")
        data = get_researcher_and_institution_metadata_sparql(
            researcher, institution)
        if data == {}:
            app.logger.warning(
                "No results found in SPARQL for institution and researcher")
            return {}
        topic_list, graph = list_given_researcher_institution(
            data['researcher_oa_link'], researcher, institution)
        results = {"metadata": data, "graph": graph, "list": topic_list}
        app.logger.info(
            f"Successfully retrieved SPARQL results for researcher: {researcher} and institution: {institution}")
        return results

    app.logger.debug(
        "Processing database results for institution and researcher")
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
    # last_known_institution = metadata['current_institution']
    metadata['work_count'] = data['author_metadata']['num_of_works']
    metadata['cited_by_count'] = data['author_metadata']['num_of_citations']

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    author_id = metadata['researcher_oa_link']
    nodes.append(
        {'id': institution, 'label': institution, 'type': 'INSTITUTION'})
    edges.append({'id': f"""{author_id}-{institution}""", 'start': author_id, 'end': institution,
                 "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
    nodes.append({'id': author_id, 'label': researcher, "type": "AUTHOR"})

    for entry in data['data']:
        topic_name = entry['topic_name']
        num_works = entry["num_of_works"]
        list.append((topic_name, num_works))
        nodes.append({'id': topic_name, 'label': topic_name, 'type': "TOPIC"})
        number_id = topic_name + ":" + str(num_works)
        nodes.append({'id': number_id, 'label': num_works, 'type': "NUMBER"})
        edges.append({'id': f"""{author_id}-{topic_name}""", 'start': author_id, 'end': topic_name,
                     "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
        edges.append({'id': f"""{topic_name}-{number_id}""", 'start': topic_name,
                     'end': number_id, "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})

    graph = {"nodes": nodes, "edges": edges}
    app.logger.info(
        f"Successfully built result for researcher: {researcher} and institution: {institution}")
    return {"metadata": metadata, "graph": graph, "list": list}


def get_institution_researcher_subfield_results(institution, researcher, topic):
    """
    Some minor results, these are the results that the user gets when the user inputs
    an institution & researcher & subfield..uses the database, to get result and then
    defaults to SPARQL if the institution or the researcher is not in the database.
    """
    data = search_by_author_institution_topic(researcher, institution, topic)
    if data is None:
        app.logger.info(
            "Using SPARQL for institution, researcher, and topic search...")
        data = get_institution_and_topic_and_researcher_metadata_sparql(
            institution, topic, researcher)
        if data == {}:
            app.logger.warning(
                "No results found in SPARQL for institution, researcher, and topic")
            return {}
        work_list, graph, extra_metadata = list_given_researcher_topic(
            topic, researcher, institution, data['topic_oa_link'], data['researcher_oa_link'], data['institution_oa_link'])
        data['work_count'] = extra_metadata['work_count']
        data['cited_by_count'] = extra_metadata['cited_by_count']
        results = {"metadata": data, "graph": graph, "list": work_list}
        app.logger.info(
            f"Successfully retrieved SPARQL results for researcher: {researcher}, institution: {institution}, and topic: {topic}")
        return results

    app.logger.debug(
        "Processing database results for institution, researcher, and topic")
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
    # last_known_institution = metadata['current_institution']

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
    nodes.append(
        {'id': institution_id, 'label': institution, 'type': 'INSTITUTION'})
    edges.append({'id': f"""{researcher_id}-{institution_id}""", 'start': researcher_id,
                 'end': institution_id, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
    nodes.append({'id': researcher_id, 'label': researcher, 'type': 'AUTHOR'})
    nodes.append({'id': subfield_id, 'label': topic, 'type': 'TOPIC'})
    edges.append({'id': f"""{researcher_id}-{subfield_id}""", 'start': researcher_id,
                 'end': subfield_id, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})

    for entry in data['data']:
        work_name = entry['work_name']
        number = entry['cited_by_count']
        list.append((work_name, number))
        nodes.append({'id': work_name, 'label': work_name, 'type': 'WORK'})
        nodes.append({'id': number, 'label': number, 'type': "NUMBER"})
        edges.append({'id': f"""{researcher_id}-{work_name}""", 'start': researcher_id,
                     'end': work_name, "label": "authored", "start_type": "AUTHOR", "end_type": "WORK"})
        edges.append({'id': f"""{work_name}-{number}""", 'start': work_name, 'end': number,
                     "label": "citedBy", "start_type": "WORK", "end_type": "NUMBER"})

    graph = {"nodes": nodes, "edges": edges}
    app.logger.info(
        f"Successfully built result for researcher: {researcher}, institution: {institution}, and topic: {topic}")
    return {"metadata": metadata, "graph": graph, "list": list}


def query_SPARQL_endpoint(endpoint_url, query):
    """
    Queries the endpoint to execute the SPARQL query. ✨
    """
    app.logger.debug(f"Executing SPARQL query: {query}")
    try:
        response = requests.post(endpoint_url, data={"query": query}, headers={
                                 'Accept': 'application/json'})
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


def get_institution_metadata_sparql(institution):
    """
    Proposed test task addition for backend: given an institution, make sure that we are querying the SemOpenAlex endpoint to retrieve metadata on the institution.
    """
    app.logger.debug(
        f"Fetching institution metadata from SPARQL for: {institution}")
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
        app.logger.warning(
            f"No SPARQL results found for institution: {institution}")
        return {}

    app.logger.debug("Processing SPARQL results for institution")
    ror = results[0]['ror']
    works_count = results[0]['workscount']
    cited_count = results[0]['citedcount']
    homepage = results[0]['homepage']
    author_count = results[0]['peoplecount']
    oa_link = results[0]['institution']
    oa_link = oa_link.replace('semopenalex', 'openalex').replace(
        'institution', 'institutions')
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
    app.logger.info(
        f"Successfully retrieved metadata for institution: {institution}")
    return metadata


def list_given_institution(ror, name, id):
    """
    Before we get the institution we have to use OpenAlex to determine the sub-fields which a given institution studies..thus we "must" iterate through all authors related to the institution and then determine what topics OpenAlex attributes, to them.
    """
    app.logger.debug(
        f"Fetching subfields for institution: {name} (ROR: {ror})")
    final_subfield_count = {}
    headers = {'Accept': 'application/json'}
    response = requests.get(
        f'https://api.openalex.org/authors?per-page=200&filter=last_known_institutions.ror:{ror}&cursor=*', headers=headers)
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
                    final_subfield_count[topic['subfield']
                                         ['display_name']] += 1
                else:
                    final_subfield_count[topic['subfield']['display_name']] = 1
        response = requests.get(
            f'https://api.openalex.org/authors?per-page=200&filter=last_known_institutions.ror:{ror}&cursor=' + next_page, headers=headers)
        data = response.json()
        authors = data['results']
        next_page = data['meta']['next_cursor']
        counter += 1

    sorted_subfields = sorted([(k, v) for k, v in final_subfield_count.items(
    ) if v > 5], key=lambda x: x[1], reverse=True)
    app.logger.info(
        f"Found {len(sorted_subfields)} subfields with more than 5 authors")

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    nodes.append({'id': id, 'label': name, 'type': 'INSTITUTION'})
    for subfield, number in sorted_subfields:
        nodes.append({'id': subfield, 'label': subfield, 'type': "TOPIC"})
        number_id = subfield + ":" + str(number)
        nodes.append({'id': number_id, 'label': number, 'type': "NUMBER"})
        edges.append({'id': f"""{id}-{subfield}""", 'start': id, 'end': subfield,
                     "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
        edges.append({'id': f"""{subfield}-{number_id}""", 'start': subfield,
                     'end': number_id, "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})
    graph = {"nodes": nodes, "edges": edges}

    app.logger.info(
        f"Successfully built subfield list and graph for institution: {name}")
    return sorted_subfields, graph


def get_author_metadata_sparql(author):
    """
    Here we have to be "ready" to push the update to the metadata..the meta-data is a part of the object in the sense that we can't have an object without the metadata..we have to query the SemOpenAlex endpoint in order to retrieve the metadata on the author.

    Return value: the metadata consists of information on the author in the form of a dictionary with the following keys: name, cited_by_count, orcid, work_count, current_institution, oa-link, institution_url
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
    oa_link = oa_link.replace(
        'semopenalex', 'openalex').replace('author', 'authors')
    institution_link = results[0]['current_institution'].replace(
        'semopenalex', 'openalex').replace('institution', 'institutions')

    return {"name": author, "cited_by_count": cited_by_count, "orcid": orcid, "work_count": work_count, "current_institution": current_institution, "oa_link": oa_link, "institution_url": institution_link}


def get_researcher_and_institution_metadata_sparql(researcher, institution):
    """
    The function works fine given an institution & researcher, where we collect the metadata for the 2 and return it as one dictionary.

    Then we return some metadata that "consists of" the informatino on the institution as well as the researcher as a dictionary with the following keys: institution_name, researcher_name, homepage, institution_oa_link, researcher_oa_link, orcid, work_count, cited_by_count, ror.
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
    In the same "sense" that we can aviate the hybrid search, we can have the user search for a researcher only or a researcher & institution. We check OpenAlex, for what topics are attributed to the author.
    """
    app.logger.debug(
        f"Building list for researcher: {name} at institution: {institution}")
    final_subfield_count = {}
    headers = {'Accept': 'application/json'}
    search_id = id.replace('https://openalex.org/authors/', '')

    app.logger.debug(f"Fetching author data from OpenAlex for ID: {search_id}")
    response = requests.get(
        f'https://api.openalex.org/authors/{search_id}', headers=headers)
    data = response.json()
    topics = data['topics']

    for t in topics:
        subfield = t['subfield']['display_name']
        if subfield in final_subfield_count:
            final_subfield_count[subfield] = final_subfield_count[subfield] + t['count']
        else:
            final_subfield_count[subfield] = t['count']
    sorted_subfields = sorted(
        final_subfield_count.items(), key=lambda x: x[1], reverse=True)
    app.logger.debug(f"Found {len(sorted_subfields)} subfields for researcher")

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    nodes.append(
        {'id': institution, 'label': institution, 'type': 'INSTITUTION'})
    edges.append({'id': f"""{id}-{institution}""", 'start': id, 'end': institution,
                 "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
    nodes.append({'id': id, 'label': name, "type": "AUTHOR"})

    for s, number in sorted_subfields:
        nodes.append({'id': s, 'label': s, 'type': "TOPIC"})
        number_id = s + ":" + str(number)
        nodes.append({'id': number_id, 'label': number, 'type': "NUMBER"})
        edges.append({'id': f"""{id}-{s}""", 'start': id, 'end': s,
                     "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
        edges.append({'id': f"""{s}-{number_id}""", 'start': s, 'end': number_id,
                     "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})
    graph = {"nodes": nodes, "edges": edges}

    app.logger.info(
        f"Successfully built list and graph for researcher: {name} at institution: {institution}")
    return sorted_subfields, graph


def get_subfield_metadata_sparql(subfield):
    """
    We finalize the subfield, as a property and then query the OpenAlex endpoint in order to retrieve the metadata on the subfield..we don't make massive code changes but we do query the database. The only thing is we don't actually query SemOpenAlex because the necessary data is faster to retrieve from OpenAlex, but this may change..in the future.
    And what we do is we realize that researchers do not work as expected at the moment.
    We have to make sure that we return the proper values. We return the metadata which consists of subfield-related information as a dictionary with the following keys--name, topic_clusters, cited_by_count, work_count, researchers, oa_link.
    """
    headers = {'Accept': 'application/json'}
    response = requests.get(
        f'https://api.openalex.org/subfields?filter=display_name.search:{subfield}', headers=headers)
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
    In order to list the given topic, we need to know that a user searches for a topic only. We search through each Historically Black College and University as well as partner institutions and we return which institutions research the subfield.

    What are the parameters that we take?
        subfield: This is the name of the subfield searched.
        id: id of the subfield, just in case the document ends up being 99 pages.

    And here is what we return, it's quite wonderful in that we can return the subfield_list, which is the subfields which OpenAlex attributes to a given institution AND the graph, which is a graphical representation of subfield_list.
    """
    headers = {'Accept': 'application/json'}
    subfield_list = []
    extra_metadata = {}
    total_work_count = 0

    for institution in autofill_inst_list:
        response = requests.get(
            f'https://api.openalex.org/institutions?select=display_name,topics&filter=display_name.search:{institution}', headers=headers)
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
    nodes.append({'id': id, 'label': subfield, 'type': 'TOPIC'})
    for i, c in subfield_list:
        if not c == 0:
            nodes.append({'id': i, 'label': i, 'type': 'INSTITUTION'})
            nodes.append({'id': c, 'label': c, 'type': "NUMBER"})
            edges.append({'id': f"""{i}-{id}""", 'start': i, 'end': id,
                         "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
            edges.append({'id': f"""{i}-{c}""", 'start': i, 'end': c,
                         "label": "number", "start_type": "INSTITUTION", "end_type": "NUMBER"})
    graph = {"nodes": nodes, "edges": edges}
    return subfield_list, graph, extra_metadata


def get_institution_and_topic_metadata_sparql(institution, topic):
    """
    We could probably dockerize the backend in such a way as to make sure that we can do a demo of the test features, we need to be able to run pytest on all of these functions which means that, given a topic & institution we collect the metadata for the 2 as well as return one as one dictionary.

    What do we return? Well, we return the metadata which consists of information on the topic & institution as a dictionary with the following keys:
        institution_name, topic_Name, work_count, cited_by_count, ror, topic_clusters, people_count, topic_oa_link, institution_oa_link, homepage
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
    Creating a venv might help. When a user searches for an institution and topic we want to use a SemOpenAlex query to retrieve the authors who work at the given institution AND HAVE published papers that are related to the provided subfield.
    """
    app.logger.debug(
        f"Building list for institution: {institution} and topic: {topic}")
    query = f"""
    SELECT DISTINCT ?author ?name (GROUP_CONCAT(DISTINCT ?work; SEPARATOR=", ") AS ?works) WHERE {"{"}
    ?institution <http://xmlns.com/foaf/0.1/name> "{institution}" .
    ?author <http://www.w3.org/ns/org#memberOf> ?institution .
    ?author <http://xmlns.com/foaf/0.1/name> ?name .
    ?work <http://purl.org/dc/terms/creator> ?author .
    ?subfield a <https://semopenalex.org/ontology/Subfield> .
    ?subfield <http://www.w3.org/2004/02/skos/core#prefLabel> "{topic}" .
    ?topic <http://www.w3.org/2004/02/skos/core#broader> ?subfield .
    << ?work <https://semopenalex.org/ontology/hasTopic> ?topic >> ?p ?o .
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
    nodes.append({'id': topic_id, 'label': topic, 'type': 'TOPIC'})
    nodes.append(
        {'id': institution_id, 'label': institution, 'type': 'INSTITUTION'})
    edges.append({'id': f"""{institution_id}-{topic_id}""", 'start': institution_id,
                 'end': topic_id, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})

    for author, name, num_works in works_list:
        nodes.append({'id': author, 'label': name, 'type': 'AUTHOR'})
        nodes.append({'id': num_works, 'label': num_works, 'type': 'NUMBER'})
        edges.append({'id': f"""{author}-{institution_id}""", 'start': author, 'end': institution_id,
                     "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
        edges.append({'id': f"""{author}-{num_works}""", 'start': author, 'end': num_works,
                     "label": "numWorks", "start_type": "AUTHOR", "end_type": "NUMBER"})

    graph = {"nodes": nodes, "edges": edges}
    extra_metadata = {"work_count": work_count, "num_people": num_people}

    app.logger.info(
        f"Successfully built list and graph for institution: {institution} and topic: {topic}")
    return final_list, graph, extra_metadata


def get_topic_and_researcher_metadata_sparql(topic, researcher):
    """
    I recommended checking the documentation for SPARQL as well because we know that when we do the unit tests, we have to confirm that these functions like SSL on Postgres being mandatory for all cloud platforms..we have got to collect the metadata for the topic and researcher which are supplied as parameters for the 2 and returns as one dictionary.

    We have got to return some metadata such as the information on the topic & researcher as a dictionary with the following keys:
        researcher_name, topic_name, orcid, current_institution, work_count, cited_by_count, topic_clusters, researcher_oa_link, topic_oa_link.

    This is how we make things happen we have made sure that every person who is on orCID has an official account, so that we can train our unit tests on more data.
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
    For error traces and such, when a user searches for a researcher and topic we know that the server-side is going to be quite "silent" to put it shortly..searching for a researcher and topic utilizes a SemOpenAlex query to retrieve works by the author that are related to the topic.
    """
    app.logger.debug(
        f"Building list for researcher: {researcher} and topic: {topic}")
    query = f"""
    SELECT DISTINCT ?work ?title ?cited_by_count WHERE {"{"}
    ?author <http://xmlns.com/foaf/0.1/name> "{researcher}" .
    ?work <http://purl.org/dc/terms/creator> ?author .
    ?work <http://xmlns.com/foaf/0.1/name> ?title .
    ?work <https://semopenalex.org/ontology/citedByCount> ?cited_by_count .
    ?subfield a <https://semopenalex.org/ontology/Subfield> .
    ?subfield <http://www.w3.org/2004/02/skos/core#prefLabel> "{topic}" .
    ?topic <http://www.w3.org/2004/02/skos/core#broader> ?subfield .
    << ?work <https://semopenalex.org/ontology/hasTopic> ?topic >> ?p ?o .
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
    nodes.append(
        {'id': institution_id, 'label': institution, 'type': 'INSTITUTION'})
    edges.append({'id': f"""{researcher_id}-{institution_id}""", 'start': researcher_id,
                 'end': institution_id, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
    nodes.append({'id': researcher_id, 'label': researcher, 'type': 'AUTHOR'})
    nodes.append({'id': topic_id, 'label': topic, 'type': 'TOPIC'})
    edges.append({'id': f"""{researcher_id}-{topic_id}""", 'start': researcher_id,
                 'end': topic_id, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})

    for work, number in work_list:
        nodes.append({'id': work, 'label': work, 'type': 'WORK'})
        nodes.append({'id': number, 'label': number, 'type': "NUMBER"})
        edges.append({'id': f"""{researcher_id}-{work}""", 'start': researcher_id,
                     'end': work, "label": "authored", "start_type": "AUTHOR", "end_type": "WORK"})
        edges.append({'id': f"""{work}-{number}""", 'start': work, 'end': number,
                     "label": "citedBy", "start_type": "WORK", "end_type": "NUMBER"})

    graph = {"nodes": nodes, "edges": edges}
    extra_metadata = {"work_count": len(
        work_list), "cited_by_count": total_citations}

    app.logger.info(
        f"Successfully built list and graph for researcher: {researcher} and topic: {topic}")
    return work_list, graph, extra_metadata


def get_institution_and_topic_and_researcher_metadata_sparql(institution, topic, researcher):
    """
    I don't know why I dropped off the metadata tag during my unit tests, but what I do know is that given an institution & topic & researcher I should be able to collect the metadata for the 3 and return it as one dictionary.
    """
    app.logger.debug(
        f"Fetching metadata for institution: {institution}, topic: {topic}, researcher: {researcher}")

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

    app.logger.info(
        f"Successfully compiled metadata for {researcher} at {institution} researching {topic}")
    return metadata


def query_SQL_endpoint(connection, query):
    """
    As for the endpoints, they help Python parse SQL queries correctly in a complicated codebase.
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
    We can remove the institutions and handle autofill for them by testing them to make sure that everything still works before pushing that code.
    """
    inst = request.json.get('institution')
    app.logger.debug(f"Processing institution autofill for: {inst}")

    possible_searches = []
    for i in autofill_inst_list:
        if inst.lower() in i.lower():
            possible_searches.append(i)

    app.logger.info(
        f"Found {len(possible_searches)} matching institutions for '{inst}'")
    return {"possible_searches": possible_searches}


@app.route('/autofill-topics', methods=['POST'])
def autofill_topics():
    """
    So once we get added to the CloudBank subscription we are ready to finish the handling of the autofill for the topics.
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

    app.logger.info(
        f"Found {len(possible_searches)} matching topics for '{topic}'")
    return {"possible_searches": possible_searches}


@app.route("/get-default-graph", methods=["POST"])
def get_default_graph():
    """
    My suggestion is that when we do the graph, we have to optimize the search. The thing about search is that it's "reasonably" fast on the CollabNext.io and the CollabNext.io/alpha subdomain, we just have to remember to return the default graph from default.json using the absolute path.
    """
    default_json_path = os.path.join(BASE_DIR, "default.json")
    app.logger.debug("Loading default graph from file")
    try:
        with open(default_json_path, "r") as file:
            graph = json.load(file)
    except Exception as e:
        app.logger.error(f"Failed to load default graph: {str(e)}")
        return {"error": "Failed to load default graph"}

    app.logger.debug("Processing default graph data")
    nodes = []
    edges = []
    cur_nodes = graph["nodes"]
    cur_edges = graph["edges"]
    most = {}
    needed_topics = set()

    for edge in cur_edges:
        if edge["start"] in most:
            if edge["connecting_works"] > most[edge["start"]]:
                most[edge["start"]] = edge["connecting_works"]
        else:
            most[edge["start"]] = edge["connecting_works"]

    for edge in cur_edges:
        if most[edge["start"]] == edge["connecting_works"]:
            edges.append(edge)
            needed_topics.add(edge["end"])

    for node in cur_nodes:
        if node["type"] == "TOPIC":
            if node["id"] in needed_topics:
                nodes.append(node)
        else:
            nodes.append(node)

    final_graph = {"nodes": nodes, "edges": edges}
    app.logger.info(
        f"Successfully processed default graph with {len(nodes)} nodes and {len(edges)} edges"
    )
    return {"graph": final_graph}


@app.route("/get-topic-space-default-graph", methods=["POST"])
def get_topic_space():
    """
    I will push a unit test draft in order to show how we can return a small lift, the default graph for the topic space (hard-coded example).
    """
    app.logger.debug("Building topic space default graph")
    nodes = [
        {"id": 1, "label": "Physical Sciences", "type": "DOMAIN"},
        {"id": 2, "label": "Life Sciences", "type": "DOMAIN"},
        {"id": 3, "label": "Social Sciences", "type": "DOMAIN"},
        {"id": 4, "label": "Health Sciences", "type": "DOMAIN"},
    ]
    edges = []
    graph = {"nodes": nodes, "edges": edges}

    app.logger.info("Successfully built topic space default graph")
    return {"graph": graph}


@app.route("/search-topic-space", methods=["POST"])
def search_topic_space():
    """
    It would be best that I write this Application Programming Interface call for searches from the user when searching the space of all topics.
    """
    search = request.json.get("topic", "")
    app.logger.debug(f"Searching topic space for: {search}")

    topic_default_json_path = os.path.join(BASE_DIR, "topic_default.json")
    try:
        with open(topic_default_json_path, "r") as file:
            graph = json.load(file)
    except Exception as e:
        app.logger.error(f"Failed to load topic space data: {str(e)}")
        return {"error": "Failed to load topic space data"}

    nodes = []
    edges = []
    matches_found = 0

    app.logger.debug("Processing topic space search results")
    for node in graph["nodes"]:
        if (
            node["label"] == search
            or node["subfield_name"] == search
            or node["field_name"] == search
            or node["domain_name"] == search
            or search in node["keywords"].split("; ")
        ):
            matches_found += 1
            node_additions = []
            edge_additions = []

            topic_node = {
                "id": node["id"],
                "label": node["label"],
                "type": "TOPIC",
                "keywords": node["keywords"],
                "summary": node["summary"],
                "wikipedia_url": node["wikipedia_url"],
            }
            node_additions.append(topic_node)

            subfield_node = {
                "id": node["subfield_id"],
                "label": node["subfield_name"],
                "type": "SUBFIELD",
            }
            node_additions.append(subfield_node)

            field_node = {
                "id": node["field_id"],
                "label": node["field_name"],
                "type": "FIELD",
            }
            node_additions.append(field_node)

            domain_node = {
                "id": node["domain_id"],
                "label": node["domain_name"],
                "type": "DOMAIN",
            }
            node_additions.append(domain_node)

            topic_subfield = {
                "id": f"""{node["id"]}-{node["subfield_id"]}""",
                "start": node["id"],
                "end": node["subfield_id"],
                "label": "hasSubfield",
                "start_type": "TOPIC",
                "end_type": "SUBFIELD",
            }
            edge_additions.append(topic_subfield)

            subfield_field = {
                "id": f"""{node["subfield_id"]}-{node["field_id"]}""",
                "start": node["subfield_id"],
                "end": node["field_id"],
                "label": "hasField",
                "start_type": "SUBFIELD",
                "end_type": "FIELD",
            }
            edge_additions.append(subfield_field)

            field_domain = {
                "id": f"""{node["field_id"]}-{node["domain_id"]}""",
                "start": node["field_id"],
                "end": node["domain_id"],
                "label": "hasDomain",
                "start_type": "FIELD",
                "end_type": "DOMAIN",
            }
            edge_additions.append(field_domain)

            for na in node_additions:
                if na not in nodes:
                    nodes.append(na)
            for ea in edge_additions:
                if ea not in edges:
                    edges.append(ea)

    final_graph = {"nodes": nodes, "edges": edges}
    app.logger.info(
        f"Found {matches_found} matches in topic space for '{search}'")
    return {"graph": final_graph}


def create_connection(host_name, user_name, user_password, db_name):
    """
    Last but not least we must create an Structured Query Language Database connection and then return the connection object. """
    app.logger.debug(
        f"Attempting to connect to MySQL database: {db_name} at {host_name}")
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name,
        )
        app.logger.info("Successfully connected to MySQL database")
    except Error as e:
        app.logger.error(f"Failed to connect to MySQL database: {str(e)}")

    return connection


def is_HBCU(openalex_id):
    """
    I merged some changes to main from the backend to fix the check whether or not an institution is a Historically Black College or University not from the perspective of loading issues on localhost or even on the Dockerized version, since there haven't really been that many backend changes from the Alpha version to the Public version, but because we have got some changes applied regarding the unit tests that are applicable to this database query format.
    """
    app.logger.debug(f"Checking HBCU status for institution ID: {openalex_id}")
    connection = create_connection(
        "openalexalpha.mysql.database.azure.com",
        "openalexreader",
        "collabnext2024reader!",
        "openalex",
    )
    local_id = openalex_id.replace("https://openalex.org/institutions/", "")
    query = f"""SELECT HBCU FROM institutions_filtered WHERE id = "{local_id}";"""
    result = query_SQL_endpoint(connection, query)

    is_hbcu = (result == [(1,)])
    app.logger.info(f"Institution {local_id} HBCU status: {is_hbcu}")
    return is_hbcu


def query_SQL_endpoint(connection, query):
    """
    In order to make everyone's lives a little bit easier, "instead of" the tedious process to execute the SQL query in a single line of code we query the endpoint and then test it.
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


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    """For now, the information on doing it manually is still preserved in the static files that we serve, and handle the routing for the frontend. """
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        app.logger.debug(f"Serving static file: {path}")
        return send_from_directory(app.static_folder, path)

    app.logger.debug("Serving index.html for frontend routing")
    return send_from_directory(app.static_folder, "index.html")


@app.route("/get-institutions", methods=["GET"])
def get_institutions():
    """
    Returns the contents without further ado we delay the institutions.csv file for our unit tests and do a quick tour of the JavaScript Object Notation format, in our app.
    """
    try:
        institutions_csv_path = os.path.join(BASE_DIR, "institutions.csv")
        with open(institutions_csv_path, "r") as file:
            institutions = file.read().split(",\n")
        return jsonify(institutions=institutions)
    except Exception as e:
        return jsonify(error=str(e)), 500


if __name__ == "__main__":
    app.logger.info("Starting Flask microservice application")
    app.run()
