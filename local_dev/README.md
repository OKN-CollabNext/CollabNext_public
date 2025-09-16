# Create Local Database (Markdown)

> Replace `{full_dataset_location}` with the full path to the extracted dataset directory on your machine (e.g., `C:\data\openalex_dump`). All commands below assume a Windows command prompt unless noted.

1. **Download the full dataset as `.dat` files (~50 GB)**  
   https://stars.renci.org/var/frink/collabnext/postgres-bkup/

2. **Unzip the files** — you should see a bunch of `.dat` files.

3. **Get `filter_copy.py` from this folder.**

4. **Prepare your institution IDs file.**  
   Collect all OpenAlex IDs for institutions you want to include in a text file named `institution_ids.txt`.

5. **Open a command prompt.**

6. **Install Postgres and Python.** These should work:
   
   ```bash
   pg_restore --version
   psql --version
   python --version
   ```

7. **Set environment variables for Postgres:**
   
   ```bash
   set PGUSER=postgres
   set PGPASSWORD=yourpassword
   set PGDATABASE=small_openalex
   set PGHOST=localhost
   set PGPORT=5432
   ```

8. **Drop and create an empty local Postgres database:**
   
   ```bash
   psql -d postgres -v ON_ERROR_STOP=1 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='small_openalex';"
   dropdb small_openalex
   createdb small_openalex
   ```

9. **Restore the database schema:**
   
   ```bash
   pg_restore --no-owner --no-privileges --section=pre-data -d small_openalex "C:\{full_dataset_location}"
   ```

10. **Navigate to your working directory with `institution_ids.txt`.**

11. **Load `openalex.institutions` into the database:**
    
    ```bash
    pg_restore -a -n openalex -t institutions -f - "C:\{full_dataset_location}" ^
    | python .\filter_copy.py --table openalex.institutions --include-col id --ids-file .\institution_ids.txt ^
    | psql -d small_openalex
    ```

12. **Load `openalex.institutions_geo`:**
    
    ```bash
    pg_restore -a -n openalex -t institutions_geo -f - "C:\{full_dataset_location}" ^
    | python .\filter_copy.py --table openalex.institutions_geo --include-col institution_id --ids-file .\institution_ids.txt ^
    | psql -d small_openalex
    ```

13. **Load `openalex.institutions_ids`:**
    
    ```bash
    pg_restore -a -n openalex -t institutions_ids -f - "C:\{full_dataset_location}" ^
    | python .\filter_copy.py --table openalex.institutions_ids --include-col institution_id --ids-file .\institution_ids.txt ^
    | psql -d small_openalex
    ```

14. **Load `openalex.institutions_types`:**
    
    ```bash
    pg_restore -a -n openalex -t institutions_types -f - "C:\{full_dataset_location}" ^
    | python .\filter_copy.py --table openalex.institutions_types --include-col institution_id --ids-file .\institution_ids.txt ^
    | psql -d small_openalex
    ```

15. **Load `openalex.institutions_counts_by_year`:**
    
    ```bash
    pg_restore -a -n openalex -t institutions_counts_by_year -f - "C:\{full_dataset_location}" ^
    | python .\filter_copy.py --table openalex.institutions_counts_by_year --include-col institution_id --ids-file .\institution_ids.txt ^
    | psql -d small_openalex
    ```

16. **Copy the `works_authorships` data into a temporary file (~7 GB):**
    
    ```bash
    pg_restore -a -n openalex -t works_authorships -f .\wa.copy "C:\{full_dataset_location}"
    ```

17. **Filter the `works_authorships` data:**
    
    ```bash
    python filter_copy.py --table openalex.works_authorships --include-col institution_id --ids-file institution_ids.txt --emit-id author_id=author_ids.txt --emit-id work_id=work_ids.txt < wa.copy > wa.filtered.copy
    ```

18. You should now have a file called `wa.filtered.copy`.

19. **Clean the file:**
    
    ```bash
    findstr /R "^https://openalex.org/" wa.filtered.copy > wa.filtered.data
    ```

20. **Load it into Postgres:**
    
    ```bash
    psql -d small_openalex -c "\COPY openalex.works_authorships FROM 'wa.filtered.data' WITH (FORMAT text, DELIMITER E'\t', NULL '\N');"
    ```

21. **Verify authorships row count (should be non-zero):**
    
    ```bash
    psql -d small_openalex -tAc "SELECT COUNT(*) FROM openalex.works_authorships;"
    ```

22. The previous process should have created two additional files: `author_ids.txt` and `work_ids.txt`. Confirm these are present.

23. **Add authors to the database:**
    
    ```bash
    pg_restore -a -n openalex -t authors -f - "C:\{full_dataset_location}" ^
    | python filter_copy.py --table openalex.authors --include-col id --ids-file author_ids.txt ^
    | psql -d small_openalex
    ```

24. **Verify author count is not 0 (or obviously incorrect):**
    
    ```bash
    psql -d small_openalex -tAc "SELECT COUNT(*) FROM openalex.authors;"
    ```

25. **Add works (longest step):**
    
    ```bash
    pg_restore -a -n openalex -t works -f - "C:\{full_dataset_location}" ^
    | python filter_copy.py --table openalex.works --include-col id --ids-file work_ids.txt ^
    | psql -d small_openalex
    ```

26. *FYI:* There are ~23 million rows. The script will print when each million is passed by the filter.

27. **Verify work count is not 0:**
    
    ```bash
    psql -d small_openalex -tAc "SELECT COUNT(*) FROM openalex.works;"
    ```

28. **Upload `openalex.works_topics` and collect topic IDs:**
    
    ```bash
    pg_restore -a -n openalex -t works_topics -f - "C:\{full_dataset_location}" ^
    | python filter_copy.py --table openalex.works_topics --include-col work_id --ids-file work_ids.txt --emit-id topic_id=topic_ids.txt ^
    | psql -d small_openalex
    ```

29. **Upload all topics:**
    
    ```bash
    pg_restore -a -n openalex -t topics -d small_openalex "C:\{full_dataset_location}"
    ```

30. **Verify topics count:**
    
    ```bash
    psql -d small_openalex -tAc "SELECT COUNT(*) FROM openalex.topics;"
    ```

31. **Load the `mup` schema data (two commands):**
    
    ```bash
    pg_restore -a -n mup -d small_openalex "C:\{full_dataset_location}"
    pg_restore --no-owner --no-privileges --section=post-data -n mup -d small_openalex "C:\{full_dataset_location}"
    ```

32. **Rebuild indexes** *(this may give an error with types, sa…)*:
    
    ```bash
    pg_restore --no-owner --no-privileges --section=post-data -n openalex -d small_openalex "C:\{full_dataset_location}"
    ```

33. **Refresh materialized views:**
    
    ```bash
    psql -d small_openalex -c "ANALYZE VERBOSE;"
    psql -d small_openalex -v ON_ERROR_STOP=1 -c "REFRESH MATERIALIZED VIEW public.search_by_authors_mv;"
    psql -d small_openalex -v ON_ERROR_STOP=1 -c "REFRESH MATERIALIZED VIEW public.search_by_institution_mv;"
    psql -d small_openalex -v ON_ERROR_STOP=1 -c "REFRESH MATERIALIZED VIEW public.search_by_institution_topic_data_mv;"
    psql -d small_openalex -v ON_ERROR_STOP=1 -c "REFRESH MATERIALIZED VIEW public.search_by_topic_data_mv;"
    psql -d small_openalex -v ON_ERROR_STOP=1 -c "REFRESH MATERIALIZED VIEW public.search_by_topic_totals_mv;"
    ```

34. **Save as a `.sql` file:**
    
    ```bash
    pg_dump -U postgres -d small_openalex -F p -f small_openalex.sql
    ```

35. **Confirm size** (~6 GB).

36. **Cleanup** — you can delete any temporary files now.

37. **(Optional) Drop the database:**
    
    ```bash
    dropdb small_openalex
    ```

38. **Restore from the saved dump later:**
    
    ```bash
    createdb -U postgres small_openalex
    psql -U postgres -d small_openalex -f small_openalex.sql
    ```
