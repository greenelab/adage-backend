import json, string
from rest_framework.test import APIClient, APITestCase
from genes.models import Gene
from organisms.models import Organism


class GeneSearchAPITests(APITestCase):
    """Test API endpoints for retrieving and searching gene data."""

    def setUp(self):
        self.organism = Organism.objects.create(
            taxonomy_id=123,
            common_name="test common organism",
            scientific_name="test scientific organism",
            slug="test-org"
        )
        self.gene1 = Gene.objects.create(
            standard_name='A1', systematic_name='a12', organism=self.organism
        )
        self.gene2 = Gene.objects.create(
            standard_name=None, systematic_name='b34', organism=self.organism
        )

        self.std_prefix = 'foobar'
        Gene.objects.create(
            standard_name=self.std_prefix, organism=self.organism
        )

        # Create 26 more genes whose standard names start with 'ans' and end
        # with an uppercase letter.
        for letter in string.ascii_uppercase:
            Gene.objects.create(
                standard_name=(self.std_prefix + letter), organism=self.organism
            )

        self.api_base = '/api/v1/genes/'
        self.client = APIClient()

    def test_get_search(self):
        """Tests gene search API with a GET request"""

        # Search by gene1's standard_name:
        response = self.client.get(
            self.api_base, {'search': self.gene1.standard_name}
        )
        json_response = json.loads(response.content)
        best_gene_result = json_response['results'][0]
        self.assertEqual(best_gene_result['standard_name'],
                         self.gene1.standard_name)
        self.assertEqual(best_gene_result['systematic_name'],
                         self.gene1.systematic_name)

    def test_get_autocomplete(self):
        """Tests gene autocomplete API with a GET request."""

        response = self.client.get(
            self.api_base, {'autocomplete': self.std_prefix, 'limit': 100}
        )
        json_response = json.loads(response.content)
        self.assertEqual(len(json_response['results']), 27)

        # The exact standard name match should have the highest rank:
        best_gene_result = json_response['results'][0]
        self.assertEqual(best_gene_result['standard_name'], self.std_prefix)

    def test_post_search(self):
        """Tests gene search API with a POST request."""

        # Search by gene2's systematic_name:
        response = self.client.post(
            self.api_base, {'search': self.gene2.systematic_name}, format='json'
        )
        json_response = json.loads(response.content)
        best_gene_result = json_response['results'][0]
        self.assertEqual(best_gene_result['standard_name'],
                         self.gene2.standard_name)
        self.assertEqual(best_gene_result['systematic_name'],
                         self.gene2.systematic_name)


    def test_post_ids(self):
        """Tests a POST request of long list of gene IDs that is longer
        than 4 KB (the maximum length of `GET` request).

        `num_genes` is set to 1100 because:
          - 9 * 1 = 9 chars of single-digit IDs (1-9)
          - 90 * 2 = 180 chars of double-digit IDs (10-99)
          - 900 * 3 = 2700 chars of triple-digit IDs (100-999)
          - 101 * 4 = 404 chars of four-digit IDs (1000-1100)
          - (1100 - 1) * 1 chars of delimiters (',')
        TOTAL = 9 + 180 + 2700 + 404 + 1099 = 4392 chars.

        This is based on "APIResourceTestCase.test_expressionvalue_big_post()"
        test in:
        https://github.com/greenelab/adage-server/blob/master/adage/analyze/tests.py
        """

        org456 = Organism.objects.create(
            taxonomy_id=456,
            common_name="org-456",
            scientific_name="scientific org-456",
            slug="org456-slug"
        )

        num_genes = 1100
        for i in range(num_genes):
            Gene.objects.create(
                entrezid=(i + 100),
                systematic_name="sys_name #" + str(i + 100),
                standard_name="std_name #" + str(i + 100),
                organism=org456
            )

        gene_ids = ",".join(
            [str(g.id) for g in Gene.objects.filter(organism=org456)]
        )

        response = self.client.post(
            self.api_base, {'pk__in': gene_ids}, format='json'
        )
        json_response = json.loads(response.content)
        num_in_response = len(json_response['results'])
        self.assertEqual(num_in_response, num_genes)
