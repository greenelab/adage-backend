import os
import itertools
import json
import logging
import pickle

from collections import defaultdict

from django.shortcuts import render, redirect
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseRedirect)
from django.utils import html

from tribe_client import utils

from .app_settings import (
    TRIBE_URL, TRIBE_ID, TRIBE_SCOPE, ACCESS_CODE_URL,
    BASE_TEMPLATE, TRIBE_LOGIN_REDIRECT, TRIBE_LOGOUT_REDIRECT,
    CROSSREF, PUBLIC_GENESET_FOLDER
)


def connect_to_tribe(request):
    if 'tribe_token' not in request.session:
        return render(
            request,
            'establish_connection.html',
            {
                'tribe_url': TRIBE_URL,
                'access_code_url': ACCESS_CODE_URL,
                'client_id': TRIBE_ID,
                'scope': TRIBE_SCOPE,
                'base_template': BASE_TEMPLATE
            }
        )
    else:
        return display_genesets(request)


def get_settings(request):
    tribe_settings = {
        'tribe_url': TRIBE_URL,
        'access_code_url': ACCESS_CODE_URL,
        'client_id': TRIBE_ID,
        'scope': TRIBE_SCOPE
    }

    json_response = json.dumps(tribe_settings)
    return HttpResponse(json_response, content_type='application/json')


def logout_from_tribe(request):
    request.session.clear()

    if TRIBE_LOGOUT_REDIRECT:
        return HttpResponseRedirect(TRIBE_LOGOUT_REDIRECT)
    else:
        return connect_to_tribe(request)


def get_token(request):
    access_code = request.GET.__getitem__('code')
    access_token = utils.get_access_token(access_code)
    request.session['tribe_token'] = access_token
    request.session['tribe_user'] = utils.retrieve_user_object(access_token)

    if TRIBE_LOGIN_REDIRECT:
        return HttpResponseRedirect(TRIBE_LOGIN_REDIRECT)
    else:
        return redirect('display_genesets')


def display_genesets(request):
    if 'tribe_token' in request.session:
        access_token = request.session['tribe_token']
        get_user = utils.retrieve_user_object(access_token)

        if (get_user == 'OAuth Token expired' or get_user == []):
            request.session.clear()
            return connect_to_tribe(request)
        else:  # The user must be logged in and has access to her/himself
            genesets = utils.retrieve_user_genesets(
                access_token, {'full_genes': 'true', 'limit': 100}
            )
            tribe_user = get_user
            return render(
                request,
                'display_genesets.html',
                {
                    'tribe_url': TRIBE_URL,
                    'genesets': genesets,
                    'tribe_user': tribe_user,
                    'base_template': BASE_TEMPLATE
                }
            )

    else:
        return connect_to_tribe(request)


def display_versions(request, geneset):
    if 'tribe_token' in request.session:
        access_token = request.session['tribe_token']
        get_user = utils.retrieve_user_object(access_token)

        if (get_user == 'OAuth Token expired' or get_user == []):
            request.session.clear()
            return connect_to_tribe(request)

        else:
            versions = utils.retrieve_user_versions(access_token, geneset)
            for version in versions:
                version['gene_list'] = []
                for annotation in version['annotations']:
                    version['gene_list'].append(
                        annotation['gene']['standard_name']
                    )
            return render(
                request,
                'display_versions.html',
                {'versions': versions, 'base_template': BASE_TEMPLATE}
            )


def return_access_token(request):
    if 'tribe_token' in request.session:
        data = {'access_token': request.session['tribe_token']}
    else:
        data = {'access_token': 'No access token'}
    data = json.dumps(data)
    return HttpResponse(data, content_type='application/json')


def create_geneset(request):
    """
    View to handle the creation of genesets on Tribe when users make
    POST request to the '/tribe_client/create_geneset' URL.

    Arguments:
    request -- Request object, which contains a dictionary-like object
    of POST data, among other things.

    * In the POST data, there should be a 'geneset' object that contains
    the information for the geneset being created. This 'geneset' is
    passed in the POST data as a string, which we load as json to get a
    dictionary. The general format for the data in this geneset object is:

    geneset = {
        organism: 'Mus musculus',  # Required
        title: 'Sample title',  # Required

        abstract: 'Sample abstract',  # Optional

        # Genes to be included in the geneset are sent in the 'annotations'
        # dictionary, and this whole dictionary is optional. The geneset
        # can have as many or as few annotations as desired. The format for
        # the annotations dictionary is:
        # {gene_id1: [<list of pubmed ids associated with that gene>],
        #  gene_id2: [<list of pubmed ids associated with that gene>]...}
        # The type of identifier for the gene_ids is whatever is set
        # in the CROSSREF setting.
        annotations: {55982: [20671152, 19583951],
                      18091: [8887666], 67087: [],
                      22410:[]}
    }

    Returns:
    Either -

    a) The Tribe URL of the geneset that has just been created, or
    b) A 401 Unauthorized response if the user is not signed in

    N.B. To gracefully save to Tribe, your interface should handle the
    case when a 400 and 401 responses are returned. One way to do this
    for the 401 Unauthorized response, for example, is to catch the error
    and send the user to the Tribe-login page ('/tribe_client' url, which
    is named 'connect_to_tribe' in urls.py). Another way to handle this
    response is to only allow the users to make a request
    to this view (via a button, etc.) when they are already signed in.

    """
    if not ('tribe_token' in request.session):
        return HttpResponse('Unauthorized', status=401)

    tribe_token = request.session['tribe_token']
    is_token_valid = utils.retrieve_user_object(tribe_token)

    if (is_token_valid == 'OAuth Token expired'):
        request.session.clear()
        return HttpResponse('Unauthorized', status=401)

    geneset_info = request.POST.get('geneset')
    geneset_info = json.loads(geneset_info)
    geneset_info['xrdb'] = CROSSREF

    tribe_response = utils.create_remote_geneset(
        tribe_token, geneset_info, TRIBE_URL
    )

    try:
        slug = tribe_response['slug']
        creator = tribe_response['creator']['username']
        geneset_url = TRIBE_URL + "/#/use/detail/" + creator + "/" + slug
        html_safe_content = html.escape(geneset_url)
        response = {'geneset_url': html_safe_content}

    # If there is an error and a json object could not be loaded from the
    # response, the create_remote_geneset() util function will return a
    # raw response from Tribe, which will trigger a TypeError when trying
    # to access a key from it like a dictionary.
    except TypeError:
        html_safe_content = html.escape(tribe_response.content)
        return HttpResponseBadRequest(
            'The following error has been returned by Tribe while attempting ' +
            'to create a geneset: "' + html_safe_content + '"'
        )

    json_response = json.dumps(response)
    return HttpResponse(json_response, content_type='application/json')


def return_user_obj(request):

    if 'tribe_token' in request.session:
        tribe_token = request.session['tribe_token']

    else:
        tribe_token = None

    tribe_response = utils.return_user_object(tribe_token)

    json_response = json.dumps(tribe_response)
    return HttpResponse(json_response, content_type='application/json')


def return_unpickled_genesets(request):
    """
    View that:

    a) unpickles public genesets from an organism's pickled public
    genesets file,

    b) requests the currently logged-in user's genesets (for that same
    organism) from Tribe,

    c) combines all of these genesets and puts the geneset information
    (including which genes are contained in which genesets) in a very
    different format, so that the front-end can run a geneset enrichment
    analysis.

    Arguments:
    request -- Request object, which contains a dictionary-like object
    of GET data, among other things.

    * The GET data should contain an 'organism' parameter. This should be
    a string of an organism's scientific name (e.g. 'Pseudomonas aeruginosa',
    or 'Homo sapiens').

    Returns:

    A json-ified dictionary, which has 3 key-value pairs:
    1) 'procs': A dictionary of geneset information, where each key is
    the Tribe geneset ID, and the value is another dictionary containing
    geneset information.

    2) 'genes': A dictionary, where each key is the gene Entrez ID and
    the value is a list of Tribe geneset ID's that contain this gene.

    3) 'bgtotal': Total count of all the different genes in all of the
    genesets.

    *N.B. The reason the dictionary in the response is formatted the way
    it is is that this code was based on some code in the GIANT webserver
    from the Troyanskaya lab. The front-end JavaScript code in GIANT expects
    a response in this format in order to calculate geneset enrichment, and
    consequently the front-end code in new webservers (like Adage) will be
    built following this structure.

    """
    organism = request.GET.get('organism')

    if not organism:
        logging.error(
            'No organism was sent in request made to '
            'return_unpickled_genesets() function.'
        )
        return HttpResponseBadRequest(
            "No organism scientific name was sent in the request. Please "
            "specify an organism's scientific name (e.g. 'Pseudomonas "
            "aeruginosa' or 'Homo sapiens') using the 'organism' parameter."
        )

    pickled_filename = organism.replace(' ', '_') + '_pickled_genesets'

    public_genesets = {}
    if PUBLIC_GENESET_FOLDER:
        pickled_filename_path = os.path.join(
            PUBLIC_GENESET_FOLDER, pickled_filename)
        if os.path.exists(pickled_filename_path):
            unpickled_contents = pickle.load(open(pickled_filename_path, 'rb'))
            public_genesets = unpickled_contents[0]
        else:
            logging.error(
                ('No pickled genesets file was found for organism with '
                 'scientific name {0} in return_unpickled_genesets() '
                 'function'
                ).format(organism))

    else:
        logging.error(
            'return_unpickled_genesets() function was called, but '
            'PUBLIC_GENESET_FOLDER setting has not been defined.'
        )

    # The code in the lines below gets the currently logged-in user's
    # genesets from Tribe (for the desired organism). If the user genesets
    # are cached in the user's session, then grab those genesets and filter
    # by organism. Otherwise, request the user genesets from Tribe for
    # the given organism.
    usergenesets = {}
    if 'tribe_genesets' in request.session:
        # User's Tribe genesets are cached in the session
        loggedin_user_genesets = request.session['tribe_genesets']
        usergenesets['My Gene Sets'] = []
        for geneset in loggedin_user_genesets:
            if geneset['organism']['scientific_name'] == organism:
                usergenesets['My Gene Sets'].append(geneset)
        usergenesets['My Gene Sets'] = loggedin_user_genesets

    elif 'tribe_token' in request.session:
        # There are no user genesets cached in the session - request them
        # from Tribe. *Note: This checks if there is a 'tribe_token' in
        # the session, or in other words if the user has logged in to Tribe
        # via this client server and authorized this server to use their
        # Tribe resources. If this is false, meaning the user is not logged
        # in, do not try to get user private genesets, just unpickle public
        # genesets.
        tribe_token = request.session['tribe_token']
        options = {'organism__species_name': organism, 'limit': '1500'}
        usergenesets['My Gene Sets'] = utils.retrieve_user_genesets(
            tribe_token, options
        )

    all_genes = set()

    # geneset_dict will be a dictionary of geneset information (but not
    # including the actual genes in the geneset). This will come in the
    # gene_dict dictionary, where each key will be the gene Entrez ID,
    # and each value will be a list of the genesets that the gene is in.
    geneset_dict, gene_dict = defaultdict(dict), defaultdict(set)

    for database, genesets in itertools.chain(
            public_genesets.items(), usergenesets.items()
    ):
        for geneset in genesets:
            if 'tip' not in geneset or geneset['tip'] is None:
                # The 'tip' is the latest geneset version. If there is no
                # tip, the geneset has no versions, meaning that it contains
                # no genes. In this case, just skip this geneset.
                continue

            geneset_id = str(geneset['id'])
            title = geneset['title']
            url = geneset['url'] if 'url' in geneset else ''

            if 'genes' in geneset['tip']:
                genes = set(geneset['tip']['genes'])
            else:
                genes = set()

            # Add genes to our set containing ALL the genes in all the
            # genesets.
            all_genes |= genes

            # Make a dictionary with just the geneset information (no genes).
            # The front-end code will only use this information if it
            # determines that this geneset is one of the ones enriched.
            # This will make the geneset-enrichment-calculating process
            # in the front-end more efficient.
            geneset_dict[geneset_id] = {
                'name': title,
                'dbase': database,
                'url': url,
                'size': len(genes)
            }
            for g in genes:
                gene_dict[str(g)].add(geneset_id)

    gene_dict = {
        gene: list(gs_set) for (gene, gs_set) in gene_dict.items()
    }

    response_dict = {
        'procs': geneset_dict,
        'genes': gene_dict,
        'bgtotal': len(all_genes)
    }
    json_response = json.dumps(response_dict)

    return HttpResponse(json_response, content_type='application/json')
