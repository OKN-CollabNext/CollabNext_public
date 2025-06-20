from postgres_queries import execute_query, get_institution_id
"""
Contains methods necessary to retrieve MUP data on institutions.
"""

def get_institution_mup_id(app, institution_name):
    app.logger.debug(f"Searching for MUP ID for institution: {institution_name}")
    institution_id = get_institution_id(app, institution_name)
    if not institution_id:
        app.logger.debug(f"No institution ID found for {institution_name}")
        return None
    
    query = """SELECT get_institution_mup_id(%s);"""
    results = execute_query(app, query, (institution_id,))
    if results:
        app.logger.info(f"Successfully fetched MUP ID for {institution_name}")
        return results[0][0]
    app.logger.info(f"No MUP ID found for {institution_name}")
    return None

def get_institution_sat_scores(app, institution_name):
    """Returns {institution_name: String, institution_id: String, data: a list of dictionaries containing 'sat', and 'year'}"""
    app.logger.debug(f"Searching for MUP SAT scores data for institution: {institution_name}")
    institution_id = get_institution_id(app, institution_name)
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

def get_institution_endowments_and_givings(app, institution_name):
    """Returns {institution_name: String, institution_id: String, data: a list of dictionaries containing 'endowment', 'giving', and 'year'}"""
    app.logger.debug(f"Searching for MUP endowments and givings data for institution: {institution_name}")
    institution_id = get_institution_id(app, institution_name)
    if not institution_id:
        app.logger.debug(f"No institution ID found for {institution_name}")
        return None
    
    query = """SELECT get_institution_endowments_and_givings(%s);"""
    results = execute_query(app, query, (institution_id,))
    if results:
        results[0][0]['institution_name'] = institution_name
        results[0][0]['institution_id'] = institution_id
        app.logger.info(f"Successfully fetched MUP endowments and givings data for {institution_name}")
        return results[0][0]
    app.logger.info(f"No MUP endowments and givings data found for {institution_name}")
    return None

def get_institution_medical_expenses(app, institution_name):
    """Returns {institution_name: String, institution_mup_id: String, data: a list of dictionaries containing 'expenditure', and 'year'}"""
    app.logger.debug(f"Searching for MUP medical expenses data for institution: {institution_name}")
    institution_mup_id = get_institution_mup_id(app, institution_name)
    if not institution_mup_id:
        app.logger.debug(f"No institution MUP ID found for {institution_name}")
        return None
    
    institution_mup_id = institution_mup_id['institution_mup_id']
    query = """SELECT get_institution_medical_expenses(%s);"""
    results = execute_query(app, query, (institution_mup_id,))
    if results:
        results[0][0]['institution_name'] = institution_name
        results[0][0]['institution_mup_id'] = institution_mup_id
        app.logger.info(f"Successfully fetched MUP medical expenses data for {institution_name}")
        return results[0][0]
    app.logger.info(f"No MUP medical expenses data found for {institution_name}")
    return None

def get_institution_doctorates_and_postdocs(app, institution_name):
    """Returns {institution_name: String, institution_id: String, data: a list of dictionaries containing 'num_postdocs', 'num_doctorates', and 'year'}"""
    app.logger.debug(f"Searching for MUP doctorates and postdocs data for institution: {institution_name}")
    institution_id = get_institution_id(app, institution_name)
    if not institution_id:
        app.logger.debug(f"No institution ID found for {institution_name}")
        return None
    
    query = """SELECT get_institution_doctorates_and_postdocs(%s);"""
    results = execute_query(app, query, (institution_id,))
    if results:
        results[0][0]['institution_name'] = institution_name
        results[0][0]['institution_id'] = institution_id
        app.logger.info(f"Successfully fetched MUP doctorates and postdocs data for {institution_name}")
        return results[0][0]
    app.logger.info(f"No MUP doctorates and postdocs data found for {institution_name}")
    return None

def get_institution_num_of_researches(app, institution_name):
    """Returns {institution_name: String, institution_id: String, data: a list of dictionaries containing 'num_federal_research', 'num_nonfederal_research', 'total_research', and 'year'}"""
    app.logger.debug(f"Searching for MUP number of researches data for institution: {institution_name}")
    institution_id = get_institution_id(app, institution_name)
    if not institution_id:
        app.logger.debug(f"No institution ID found for {institution_name}")
        return None
    
    query = """SELECT get_institution_num_of_researches(%s);"""
    results = execute_query(app, query, (institution_id,))
    if results:
        results[0][0]['institution_name'] = institution_name
        results[0][0]['institution_id'] = institution_id
        app.logger.info(f"Successfully fetched MUP number of researchers data for {institution_name}")
        return results[0][0]
    app.logger.info(f"No MUP number of researchers data found for {institution_name}")
    return None

def get_institutions_faculty_awards(app, institution_name):
    """Returns {institution_name: String, institution_id: String, data: a list of dictionaries containing 'nae', 'nam', 'nas', 'num_fac_awards', and 'year'}"""
    app.logger.debug(f"Searching for MUP faculty awards data for institution: {institution_name}")
    institution_id = get_institution_id(app, institution_name)
    if not institution_id:
        app.logger.debug(f"No institution ID found for {institution_name}")
        return None

    query = """SELECT get_institutions_faculty_awards(%s);"""
    results = execute_query(app, query, (institution_id,))
    if results:
        results[0][0]['institution_name'] = institution_name
        results[0][0]['institution_id'] = institution_id
        app.logger.info(f"Successfully fetched MUP faculty awards data for {institution_name}")
        return results[0][0]
    app.logger.info(f"No MUP faculty awards data found for {institution_name}")
    return None

def get_institutions_r_and_d(app, institution_name):
    """Returns {institution_name: String, institution_id: String, data: a list of dictionaries containing 'category', 'federal', 'percent_federal', 'total', and 'percent_total'}"""
    app.logger.debug(f"Searching for MUP R&D data for institution: {institution_name}")
    institution_id = get_institution_id(app, institution_name)
    if not institution_id:
        app.logger.debug(f"No institution ID found for {institution_name}")
        return None

    query = """SELECT get_institutions_r_and_d(%s);"""
    results = execute_query(app, query, (institution_id,))
    if results:
        results[0][0]['institution_name'] = institution_name
        results[0][0]['institution_id'] = institution_id
        app.logger.info(f"Successfully fetched MUP R&D data for {institution_name}")
        return results[0][0]
    app.logger.info(f"No MUP R&D datafound for {institution_name}")
    return None

