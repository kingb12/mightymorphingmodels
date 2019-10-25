import logging
from . import objects
import cobrakbase
from cobrakbase.core import KBaseFBAModel, KBaseBiochemMedia
from cobrakbase.core.converters import KBaseFBAModelToCobraBuilder

logger = logging.getLogger(__name__)

class AbstractGrowthCondition:
    """
    an interface for processing reactions according to some condition

    Subclases must implement evaluate(args) and return true or false. The primary use
    for this class is in the process_reactions method of the Client module, which removes
    reactions iteratiely, and decides to keep or remove a reaction based on the outcome of
    a GrowthCondition.  Here is an example:
        class SimpleCondition(AbstractGrowthCondition):
            def evaluate(args):
                # args must have attribute model
                fba = runfba(args['model'])
                return fba['Objective'] > 0
    This SimpleCondition keeps all reactions that are absolutely necessary for the models growth
    """

    def __init__(self, service=None):
        self.fba = None
        self.service = service

    def evaluate(self, arguments):
        raise NotImplementedError()


class SimpleCondition(AbstractGrowthCondition):
    """
    a growth conditon for absolute growth (objective > 0)

    Required attributes of args:
        - morph
        - model
        - fba_name
    """

    def evaluate(self, arguments):
        morph = arguments['morph']
        model = arguments['model'] if 'model' in arguments else morph.model
        info = self.service.runfba(model, morph.media, workspace=morph.ws_id)
        self.fba = objects.FBA(info[0], info[1], service=self.service)
        return self.fba.objective > 0.0

class CobraCondition(AbstractGrowthCondition):
    """
    a growth conditon for absolute growth (objective > 0)

    Required attributes of args:
        - morph
        - model
        - fba_name
    """

    def evaluate(self, arguments):
        morph = arguments['morph']
        model = arguments['model'] if 'model' in arguments else morph.model
        
        fbamodel = KBaseFBAModel(model.get_object())
        m = KBaseBiochemMedia(morph.media.get_object())
        cobra_model = KBaseFBAModelToCobraBuilder(fbamodel).with_media(m).build()
        solution = cobra_model.optimize()
        
        if not solution.status == 'optimal':
            return False
        
        logger.debug('solution %s', solution)
        self.fba = solution
        return solution.objective_value > 0.0 #intead of 0.0 should be EPS

class BarkeriCondition(AbstractGrowthCondition):
    """
    a growth condition for barkeri (3 media)
    """
    def evaluate(self, arguments):
        raise NotImplementedError()
        # morph = arguments['morph']
        # model = arguments['model'] if 'model' in arguments else morph.model
        # info = self.service.runfba(model, morph.media, workspace=morph.ws_id)
        # fba = objects.FBA(info[0], info[1], service=self.service)


class AllMedia(AbstractGrowthCondition):

    def __init__(self, media):
        AbstractGrowthCondition.__init__(self)
        self.media = media

    def evaluate(self, args):
        morph = args['morph']
        ws = morph.ws_id
        for med in self.media:
            morph = args['morph']
            model = args['model'] if 'model' in args else morph.model
            info = self.service.runfba(model, med, workspace=morph.ws_id)
            fba = objects.FBA(info[0], info[1], service=self.service)
            self.fba = fba
            if not fba.objective > 0.0:
                return False
        return True




