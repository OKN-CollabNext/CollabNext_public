--
-- PostgreSQL database dump
--

-- Dumped from database version 16.8
-- Dumped by pg_dump version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: mup; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA mup;


--
-- Name: openalex; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA openalex;


--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: get_author_ids(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_author_ids(author_name text) RETURNS json
    LANGUAGE plpgsql
    AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_agg(json_build_object(
        'author_id', distinct_results.id,
        'institution_name', distinct_results.display_name
    ))
    INTO result
    FROM (
        SELECT DISTINCT a.id, i.display_name
        FROM openalex.authors AS a
        JOIN openalex.works_authorships AS w_a ON a.id = w_a.author_id
        JOIN openalex.institutions AS i ON w_a.institution_id = i.id
        WHERE a.display_name = author_name
    ) AS distinct_results;

    RETURN COALESCE(result, '[]'::JSON);
END;
$$;


--
-- Name: get_institution_id(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_institution_id(institution_name text) RETURNS json
    LANGUAGE plpgsql
    AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(        
        'institution_id', id
    )
    INTO result
    FROM openalex.institutions
    WHERE display_name = institution_name;

    -- Return the result, or an explicitly empty JSON object if no match is found
    RETURN COALESCE(result, json_build_object());
END;
$$;


--
-- Name: search_by_author(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.search_by_author(author_id text) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN jsonb_build_object(
        'author_metadata', (
            SELECT row_to_json(a)
            FROM (
                SELECT 
                    a.id AS openalex_url, 
                    a.orcid, 
                    a.display_name AS name, 
                    a.last_known_institution, 
                    a.works_count AS num_of_works, 
                    a.cited_by_count AS num_of_citations
                FROM openalex.authors AS a
                WHERE a.id = search_by_author.author_id
            ) AS a
        ),
        'data', (
            SELECT jsonb_agg(row_to_json(data))
            FROM (
                SELECT
                    subfield_display_name AS topic,
                    num_of_works
                FROM search_by_authors_mv AS authors_mv
                WHERE authors_mv.author_id = search_by_author.author_id
                ORDER BY num_of_works DESC
            ) AS data
        ),
        'subfield_metadata', (
            -- Get each unique subfield in the 'data' field
            WITH subfields AS (
                SELECT DISTINCT subfield_display_name
                FROM search_by_authors_mv AS authors_mv
                WHERE authors_mv.author_id = search_by_author.author_id
            )
            SELECT COALESCE(
                jsonb_object_agg(
                    sf.subfield_display_name,
                    -- For each subfield, aggregate its related topics into an array
                    (
                        SELECT COALESCE(
                            jsonb_agg(jsonb_build_object(
                                'topic_id',       t.id,
                                'topic_display_name', t.display_name
                            )),
                            '[]'::jsonb
                        )
                        FROM openalex.topics t
                        WHERE t.subfield_display_name = sf.subfield_display_name
                    )
                ),
                '{}'::jsonb  -- If there are no subfields, return an empty object
            )
            FROM subfields sf
        )
    );
END;
$$;


--
-- Name: search_by_author_institution(text, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.search_by_author_institution(author_id text, institution_id text) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    result JSONB;
BEGIN
    WITH topic_data AS (
        SELECT 
            t.subfield_display_name AS topic_name, 
            COUNT(DISTINCT w_a.work_id) AS num_of_works
        FROM openalex.works_authorships AS w_a
        JOIN openalex.works_topics AS w_t ON w_a.work_id = w_t.work_id
        JOIN openalex.topics AS t ON w_t.topic_id = t.id
        WHERE 
            w_a.institution_id = search_by_author_institution.institution_id AND 
            w_a.author_id = search_by_author_institution.author_id
        GROUP BY t.subfield_display_name
    )
    SELECT jsonb_build_object(
        'institution_metadata', (
            SELECT row_to_json(i)
            FROM (
                SELECT 
                    i.id AS openalex_url, 
                    i.ror AS ror, 
                    i.display_name AS institution_name, 
                    i.homepage_url AS url,
                    (
                    SELECT jsonb_agg(i_t.type_id ORDER BY i_t.type_id)
                    FROM openalex.institutions_types AS i_t
                    WHERE i_t.institution_id = search_by_author_institution.institution_id
                    ) AS types
                FROM openalex.institutions AS i
                WHERE i.id = search_by_author_institution.institution_id
            ) i
        ),
        'author_metadata', (
            SELECT row_to_json(a)
            FROM (
                SELECT 
                    a.id AS openalex_url, 
                    a.orcid, 
                    a.display_name AS name, 
                    a.works_count AS num_of_works, 
                    a.cited_by_count AS num_of_citations
                FROM openalex.authors AS a
                WHERE a.id = search_by_author_institution.author_id
            ) a
        ),
        'data', (
            SELECT jsonb_agg(row_to_json(data))
            FROM (
                SELECT topic_name, num_of_works
                FROM topic_data
                ORDER BY num_of_works DESC
            ) data
        ),
        'subfield_metadata', (
            SELECT COALESCE(
                jsonb_object_agg(
                    td.topic_name,
                    -- For each subfield, aggregate its related topics into an array
                    (
                        SELECT COALESCE(
                            jsonb_agg(jsonb_build_object(
                                'topic_id',       t.id,
                                'topic_display_name', t.display_name
                            )),
                            '[]'::jsonb
                        )
                        FROM openalex.topics t
                        WHERE t.subfield_display_name = td.topic_name
                    )
                ),
                '{}'::jsonb  -- If there are no subfields, return an empty object
            )
            FROM topic_data td
        )
    ) INTO result;
    
    RETURN result;
END;
$$;


--
-- Name: search_by_author_institution_topic(text, text, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.search_by_author_institution_topic(author_id text, institution_id text, subfield_name text) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN (
        WITH data_works AS (
            SELECT distinct w.display_name AS work_name, w.cited_by_count FROM openalex.works_authorships AS w_a
                JOIN openalex.works AS w ON w_a.work_id = w.id
                JOIN openalex.works_topics AS w_t ON w.id = w_t.work_id
                JOIN openalex.topics AS t ON w_t.topic_id = t.id
                WHERE 
                    w_a.institution_id = search_by_author_institution_topic.institution_id AND 
                    w_a.author_id = search_by_author_institution_topic.author_id AND 
                    t.subfield_display_name = search_by_author_institution_topic.subfield_name
        )
        SELECT jsonb_build_object(
        'author_metadata', (
            SELECT row_to_json(a)
            FROM (
                SELECT id AS openalex_url, orcid, display_name AS name
                FROM openalex.authors
                WHERE id = search_by_author_institution_topic.author_id
            ) a
        ),
        'institution_metadata', (
            SELECT row_to_json(i)
            FROM (
                SELECT 
                    id AS openalex_url, 
                    ror, 
                    display_name AS institution_name, 
                    homepage_url AS url,
                    (
                    SELECT jsonb_agg(i_t.type_id ORDER BY i_t.type_id)
                    FROM openalex.institutions_types AS i_t
                    WHERE i_t.institution_id = search_by_author_institution_topic.institution_id
                    ) AS types
                FROM openalex.institutions
                WHERE id = search_by_author_institution_topic.institution_id
            ) i
        ),
        'subfield_metadata', (
            SELECT jsonb_agg(row_to_json(s))
            FROM (
                SELECT 
                    subfield_display_name AS subfield, 
                    subfield_id AS subfield_url,
                    id AS openalex_url, 
                    display_name AS topic
                FROM openalex.topics
                WHERE subfield_display_name = search_by_author_institution_topic.subfield_name
            ) s
        ),
        'totals', (
            SELECT row_to_json(totals)
            FROM (
                SELECT COUNT(*) AS total_num_of_works, COALESCE(SUM(cited_by_count), 0) AS total_num_of_citations FROM data_works
            ) totals
        ),
        'data', (
            SELECT jsonb_agg(row_to_json(data))
            FROM (
                SELECT d.work_name, d.cited_by_count FROM data_works as d
                ORDER BY d.cited_by_count DESC
            ) data
        )
        )
    );
END;
$$;


--
-- Name: search_by_author_topic(text, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.search_by_author_topic(author_id text, subfield_name text) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN (
    WITH data_works AS (
            SELECT DISTINCT 
                w.display_name AS work_name, 
                w.cited_by_count AS num_of_citations
            FROM openalex.works_authorships AS w_a
            JOIN openalex.works AS w ON w_a.work_id = w.id
            JOIN openalex.works_topics AS w_t ON w_t.work_id = w_a.work_id
            JOIN openalex.topics AS t ON t.id = w_t.topic_id
            WHERE 
                w_a.author_id = search_by_author_topic.author_id AND 
                t.subfield_display_name = search_by_author_topic.subfield_name
        )
    SELECT jsonb_build_object(        
        'author_metadata', (
            SELECT row_to_json(a)
            FROM (
                SELECT 
                    a.id AS openalex_url, 
                    a.orcid, 
                    a.display_name AS name, 
                    a.last_known_institution
                FROM openalex.authors AS a
                WHERE a.id = search_by_author_topic.author_id
            ) AS a
        ),
        'subfield_metadata', (
            SELECT jsonb_agg(row_to_json(s))
            FROM (
                SELECT 
                    t.subfield_display_name AS subfield, 
                    t.subfield_id AS subfield_url,
                    t.id AS openalex_url, 
                    t.display_name AS topic
                FROM openalex.topics AS t
                WHERE t.subfield_display_name = search_by_author_topic.subfield_name
            ) AS s
        ),
        'data', (
            SELECT jsonb_agg(row_to_json(data))
            FROM (
                SELECT 
                    work_name, 
                    num_of_citations
                FROM data_works
                ORDER BY num_of_citations DESC
            ) AS data
        ),
        'totals', (
            SELECT row_to_json(totals)
            FROM (
                SELECT 
                    COUNT(work_name) AS total_num_of_works, 
                    SUM(num_of_citations) AS total_num_of_citations
                FROM data_works
            ) AS totals
        )
    )
    );
END;
$$;


--
-- Name: search_by_institution(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.search_by_institution(institution_id text) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN jsonb_build_object(
        'institution_metadata', (
            SELECT row_to_json(i)
            FROM (
                SELECT 
                    i.id AS openalex_url, 
                    i.ror AS ror, 
                    i.display_name AS institution_name, 
                    i.homepage_url AS url, 
                    i.works_count AS num_of_works, 
                    i.cited_by_count AS num_of_citations, 
                    i.authors_count AS num_of_authors,
                    (
                        SELECT jsonb_agg(i_t.type_id ORDER BY i_t.type_id)
                        FROM openalex.institutions_types AS i_t
                        WHERE i_t.institution_id = search_by_institution.institution_id
                    ) AS types
                FROM openalex.institutions AS i
                WHERE i.id = search_by_institution.institution_id
            ) AS i
        ),
        'data', (
            SELECT jsonb_agg(row_to_json(data))
            FROM (
                SELECT
                    topic_subfield, 
                    num_of_authors
                FROM search_by_institution_mv
                WHERE id = search_by_institution.institution_id
                ORDER BY num_of_authors DESC
            ) AS data
        ),
        'subfield_metadata', (
            -- Get each unique subfield in the 'data' field
            WITH subfields AS (
                SELECT DISTINCT topic_subfield
                FROM search_by_institution_mv
                WHERE id = search_by_institution.institution_id
            )
            SELECT COALESCE(
                jsonb_object_agg(
                    sf.topic_subfield,
                    -- For each subfield, aggregate its related topics into an array
                    (
                        SELECT COALESCE(
                            jsonb_agg(jsonb_build_object(
                                'topic_id',       t.id,
                                'topic_display_name', t.display_name
                            )),
                            '[]'::jsonb
                        )
                        FROM openalex.topics t
                        WHERE t.subfield_display_name = sf.topic_subfield
                    )
                ),
                '{}'::jsonb  -- If there are no subfields, return an empty object
            )
            FROM subfields sf
        )
    );
END;
$$;


--
-- Name: search_by_institution_topic(text, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.search_by_institution_topic(institution_id text, subfield_name text) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN jsonb_build_object(
        'institution_metadata', (
            SELECT row_to_json(i)
            FROM (
                SELECT 
                    i.id AS openalex_url, 
                    i.ror AS ror, 
                    i.display_name AS institution_name, 
                    i.homepage_url AS url,
                    (
                    SELECT jsonb_agg(i_t.type_id ORDER BY i_t.type_id)
                    FROM openalex.institutions_types AS i_t
                    WHERE i_t.institution_id = search_by_institution_topic.institution_id
                    ) AS types
                FROM openalex.institutions AS i
                WHERE i.id = search_by_institution_topic.institution_id
            ) i
        ),
        'subfield_metadata', (
            SELECT jsonb_agg(row_to_json(s))
            FROM (
                SELECT 
                    t.subfield_display_name AS subfield,
                    t.subfield_id AS subfield_url, 
                    t.id AS openalex_url, 
                    t.display_name AS topic
                FROM openalex.topics AS t
                WHERE t.subfield_display_name = search_by_institution_topic.subfield_name
            ) s
        ),
        'data', (
            SELECT jsonb_agg(row_to_json(data))
            FROM (
                SELECT
                    data_mv.author_id,
                    data_mv.author_name,
                    data_mv.num_of_works
                FROM search_by_institution_topic_data_mv AS data_mv
                WHERE
                    data_mv.institution_id = search_by_institution_topic.institution_id
                    AND data_mv.subfield_display_name = search_by_institution_topic.subfield_name
                ORDER BY data_mv.num_of_works DESC
            ) data
        ),
        'totals', (
            SELECT row_to_json(totals)
            FROM (
                SELECT 
                    SUM(data_mv.num_of_works) AS total_num_of_works,
                    SUM(data_mv.num_of_citations) AS total_num_of_citations,
                    COUNT(data_mv.author_name) AS total_num_of_authors
                FROM search_by_institution_topic_data_mv AS data_mv
                WHERE data_mv.subfield_display_name = search_by_institution_topic.subfield_name
                AND data_mv.institution_id = search_by_institution_topic.institution_id
            ) totals
        )
    );
END;
$$;


--
-- Name: search_by_topic(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.search_by_topic(subfield_name text) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN jsonb_build_object(
        'subfield_metadata', (
            SELECT jsonb_agg(row_to_json(s))
            FROM (
                SELECT 
                    t.subfield_display_name AS subfield,
                    t.subfield_id AS subfield_url, 
                    t.id AS openalex_url, 
                    t.display_name AS topic
                FROM openalex.topics AS t
                WHERE t.subfield_display_name = search_by_topic.subfield_name
            ) AS s
        ),
        'data', (
            SELECT jsonb_agg(row_to_json(data))
            FROM (
                SELECT
                    data_mv.institution_id,
                    data_mv.institution_name,
                    data_mv.num_of_authors,
                    data_mv.num_of_works,
                    (
                        SELECT jsonb_agg(i_t.type_id ORDER BY i_t.type_id)
                        FROM openalex.institutions_types AS i_t
                        WHERE i_t.institution_id = data_mv.institution_id
                    ) AS types
                FROM search_by_topic_data_mv AS data_mv
                WHERE data_mv.subfield_display_name = search_by_topic.subfield_name
                ORDER BY data_mv.num_of_authors DESC, data_mv.num_of_works DESC
            ) AS data
        ),
        'totals', (
            SELECT row_to_json(totals)
            FROM (
                SELECT
                    total_num_of_works,
                    total_num_of_authors,
                    total_num_of_citations
                FROM search_by_topic_totals_mv
                WHERE subfield_display_name = search_by_topic.subfield_name
            ) AS totals
        )
    );
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: institution_sat_act_data; Type: TABLE; Schema: mup; Owner: -
--

CREATE TABLE mup.institution_sat_act_data (
    openalex_id character varying(255),
    year integer,
    sat integer,
    sat_reading_25_percentile integer,
    sat_reading_75_percentile integer,
    sat_math_25_percentile integer,
    sat_math_75_percentile integer,
    act_25_percentile integer,
    act_75_percentile integer
);


--
-- Name: institutions_carnegie_classification; Type: TABLE; Schema: mup; Owner: -
--

CREATE TABLE mup.institutions_carnegie_classification (
    openalex_id text,
    mup_id integer,
    name text,
    city text,
    state text,
    control integer,
    sector integer,
    cc2000 integer,
    basic2005 integer,
    basic2010 integer,
    basic2015 integer,
    basic2018 integer,
    sizeset2018 integer,
    landgrnt integer,
    medical integer,
    numcip2 integer
);


--
-- Name: institutions_copy; Type: TABLE; Schema: mup; Owner: -
--

CREATE TABLE mup.institutions_copy (
    id character varying(255) NOT NULL,
    display_name character varying(255),
    country_code character varying(255),
    type character varying(255),
    federal_research_focus character varying(255),
    total_research_focus character varying(255)
);


--
-- Name: institutions_designations; Type: TABLE; Schema: mup; Owner: -
--

CREATE TABLE mup.institutions_designations (
    institution_name character varying(255) NOT NULL,
    msi_designation character varying(50) NOT NULL,
    is_r1 boolean NOT NULL,
    is_r2 boolean NOT NULL,
    is_hbcu boolean NOT NULL,
    is_tcu boolean NOT NULL,
    is_non_msi boolean NOT NULL,
    is_aanapisi boolean NOT NULL,
    is_pbi boolean NOT NULL,
    is_hsi boolean NOT NULL,
    is_nasnti boolean NOT NULL,
    is_annh boolean NOT NULL
);


--
-- Name: institutions_expense_inflation_factors; Type: TABLE; Schema: mup; Owner: -
--

CREATE TABLE mup.institutions_expense_inflation_factors (
    id integer NOT NULL,
    year integer NOT NULL,
    price_index numeric(10,2) NOT NULL,
    research_multiplier numeric(20,14),
    giving_multiplier numeric(20,14)
);


--
-- Name: institutions_faculty_awards_data; Type: TABLE; Schema: mup; Owner: -
--

CREATE TABLE mup.institutions_faculty_awards_data (
    openalex_id text,
    mup_id integer,
    control text,
    institution_name text,
    year integer,
    nae integer,
    nam integer,
    nas integer,
    num_fac_awards integer
);


--
-- Name: institutions_financial_data; Type: TABLE; Schema: mup; Owner: -
--

CREATE TABLE mup.institutions_financial_data (
    openalex_id text,
    mup_id integer,
    control text,
    institution_name text,
    year integer,
    endowment double precision,
    endowment_constant_dollars double precision,
    giving double precision,
    giving_constant_dollars double precision
);


--
-- Name: institutions_medical_expenditures; Type: TABLE; Schema: mup; Owner: -
--

CREATE TABLE mup.institutions_medical_expenditures (
    mup_id integer NOT NULL,
    institution character varying(255),
    control character varying(255),
    standalone_institution boolean,
    year integer NOT NULL,
    expenditure double precision
);


--
-- Name: institutions_postdoc_data; Type: TABLE; Schema: mup; Owner: -
--

CREATE TABLE mup.institutions_postdoc_data (
    openalex_id text,
    mup_id integer,
    control text,
    institution_name text,
    year integer,
    num_postdocs integer,
    num_doctorates integer
);


--
-- Name: institutions_r_and_d; Type: TABLE; Schema: mup; Owner: -
--

CREATE TABLE mup.institutions_r_and_d (
    institution_id character varying(255) NOT NULL,
    category character varying(255) NOT NULL,
    federal double precision,
    percent_federal double precision,
    total double precision,
    percent_total double precision
);


--
-- Name: institutions_research_funding_by_year; Type: TABLE; Schema: mup; Owner: -
--

CREATE TABLE mup.institutions_research_funding_by_year (
    institution_id character varying(255) NOT NULL,
    year integer NOT NULL,
    federal_research double precision,
    federal_research_constant double precision,
    nonfederal_research double precision,
    nonfederal_research_constant double precision,
    total_research double precision,
    total_research_constant double precision
);


--
-- Name: mup_institutions_expense_inflation_factors_id_seq; Type: SEQUENCE; Schema: mup; Owner: -
--

CREATE SEQUENCE mup.mup_institutions_expense_inflation_factors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: mup_institutions_expense_inflation_factors_id_seq; Type: SEQUENCE OWNED BY; Schema: mup; Owner: -
--

ALTER SEQUENCE mup.mup_institutions_expense_inflation_factors_id_seq OWNED BY mup.institutions_expense_inflation_factors.id;


--
-- Name: openalex_mup_mapping; Type: TABLE; Schema: mup; Owner: -
--

CREATE TABLE mup.openalex_mup_mapping (
    openalex text NOT NULL,
    mup integer
);


--
-- Name: authors; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.authors (
    id text NOT NULL,
    orcid text,
    display_name text,
    display_name_alternatives json,
    works_count integer,
    cited_by_count integer,
    last_known_institution text,
    works_api_url text,
    updated_date timestamp without time zone
);


--
-- Name: institutions; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.institutions (
    id text NOT NULL,
    ror text,
    display_name text,
    country_code text,
    type text,
    homepage_url text,
    image_url text,
    image_thumbnail_url text,
    display_name_acronyms json,
    display_name_alternatives json,
    works_count integer,
    cited_by_count integer,
    works_api_url text,
    updated_date timestamp without time zone,
    authors_count integer
);


--
-- Name: institutions_counts_by_year; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.institutions_counts_by_year (
    institution_id text NOT NULL,
    year integer NOT NULL,
    works_count integer,
    cited_by_count integer,
    oa_works_count integer
);


--
-- Name: institutions_geo; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.institutions_geo (
    institution_id text NOT NULL,
    city text,
    geonames_city_id text,
    region text,
    country_code text,
    country text,
    latitude real,
    longitude real
);


--
-- Name: institutions_ids; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.institutions_ids (
    institution_id text NOT NULL,
    openalex text,
    ror text,
    grid text,
    wikipedia text,
    wikidata text,
    mag bigint
);


--
-- Name: institutions_types; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.institutions_types (
    institution_id text NOT NULL,
    type_id text NOT NULL
);


--
-- Name: temp_authors; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.temp_authors (
    id text,
    orcid text,
    display_name text,
    display_name_alternatives json,
    works_count integer,
    cited_by_count integer,
    last_known_institution text,
    works_api_url text,
    updated_date timestamp without time zone
);


--
-- Name: temp_institutions; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.temp_institutions (
    id text,
    ror text,
    display_name text,
    country_code text,
    type text,
    homepage_url text,
    image_url text,
    image_thumbnail_url text,
    display_name_acronyms json,
    display_name_alternatives json,
    works_count integer,
    cited_by_count integer,
    works_api_url text,
    updated_date timestamp without time zone
);


--
-- Name: temp_institutions_counts_by_year; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.temp_institutions_counts_by_year (
    institution_id text,
    year integer,
    works_count integer,
    cited_by_count integer,
    oa_works_count integer
);


--
-- Name: temp_institutions_geo; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.temp_institutions_geo (
    institution_id text NOT NULL,
    city text,
    geonames_city_id text,
    region text,
    country_code text,
    country text,
    latitude real,
    longitude real
);


--
-- Name: temp_institutions_ids; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.temp_institutions_ids (
    institution_id text,
    openalex text,
    ror text,
    grid text,
    wikipedia text,
    wikidata text,
    mag bigint
);


--
-- Name: temp_topics; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.temp_topics (
    id text,
    display_name text,
    subfield_id text,
    subfield_display_name text,
    field_id text,
    field_display_name text,
    domain_id text,
    domain_display_name text,
    description text,
    keywords text,
    works_api_url text,
    wikipedia_id text,
    works_count integer,
    cited_by_count integer,
    siblings json,
    updated_date timestamp without time zone
);


--
-- Name: temp_works; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.temp_works (
    id text,
    doi text,
    title text,
    display_name text,
    publication_year integer,
    publication_date text,
    type text,
    cited_by_count integer,
    is_retracted boolean,
    is_paratext boolean,
    cited_by_api_url text,
    abstract_inverted_index json,
    language text
);


--
-- Name: temp_works_authorships; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.temp_works_authorships (
    work_id text,
    author_position text,
    author_id text,
    institution_id text,
    raw_affiliation_string text
);


--
-- Name: temp_works_topics; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.temp_works_topics (
    work_id text,
    topic_id text,
    score real
);


--
-- Name: topics; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.topics (
    id text NOT NULL,
    display_name text,
    subfield_id text,
    subfield_display_name text,
    field_id text,
    field_display_name text,
    domain_id text,
    domain_display_name text,
    description text,
    keywords text,
    works_api_url text,
    wikipedia_id text,
    works_count integer,
    cited_by_count integer,
    siblings json,
    updated_date timestamp without time zone
);


--
-- Name: types; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.types (
    id text NOT NULL
);


--
-- Name: works; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.works (
    id text NOT NULL,
    doi text,
    title text,
    display_name text,
    publication_year integer,
    publication_date text,
    type text,
    cited_by_count integer,
    is_retracted boolean,
    is_paratext boolean,
    cited_by_api_url text,
    abstract_inverted_index json,
    language text
);


--
-- Name: works_authorships; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.works_authorships (
    work_id text NOT NULL,
    author_position text,
    author_id text NOT NULL,
    institution_id text NOT NULL,
    raw_affiliation_string text
);


--
-- Name: works_topics; Type: TABLE; Schema: openalex; Owner: -
--

CREATE TABLE openalex.works_topics (
    work_id text NOT NULL,
    topic_id text NOT NULL,
    score real
);


--
-- Name: search_by_authors_mv; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.search_by_authors_mv AS
 SELECT w_a.author_id,
    t.subfield_display_name,
    count(DISTINCT w_a.work_id) AS num_of_works
   FROM ((openalex.works_authorships w_a
     JOIN openalex.works_topics w_t ON ((w_t.work_id = w_a.work_id)))
     JOIN openalex.topics t ON ((t.id = w_t.topic_id)))
  GROUP BY w_a.author_id, t.subfield_display_name
  WITH NO DATA;


--
-- Name: search_by_institution_mv; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.search_by_institution_mv AS
 SELECT w_a.institution_id AS id,
    t.subfield_display_name AS topic_subfield,
    count(DISTINCT w_a.author_id) AS num_of_authors
   FROM ((openalex.works_authorships w_a
     JOIN openalex.works_topics w_t ON ((w_a.work_id = w_t.work_id)))
     JOIN openalex.topics t ON ((w_t.topic_id = t.id)))
  GROUP BY w_a.institution_id, t.subfield_display_name
  WITH NO DATA;


--
-- Name: search_by_institution_topic_data_mv; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.search_by_institution_topic_data_mv AS
 WITH distinct_works AS (
         SELECT DISTINCT w_a.institution_id,
            t.subfield_display_name,
            a.id AS author_id,
            a.display_name AS author_name,
            w.id AS work_id,
            w.cited_by_count
           FROM ((((openalex.works_authorships w_a
             JOIN openalex.authors a ON ((w_a.author_id = a.id)))
             JOIN openalex.works w ON ((w_a.work_id = w.id)))
             JOIN openalex.works_topics w_t ON ((w.id = w_t.work_id)))
             JOIN openalex.topics t ON ((w_t.topic_id = t.id)))
        )
 SELECT institution_id,
    subfield_display_name,
    author_id,
    author_name,
    count(*) AS num_of_works,
    sum(cited_by_count) AS num_of_citations
   FROM distinct_works
  GROUP BY institution_id, subfield_display_name, author_id, author_name
  WITH NO DATA;


--
-- Name: search_by_topic_data_mv; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.search_by_topic_data_mv AS
 SELECT t.subfield_display_name,
    i.id AS institution_id,
    i.display_name AS institution_name,
    count(DISTINCT w_a.author_id) AS num_of_authors,
    count(DISTINCT w_a.work_id) AS num_of_works
   FROM (((openalex.works_authorships w_a
     JOIN openalex.institutions i ON ((w_a.institution_id = i.id)))
     JOIN openalex.works_topics w_t ON ((w_a.work_id = w_t.work_id)))
     JOIN openalex.topics t ON ((w_t.topic_id = t.id)))
  GROUP BY t.subfield_display_name, i.id, i.display_name
  WITH NO DATA;


--
-- Name: search_by_topic_totals_mv; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.search_by_topic_totals_mv AS
 WITH distinct_institutions AS (
         SELECT t.subfield_display_name,
            w_a.institution_id
           FROM ((openalex.works_authorships w_a
             JOIN openalex.works_topics w_t ON ((w_a.work_id = w_t.work_id)))
             JOIN openalex.topics t ON ((w_t.topic_id = t.id)))
          GROUP BY t.subfield_display_name, w_a.institution_id
        )
 SELECT di.subfield_display_name,
    sum(i.works_count) AS total_num_of_works,
    sum(i.authors_count) AS total_num_of_authors,
    sum(i.cited_by_count) AS total_num_of_citations
   FROM (distinct_institutions di
     JOIN openalex.institutions i ON ((di.institution_id = i.id)))
  GROUP BY di.subfield_display_name
  WITH NO DATA;


--
-- Name: institutions_expense_inflation_factors id; Type: DEFAULT; Schema: mup; Owner: -
--

ALTER TABLE ONLY mup.institutions_expense_inflation_factors ALTER COLUMN id SET DEFAULT nextval('mup.mup_institutions_expense_inflation_factors_id_seq'::regclass);


--
-- Name: institutions_designations institutions_designations_pkey; Type: CONSTRAINT; Schema: mup; Owner: -
--

ALTER TABLE ONLY mup.institutions_designations
    ADD CONSTRAINT institutions_designations_pkey PRIMARY KEY (institution_name);


--
-- Name: institutions_research_funding_by_year institutions_research_funding_by_year_pkey; Type: CONSTRAINT; Schema: mup; Owner: -
--

ALTER TABLE ONLY mup.institutions_research_funding_by_year
    ADD CONSTRAINT institutions_research_funding_by_year_pkey PRIMARY KEY (institution_id, year);


--
-- Name: institutions_copy mup_institutions_copy_pkey; Type: CONSTRAINT; Schema: mup; Owner: -
--

ALTER TABLE ONLY mup.institutions_copy
    ADD CONSTRAINT mup_institutions_copy_pkey PRIMARY KEY (id);


--
-- Name: institutions_expense_inflation_factors mup_institutions_expense_inflation_factors_pkey; Type: CONSTRAINT; Schema: mup; Owner: -
--

ALTER TABLE ONLY mup.institutions_expense_inflation_factors
    ADD CONSTRAINT mup_institutions_expense_inflation_factors_pkey PRIMARY KEY (id);


--
-- Name: institutions_expense_inflation_factors mup_institutions_expense_inflation_factors_year_key; Type: CONSTRAINT; Schema: mup; Owner: -
--

ALTER TABLE ONLY mup.institutions_expense_inflation_factors
    ADD CONSTRAINT mup_institutions_expense_inflation_factors_year_key UNIQUE (year);


--
-- Name: institutions_medical_expenditures mup_institutions_medical_expenditures_pkey; Type: CONSTRAINT; Schema: mup; Owner: -
--

ALTER TABLE ONLY mup.institutions_medical_expenditures
    ADD CONSTRAINT mup_institutions_medical_expenditures_pkey PRIMARY KEY (mup_id, year);


--
-- Name: institutions_r_and_d mup_institutions_r_and_d_pkey; Type: CONSTRAINT; Schema: mup; Owner: -
--

ALTER TABLE ONLY mup.institutions_r_and_d
    ADD CONSTRAINT mup_institutions_r_and_d_pkey PRIMARY KEY (institution_id, category);


--
-- Name: openalex_mup_mapping mup_openalex_mup_mapping_pkey; Type: CONSTRAINT; Schema: mup; Owner: -
--

ALTER TABLE ONLY mup.openalex_mup_mapping
    ADD CONSTRAINT mup_openalex_mup_mapping_pkey PRIMARY KEY (openalex);


--
-- Name: authors authors_pkey; Type: CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.authors
    ADD CONSTRAINT authors_pkey PRIMARY KEY (id);


--
-- Name: institutions_counts_by_year institutions_counts_by_year_pkey; Type: CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.institutions_counts_by_year
    ADD CONSTRAINT institutions_counts_by_year_pkey PRIMARY KEY (institution_id, year);


--
-- Name: institutions_geo institutions_geo_pkey; Type: CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.institutions_geo
    ADD CONSTRAINT institutions_geo_pkey PRIMARY KEY (institution_id);


--
-- Name: institutions_ids institutions_ids_pkey; Type: CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.institutions_ids
    ADD CONSTRAINT institutions_ids_pkey PRIMARY KEY (institution_id);


--
-- Name: institutions institutions_pkey; Type: CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.institutions
    ADD CONSTRAINT institutions_pkey PRIMARY KEY (id);


--
-- Name: institutions_types institutions_types_pkey; Type: CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.institutions_types
    ADD CONSTRAINT institutions_types_pkey PRIMARY KEY (institution_id, type_id);


--
-- Name: topics topics_pkey; Type: CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.topics
    ADD CONSTRAINT topics_pkey PRIMARY KEY (id);


--
-- Name: types types_pkey; Type: CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.types
    ADD CONSTRAINT types_pkey PRIMARY KEY (id);


--
-- Name: works_authorships works_authorships_pkey; Type: CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.works_authorships
    ADD CONSTRAINT works_authorships_pkey PRIMARY KEY (work_id, author_id, institution_id);


--
-- Name: works works_pkey; Type: CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.works
    ADD CONSTRAINT works_pkey PRIMARY KEY (id);


--
-- Name: works_topics works_topics_pkey; Type: CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.works_topics
    ADD CONSTRAINT works_topics_pkey PRIMARY KEY (work_id, topic_id);


--
-- Name: author_name_idx; Type: INDEX; Schema: openalex; Owner: -
--

CREATE INDEX author_name_idx ON openalex.authors USING btree (display_name);


--
-- Name: authors_id_idx; Type: INDEX; Schema: openalex; Owner: -
--

CREATE INDEX authors_id_idx ON openalex.authors USING btree (id);


--
-- Name: idx_works_authorships_institution_author_work; Type: INDEX; Schema: openalex; Owner: -
--

CREATE INDEX idx_works_authorships_institution_author_work ON openalex.works_authorships USING btree (institution_id, author_id, work_id);


--
-- Name: institution_name_idx; Type: INDEX; Schema: openalex; Owner: -
--

CREATE INDEX institution_name_idx ON openalex.institutions USING btree (display_name);


--
-- Name: institutions_id_idx; Type: INDEX; Schema: openalex; Owner: -
--

CREATE INDEX institutions_id_idx ON openalex.institutions USING btree (id);


--
-- Name: topic_name_idx; Type: INDEX; Schema: openalex; Owner: -
--

CREATE INDEX topic_name_idx ON openalex.topics USING btree (display_name);


--
-- Name: topic_subfield_name_idx; Type: INDEX; Schema: openalex; Owner: -
--

CREATE INDEX topic_subfield_name_idx ON openalex.topics USING btree (subfield_display_name);


--
-- Name: topics_id_idx; Type: INDEX; Schema: openalex; Owner: -
--

CREATE INDEX topics_id_idx ON openalex.topics USING btree (id);


--
-- Name: work_name_idx; Type: INDEX; Schema: openalex; Owner: -
--

CREATE INDEX work_name_idx ON openalex.works USING btree (display_name);


--
-- Name: works_authorships_author_id_idx; Type: INDEX; Schema: openalex; Owner: -
--

CREATE INDEX works_authorships_author_id_idx ON openalex.works_authorships USING btree (author_id);


--
-- Name: works_authorships_institution_id_idx; Type: INDEX; Schema: openalex; Owner: -
--

CREATE INDEX works_authorships_institution_id_idx ON openalex.works_authorships USING btree (institution_id);


--
-- Name: works_authorships_work_id_idx; Type: INDEX; Schema: openalex; Owner: -
--

CREATE INDEX works_authorships_work_id_idx ON openalex.works_authorships USING btree (work_id);


--
-- Name: works_id_idx; Type: INDEX; Schema: openalex; Owner: -
--

CREATE INDEX works_id_idx ON openalex.works USING btree (id);


--
-- Name: works_topics_topic_id_idx; Type: INDEX; Schema: openalex; Owner: -
--

CREATE INDEX works_topics_topic_id_idx ON openalex.works_topics USING btree (topic_id);


--
-- Name: works_topics_work_id_idx; Type: INDEX; Schema: openalex; Owner: -
--

CREATE INDEX works_topics_work_id_idx ON openalex.works_topics USING btree (work_id);


--
-- Name: works_topics_work_id_topic_id_idx; Type: INDEX; Schema: openalex; Owner: -
--

CREATE INDEX works_topics_work_id_topic_id_idx ON openalex.works_topics USING btree (work_id, topic_id);


--
-- Name: search_by_authors_mv_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX search_by_authors_mv_idx ON public.search_by_authors_mv USING btree (author_id);


--
-- Name: search_by_institution_mv_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX search_by_institution_mv_idx ON public.search_by_institution_mv USING btree (id);


--
-- Name: search_by_institution_topic_data_mv_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX search_by_institution_topic_data_mv_idx ON public.search_by_institution_topic_data_mv USING btree (institution_id, subfield_display_name);


--
-- Name: search_by_topic_data_mv_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX search_by_topic_data_mv_idx ON public.search_by_topic_data_mv USING btree (subfield_display_name);


--
-- Name: search_by_topic_totals_mv_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX search_by_topic_totals_mv_idx ON public.search_by_topic_totals_mv USING btree (subfield_display_name);


--
-- Name: works_authorships fk_author_id; Type: FK CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.works_authorships
    ADD CONSTRAINT fk_author_id FOREIGN KEY (author_id) REFERENCES openalex.authors(id);


--
-- Name: works_authorships fk_institution_id; Type: FK CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.works_authorships
    ADD CONSTRAINT fk_institution_id FOREIGN KEY (institution_id) REFERENCES openalex.institutions(id);


--
-- Name: institutions_counts_by_year fk_institution_id; Type: FK CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.institutions_counts_by_year
    ADD CONSTRAINT fk_institution_id FOREIGN KEY (institution_id) REFERENCES openalex.institutions(id);


--
-- Name: institutions_ids fk_institution_id; Type: FK CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.institutions_ids
    ADD CONSTRAINT fk_institution_id FOREIGN KEY (institution_id) REFERENCES openalex.institutions(id);


--
-- Name: institutions_geo fk_institution_id; Type: FK CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.institutions_geo
    ADD CONSTRAINT fk_institution_id FOREIGN KEY (institution_id) REFERENCES openalex.institutions(id);


--
-- Name: institutions_types fk_institution_id; Type: FK CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.institutions_types
    ADD CONSTRAINT fk_institution_id FOREIGN KEY (institution_id) REFERENCES openalex.institutions(id);


--
-- Name: works_topics fk_topic_id; Type: FK CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.works_topics
    ADD CONSTRAINT fk_topic_id FOREIGN KEY (topic_id) REFERENCES openalex.topics(id);


--
-- Name: institutions_types fk_type_id; Type: FK CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.institutions_types
    ADD CONSTRAINT fk_type_id FOREIGN KEY (type_id) REFERENCES openalex.types(id);


--
-- Name: works_authorships fk_work_id; Type: FK CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.works_authorships
    ADD CONSTRAINT fk_work_id FOREIGN KEY (work_id) REFERENCES openalex.works(id);


--
-- Name: works_topics fk_work_id; Type: FK CONSTRAINT; Schema: openalex; Owner: -
--

ALTER TABLE ONLY openalex.works_topics
    ADD CONSTRAINT fk_work_id FOREIGN KEY (work_id) REFERENCES openalex.works(id);


--
-- Name: search_by_authors_mv; Type: MATERIALIZED VIEW DATA; Schema: public; Owner: -
--

REFRESH MATERIALIZED VIEW public.search_by_authors_mv;


--
-- Name: search_by_institution_mv; Type: MATERIALIZED VIEW DATA; Schema: public; Owner: -
--

REFRESH MATERIALIZED VIEW public.search_by_institution_mv;


--
-- Name: search_by_institution_topic_data_mv; Type: MATERIALIZED VIEW DATA; Schema: public; Owner: -
--

REFRESH MATERIALIZED VIEW public.search_by_institution_topic_data_mv;


--
-- Name: search_by_topic_data_mv; Type: MATERIALIZED VIEW DATA; Schema: public; Owner: -
--

REFRESH MATERIALIZED VIEW public.search_by_topic_data_mv;


--
-- Name: search_by_topic_totals_mv; Type: MATERIALIZED VIEW DATA; Schema: public; Owner: -
--

REFRESH MATERIALIZED VIEW public.search_by_topic_totals_mv;


--
-- PostgreSQL database dump complete
--

