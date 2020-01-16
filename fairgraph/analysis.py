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


CONTEXT = [
    "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
    "{{base}}/contexts/nexus/core/resource/v0.3.0",
    {
        "wasGeneratedBy": "prov:wasGeneratedBy",
        "name": "schema:name",
        "label": "rdfs:label",
        "alias": "nsg:alias",
        "author": "schema:author",
        "owner": "nsg:owner",
        "description": "schema:description",
        "json_description": "schema:description", # for machine-readable description
        "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
        "prov": "http://www.w3.org/ns/prov#",
        "schema": "http://schema.org/",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "dateCreated": "schema:dateCreated",
        "dataType": "nsg:dataType",
        "version": "schema:version",
        "parameters": "nsg:parameters",
        "used": "prov:used",
        "testUsed": "prov:used",
        "configurationUsed": "prov:used",
        "dataUsed": "prov:used",
        "startedAtTime": "prov:startedAtTime",
        "endedAtTime": "prov:endedAtTime",
        "wasAssociatedWith": "prov:wasAssociatedWith",
    }
]

class AnalysisActivity(KGObject):
    """  Here this is the Simulation *Activity*
    Schema (use the environment setting in Postman to replace {{base}} with the desired nexus endpoint) :
{
    "@context": [
        "{{base}}/contexts/neurosciencegraph/core/schema/v0.1.0",
        {
            "this": "{{base}}/schemas/modelvalidation/simulation/analysisactivity/v0.0.1/shapes/"
        },
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ],
    "@id": "{{base}}/schemas/modelvalidation/simulation/analysisactivity/v0.0.1",
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
                            "minCount": 2,
                            "path": "prov:used"
                        },
                        {
                            "class": "nsg:AnalysisResult",
                            "description": "Generated simulation result.",
                            "minCount": 1,
                            "name": "Result",
                            "path": "prov:generated",
                            "seeAlso": "{{base}}/schemas/modelvalidation/simulation/analysisresult/v0.0.1/shapes/AnalysisResultShape"
                        }
                    ]
                }
            ],
            "label": "Simulation report analysis shape",
            "nodekind": "sh:BlankNodeOrIRI",
            "targetClass": "nsg:AnalysisActivity"
        }
    ],
    "links": {
        "@context": "{{base}}/contexts/nexus/core/links/v0.2.0",
        "self": "{{base}}/schemas/modelvalidation/simulation/analysisactivity/v0.0.1"
    }
}
    """
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/analysisactivity/v0.0.1"
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
        Field("name", basestring, "name"),
        Field("description", basestring, "description"),
        Field("analysis_script", "AnalysisScript", "scriptUsed", required=True),
        Field("configuration_used", "AnalysisConfiguration", "configUsed", required=True),
        Field("timestamp", datetime,  "startedAtTime", required=True),
        Field("end_timestamp",  datetime, "endedAtTime"),
        Field("result", "AnalysisResult", "generated", required=True),
        Field("started_by", Person, "wasAssociatedWith")
    )


class AnalysisConfiguration(KGObject):
    """
{
    "@context": [
        "{{base}}/contexts/neurosciencegraph/core/schema/v0.1.0",
        {
            "this": "{{base}}/schemas/modelvalidation/simulation/analysisconfiguration/v0.0.1/shapes/"
        },
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ],
    "@id": "{{base}}/schemas/modelvalidation/simulation/analysisconfiguration/v0.0.1",
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
        "self": "{{base}}/schemas/modelvalidation/simulation/analysisconfiguration/v0.0.1"
    }
}
    """
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/analysisconfiguration/v0.0.1"
    type = ["prov:Entity", "nsg:Entity", "nsg:AnalysisConfiguration"]
    context = {"schema": "http://schema.org/",
               "name": "schema:name",
               "description": "schema:description",
               "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/"}
    fields = (
        Field("name", basestring, "name", required=True),
        Field("description", basestring, "description"),
        Field("config_file", (Distribution, basestring), "distribution"),
        Field("json_description", basestring, "json_description") 
    )

    def __init__(self,
                 name,
                 config_file='',
                 description='',
                 json_description='',
                 id=None, instance=None):
        
        super(AnalysisConfiguration, self).__init__(
            name=name,
            config_file=config_file,
            description=description,
            json_description=json_description,
            id=id,
            instance=instance)
        self._file_to_upload = None
        if isinstance(config_file, basestring):
            if config_file.startswith("http"):
                self.config_file = Distribution(location=config_file)
            elif os.path.isfile(config_file):
                self._file_to_upload = config_file
                self.config_file = None
        elif config_file is not None:
            for rf in as_list(self.config_file):
                assert isinstance(rf, Distribution)

    def save(self, client):
        super(AnalysisConfiguration, self).save(client)
        if self._file_to_upload:
            self.upload_attachment(self._file_to_upload, client)

    def upload_attachment(self, file_path, client):
        upload_attachment(self, file_path, client)
        
    def download(self, local_directory, client):
        for rf in as_list(self.config_file):
            rf.download(local_directory, client)
    

class AnalysisResult(KGObject):
    """
    Schema (use the environment setting in Postman to replace {{base}} with the desired nexus endpoint) :
{
    "@context": [
        "{{base}}/contexts/neurosciencegraph/core/schema/v0.1.0",
        {
            "this": "{{base}}/schemas/modelvalidation/simulation/analysisresult/v0.0.1/shapes/"
        },
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ],
    "@id": "{{base}}/schemas/modelvalidation/simulation/analysisresult/v0.0.1",
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
        "self": "{{base}}/schemas/modelvalidation/simulation/analysisresult/v0.0.1"
    }
}
    """
    namespace = DEFAULT_NAMESPACE
    type = ["prov:Entity", "nsg:Entity", "nsg:AnalysisResult"]
    _path = "/simulation/analysisresult/v0.0.1"
    context = {"schema": "http://schema.org/",
               "name": "schema:name",
               "description": "schema:description",
               "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
               "variable": "nsg:variable",
               "dataType": "nsg:dataType",
               "prov": "http://www.w3.org/ns/prov#",
               "startedAtTime": "prov:startedAtTime",
               "wasGeneratedBy": "prov:wasGeneratedBy"}
    fields = (Field("name", basestring, "name", required=True),
              Field("variable", basestring, "variable"),
              Field("report_file", (Distribution, basestring), "distribution"),
              Field("generated_by", (AnalysisActivity, basestring), "wasGeneratedBy"),
              Field("data_type", basestring, "dataType"),
              Field("description", basestring, "description"),
              Field("timestamp", datetime,  "startedAtTime"))

    def __init__(self,
                 name,
                 generated_by='',
                 report_file=None,
                 data_type = '',
                 variable='',
                 description='',
                 timestamp=None,
                 id=None, instance=None):
        
        super(AnalysisResult, self).__init__(
            name=name,
            generated_by=generated_by,
            report_file=report_file,
            data_type=data_type,
            variable=variable,
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

    def upload_attachment(self, file_path, client):
        upload_attachment(self, file_path, client)
        
    def download(self, local_directory, client):
        for rf in as_list(self.report_file):
            rf.download(local_directory, client)

            
AnalysisScript = brainsimulation.SimulationScript
    

def list_kg_classes():
    """List all KG classes defined in this module"""
    return [obj for name, obj in inspect.getmembers(sys.modules[__name__])
            if inspect.isclass(obj) and issubclass(obj, KGObject) and obj.__module__ == __name__]


def use_namespace(namespace):
    """Set the namespace for all classes in this module."""
    for cls in list_kg_classes():
        cls.namespace = namespace
