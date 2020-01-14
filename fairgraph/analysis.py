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
from .core import Organization, Person, Age, Collection
from .utility import compact_uri, standard_context
import minds, uniminds # for datasets

from .model_validation import ATTACHMENT_SIZE_LIMIT, upload_attachment, HasAliasMixin

logger = logging.getLogger("fairgraph")
mimetypes.init()

DEFAULT_NAMESPACE = "modelvalidation"
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

class Analysis(KGObject):
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/analysis/v0.0.1"
    type = ["prov:Activity", "nsg:Activity", "nsg:Analysis"]
    context =  CONTEXT
    fields = (
        Field("name", basestring, "name", required=True),
        Field("description", basestring, "description"),
        Field("data_used", (uniminds.Dataset, minds.Dataset, basestring), "dataUsed", multiple=True),
        Field("configuration_used", AnalysisConfiguration, "configurationUsed", multiple=True),
        Field("started_at_time", datetime, "startedAtTime", default=datetime.now),
        Field("ended_at_time", datetime, "endedAtTime"),
    )


class AnalysisConfiguration(KGObject):
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/analysisconfiguration/v0.0.1"
    type = ["prov:Entity", "nsg:Entity", "nsg:AnalysisConfiguration"]
    context =  CONTEXT
    fields = (
        Field("name", basestring, "name", required=True),
        Field("description", basestring, "description"),
        Field("json_description", basestring, "json_description") # this should store the machine-readable parameters
    )


class AnalysisResult(KGObject):
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/analysisresult/v0.0.1"
    type = ["prov:Entity", "nsg:Entity", "nsg:AnalysisResult"]
    context =  CONTEXT
    fields = (
        Field("name", basestring, "name", required=True),
        Field("result_file", (Distribution, basestring), "distribution"),
        Field("generated_by", "Analysis", "wasGeneratedBy"),
        Field("timestamp", datetime, "generatedAtTime", default=datetime.now)
    )

    def __init__(self, name, result_file=None, timestamp=None, id=None, instance=None):
        super(AnalysisResult, self).__init__(
            name=name, result_file=result_file, timestamp=timestamp,
            id=id, instance=instance
        )
        self._file_to_upload = None
        if isinstance(result_file, basestring):
            if result_file.startswith("http"):
                self.result_file = Distribution(location=result_file)
            elif os.path.isfile(result_file):
                self._file_to_upload = result_file
                self.result_file = None
        elif result_file is not None:
            for rf in as_list(self.result_file):
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
                },
                {
                    "path": "prov:generatedAtTime",
                    "op": "eq",
                    "value": self.timestamp.isoformat()
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
        for rf in as_list(self.result_file):
            rf.download(local_directory, client)



def list_kg_classes():
    """List all KG classes defined in this module"""
    return [obj for name, obj in inspect.getmembers(sys.modules[__name__])
            if inspect.isclass(obj) and issubclass(obj, KGObject) and obj.__module__ == __name__]


def use_namespace(namespace):
    """Set the namespace for all classes in this module."""
    for cls in list_kg_classes():
        cls.namespace = namespace
