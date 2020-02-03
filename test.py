import sys, os, hashlib
from logging.config import dictConfig

logging_config = dict(
    version = 1,
    formatters = {
        'f': {'format':
              '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'}
    },
    handlers = {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'fairgraph.log',
            'formatter': 'f'
        }
    },
    loggers = {
        'openid_http_client.http_client': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
        'fairgraph': {
            'handlers': ['file'],
            'level': 'DEBUG',
        }
    }
)

dictConfig(logging_config)


import os
from fairgraph import client, uniminds
client = client.KGClient(os.environ['HBP_token'])
name, version = 'test ksjdfhkjsdfhskjdfh yann', '37'
my_model = uniminds.ModelInstance(name=name,
                                  identifier=hashlib.md5("{} @ {}".format(name, version).encode('utf-8')).hexdigest())
my_model.save(client)

# if sys.argv[-1]=='simulation':

#     from fairgraph import KGClient, base, brainsimulation

#     # class AnalysisResult(base.KGObject):
#     #     namespace = 'modelvalidation'
#     #     type = ["prov:Entity", "nsg:Entity", "nsg:AnalysisResult"]
#     #     _path = "/simulation/analysisresult/v1.0.0" # Why is the version working "v1.0.0" ?? It doesn't seem to exist from Postman...
#     #     context =  [
#     #         "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
#     #         "{{base}}/contexts/nexus/core/resource/v0.3.0"
#     #     ]
#     #     fields = (base.Field("name", str, "name", required=True),)

#     # class SimulationResult(base.KGObject):
#     #     namespace = 'modelvalidation'
#     #     type = ["prov:Entity"]
#     #     _path = "/simulation/simulationresult/v1.0.0" # Why is the version working "v1.0.0" ?? It doesn't seem to exist from Postman...
#     #     context =  [
#     #         "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
#     #         "{{base}}/contexts/nexus/core/resource/v0.3.0"
#     #     ]
#     #     fields = (base.Field("name", str, "name", required=True),)
        
#     # class VariableReport(base.KGObject):
#     #     namespace = 'modelvalidation'
#     #     type = ["prov:Entity", "nsg:Entity", "nsg:VariableReportShape"]
#     #     _path = "/simulation/variablereport/v0.1.0" # doesn't work neither for v0.1.0
#     #     context = {"name": "schema:name",
#     #     	   "description": "schema:description",
#     #     	   "variable": "nsg:variable",
#     #     	   "target": "nsg:target",
#     #     	   "schema": "http://schema.org/",
#     #     	   "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
#     #     	   "prov": "http://www.w3.org/ns/prov#"}
#     #     fields = (base.Field("name", str, "name", required=True),
#     #               base.Field("description", str, "description", required=False),
#     #               base.Field("variable", str, "Variable shape (e.g: voltage, curent).", required=True),
#     #               base.Field("target", str, "The variable report target.", required=True))

#     client = KGClient(os.environ["HBP_token"])

    
#     # # file_location = base.Distribution()
#     model_script = brainsimulation.ModelScript(name='Script for Toy model of network dynamics',
#                                                code_format='python',
#                                                # distribution=[...], # you should add a link to an existing script with a base.Distribution object
#                                                license='CC BY-SA')
#     model_script.save(client)
#     my_model = brainsimulation.ModelInstance(name='Toy model of neural network dynamics',
#                                              main_script=model_script,
#                                              version='v0')
#     my_model.save(client)

#     # # results = AnalysisResult(name='Test by Yann') # creating AnalysisResult
#     spike_result = brainsimulation.SimulationResult(name='Test by Yann spike',
#                                                   report_file='data.npz',
#                                                   generated_by = my_model,
#                                                   variable='spike',
#                                                   target='soma',
#                                                   description='description for Test by Yann')
#     spike_result.save(client)
#     # let's try to do the same for the 
#     # Vm_result = brainsimulation.SimulationResult(name='Test by Yann Vm',
#     #                                              report_file='Vm_data.npz',
#     #                                              generated_by = my_model,
#     #                                              variable='Vm',
#     #                                              target='soma',
#     #                                              description='description for Test by Yann')

#     # Vm_result.save(client)

#     # try:
#     #     results.save(client)# this works fine !
#     #     print('[ok] --> AnalysisResults succesfully saved')
#     # except BaseException as e:
#     #     print('[!!] --> saving AnalysisResults failed')
#     #     print(e)
#     # try:
#     #     report.save(client)
#     #     print('[ok] --> VariableReport succesfully saved')
#     # except BaseException as e:
#     #     print('[!!] --> saving VariableReport failed')
#     #     print(e)

# if sys.argv[-1]=='model':
#     from fairgraph import uniminds, KGClient
#     from fairgraph.uniminds import Dataset
#     client = KGClient(os.environ["HBP_token"])
#     datas = Dataset.list(client, api='query', scope='inferred', resolved=True, size=10)
#     print(datas[0])
# if sys.argv[-1]=='filebundle':

#     from fairgraph import uniminds, KGClient
#     import hashlib
#     client = KGClient(os.environ["HBP_token"])

#     name = 'Test by Yann'

#     data = uniminds.Dataset.by_name('Morphological reconstructions of the striatal fast-spiking cells', client, scope='inferred')
#     print(data)
    
#     minst = uniminds.ModelInstance(name=name,
#                                    identifier = hashlib.sha1(name.encode('utf-8')).hexdigest(),
#                                    description='this is a test 2',
#                                    generated_by=data,
#                                    version='v2')
#     minst.save(client)


#     full_name = 'filebundle for %s' % name
#     # create a FileBundle
#     fb = uniminds.FileBundle(name=full_name,
#                              description='blabla',
#                              url='www.theurlofthemodel.eu',
#                              identifier = hashlib.sha1(full_name.encode('utf-8')).hexdigest(),
#                 model_instance = minst)
#     fb.save(client)
    

# # for cls in electrophysiology.list_kg_classes():
# #     cls.store_queries(client)
# # for cls in brainsimulation.list_kg_classes():
# #     cls.store_queries(client)
# # core.use_namespace("neuralactivity")
# # for cls in core.list_kg_classes():
# #     cls.store_queries(client)
# # core.use_namespace("modelvalidation")
# # for cls in core.list_kg_classes():
# #     cls.store_queries(client)

# # import os, hashlib
# # from logging.config import dictConfig
# # from fairgraph import KGClient, uniminds, minds

# # client = KGClient(os.environ["HBP_token"])

# # # logging.basicConfig(filename='test.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

# # logging_config = dict(
# #     version = 1,
# #     formatters = {
# #         'f': {'format':
# #               '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'}
# #     },
# #     handlers = {
# #         'file': {
# #             'level': 'DEBUG',
# #             'class': 'logging.FileHandler',
# #             'filename': 'fairgraph.log',
# #             'formatter': 'f'
# #         }
# #     },
# #     loggers = {
# #         'openid_http_client.http_client': {
# #             'handlers': ['file'],
# #             'level': 'DEBUG',
# #         },
# #         'fairgraph': {
# #             'handlers': ['file'],
# #             'level': 'DEBUG',
# #         }
# #     }
# # )

# # dictConfig(logging_config)

# # name="Test by yann"

# # for cls in minds.list_kg_classes():
# #     entry = cls(name=name,
# #                 identifier = hashlib.sha1(name.encode('utf-8')).hexdigest())
# #     try:
# #         entry.save(client)
# #         print('[ok] Entry saved for %s ' % cls)
# #     except Exception as e:
# #         print("[!!] Entry *NOT* saved for %s" % cls)

# # # entry = uniminds.AbstractionLevel(name=name,
# # #                                   identifier = hashlib.sha1(name.encode('utf-8')).hexdigest())
# # # entry.save(client)
# # # create a new ModelInstance
# # # minst = ModelInstance(name=name,
# # #                       description='this is a test 2',
# # #                       version='v2')
# # # minst.save(client)

# # # full_name = 'filebundle for %s' % name
# # # # create a FileBundle
# # # fb = FileBundle(name=full_name,
# # #                 url='www.theurlofthemodel.eu',
# # #                 identifier = hashlib.sha1(full_name.encode('utf-8')).hexdigest(),
# # #                 model_instance = minst)
# # # fb.save(client)

# # # # name = 'test by yann'
# # # # ep = FileBundleGroup(name=name,
# # # #                      identifier = hashlib.sha1(name.encode('utf-8')).hexdigest())
# # # # ep.save(client)
