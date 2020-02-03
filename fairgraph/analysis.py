"""
analysis
"""

try:
    basestring
except NameError:
    basestring = str
import os.path
import logging
from datetime import datetime, date
import mimetypes
from itertools import chain
import sys
import inspect
from dateutil import parser as date_parser
import requests
from .base import KGObject, cache, KGProxy, build_kg_object, Distribution, as_list, KGQuery, Field, IRI
from .commons import BrainRegion, CellType, Species, AbstractionLevel, ModelScope, OntologyTerm
from . import core ## What's the way to work with "core" classes ? 
from .utility import compact_uri, standard_context

from . import brainsimulation
from .brainsimulation import ATTACHMENT_SIZE_LIMIT, upload_attachment, HasAliasMixin

logger = logging.getLogger("fairgraph")
mimetypes.init()

DEFAULT_NAMESPACE = "modelvalidation"
## What's the way to work with "core" classes ? Temporary fix:
core.use_namespace(DEFAULT_NAMESPACE)
Person = core.Person
Collection = core.Collection
Organization = core.Organization
Age = core.Age


class AnalysisActivity(KGObject):
    """  Here this is the Analysis *Activity*
    Schema (use the environment setting in Postman to replace {{base}} with the desired nexus endpoint) :
{
    "@context": [
        "{{base}}/contexts/neurosciencegraph/core/schema/v0.1.0",
        {
            "this": "{{base}}/schemas/modelvalidation/simulation/analysisactivity/v0.1.0/shapes/"
        },
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ],
    "@id": "{{base}}/schemas/modelvalidation/simulation/analysisactivity/v0.1.0",
    "@type": "nxv:Schema",
    "imports": [
        "{{base}}/schemas/neurosciencegraph/commons/activity/v0.1.4"
    ],
    "shapes": [
        {
            "@id": "this:AnalysisActivityShape",
            "@type": "sh:NodeShape",
            "and": [
                {
                    "node": "{{base}}/schemas/neurosciencegraph/commons/activity/v0.1.1/ActivityShape"
                },
                {
                    "property": [
                        {
                            "datatype": "xsd:string",
                            "description": "name of activity analysis",
                            "minCount": 1,
                            "name": "name",
                            "path": "schema:name"
                        }
                    ]
                }
            ],
            "label": "Analysis activity shape",
            "nodekind": "sh:BlankNodeOrIRI",
            "targetClass": "nsg:AnalysisActivity"
        }
    ],
    "links": {
        "@context": "{{base}}/contexts/nexus/core/links/v0.2.0",
        "self": "{{base}}/schemas/modelvalidation/simulation/analysisactivity/v0.1.0"
    }
}
    """
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/analysisactivity/v0.1.0"
    type = ["prov:Activity", "nsg:Activity", "nsg:AnalysisActivity"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {
            "schema": "http://schema.org/",
            "name": "schema:name",
            "description": "schema:description",
            "prov": "http://www.w3.org/ns/prov#",
            "generated": "prov:generated",
            "used": "prov:used",
            "dataUsed": "prov:used",
            "scriptUsed": "prov:used",
            "configUsed": "prov:used",
            "startedAtTime": "prov:startedAtTime",
            "endedAtTime": "prov:endedAtTime",
            "wasAssociatedWith": "prov:wasAssociatedWith",
            "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
            "referenceData": "nsg:referenceData"
        }
    ]
    fields = (
        Field("name", basestring, "name", required=True),
        Field("description", basestring, "description"),
        Field("input_data", KGObject, "dataUsed", multiple=True),
        Field("analysis_script", "analysis.AnalysisScript", "scriptUsed", multiple=True),
        Field("configuration_used", "analysis.AnalysisConfiguration", "configUsed", multiple=True),
        Field("timestamp", datetime,  "startedAtTime"),
        Field("end_timestamp",  datetime, "endedAtTime"),
        Field("result", "analysis.AnalysisResult", "generated", multiple=True),
        Field("started_by", Person, "wasAssociatedWith")
    )


    def __init__(self,
                 name,
                 input_data=None,
                 analysis_script=None,
                 configuration_used=None,
                 timestamp=None,
                 result=None,
                 end_timestamp=None,
                 started_by=None,
                 id=None, instance=None):
        
        super(AnalysisActivity, self).__init__(
            name=name,
            report_file=report_file,
            variable=variable,
            data_type=data_type,
            description=description,
            timestamp=timestamp,
            started_by=started_by,
            id=id,
            instance=instance)

        # adding provenance details to results here
        if result:
            result.add_provenance_from_activity(self)
    
    

class AnalysisConfiguration(KGObject):
    """
{
    "@context": [
        "{{base}}/contexts/neurosciencegraph/core/schema/v0.1.0",
        {
            "this": "{{base}}/schemas/modelvalidation/simulation/analysisconfiguration/v0.1.0/shapes/"
        },
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ],
    "@id": "{{base}}/schemas/modelvalidation/simulation/analysisconfiguration/v0.1.0",
    "@type": "nxv:Schema",
    "imports": [
        "{{base}}/schemas/neurosciencegraph/commons/entity/v0.1.0"
    ],
    "shapes": [
        {
            "@id": "this:AnalysisConfigurationShape",
            "@type": "sh:NodeShape",
            "and": [
                {
                    "node": "{{base}}/schemas/neurosciencegraph/commons/entity/v0.1.0/shapes/EntityShape"
                },
                {
                    "property": [
                        {
                            "datatype": "xsd:string",
                            "description": "name of config",
                            "minCount": 1,
                            "name": "name",
                            "path": "schema:name"
                        }
                    ]
                }
            ],
            "label": "Analysis Configuration shape",
            "nodekind": "sh:BlankNodeOrIRI",
            "targetClass": "nsg:AnalysisConfiguration"
        }
    ],
    "links": {
        "@context": "{{base}}/contexts/nexus/core/links/v0.2.0",
        "self": "{{base}}/schemas/modelvalidation/simulation/analysisconfiguration/v0.1.0"
    }
}
    """
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/analysisconfiguration/v0.1.0"
    type = ["prov:Entity", "nsg:Entity", "nsg:AnalysisConfiguration"]
    context = {"schema": "http://schema.org/",
               "name": "schema:name",
               "description": "schema:description",
               "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
               "distribution": "nsg:distribution"}
    fields = (
        Field("name", basestring, "name", required=True),
        Field("description", basestring, "description"),
        Field("config", (Distribution, dict, basestring), "distribution")
    )

    ## TODO : write the different cases: Distribution, dict, basestring
    
    # def __init__(self,
    #              name,
    #              config_file='',
    #              description='',
    #              json_description='',
    #              id=None, instance=None):
        
    #     super(AnalysisConfiguration, self).__init__(
    #         name=name,
    #         config_file=config_file,
    #         description=description,
    #         json_description=json_description,
    #         id=id,
    #         instance=instance)
    #     self._file_to_upload = None
    #     if isinstance(config_file, basestring):
    #         if config_file.startswith("http"):
    #             self.config_file = Distribution(location=config_file)
    #         elif os.path.isfile(config_file):
    #             self._file_to_upload = config_file
    #             self.config_file = None
    #     elif config_file is not None:
    #         for rf in as_list(self.config_file):
    #             assert isinstance(rf, Distribution)

    # def save(self, client):
    #     super(AnalysisConfiguration, self).save(client)
    #     if self._file_to_upload:
    #         self.upload_attachment(self._file_to_upload, client)

    # def upload_attachment(self, file_path, client):
    #     upload_attachment(self, file_path, client)
        
    # def download(self, local_directory, client):
    #     for rf in as_list(self.config_file):
    #         rf.download(local_directory, client)
    

class AnalysisResult(KGObject):
    """
    Schema (use the environment setting in Postman to replace {{base}} with the desired nexus endpoint) :
{
    "@context": [
        "{{base}}/contexts/neurosciencegraph/core/schema/v0.1.0",
        {
            "this": "{{base}}/schemas/modelvalidation/simulation/analysisresult/v0.1.2/shapes/"
        },
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ],
    "@id": "{{base}}/schemas/modelvalidation/simulation/analysisresult/v0.1.2",
    "@type": "nxv:Schema",
    "imports": [
        "{{base}}/schemas/neurosciencegraph/commons/entity/v0.1.0"
    ],
    "shapes": [
        {
            "@id": "this:AnalysisResultShape",
            "@type": "sh:NodeShape",
            "and": [
                {
                    "node": "{{base}}/schemas/neurosciencegraph/commons/entity/v0.1.0/shapes/EntityShape"
                },
                {
                    "property": [
                        {
                            "datatype": "xsd:string",
                            "description": "name of the analysis result",
                            "minCount": 1,
                            "name": "name",
                            "path": "schema:name"
                        }
                    ]
                }
            ],
            "label": "Analysis Result shape",
            "nodekind": "sh:BlankNodeOrIRI",
            "targetClass": "nsg:AnalysisResult"
        }
    ],
    "links": {
        "@context": "{{base}}/contexts/nexus/core/links/v0.2.0",
        "self": "{{base}}/schemas/modelvalidation/simulation/analysisresult/v0.1.2"
    }
}
    """
    namespace = DEFAULT_NAMESPACE
    type = ["prov:Entity", "nsg:Entity", "nsg:AnalysisResult"]
    _path = "/simulation/analysisresult/v0.1.2"
    context = {"schema": "http://schema.org/",
               "name": "schema:name",
               "description": "schema:description",
               "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
               "variable": "nsg:variable",
               "dataType": "nsg:dataType",
               "distribution": "nsg:distribution",
               "prov": "http://www.w3.org/ns/prov#",
               "startedAtTime": "prov:startedAtTime",
               "wasDerivedFrom":"prov:wasDerivedFrom",
               "wasGeneratedBy": "prov:wasGeneratedBy"}
    fields = (Field("name", basestring, "name", required=True),
              Field("report_file", (Distribution, basestring), "distribution", multiple=True),
              Field("variable", basestring, "variable", multiple=True),
              Field("data_type", basestring, "dataType", multiple=True),
              Field("generated_by", AnalysisActivity, "wasGeneratedBy"), # SHOULD BE SET UP  BY THE ACTIVITY
              Field("derived_from", KGObject, "wasDerivedFrom"), # SHOULD BE SET UP BY THE ACTIVITY
              Field("description", basestring, "description"),
              Field("timestamp", datetime,  "startedAtTime"))

    def __init__(self,
                 name,
                 report_file=None,
                 data_type = '',
                 variable='',
                 description='',
                 timestamp=None,
                 id=None, instance=None):
        
        super(AnalysisResult, self).__init__(
            name=name,
            report_file=report_file,
            variable=variable,
            data_type=data_type,
            description=description,
            timestamp=timestamp,
            id=id,
            instance=instance)
        self._file_to_upload = None
        if isinstance(report_file, basestring):
            if report_file.startswith("http"):
                self.report_file = Distribution(location=report_file)
            elif os.path.isfile(report_file):
                self._file_to_upload = report_file
                self.report_file = None
        elif report_file is not None:
            for rf in as_list(self.report_file):
                assert isinstance(rf, Distribution)
        else:
            print('/!\ Need to provide a "report_file" argument, either a string path to a file (local or public on the web) or a Distribution object')

    @property
    def _existence_query(self):
        return {
            "op": "and",
            "value": [
                {
                    "path": "schema:name",
                    "op": "eq",
                    "value": self.name
                }
            ]
        }

    def save(self, client):
        super(AnalysisResult, self).save(client)
        if self._file_to_upload:
            self.upload_attachment(self._file_to_upload, client)

    def add_provenance_from_activity(self, activity):
        """
        provenance setting should be called within the activity construction
        """
        self.generated_by = activity
        self.derived_from = activity.input_data
            
    def upload_attachment(self, file_path, client):
        upload_attachment(self, file_path, client)
        
    def download(self, local_directory, client):
          for rf in as_list(self.report_file):
            rf.download(local_directory, client)

            
class AnalysisScript(KGObject):
    """
    Schema (use the environment setting in Postman to replace {{base}} with the desired nexus endpoint) :
{
    "@context": [
        "{{base}}/contexts/neurosciencegraph/core/schema/v0.1.0",
        {
            "this": "{{base}}/schemas/modelvalidation/simulation/analysisscript/v0.1.0/shapes/"
        },
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ],
    "@id": "{{base}}/schemas/modelvalidation/simulation/analysisscript/v0.1.0",
    "@type": "nxv:Schema",
    "imports": [
        "{{base}}/schemas/neurosciencegraph/commons/entity/v0.1.0"
    ],
    "shapes": [
        {
            "@id": "this:AnalysisScriptShape",
            "@type": "sh:NodeShape",
            "and": [
                {
                    "node": "{{base}}/schemas/neurosciencegraph/commons/entity/v0.1.0/shapes/EntityShape"
                },
                {
                    "property": [
                        {
                            "datatype": "xsd:string",
                            "description": "name of the analysis script",
                            "minCount": 1,
                            "name": "name",
                            "path": "schema:name"
                        }
                    ]
                }
            ],
            "label": "Analysis Script shape",
            "nodekind": "sh:BlankNodeOrIRI",
            "targetClass": "nsg:AnalysisScript"
        }
    ],
    "links": {
        "@context": "{{base}}/contexts/nexus/core/links/v0.2.0",
        "self": "{{base}}/schemas/modelvalidation/simulation/analysisscript/v0.1.0"
    }
}
    """
    namespace = DEFAULT_NAMESPACE
    type = ["prov:Entity", "nsg:Entity", "nsg:AnalysisScript"]
    _path = "/simulation/analysisscript/v0.1.0"
    context = {"schema": "http://schema.org/",
               "name": "schema:name",
               "description": "schema:description",
               "license": "schema:license",
               "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
               "distribution": "nsg:distribution",
               "code_format": "nsg:code_format"}
    fields = (
        Field("name", basestring, "name", required=True),
        Field("script_file", (Distribution, basestring), "distribution"),
        Field("code_format", basestring, "code_format", multiple=True),
        Field("license", basestring, "license"),
        Field("distribution", Distribution,  "distribution")
    )

    def __init__(self, name,
                 script_file=None,
                 code_format=None,
                 license=None,
                 id=None,
                 instance=None):
        super(AnalysisScript, self).__init__(name=name,
                                             script_file=script_file,
                                             code_format=code_format,
                                             license=license,
                                             id=id,
                                             instance=instance)
        self._file_to_upload = None
        if isinstance(script_file, basestring):
            if script_file.startswith("http"):
                self.script_file = Distribution(location=script_file)
            elif os.path.isfile(script_file):
                self._file_to_upload = script_file
                self.script_file = None
        elif script_file is not None:
            for rf in as_list(self.script_file):
                assert isinstance(rf, Distribution)
        else:
            print('/!\ Need to provide a "script_file" argument, either a string path to a file (local or public on the web) or a Distribution object')

    def save(self, client):
        super(AnalysisScript, self).save(client)
        if self._file_to_upload:
            self.upload_attachment(self._file_to_upload, client)
            
    @property
    def script_location(self):
        if self.distribution:
            return self.distribution.location
        else:
            print('script attached to the KG entry, use the "download" method to fetch it')
            return None

    def download(self, local_directory, client):
        for rf in as_list(self.script_file):
            rf.download(local_directory, client)


########################################################################
### ------ end of class definitions -------------------------------- ###
########################################################################


def provenance_tracking_of_result(analysis_result,
                                  with_activities=True):

    Provenance_loop_continues = True
    GENERATING_ENTITIES_BY_LAYER = [analysis_result]
    while Provenance_loop_continues:

        if with_activities:

        else:
            GENERATING_ENTITIES_BY_LAYER.append([])
            for quant in GENERATING_ENTITIES_BY_LAYER[-1]:
                GENERATING_ENTITIES_BY_LAYER += as_list(quant.derived_from)
            
        
def list_kg_classes():
    """List all KG classes defined in this module"""
    return [obj for name, obj in inspect.getmembers(sys.modules[__name__])
            if inspect.isclass(obj) and issubclass(obj, KGObject) and obj.__module__ == __name__]


def use_namespace(namespace):
    """Set the namespace for all classes in this module."""
    for cls in list_kg_classes():
        cls.namespace = namespace
