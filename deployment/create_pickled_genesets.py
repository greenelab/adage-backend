# This Python script reads in `../data/Pseudomonas_aeruginosa_genesets.json`,
# then pickles the result into `../data/Pseudomonas_aeruginosa_pickled_genesets`,
# which will be used by the following endpoint:
# <host>/api/v1/tribe_client/return_unpickled_genesets?organism=Pseudomonas+aeruginosa

import json
import pickle

json_filename = "../data/Pseudomonas_aeruginosa_genesets.json"
pa_genesets = json.load(open(json_filename))

pkl_filename = "../data/Pseudomonas_aeruginosa_pickled_genesets"
pickle.dump(pa_genesets, open(pkl_filename, 'wb'))
