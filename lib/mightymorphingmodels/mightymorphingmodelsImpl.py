# -*- coding: utf-8 -*-
#BEGIN_HEADER
from service import Service
from objects import *
from morph import Morph
import uuid, sys, os, traceback
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
    GIT_URL = "https://github.com/kingb12/mightymorphingmodels.git"
    GIT_COMMIT_HASH = "b91c1c13202afa7588431b344b73742d20dce68d"

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.workspaceURL = config['workspace-url']
        self.scratch = config['scratch']
        #END_CONSTRUCTOR
        pass


    def morph_model(self, ctx, params):
        """
        Morph Function
        :param params: instance of type "CallingParams" (Insert your typespec
           information here.) -> structure: parameter "workspace" of String,
           parameter "fbamodel_id" of String, parameter "output_id" of String
        :returns: instance of type "CallingResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: returnVal
        #BEGIN morph_model
        service = Service(self.callback_url, self.workspaceURL, ctx)
        required_args = ['fbamodel_id', 'fbamodel_workspace', 'media_id', 'media_workspace']
        for r in required_args:
            if r not in params:
                raise ValueError("insufficient params supplied")
        model = FBAModel(params['fbamodel_id'], params['fbamodel_workspace'], service=service)
        media = Media(params['media_id'], params['media_workspace'], service=service)
        morph = Morph(service=service, src_model=model, media=media, ws_id=params['workspace'])
        morph.fill_src_to_media()

        reportObj = {
            'objects_created':[],
            'text_message':"MIGHTY"
        }
        #save report
        provenance = [{}]
        if 'provenance' in ctx:
            provenance = ctx['provenance']
        # add additional info to provenance here, in this case the input data object reference
        provenance[0]['input_ws_objects'] = [params['workspace']+'/'+params['fbamodel_id']]
        try:
            report_info_list = service.ws_client.save_objects({
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
