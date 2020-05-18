#!/bin/bash

set -e -x

DATA_DIR="../data"
BASE_DIR="../adage"

# Populate database
cd ${BASE_DIR}

echo "`date`: creating new organism ..."
./manage.py update_or_create_organism \
	    --tax_id=208964 \
	    --scientific_name="Pseudomonas aeruginosa" \
	    --common_name="Pseudomonas aeruginosa" \
	    --url_template="http://www.pseudomonas.com/feature/show/?locus_tag=<systematic_name>"

echo "`date`: creating xrdb ..."
./manage.py create_or_update_xrdb \
	    --name="PseudoCap" \
	    --URL="http://www.pseudomonas.com/getAnnotation.do?locusID=_REPL_"

echo "`date`: importing gene_info ..."
./manage.py import_gene_info \
	  --filename="${DATA_DIR}/Pseudomonas_aeruginosa_PAO1.gene_info" \
	  --tax_id=208964 \
	  --systematic_col=3 \
	  --symbol_col=2 \
	  --put_systematic_in_xrdb="PseudoCap"

echo "`date`: importing gene_history ..."
./manage.py import_gene_history \
	    --filename="${DATA_DIR}/gene_history_208964" \
	    --tax_id=208964 \
	    --tax_id_col=1 \
	    --discontinued_id_col=3 \
	    --discontinued_symbol_col=4

echo "`date`: importing updated genes ..."
./manage.py import_updated_genes ${DATA_DIR}/updated_genes.tsv
