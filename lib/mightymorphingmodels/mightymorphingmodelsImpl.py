# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging

from .service import Service
from .objects import *
from .morph import Morph
import uuid, sys, os, traceback
from installed_clients.KBaseReportClient import KBaseReport
#END_HEADER


class mightymorphingmodels:
    '''
    Module Name:
    mightymorphingmodels

    Module Description:
    A KBase module: mightymorphingmodels
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = ""
    GIT_COMMIT_HASH = ""

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.workspace_url = config['workspace-url']
        self.shared_folder = config['scratch']
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                        level=logging.INFO)
        #END_CONSTRUCTOR
        pass


    def morph_model(self, ctx, params):
        """
        Morph Function
        :param params: instance of type "CallingParams" (Insert your typespec
           information here.) -> structure: parameter "fbamodel_workspace" of
           String, parameter "fbamodel_id" of String, parameter
           "media_workspace" of String, parameter "media_id" of String,
           parameter "genome_workspace" of String, parameter "genome_id" of
           String, parameter "proteincomparison_workspace" of String,
           parameter "proteincomparison_id" of String, parameter "fill_src"
           of Long, parameter "translate_media" of Long, parameter
           "num_reactions_to_process" of Long, parameter
           "translate_media_workspace" of String, parameter
           "translate_media_id" of String, parameter "output_id" of String,
           parameter "workspace" of String
        :returns: instance of type "CallingResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: returnVal
        #BEGIN morph_model
        self.service = Service(self.callback_url, self.workspace_url, ctx)
        required_args = ['fbamodel_name',
                         'fbamodel_workspace',
                         'media_name',
                         'media_workspace',
                         'proteincomparison_name',
                         'proteincomparison_workspace',
                         'genome_name',
                         'genome_workspace',
                         'output_name']
        for r in required_args:
            if r not in params:
                raise ValueError("insufficient params supplied: " + str(r))


        def _translate_obj_identity(workspace, name):
            info = self.service.get_info(workspace, name=name)
            return info[0], workspace
        objid, ws = _translate_obj_identity(params['fbamodel_workspace'], params['fbamodel_name'])
        model = FBAModel(objid, ws, service=self.service)
        objid, ws = _translate_obj_identity(params['media_workspace'], params['media_name'])
        media = Media(objid, ws, service=self.service)
        objid, ws = _translate_obj_identity(params['proteincomparison_workspace'], params['proteincomparison_name'])
        protcomp = ProteomeComparison(objid, ws, service=self.service)
        objid, ws = _translate_obj_identity(params['genome_workspace'], params['genome_name'])
        genome = Genome(objid, ws, service=self.service)
        probanno = None
        if 'rxn_probs_name' in params and 'rxn_probs_workspace' in params and \
                params['rxn_probs_name'] is not None and len(params['rxn_probs_name']) > 0:
            objid, ws = _translate_obj_identity(params['rxn_probs_workspace'], params['rxn_probs_name'])
            probanno = ReactionProbabilities(objid, ws, service=self.service)
        morph = Morph(service=self.service,
                      src_model=model,
                      media=media,
                      probanno=probanno,
                      protcomp=protcomp,
                      genome=genome,
                      ws_id=params['workspace'])
        if 'fill_src' in params and params['fill_src']:
            morph.fill_src_to_media()
        morph.translate_features()
        morph.reconstruct_genome()
        morph.label_reactions()
        morph.build_supermodel()
        if 'translate_media' in params and params['translate_media']:
            if 'target_media_name' in params and 'target_media_workspace' in params:
                objid, ws = self._translate_obj_identity(params['target_media_workspace'], params['target_media_name'])
                new_media = Media(objid, ws, service=self.service)
            else:
                new_media = morph.media
            morph.translate_media(new_media)
        output_name = params['output_name'] if 'output_name' in params else 'MorphedModel'
        if 'num_reactions_to_process' in params:
            morph.process_reactions(num_reactions=int(params['num_reactions_to_process']), name=output_name)
        else:
            morph.process_reactions(name=output_name)

        
        reportObj = {
            'objects_created':[],
            'text_message': "MIGHTY"
        }
        #save report
        provenance = [{}]
        if 'provenance' in ctx:
            provenance = ctx['provenance']
        # add additional info to provenance here, in this case the input data object reference
        provenance[0]['input_ws_objects'] = [params['workspace']+'/'+params['fbamodel_name']]
        try:
            report_info_list = self.service.ws_client.save_objects({
                'workspace': params['workspace'],
                'objects': [
                    {
                        'type':'KBaseReport.Report',
                        'data':reportObj,
                        'name':'CallingFBA_report' + str(hex(uuid.getnode())),
                        'meta':{},
                        'hidden': 1, # important!  make sure the report is hidden
                        'provenance':provenance
                    }
                ]
            })
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            orig_error = ''.join('    ' + line for line in lines)
            raise ValueError('Error saving Report object to workspace:\n' + orig_error)
        report_info = report_info_list[0]
        print('Ready to return')
        returnVal = {
            'report_name':'FS_report',
            'report_ref': str(report_info[6]) + '/' + str(report_info[0]) + '/' + str(report_info[4])
        }
        #END morph_model

        # At some point might do deeper type checking...
        if not isinstance(returnVal, dict):
            raise ValueError('Method morph_model return value ' +
                             'returnVal is not type dict as required.')
        # return the results
        return [returnVal]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
