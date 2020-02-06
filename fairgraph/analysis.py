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
    """
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
            "identifier": "schema:identifier",
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
        Field("identifier", basestring, "identifier"),
        Field("input_data", KGObject, "dataUsed", multiple=True),
        Field("analysis_script", "analysis.AnalysisScript", "scriptUsed", multiple=True),
        Field("configuration_used", "analysis.AnalysisConfiguration", "configUsed", multiple=True),
        Field("timestamp", datetime,  "startedAtTime"),
        Field("end_timestamp",  datetime, "endedAtTime"),
        Field("result", "analysis.AnalysisResult", "generated", multiple=True),
        Field("started_by", Person, "wasAssociatedWith")
    )
    

class AnalysisConfiguration(KGObject):
    """
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
        Field("config_file", (Distribution, basestring), "distribution")
    )

    ## TODO : write the different cases: Distribution, dict, basestring
    
    def __init__(self,
                 name,
                 description='',
                 config_file=None,
                 id=None, instance=None):
        
        super(AnalysisConfiguration, self).__init__(
            name=name,
            description=description,
            config_file=config_file,
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

    def upload_attachment(self, file_path, client):
        upload_attachment(self, file_path, client)
        
    def save(self, client):
        super(AnalysisConfiguration, self).save(client)
        if self._file_to_upload:
            self.upload_attachment(self._file_to_upload, client)

    def download(self, local_directory, client):
        for rf in as_list(self.config_file):
            rf.download(local_directory, client)
    

class AnalysisResult(KGObject):
    """
    """
    namespace = DEFAULT_NAMESPACE
    type = ["prov:Entity", "nsg:Entity", "nsg:AnalysisResult"]
    _path = "/simulation/analysisresult/v0.1.2"
    context = {"schema": "http://schema.org/",
               "name": "schema:name",
               "description": "schema:description",
               "identifier": "schema:identifier",
               "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
               "variable": "nsg:variable",
               "dataType": "nsg:dataType",
               "distribution": "nsg:distribution",
               "prov": "http://www.w3.org/ns/prov#",
               "startedAtTime": "prov:startedAtTime",
               "wasDerivedFrom":"prov:wasDerivedFrom",
               "wasGeneratedBy": "prov:wasGeneratedBy"}
    fields = (Field("name", basestring, "name", required=True),
              Field("description", basestring, "description"),
              Field("identifier", basestring, "identifier"),
              Field("report_file", (Distribution, basestring), "distribution", multiple=True),
              Field("variable", basestring, "variable", multiple=True),
              Field("data_type", basestring, "dataType", multiple=True),
              Field("generated_by", AnalysisActivity, "wasGeneratedBy", multiple=True), # SHOULD BE SET UP  BY THE ACTIVITY
              Field("derived_from", KGObject, "wasDerivedFrom", multiple=True), # SHOULD BE SET UP BY THE ACTIVITY (NOT YET)
              Field("timestamp", datetime,  "startedAtTime"))

    def __init__(self,
                 name,
                 description='',
                 identifier='',
                 report_file=None,
                 variable='',
                 data_type = '',
                 generated_by=None,
                 derived_from=None,
                 timestamp=None,
                 id=None, instance=None):

        super(AnalysisResult, self).__init__(
            name=name,
            description=description,
            identifier=identifier,
            report_file=report_file,
            variable=variable,
            data_type=data_type,
            generated_by=generated_by,
            derived_from=derived_from,
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

    def add_provenance_from_activity(self, activity, client):
        """
        provenance setting should be called within the activity construction
        """
        self.generated_by = activity.resolve(client)
        # self.derived_from = activity.input_data #.resolve(client)
            
    def upload_attachment(self, file_path, client):
        upload_attachment(self, file_path, client)
        
    def download(self, local_directory, client):
          for rf in as_list(self.report_file):
            rf.download(local_directory, client)

            
class AnalysisScript(KGObject):
    """
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

    def upload_attachment(self, file_path, client):
        upload_attachment(self, file_path, client)
        
    def download(self, local_directory, client):
        for rf in as_list(self.script_file):
            rf.download(local_directory, client)


def list_kg_classes():
    """List all KG classes defined in this module"""
    return [obj for name, obj in inspect.getmembers(sys.modules[__name__])
            if inspect.isclass(obj) and issubclass(obj, KGObject) and obj.__module__ == __name__]


def use_namespace(namespace):
    """Set the namespace for all classes in this module."""
    for cls in list_kg_classes():
        cls.namespace = namespace
