#!/usr/bin/env python3

# This Python script reads in `../data/Pseudomonas_aeruginosa_genesets.json`,
# then pickles the result into `../data/Pseudomonas_aeruginosa_pickled_genesets`,
# which will be used by the following endpoint:
# `/api/v1/tribe_client/return_unpickled_genesets?organism=Pseudomonas+aeruginosa`

# Note that if Adage has been configured correctly and Tribe is live, the pickled
# file can also be created by the following management command in `tribe_client`:
#   manage.py pickle_public_genesets
#
# The current script and `../data/Pseudomonas_aeruginosa_genesets.json` are added
# to the repo to minimize Adage's dependency on Tribe.


import json
import pickle

json_filename = "../data/Pseudomonas_aeruginosa_genesets.json"
pa_genesets = json.load(open(json_filename))

pkl_filename = "../data/Pseudomonas_aeruginosa_pickled_genesets"
pickle.dump(pa_genesets, open(pkl_filename, 'wb'))
