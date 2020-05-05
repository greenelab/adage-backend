#!/usr/bin/env python3

"""
This script reads three gene information files and combine them into a
single tab-delimited file, which will be used as the input file of the
management command `update_gene_names_aliases.py` in the parent directory.
"""

import csv

gene_annotations = dict()


def get_PA14_names():
    """
    Reads in a CSV file that maps PAO1 names (aka. systematic_name) to PA14
    names. If a line's column #4 is "Pseudomonas aeruginosa UCBPP-PA14", then
    column #2 is PAO1 name, and column #5 is its PA14 name.

    Returns a dict whose key is PAO1 name, and value is a list of PA14 names.
    """

    PA14_src = 'Pseudomonas_aeruginosa_PAO1_107_orthologs.csv'
    pao1_to_pa14 = dict()
    with open(PA14_src) as fh:
        reader = csv.reader(fh, delimiter=',', quotechar='"')
        line_num = 0
        for row in reader:
            line_num += 1
            if line_num == 1 or row[3] != 'Pseudomonas aeruginosa UCBPP-PA14':
                continue

            pao1_name = row[1]
            pa14_name = row[4]
            pa14_list = pao1_to_pa14.get(pao1_name, [])
            if pa14_name not in pa14_list:
                pa14_list.append(pa14_name)

            pao1_to_pa14[pao1_name] = pa14_list

    return pao1_to_pa14


def read_errata():
    """
    Reads in a TSV errata file, whose column #1 is PAO1 name
    (aka. systematic_name), column #2 is the gene name (aka. standard_name),
    column #3 is a list of synonyms delimited by space character.

    Returns a dict whose key is PAO1 name, value is a two-element tuple, the
    first element is gene_name, the second element is list of synonyms.

    This function should be called before read_gene_annotation() so that if
    a PAO1 name already exists in the dict, read_gene_annotation() won't read
    the line with the same PAO1 name.
    """

    errata_src = 'gene_name_alias_corrections.tsv'
    with open(errata_src) as fh:
        line_num = 0
        for line in fh:
            line_num += 1
            if line_num == 1:
                continue
            tokens = line.strip().split('\t')
            pao1_name = tokens[0]
            gene_name = tokens[1]
            if gene_name == 'NULL':
                gene_name = ''
            synonyms = tokens[2]
            if len(synonyms) > 0 and synonyms != 'NULL':
                synonyms = tokens[2].strip().split(' ')
            else:
                synonyms = list()
            gene_annotations[pao1_name] = (gene_name, synonyms)

    return gene_annotations


def read_gene_annotation():
    """
    Read in a CSV file of Pseudomonas gene annotations. Column #6 is PAO1 name
    (aka. systematic_name), column #11 is gene name (aka. standard_name), and
    column #12 is a list of synonyms (delimited by " ; ").

    Returns a dict whose key is PAO1 name, value is a two-element tuple, the
    first element is gene_name, the second element is list of synonyms.

    This function should be called before read_errata().
    """
    gene_annotation_src = 'Pseudomonas_aeruginosa_PAO1_107.csv'
    with open(gene_annotation_src) as fh:
        reader = csv.reader(fh, delimiter=',', quotechar='"')
        line_num = 0
        for row in reader:
            line_num += 1
            if line_num == 1 or row[0].startswith('#'):
                continue

            # Skip the line if PAO1 name is already found in errta file
            pao1_name = row[5]
            if pao1_name in gene_annotations:
                continue

            gene_name = row[10]
            synonyms = row[11].split(' ; ')
            gene_annotations[pao1_name] = (gene_name, synonyms)


# main
pao1_to_pa14 = get_PA14_names()
read_errata()
read_gene_annotation()

# Merge pao1_to_pa14 and gene_annotations
print("#systematic_name", "standard_name", "synonyms", sep='\t')
for pao1_name, annotation in gene_annotations.items():
    gene_name = annotation[0]
    synonyms = annotation[1]
    if pao1_name in pao1_to_pa14:
        synonyms += pao1_to_pa14[pao1_name]
        synonyms.sort()
    synonyms = ' '.join(synonyms).strip()
    print(pao1_name, gene_name, synonyms, sep='\t')
