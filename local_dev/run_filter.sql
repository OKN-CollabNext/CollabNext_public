DROP TABLE IF EXISTS temp_ids;

CREATE TABLE temp_ids (id TEXT);

\COPY temp_ids FROM 'C:\Users\absol\OneDrive\Documents\Homework\NSF-OKN\institution_ids.txt' CSV;

DROP TABLE IF EXISTS temp_ids_norm;

CREATE TEMP TABLE temp_ids_norm AS
    SELECT DISTINCT
      CASE
        WHEN id ~* '^https?://openalex\.org/[iI][0-9]+$'
             THEN regexp_replace(id, '^https?://openalex\.org/', 'https://openalex.org/')
        WHEN id ~* '^[iI][0-9]+$'
             THEN 'https://openalex.org/' || upper(id)
        WHEN id ~* '^[0-9]+$'
             THEN 'https://openalex.org/I' || id
        ELSE id
      END AS id
    FROM temp_ids;

DROP TABLE IF EXISTS institutions_subset;

CREATE TABLE institutions_subset AS
    SELECT t.*
    FROM "openalex"."institutions" t
    WHERE CAST(t."id" AS TEXT) IN (SELECT id FROM temp_ids)
       OR CAST(t."id" AS TEXT) IN (SELECT id FROM temp_ids_norm);

DROP TABLE IF EXISTS works_authorships_subset;
CREATE TABLE works_authorships_subset AS
SELECT DISTINCT t.*
FROM "openalex"."works_authorships" t
JOIN institutions_subset p ON t."institution_id" = p."id";

DROP TABLE IF EXISTS institutions_counts_by_year_subset;
CREATE TABLE institutions_counts_by_year_subset AS
SELECT DISTINCT t.*
FROM "openalex"."institutions_counts_by_year" t
JOIN institutions_subset p ON t."institution_id" = p."id";

DROP TABLE IF EXISTS institutions_ids_subset;
CREATE TABLE institutions_ids_subset AS
SELECT DISTINCT t.*
FROM "openalex"."institutions_ids" t
JOIN institutions_subset p ON t."institution_id" = p."id";

DROP TABLE IF EXISTS institutions_geo_subset;
CREATE TABLE institutions_geo_subset AS
SELECT DISTINCT t.*
FROM "openalex"."institutions_geo" t
JOIN institutions_subset p ON t."institution_id" = p."id";

DROP TABLE IF EXISTS institutions_types_subset;
CREATE TABLE institutions_types_subset AS
SELECT DISTINCT t.*
FROM "openalex"."institutions_types" t
JOIN institutions_subset p ON t."institution_id" = p."id";

DROP TABLE IF EXISTS authors_subset;
CREATE TABLE authors_subset AS
SELECT DISTINCT t.*
FROM "openalex"."authors" t
JOIN works_authorships_subset c ON t."id" = c."author_id";

DROP TABLE IF EXISTS types_subset;
CREATE TABLE types_subset AS
SELECT DISTINCT t.*
FROM "openalex"."types" t
JOIN institutions_types_subset c ON t."id" = c."type_id";

DROP TABLE IF EXISTS works_subset;
CREATE TABLE works_subset AS
SELECT DISTINCT t.*
FROM "openalex"."works" t
JOIN works_authorships_subset c ON t."id" = c."work_id";

DROP TABLE IF EXISTS works_topics_subset;
CREATE TABLE works_topics_subset AS
SELECT DISTINCT t.*
FROM "openalex"."works_topics" t
JOIN works_subset p ON t."work_id" = p."id";

DROP TABLE IF EXISTS topics_subset;
CREATE TABLE topics_subset AS
SELECT DISTINCT t.*
FROM "openalex"."topics" t
JOIN works_topics_subset c ON t."id" = c."topic_id";