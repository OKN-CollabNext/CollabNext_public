-- Get the institution id from the institution name
CREATE OR REPLACE FUNCTION get_institution_id_from_mup(institution_name TEXT)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(        
        'institution_id', id
    )
    INTO result
    FROM mup.institutions_copy
    WHERE display_name = institution_name;

    -- Return the result, or an explicitly empty JSON object if no match is found
    RETURN COALESCE(result, json_build_object());
END;
$$ LANGUAGE plpgsql;

-- Get the institution mup id from institution id
CREATE OR REPLACE FUNCTION get_institution_mup_id(institution_id TEXT)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(        
        'institution_mup_id', mup
    )
    INTO result
    FROM mup.openalex_mup_mapping
    WHERE openalex = institution_id;

    -- Return the result, or an explicitly empty JSON object if no match is found
    RETURN COALESCE(result, json_build_object());
END;
$$ LANGUAGE plpgsql;

-- Get the institution's SAT scores across years
CREATE OR REPLACE FUNCTION get_institution_sat_scores(
    institution_id TEXT
)
RETURNS JSONB AS $$
BEGIN
    RETURN jsonb_build_object(
        'data', (
            SELECT jsonb_agg(row_to_json(data))
            FROM (
                SELECT
                    year,
                    sat
                FROM mup.institution_sat_act_data
                WHERE openalex_id = institution_id                
                ORDER BY year
            ) AS data
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Get the institution's endowment and giving data across years
CREATE OR REPLACE FUNCTION get_institution_endowments_and_givings(
    institution_id TEXT
)
RETURNS JSONB AS $$
BEGIN
    RETURN jsonb_build_object(
        'data', (
            SELECT jsonb_agg(row_to_json(data))
            FROM (
                SELECT
                    year,
                    endowment,
                    giving
                FROM mup.institutions_financial_data
                WHERE openalex_id = institution_id                
                ORDER BY year
            ) AS data
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Get the institution's medical expenses data across years
CREATE OR REPLACE FUNCTION get_institution_medical_expenses(
    institution_mup_id INTEGER
)
RETURNS JSONB AS $$
BEGIN
    RETURN jsonb_build_object(
        'data', (
            SELECT jsonb_agg(row_to_json(data))
            FROM (
                SELECT
                    year,
                    expenditure                    
                FROM mup.institutions_medical_expenditures
                WHERE mup_id = institution_mup_id                
                ORDER BY year
            ) AS data
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Get the institution's doctorate and postdoc data across years
CREATE OR REPLACE FUNCTION get_institution_doctorates_and_postdocs(
    institution_id TEXT
)
RETURNS JSONB AS $$
BEGIN
    RETURN jsonb_build_object(
        'data', (
            SELECT jsonb_agg(row_to_json(data))
            FROM (
                SELECT
                    year,
                    num_postdocs,
                    num_doctorates                    
                FROM mup.institutions_postdoc_data
                WHERE openalex_id = institution_id                
                ORDER BY year
            ) AS data
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Get the institution's number of federal and non-federal researches and total number of researches across years
CREATE OR REPLACE FUNCTION get_institution_num_of_researches(
    institution_id TEXT
)
RETURNS JSONB AS $$
BEGIN
    RETURN jsonb_build_object(
        'data', (
            SELECT jsonb_agg(row_to_json(data))
            FROM (
                SELECT
                    year,
                    federal_research as num_federal_research,
                    nonfederal_research as num_nonfederal_research,
                    total_research        
                FROM mup.institutions_research_funding_by_year as irf
                WHERE irf.institution_id = get_institution_num_of_researches.institution_id                
                ORDER BY year
            ) AS data
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Get the institution's faculty awards data across years
CREATE OR REPLACE FUNCTION get_institutions_faculty_awards(
    institution_id TEXT
)
RETURNS JSONB AS $$
BEGIN
    RETURN jsonb_build_object(
        'data', (
            SELECT jsonb_agg(row_to_json(data))
            FROM (
                SELECT
                    year,
                    nae,
                    nam,
                    nas,
                    num_fac_awards
                FROM mup.institutions_faculty_awards_data
                WHERE openalex_id = institution_id
                ORDER BY year
            ) AS data
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Get the institution's R&D numbers across different categories
CREATE OR REPLACE FUNCTION get_institutions_r_and_d(
    institution_id TEXT
)
RETURNS JSONB AS $$
BEGIN
    RETURN jsonb_build_object(
        'data', (
            SELECT jsonb_agg(row_to_json(data))
            FROM (
                SELECT
                    category,
                    federal,
                    percent_federal,
                    total,
                    percent_total
                FROM mup.institutions_r_and_d as ird
                WHERE ird.institution_id = get_institutions_r_and_d.institution_id
            ) AS data
        )
    );
END;
$$ LANGUAGE plpgsql;