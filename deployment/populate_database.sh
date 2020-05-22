#!/bin/bash
# set -e: exit at any error
# set -x: print out every command executed
set -e

# This script took ~33 minutes to populate a local Postgres database on
# Linux desktop in Greene Lab.

# Get absolute paths based on current script's path
SCRIPT_DIR=$(dirname $0)
ABS_SCRIPT_DIR=$(cd ${SCRIPT_DIR}; pwd)  # absolute path of script dir
REPO_DIR=$(dirname ${ABS_SCRIPT_DIR})
PROJECT_DIR="${REPO_DIR}/adage"
DATA_DIR="${REPO_DIR}/data"
DIVIDER="-------------------------------------------------"

# Constants used in management commands
TAX_ID=208964
SIMPLE_MODEL="Ensemble ADAGE 300"
COMPLEX_MODEL="Ensemble ADAGE 300 with more complex gene-gene network"
PARTICIPATION_TYPE="High-weight genes"

# Populate database
cd ${PROJECT_DIR}

date; echo "Creating new organism ..."
./manage.py create_or_update_organism \
	    --create_only \
	    --tax_id=${TAX_ID} \
	    --scientific_name="Pseudomonas aeruginosa" \
	    --common_name="Pseudomonas aeruginosa" \
	    --url_template="http://www.pseudomonas.com/feature/show/?locus_tag=<systematic_name>"

echo $DIVIDER; date; echo "Creating CrossRefDB ..."
./manage.py create_or_update_xrdb \
	    --name="PseudoCap" \
	    --URL="http://www.pseudomonas.com/getAnnotation.do?locusID=_REPL_"

echo $DIVIDER; date; echo "Importing gene_info ..."
./manage.py import_gene_info \
	  --filename="${DATA_DIR}/Pseudomonas_aeruginosa_PAO1.gene_info" \
	  --tax_id=${TAX_ID} \
	  --put_systematic_in_xrdb="PseudoCap"

echo $DIVIDER; date; echo "Importing gene_history ..."
./manage.py import_gene_history \
	    --filename="${DATA_DIR}/gene_history_208964" \
	    --tax_id=${TAX_ID}

echo $DIVIDER; date; echo "Importing updated genes ..."
./manage.py import_updated_genes "${DATA_DIR}/updated_genes.tsv"

echo $DIVIDER; date; echo "Importing experiments and samples ..."
./manage.py import_experiments_samples "${DATA_DIR}/experiment_sample_annotation.tsv"

echo $DIVIDER; date; echo "Adding samples_info to each experiment ..."
./manage.py add_samples_info_to_experiment

echo $DIVIDER; date; echo "Adding simple machine learning model ..."
./manage.py create_or_update_ml_model "${DATA_DIR}/simple_ml_model.yml"

echo $DIVIDER; date; echo "Adding complex machine learning model ..."
./manage.py create_or_update_ml_model "${DATA_DIR}/complex_ml_model.yml"

echo $DIVIDER; date; echo "Importing sample-signature activity for simple ML model ..."
# The following command took ~10 minutes to import sample-signature activity data to a local
# Postgres database on Linux desktop in Greene Lab, with six warning messages:
#  * Input file line #973: data_source in column #1 not found in database: JS-1B4.9.07.CEL
#  * Input file line #974: data_source in column #1 not found in database: JS-A164.9.07.CEL
#  * Input file line #975: data_source in column #1 not found in the database: JS-A84.9.07.CEL
#  * Input file line #976: data_source in column #1 not found in database: JS-G164.9.07.CEL
#  * Input file line #977: data_source in column #1 not found in database: JS-G84.18.07.CEL
#  * Input file line #978: data_source in column #1 not found in database: JS-T24.9.07.CEL
./manage.py import_sample_signature_activity \
	    --filename="${DATA_DIR}/sample_signature_activity.tsv" \
	    --ml_model="${SIMPLE_MODEL}"

echo $DIVIDER; date; echo "Importing sample-signature activity for complex ML model ..."
# The following command took ~10 minutes to import sample-signature activity data to a local
# Postgres database on Linux desktop in Greene Lab, with six warning messages:
#  * Input file line #973: data_source in column #1 not found in database: JS-1B4.9.07.CEL
#  * Input file line #974: data_source in column #1 not found in database: JS-A164.9.07.CEL
#  * Input file line #975: data_source in column #1 not found in the database: JS-A84.9.07.CEL
#  * Input file line #976: data_source in column #1 not found in database: JS-G164.9.07.CEL
#  * Input file line #977: data_source in column #1 not found in database: JS-G84.18.07.CEL
#  * Input file line #978: data_source in column #1 not found in database: JS-T24.9.07.CEL
./manage.py import_sample_signature_activity \
	  --filename="${DATA_DIR}/sample_signature_activity.tsv" \
	  --ml_model="${COMPLEX_MODEL}"

echo $DIVIDER; date; echo "Importing gene-gene network for simple ML model ..."
./manage.py import_gene_network \
	  --filename="${DATA_DIR}/gene_gene_network_cutoff_0.2.txt" \
	  --ml_model="${SIMPLE_MODEL}"

echo $DIVIDER; date; echo "Importing gene-gene network for complex ML model ..."
# The following command took ~3.5 minutes to import gene-gene network data to a local
# Postgres database on Linux desktop in Greene Lab.
./manage.py import_gene_network \
	  --filename="${DATA_DIR}/gene_gene_network_cutoff_0.2.txt" \
	  --ml_model="${COMPLEX_MODEL}"

echo $DIVIDER; date; echo "Creating new participation type ..."
./manage.py create_or_update_participation_type \
	    --name="${PARTICIPATION_TYPE}" \
	    --desc="High-weight genes are those that most strongly influence the signature's activity, and we have found that they often reveal the underlying process or processes captured by the signature."

echo $DIVIDER; date; echo "Importing gene-signature participation data for simple ML model ..."
# The following command took ~2 minutes to import gene-signature participation data to a local
# Postgres database on Linux desktop in Greene Lab.
./manage.py import_gene_signature_participation \
	    --filename="${DATA_DIR}/gene_signature_participation.tsv" \
	    --ml_model="${SIMPLE_MODEL}" \
	    --participation_type="${PARTICIPATION_TYPE}"

echo $DIVIDER; date; echo "Importing gene-signature participation data for complex ML model ..."
# The following command took ~2 minutes to import gene-signature participation data to a local
# Postgres database on Linux desktop in Greene Lab.
./manage.py import_gene_signature_participation \
	    --filename="${DATA_DIR}/gene_signature_participation.tsv" \
	    --ml_model="${COMPLEX_MODEL}" \
	    --participation_type="${PARTICIPATION_TYPE}"


echo $DIVIDER; date; echo "Importing gene-sample expression data ..."
# The following command took ~6 minutes to import gene-sample-signature expression data to a
# local Postgres database on Linux in Greene Lab, with six warning messages:
#   * line #1: data_source in column #973 not found in database: JS-1B4.9.07.CEL
#   * line #1: data_source in column #974 not found in database: JS-A164.9.07.CEL
#   * line #1: data_source in column #975 not found in database: JS-A84.9.07.CEL
#   * line #1: data_source in column #976 not found in database: JS-G164.9.07.CEL
#   * line #1: data_source in column #977 not found in database: JS-G84.18.07.CEL
#   * line #1: data_source in column #978 not found in database: JS-T24.9.07.CEL
./manage.py import_gene_sample_expression \
	    --filename="${DATA_DIR}/gene_sample_expression.tsv" \
	    --tax_id=${TAX_ID}

echo $DIVIDER; echo "Database populated successfully!"; date
