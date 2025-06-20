from mysql.connector import Error

"""
Methods which were used in a previous version of the app, but not the current version.
"""

def query_SQL_endpoint(app, connection, query):
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

def create_connection(app, host_name, user_name, user_password, db_name):
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

def combine_graphs(graph1, graph2):
  dup_nodes = graph1['nodes'] + graph2['nodes']
  dup_edges = graph1['edges'] + graph2['edges']
  final_nodes = list({tuple(d.items()): d for d in dup_nodes}.values())
  final_edges = list({tuple(d.items()): d for d in dup_edges}.values())
  return {"nodes": final_nodes, "edges": final_edges}