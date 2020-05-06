#!/usr/bin/env python3

"""
This script reads three gene information files, merges them together,
and prints them out. The output will be used as the input file of the
management command `update_gene_names_aliases.py`.
"""

import csv

gene_annotations = dict()


def get_PA14_names():
    """
    Reads in a CSV file that maps PAO1 names (aka. systematic_name) to PA14
    names.  The CSV file includes 8 columns:
        #1: "Strain(Query)"
        #2: "Locus Tag(Query)"
        #3: "Description(Query)"
        #4: "Strain(Hit)"
        #5: "Locus Tag(Hit)"
        #6: "Description(Hit)"
        #7: "Percent Identity"
        #8: "Alignment Length"
    #2 is a gene's PAO1 name, when #4 is 'Pseudomonas aeruginosa UCBPP-PA14',
    the value in #5 is the gene's PA14 name.

    Returns a dict whose key is PAO1 name, and value is a list of PA14 names.
    """

    PA14_src = 'Pseudomonas_aeruginosa_PAO1_107_orthologs.csv'
    pao1_to_pa14 = dict()
    with open(PA14_src) as fh:
        reader = csv.reader(fh, delimiter=',', quotechar='"')
        for line_num, row in enumerate(reader, start=1):
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
        for line_num, line in enumerate(fh, start=1):
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
    Read in a CSV file of Pseudomonas gene annotations. The file includes 21 columns:
        #1:  DB Version
        #2:  Assembly Accession
        #3:  Chromosome/Plasmid Name
        #4:  Chromosome/Plasmid Xref
        #5:  PGD Gene ID
        #6:  Locus Tag
        #7:  Feature Type
        #8:  Start
        #9:  End
        #10: Strand
        #11: Gene Name
        #12: Gene synonyns
        #13: Product Name
        #14: Product Name Confidence Class
        #15: Product Synonyms
        #16: RefSeq Accession
        #17: Length (nucleotides)
        #18: Length (amino acids)
        #19: Molecular Weight (predicted)
        #20: Isoelectric Point (predicted)
        #21: Subcellular Localization [Confidence Class]
    #6 is PAO1 name (aka. systematic_name), #11 is gene name (aka. standard_name),
    column #12 is a list of synonyms delimited by " ; ".

    Returns a dict whose key is PAO1 name, value is a two-element tuple, the
    first element is gene_name, the second element is list of synonyms.

    NOTE: This function should be called before read_errata().
    """

    gene_annotation_src = 'Pseudomonas_aeruginosa_PAO1_107.csv'
    with open(gene_annotation_src) as fh:
        reader = csv.reader(fh, delimiter=',', quotechar='"')
        for line_num, row in enumerate(reader, start=1):
            if line_num == 1 or row[0].startswith('#'):
                continue

            # Skip the line if PAO1 name is already found in errta file
            pao1_name = row[5]
            if pao1_name in gene_annotations:
                continue

            gene_name = row[10]
            synonyms = row[11].split(' ; ')
            gene_annotations[pao1_name] = (gene_name, synonyms)

if __name__ == '__main__':
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
