# -*- coding: utf-8 -*-
import os
import time
import unittest
from configparser import ConfigParser
from pprint import pformat as pprint

from dakotaHelloWorld.dakotaHelloWorldImpl import dakotaHelloWorld
from dakotaHelloWorld.dakotaHelloWorldServer import MethodContext
from dakotaHelloWorld.authclient import KBaseAuth as _KBaseAuth

from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.WorkspaceClient import Workspace


class dakotaHelloWorldTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = os.environ.get('KB_AUTH_TOKEN', None)
        config_file = os.environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('dakotaHelloWorld'):
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
                            {'service': 'dakotaHelloWorld',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = Workspace(cls.wsURL)
        cls.serviceImpl = dakotaHelloWorld(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']
        cls.dfu = DataFileUtil(cls.callback_url, token=token)
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
        # ret = self.getImpl().your_method(self.getContext(), parameters...)
        #
        # Check returned data with
        # self.assertEqual(ret[...], ...) or other unittest methods
        ret = self.serviceImpl.run_dakotaHelloWorld(self.ctx, {
            'workspace_name': self.wsName,
            'parameter_1': 'Hello World!'
        })
        print('report_name', ret[0]['report_name'])

    def get_workspaces_with_objects_by_owner(self, owner):
        client = self.wsClient
        workspaces = client.list_workspace_info(dict(
            owners=[owner]
        ))
        wmetas = [(user, name, wid) for [wid, name, user, *rest] in workspaces]
        out = {}
        for (user, name, wid) in wmetas:
            objects = client.list_objects(dict(
                workspaces=[name],
            ))
            if(len(objects)):
                out[wid] = objects
        return out

    def test_workspace_service(self):
        client = self.wsClient
        print(':'*71)
        workspaces = client.list_workspace_info(dict(
            owners=['dakota']
        ))
        print('workspace info')
        wmetas = [(user, name, wid) for [wid, name, user, *rest] in workspaces]
        for (user, name, wid) in wmetas:
            print('workspace name', name)
            objects = client.list_objects(dict(
                workspaces=[name],
                type='KBaseNarrative.Narrative-4.0',
            ))
            if(len(objects)):
                print(pprint(objects))
        print(':'*71)

    def test_dfu_module(self):
        dws = self.get_workspaces_with_objects_by_owner('dakota')
        print(f'''dakota's workspaces: {pprint(dws)}''')
        ws0 = list(dws.keys())[0]
        some_obj = self.dfu.get_objects({"object_refs": [f'{ws0}/7/1']})
        print(f'''some object: {pprint(some_obj)}''')
