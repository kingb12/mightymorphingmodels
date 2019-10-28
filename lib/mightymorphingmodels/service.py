import random

from installed_clients.fba_toolsClient import fba_tools
from installed_clients.WorkspaceClient import Workspace

# =====================================================================================================================
# Type Strings From KBase

def types():
    return {'FBAModel': 'KBaseFBA.FBAModel',
            'Biochemistry': 'KBaseBiochem.Biochemistry',
            'Genome': 'KBaseGenomes.Genome',
            'FBA': 'KBaseFBA.FBA',
            'ReactionProbabilities': 'ProbabilisticAnnotation.RxnProbs',
            'ProteomeComparison': 'GenomeComparison.ProteomeComparison',
            'Media': 'KBaseBiochem.Media'
            }


# TODO: More pragmatic approach, have these stored in some sort of XML or plain text file that can be read in
# =====================================================================================================================



class Service:
    def __init__(self, fba_url, ws_url, ctx):
        self.ws_client = Workspace(ws_url, token=ctx['token'])
        self.fba_client = fba_tools(fba_url)

    def get_object(self, objid, wsid, name=None):
        """
        Returns an object and it's associated KBase information

        Returns an ObjectData (dictionary) like what is returned in the workspace service 'get_objects' function:

        /* The data and supplemental info for an object.

            UnspecifiedObject data - the object's data or subset data.
            object_info info - information about the object.
            list<ProvenanceAction> provenance - the object's provenance.
            username creator - the user that first saved the object to the
                workspace.
            timestamp created - the date the object was first saved to the
                workspace.
            list<obj_ref> - the references contained within the object.
            obj_ref copied - the reference of the source object if this object is
                a copy and the copy source exists and is accessible.
                null otherwise.
            boolean copy_source_inaccessible - true if the object was copied from
                another object, but that object is no longer accessible to the
                user. False otherwise.
            mapping<id_type, list<extracted_id>> extracted_ids - any ids extracted
                from the object.
            string handle_error - if an error occurs while setting ACLs on
                embedded handle IDs, it will be reported here.
            string handle_stacktrace - the stacktrace for handle_error.

        */
        typedef structure {
            UnspecifiedObject data;
            object_info info;
            list<ProvenanceAction> provenance;
            username creator;
            timestamp created;
            list<obj_ref> refs;
            obj_ref copied;
            boolean copy_source_inaccessible;
            mapping<id_type, list<extracted_id>> extracted_ids;
            string handle_error;
            string handle_stacktrace;
        } ObjectData;

        :param name: (optional) the name for the object to be retrieved. if included, favored over ID
        :param wsid: the workspace to retrieve the object from
        :param objid: the id of the object to be retrieved

        """
        if name is None:
            result = self.ws_client.get_objects2({'objects': [{'objid': objid, 'workspace': wsid}]})['data'][0]
        else:
            result = self.ws_client.get_objects2({'objects': [{'name': name, 'workspace': wsid}]})[0]
        return result['data'], result['info']


    def get_info(self, wsid, objid=None, name=None):
        if name is None:
            return self.ws_client.get_object_info_new({'objects': [{'objid': objid, 'workspace': wsid}]})[0]
        else:
            return self.ws_client.get_object_info_new({'objects': [{'name': name, 'workspace': wsid}]})[0]


    def save_object(self, data, type, wsid, objid=None, name=None):
        """
        Saves an object in KBase

        :param data: data representing the object to be saved
        :param type: a string representing the KBase type of the object
        :param wsid: destination workspace
        :param objid: (optional) ID for location of object to be saved (use with care, overwriting/failures are at KBase's
            discretion).
        :param name: (optional) string name for the pbject to be saved
        :return: a list of information about the object as it is stored in KBase
        """
        sv = {'data': data, 'type': type, 'name': name}
        if objid is not None:
            sv['objid'] = objid
        if name is not None:
            sv['name'] = name
        info = self.ws_client.save_objects({'workspace': wsid, 'objects': [sv]})[0]
        return info[0], info[7]


    def list_objects(self, workspace_id, typestr=None):
        """
        returns a list of all the objects within a workspace in tuples (obj_id, ws_id, object_name)

        :rtype: list
        :param typestr: (optional) if set, lists only objects of this type (filter over default case)
        :param workspace_id: the workspace to list the objects from
        :return: a list of tuples of objects
        """
        objects = self.ws_client.list_objects({'workspaces': [workspace_id]})
        result = list()
        for obj in objects:
            object_type = obj[2]
            if typestr is None or typestr in object_type or types()[typestr] in object_type:  # type filtering of our list
                result.append((obj[0], obj[6], obj[1], obj[2]))
        return result


    def clear_workspace(self, workspace_id):
        """
        clear all objects in a workspace (except for a Narrative object if applicable)
        :param workspace_id: workspace to clear
        :return: None
        """
        object_ids = [{'objid': info[0], 'wsid': workspace_id} for info in
                      self.ws_client.list_objects({'ids': [workspace_id]}) if not info[2].startswith('KBaseNarrative')]
        if len(object_ids) > 0:
            self.ws_client.delete_objects(object_ids)


    def delete_objects(self, object_tuples):
        """
        delete objects
        :param object_tuples: list of tuples representing objects to delete of the form (obj_id, ws_id)
        :return: None
        """
        object_ids = [{'objid': info[0], 'wsid': info[1]} for info in object_tuples]
        if len(object_ids) > 0:
            self.ws_client.delete_objects(object_ids)


    def copy_object(self, from_tuple, to_tuple):
        """
        Copies an object in the service to another location in the service

        :param from_tuple: (objid, wsid) of the object to be copied
        :param to_tuple: (name, wsid) of the destination. workspace may differ. NOTE NAME IS A STRING
        :return: a tuple with information on the new objectmodel
        """
        info = self.ws_client.copy_object({'from': {'workspace': from_tuple[1],
                                               'objid': from_tuple[0]},
                                      'to': {'workspace': to_tuple[1], 'name': to_tuple[0]}})
        return info[0], info[7]


    def gapfill_model(self, model, media, workspace=None):
        """

        :param model: FBAModel to gapfill
        :param media: Media to gapfill the model to
        :param workspace: destination workspace for new model and gapfill object
        :param name: (optional) name for new model. KBase will overwrite original if left unspecified.
        :return: the information for a new gap-filled model
        """
        if workspace is None:
            workspace = model.workspace_id
        params = {'fbamodel_id': str(model.object_id),
                  'fbamodel_workspace': str(model.workspace_id),
                  'fbamodel_output_id': str(model.name),
                  'workspace': workspace,
                  'media_id': media.object_id,
                  'media_workspace': media.workspace_id,
                  'comprehensive_gapfill': False}
        self.fba_client.gapfill_metabolic_model(params)
        return model.object_id, model.workspace_id


    def _gapfill_solution(self, fba):
            """
            If this FBA was created as a gapfilling solution, then this returns a list of reactions to be added/adjusted
            :return: list(tuple) (rxn_id, direction, etc.)
            """
            # For now, naively assume first = best = only gap-filling solution
            solutions = fba['gapfillingSolutions']
            if len(solutions) < 1:
                raise ValueError("This is not a gapfilling solution")
            gsol = solutions[0]['gapfillingSolutionReactions']
            result = []
            for r in gsol:
                reaction_id = r['reaction_ref'].split('/')[-1] + '_' + \
                              r['compartment_ref'].split('/')[-1] + str(r['compartmentIndex'])
                direction = r['direction']
                result.append((reaction_id, direction))
            return result


    def fba_formulation(self, media):
        return {'media': str(media.object_id), 'media_workspace': str(media.workspace_id)}


    def runfba(self, model, media, workspace=None):
        """
        runs Flux Balance Analysis on an FBAModel in the fba modeling service

        :param model: FBAModel to run flux balance analysis on
        :param media: Media to run FBA with
        :param workspace: (optional) workspace for the FBA object to be left in, default is model workspace
        :return: tuple identity of the FBA stored in the service
        """
        if workspace is None:
            workspace = model.workspace_id
        fba_params = {'workspace': workspace,
                      'fbamodel_id': model.object_id,
                      'fbamodel_workspace': model.workspace_id,
                      'media_workspace': str(media.workspace_id),
                      'media_id': str(media.object_id),
                      'fba_output_id': model.name + '_fba'}
        info = self.fba_client.run_flux_balance_analysis(fba_params)
        obj_id = info['new_fba_ref'].split('/')[1]
        return obj_id, workspace


    def runfva(self, model, media, workspace=None):
        """
        runs Flux Balance Analysis on an FBAModel in the fba modeling service

        :param model: FBAModel to run flux balance analysis on
        :param media: Media to run FBA with
        :param workspace: (optional) workspace for the FBA object to be left in, default is model workspace
        :return: tuple identity of the FBA stored in the service
        """
        if workspace is None:
            workspace = model.workspace_id
        fba_params = {'workspace': workspace, 'model': model.object_id, 'model_workspace': model.workspace_id,
                      'formulation': self.fba_formulation(media), 'fva': True}
        info = self.fba_client.runfba(fba_params)
        obj_id = info['new_fba_ref'].split('/')[1]
        return obj_id, workspace


    def translate_model(self, src_model, protcomp, workspace=None):
        """
        Uses the service to translate an FBAModel to a close genome relative
        :param protcomp: ProteomeComparison with source and target Genome
        :param src_model: FBAModel of source
        return: tuple identity of the translated model stored in the service
        """
        if workspace is None:
            workspace = src_model.workspace_id
        trans_params = {'keep_nogene_rxn': 1,
                        'proteincomparison_id': protcomp.object_id,
                        'proteincomparison_workspace': protcomp.workspace_id,
                        'fbamodel_id': src_model.object_id,
                        'fbamodel_output_id': 'translated_' + src_model.name,
                        'fbamodel_workspace': src_model.workspace_id,
                        'workspace': workspace}
        info = self.fba_client.propagate_model_to_new_genome(trans_params)
        obj_id = info['new_fbamodel_ref'].split('/')[1]
        return obj_id, workspace


    def reconstruct_genome(self, genome, workspace=None):
        """
        Reconstructs a genome and returns the identity of a stored draft recon model (FBAModel)
        :param workspace: (optional) destination workspace. Default is genome.workspace_id
        :param genome: Genome to draft a reconstruction for
        :return: tuple identity of the draft model stored in the service (FBAModel)
        """
        if workspace is None:
            workspace = genome.workspace_id
        recon_params = {'genome_id': genome.object_id,
                        'genome_workspace': genome.workspace_id,
                        'fbamodel_output_id': 'recon_' + genome.name,
                        'gapfill_model': False,  # TODO parameterize as option
                        'workspace': workspace}
        info = self.fba_client.build_metabolic_model(recon_params)
        # references returned here are sometimes inconsistent from other fba_tools APIs. Fetch obj info from ws service
        obj_name = info['new_fbamodel_ref'].split('/')[1]
        try:
            return int(obj_name), workspace
        except ValueError:
            ws_object_info = self.ws_client.get_object_info_new({'objects': [{'name': obj_name, 'workspace': workspace}]})[0]
            return ws_object_info[0], workspace


    def remove_reactions_in_place(self, model, reactions_to_remove):
        """
        Removes reactions from an FBAModel IN PLACE (changes object as it is stored)

        Recommended to make a copy first

        :param model: FBAModel to remove reactions form
        :param reactions_to_remove: reactions to remove (removal_id's)
        :return:
        """
        model_data, model_info = self.get_object(model.object_id, model.workspace_id)
        rxns_to_remove = set(reactions_to_remove)
        prior_ids = set([r['id'] for r in model_data['modelreactions']])
        model_data['modelreactions'] = [r for r in model_data['modelreactions'] if r['id'] not in rxns_to_remove]
        current_ids = set([r['id'] for r in model_data['modelreactions']])
        removed = set([rxn_id for rxn_id in prior_ids if rxn_id not in current_ids])
        if len(reactions_to_remove) != len(removed):
            print("WARNING: expected to remove", len(reactions_to_remove), "reactions but only removed", removed)
            print("Failed to remove", set(reactions_to_remove) - removed)
            print("Full arg reactions_to_remove:", ', '.join(reactions_to_remove))
        return self.save_object(model_data, model_info[2], model.workspace_id, name=model.name)


    def remove_reaction(self, model, reaction, output_id=None, in_place=False):
        """

        :param model: FBAModel to remove the reaction from
        :param reaction: removal_id (str) of the reaction to remove
        :param output_id: (optional) (str) of the new name for the output model
        :param in_place: (optional) set to true if you want to remove the reaction from the model in place instead of making
            a new model. Will disregard output_id argument if set to true
        :return: info tuple for the new FBAModel in the stored environment
        """

        if in_place:
            self.remove_reactions_in_place(model, [reaction])
        if output_id is None:
            i = 0
            output_id = model.name + '-' + str(i)
            names = set([info[3] for info in self.list_objects(model.workspace_id)])
            while output_id in names:
                i += 1
                output_id = model.name + '-' + str(i)

        model_data, model_info = self.get_object(model.object_id, model.workspace_id)
        for i, r in enumerate(model_data['modelreactions']):
            if reaction == r['id']:
                # remove in json and save
                del model_data['modelreactions'][i]
        return self.save_object(model_data, model_info[2], model.workspace_id, name=output_id)


    def add_reactions(self, model, new_reactions, workspace=None, name=None):
        """
        adds reactions to an FBAModel, in place or with a copy (set name to a new name)
        :param model: FBAModel to add reactions to
        :param new_reactions: list of tuples of the form (rxn_id, rxn_comp, direction, gpr) (gpr is optional)
        :param workspace: (optional) destination workspace, default is model.workspace_id
        :param name: output name for the new model. use to make a new one or modify in place
        :return: tuple identity of the model stored in the service (FBAModel)
        """
        reactions_to_add = [{
            'add_reaction_id': r[0],
            'reaction_compartment_id': len(r) > 1 and [r[1]] or [],
            'add_reaction_name': r[0],
            'add_reaction_direction': len(r) > 2 and r[2] or '=',
            'add_reaction_gpr': len(r) > 3 and r[3] or '',
        } for r in new_reactions]
        add_rxn_args = {'fbamodel_id': model.object_id,
                        'fbamodel_workspace': model.workspace_id,
                        'fbamodel_output_id': name or model.name,
                        'workspace': workspace or model.workspace_id,
                        'reactions_to_add': reactions_to_add}
        info = self.fba_client.edit_metabolic_model(add_rxn_args)
        return self._parse_objid_from_ref(info['new_fbamodel_ref']), model.workspace_id



    def add_reactions_manually(self, model, reactions, workspace=None, name=None):
        """
        Manually fix special reactions within the the object itself (use with caution)
        :param name: what to name the model when it is saved
        :param workspace: workspace to save the new FBAModel in
        :param reactions: (list<ModelReaction>) list of reactions to add manually
        :param model: FBAModel to add the reactions to
        """
        model.get_object()
        if workspace is None:
            workspace = model.workspace_id
        obj = model.data
        cpds = dict([(c['id'], c) for c in obj['modelcompounds']])
        for r in reactions:
            obj['modelreactions'].append(r.data)
            for cpd in r.data['modelReactionReagents']:
                c = cpd['modelcompound_ref'].split('/')[-1]
                if c not in cpds:
                    compound = {'id': c,
                                'name': c,
                                'aliases': ['mdlid:' + c.split('_')[0]],
                                'charge': 0,
                                'compound_ref': '489/6/6/compounds/id/cpd00000',
                                'modelcompartment_ref': '~/modelcompartments/id/' + c.split('_')[-1],
                                'formula': ''
                                }
                    obj['modelcompounds'].append(compound)
                    cpds = dict([(c['id'], c) for c in obj['modelcompounds']])
        if name is not None:
            return self.save_object(obj, types()['FBAModel'], workspace, name=name)
        return self.save_object(obj, types()['FBAModel'], workspace, objid=model.object_id)


    def adjust_directions_and_gprs(self, model, adjustments):
        reactions_to_change = [{
            'change_reaction_id': [r[0]],
            'change_reaction_direction': str(r[1]),
            'change_reaction_gpr': str(r[2])[1:-1],
        } for r in adjustments]
        change_rxn_args = {'fbamodel_id': model.object_id,
                        'fbamodel_workspace': model.workspace_id,
                        'fbamodel_output_id': model.name,
                        'workspace': model.workspace_id,
                        'reactions_to_change': reactions_to_change}
        self.fba_client.edit_metabolic_model(change_rxn_args)

    def adjust_directions(self, model, adjustments):
        """
        adjusts directions for reactions in an FBAModel
        :param model: FBAModel to adjust directions for
        :param adjustments: list<tuple> (rxn_id, direction). if rxn_id is not already in the model, it may be added
        :return: None
        """
        adjust_args = {'model': model.object_id,
                        'workspace': model.workspace_id,
                        'reaction': [r[0] for r in adjustments],
                        'direction': [str(r[1]) for r in adjustments]
                        }
        self.fba_client.adjust_model_reaction(adjust_args)

    def _integrate_gapfill(self, model, solution_fba, workspace=None):
        changes = self._gapfill_solution(solution_fba)
        reactions = dict([(r.rxn_id(), r) for r in model.get_reactions()])
        dirs = []
        additions = []
        for r in changes:
            if r[0] in reactions:
                dirs.append((reactions[r[0]].get_removal_id(), r[1]))
            else:
                temp = r[0].split('_')
                rxn_id = temp[0]
                rxn_comp = temp[1]
                additions.append((rxn_id, rxn_comp, r[1]))
        self.adjust_directions(model, dirs)
        info = self.add_reactions(model, additions, workspace=workspace)
        return info


    def model_info(self, model):
        comp = self.fba_client.compare_models({'models': [model.object_id], 'workspaces': [model.workspace_id]})
        return (comp['model_comparisons'], dict([(r['reaction'], r) for r in comp['reaction_comparisons']]))

    def init_workspace(self, ws=None, name=None):
        ws_id = ws
        ws_name = name
        if ws_name is None:
            ws_name = 'MMws'
        if ws is None:
            ws_conflict = True
            while ws_conflict:
                create_ws_params = {'workspace': ws_name, 'globalread': 'r', 'description':
                    "A workspace for storing the FBA's and meta data of the algorithm"}
                # Try to create a workspace, catch an error if the name is already in use
                try:
                    new_ws = self.ws_client.create_workspace(create_ws_params)
                    # new_ws is type workspace_info, a tuple where 0, 1 are id, name
                    ws_id = new_ws[0]
                    ws_name = new_ws[1]
                    ws_conflict = False
                except BaseException:
                    ws_name += str(random.randint(1, 9))
        return ws_id, ws_name

    def _parse_objid_from_ref(self, ref):
        return ref.split('/')[1]
    
class DummyService(Service):
    
    def __init__(self):
        self.ws_client = None
        self.fba_client = None