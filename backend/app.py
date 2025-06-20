import os
import json
import logging
import requests

from flask import Flask, send_from_directory, request, jsonify, abort
from dotenv import load_dotenv
from flask_cors import CORS

from basic_searches import get_researcher_result, get_institution_results, get_subfield_results, get_multiple_researcher_results, get_multiple_institution_results, get_institution_and_subfield_results, get_researcher_and_subfield_results, get_institution_and_researcher_results, get_institution_researcher_subfield_results
from mup_data import *
from logger import *

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

# Setup the app
app= Flask(__name__, static_folder='build', static_url_path='/')
CORS(app)

# Initialize logger
logger = setup_logger()
app.logger.handlers = logger.handlers
app.logger.setLevel(logger.level)

# Creates lists for autofill functionality from the institution and keyword csv files
with open('institutions.csv', 'r', encoding='UTF-8') as file:
    autofill_inst_list = file.read().split('\n')
    for i in range(0, len(autofill_inst_list)):
        autofill_inst_list[i] = autofill_inst_list[i].replace('"', '')
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

@app.route('/initial-search', methods=['POST'])
def initial_search():
  """
  Api call for searches from the user. Calls other methods depending on what the user inputted.

  Expects the frontend to pass in the following values:
  organization : input from the "organization" search box
  researcher : input from the "researcher name" search box
  topic : input from the "topic keyword" search box
  type : input from the "type" search box (for now, this is always HBCU)

  Returns:
  metadata : the metadata for the search
  graph : the graph for the search in the form {nodes: [], edges: []}
  list : the list view for the search
  """

  request_data = request.get_json()
  page = request_data.get('page', 1)
  per_page = request_data.get('per_page',25)

  institution = request.json.get('organization')
  researcher = request.json.get('researcher')
  researcher = researcher.title()
  type = request.json.get('type')
  topic = request.json.get('topic')
  extra_institutions = request.json.get('extra_institutions')
  app.logger.info(f"Received search request - Institution: {institution}, Researcher: {researcher}, Topic: {topic}, Type: {type}")
  try:
    if institution and researcher and topic:
      results = get_institution_researcher_subfield_results(app, institution, researcher, topic, page, per_page)
    elif institution and researcher:
      results = get_institution_and_researcher_results(app, institution, researcher, page, per_page)
    elif institution and topic:
      results = get_institution_and_subfield_results(app, institution, topic, page, per_page)
    elif researcher and topic:
      results = get_researcher_and_subfield_results(app, researcher, topic, page, per_page)
    elif topic:
      results = get_subfield_results(app, topic, page, per_page)
    elif researcher:
      researcher = researcher.splitlines()
      if len(researcher) == 1:
        results = get_researcher_result(app, researcher[0], page, per_page)
      else:
        results = get_multiple_researcher_results(app, researcher, page, per_page)
    elif extra_institutions:
        extra_institutions = extra_institutions.splitlines()
        results = get_multiple_institution_results(app, extra_institutions, page, per_page, True)
    elif institution:
      if extra_institutions == []:
        results = get_institution_results(app, institution, page, per_page)
      else:
        extra_institutions.insert(0, institution)
        results = get_multiple_institution_results(app, extra_institutions, page, per_page)
    if not results:
      app.logger.warning("Search returned no results")
      return {}
    app.logger.info("Search completed successfully")
    return results

  except Exception as e:
    app.logger.critical(f"Critical error during search: {str(e)}")
    return {"error": "An unexpected error occurred"}

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
    result = get_institution_mup_id(app, institution_name)
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
    result = get_institution_sat_scores(app, institution_name)
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
    result = get_institution_endowments_and_givings(app, institution_name)
    if result:
        return jsonify(result)
    else:
        abort(404, description=f"No data found for {institution_name}")

@app.route('/institution_num_of_researches', methods=['POST'])
def institution_num_of_researches():
    data = request.get_json()
    institution_name = data.get('institution_name')
    result = get_institution_num_of_researches(app, institution_name)
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "No data found"}), 404

@app.route('/institution_medical_expenses', methods=['POST'])
def institution_medical_expenses():
    data = request.get_json()
    institution_name = data.get('institution_name')
    result = get_institution_medical_expenses(app, institution_name)
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "No data found"}), 404

@app.route('/institution_doctorates_and_postdocs', methods=['POST'])
def institution_doctorates_and_postdocs():
    data = request.get_json()
    institution_name = data.get('institution_name')
    result = get_institution_doctorates_and_postdocs(app, institution_name)
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
    result = get_institutions_faculty_awards(app, institution_name)
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
    result = get_institutions_r_and_d(app, institution_name)
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "No R&D numbers found"}), 404

## Main 
if __name__ =='__main__':
  app.logger.info("Starting Flask application")
  app.run()