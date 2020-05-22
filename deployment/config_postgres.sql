/* PSQL statements that should be run AFTER Postgres database has been populated.
 * This file should be run either from shell command:
 *   psql --username=<user> --host=<host> --dbnamed=<db_name> --echo-all --file=config_postgres.sql
 *   psql -U <user> -h <host> -d <db_name> -a -f config_postgres.sql  # shorter version
 * or from PSQL console:
 *   \include config_postgres.sql
 *   \i config_postgres.sql        -- shorter version
 */

-- Enable "pg_trgm" extension (if it's not enabled yet)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

/* Show all available indexes in a certain table:
 *   SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'genes_gene';
 */

/* ----------------------------------------------------------------------
 *  7 default indexes in 'genes_gene' table (created by migration files):
 * ----------------------------------------------------------------------
 * (1) genes_gene_pkey
 * CREATE UNIQUE INDEX genes_gene_pkey ON public.genes_gene USING btree (id);
 *
 * (2) genes_gene_entrez_id_key
 * CREATE UNIQUE INDEX genes_gene_entrez_id_key ON public.genes_gene
 * USING btree (entrez_id);
 *
 * (3) genes_gene_systematic_name_d0de6832
 * CREATE INDEX genes_gene_systematic_name_d0de6832 ON public.genes_gene
 * USING btree (systematic_name);
 *
 * (4) genes_gene_systematic_name_d0de6832_like
 * CREATE INDEX genes_gene_systematic_name_d0de6832_like ON public.genes_gene
 * USING btree (systematic_name varchar_pattern_ops);
 *
 * (5) genes_gene_standard_name_f45ee6b8
 * CREATE INDEX genes_gene_standard_name_f45ee6b8 ON public.genes_gene
 * USING btree (standard_name);
 *
 * (6) genes_gene_standard_name_f45ee6b8_like
 * CREATE INDEX genes_gene_standard_name_f45ee6b8_like ON public.genes_gene
 * USING btree (standard_name varchar_pattern_ops);
 *
 * (7) genes_gene_organism_id_958c1ab6
 * CREATE INDEX genes_gene_organism_id_958c1ab6 ON public.genes_gene
 * USING btree (organism_id);
 */

/* ================================================
 *   Create 4 extra indexes in "genes_gene" table
 * ================================================
 */
-- (1) Trigram index on gene's systematic_name
CREATE INDEX genes_gene_systematic_name_trgm_idx ON public.genes_gene
USING gin (systematic_name gin_trgm_ops);

-- (2) Trigram index on gene's standard_name
CREATE INDEX genes_gene_standard_name_trgm_idx ON public.genes_gene
USING gin (standard_name gin_trgm_ops);

-- (3) Trigram index on gene's aliases
CREATE INDEX genes_gene_aliases_trgm_idx ON public.genes_gene
USING gin (aliases gin_trgm_ops);

-- (4) Trigram index on gene's description
CREATE INDEX genes_gene_desc_trgm_idx ON public.genes_gene
USING gin (description gin_trgm_ops);

/* -------------------------------------------------------------------------------
 *  3 default indexes in 'analyses_experiment' table (created by migration files):
 * -------------------------------------------------------------------------------
 * (1) analyses_experiment_pkey
 * CREATE UNIQUE INDEX analyses_experiment_pkey ON public.analyses_experiment
 * USING btree (id)
 *
 * (2) analyses_experiment_accession_key
 * CREATE UNIQUE INDEX analyses_experiment_accession_key ON public.analyses_experiment
 * USING btree (accession)

 * (3) analyses_experiment_accession_d73a87fe_like
 * CREATE INDEX analyses_experiment_accession_d73a87fe_like ON public.analyses_experiment
 * USING btree (accession varchar_pattern_ops)
 */

/* ======================================================
 *  Create 1 extra index in "analyses_experiment" table
 * ======================================================
 */
-- (1) Trigram index on experient's accession
CREATE INDEX analyses_experiment_accession_trgm_idx ON public.analyses_experiment
USING gin (accession gin_trgm_ops);
