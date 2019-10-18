# -*- coding: utf-8 -*-
import os
import time
import unittest
from configparser import ConfigParser

from mightymorphingmodels.mightymorphingmodelsImpl import mightymorphingmodels
from mightymorphingmodels.mightymorphingmodelsServer import MethodContext
from mightymorphingmodels.authclient import KBaseAuth as _KBaseAuth

from installed_clients.WorkspaceClient import Workspace


class mightymorphingmodelsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = os.environ.get('KB_AUTH_TOKEN', None)
        config_file = os.environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('mightymorphingmodels'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'mightymorphingmodels',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = Workspace(cls.wsURL)
        cls.serviceImpl = mightymorphingmodels(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']
        suffix = int(time.time() * 1000)
        cls.wsName = "test_ContigFilter_" + str(suffix)
        ret = cls.wsClient.create_workspace({'workspace': cls.wsName})  # noqa

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    def test_your_method(self):
        # Prepare test objects in workspace if needed using
        # self.getWsClient().save_objects({'workspace': self.getWsName(),
        #                                  'objects': []})
        #
        # Run your method by
        ws = "bking:narrative_1550692997297"
        params = {
            "fbamodel_name": "shewanella_amazonesis_source_model_prefilled_2",
            "fbamodel_workspace": ws,
            "proteincomparison_name": "s_amazonesis_s_colwelliana_proteome_comparison",
            "proteincomparison_workspace": ws,
            "genome_name": "shewanella_colwelliana_genome",
            "genome_workspace": ws,
            "media_name": "MR1_Minimal_Media",
            "media_workspace": ws,
            "translate_media": False,
            "num_reactions_to_process": "2",
            "workspace": ws,
            "output_name": "my_py3_morphed_model"
        }
        ret = self.serviceImpl.morph_model(self.ctx, params)
        # ret = self.getImpl().your_method(self.getContext(), parameters...)
        #
        # Check returned data with
        # self.assertEqual(ret[...], ...) or other unittest methods
