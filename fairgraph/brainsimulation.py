"""
brain simulation
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
# from .core import Organization, Person, Age, Collection
from .utility import compact_uri, standard_context


logger = logging.getLogger("fairgraph")
mimetypes.init()

DEFAULT_NAMESPACE = "modelvalidation"

## What's the way to work with "core" classes ? Temporary fix:
core.use_namespace(DEFAULT_NAMESPACE)
Person = core.Person
Collection = core.Collection
Organization = core.Organization
Age = core.Age

ATTACHMENT_SIZE_LIMIT = 1024 * 1024  # 1 MB

# An upload function used by all Results entity classes
def upload_attachment(cls, file_path, client):
    assert os.path.isfile(file_path)
    statinfo = os.stat(file_path)
    if statinfo.st_size > ATTACHMENT_SIZE_LIMIT:
        raise Exception("File is too large to store directly in the KnowledgeGraph, please upload it to a Swift container")
    # todo, use the Nexus HTTP client directly for the following
    headers = client._nexus_client._http_client.auth_client.get_headers()
    content_type, encoding = mimetypes.guess_type(file_path, strict=False)
    response = requests.put("{}/attachment?rev={}".format(cls.id, cls.rev or 1),
                            headers=headers,
                            files={
                                "file": (os.path.basename(file_path),
                                         open(file_path, "rb"),
                                         content_type)
                            })
    if response.status_code < 300:
        logger.info("Added attachment {} to {}".format(file_path, cls.id))
        cls._file_to_upload = None
        cls.report_file = Distribution.from_jsonld(response.json()["distribution"][0])
    else:
        raise Exception(str(response.content))

class HasAliasMixin(object):

    @classmethod
    def from_alias(cls, alias, client):
        context = {
            "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/"
        }
        query = {
            "path": "nsg:alias",
            "op": "eq",
            "value": alias
        }
        return KGQuery(cls, query, context).resolve(client)


# class Collection(core.Collection):
#     """docstring"""
#     namespace = DEFAULT_NAMESPACE
#     def __init__(self, name, members, id=None, instance=None):
#         args = locals()
#         args.pop("self")
#         core.Collection.__init__(self, **args)


# class Person(core.Person):
#     """docstring"""
#     namespace = DEFAULT_NAMESPACE
#     def __init__(self, family_name, given_name, email=None, affiliation=None, id=None, instance=None):
#         args = locals()
#         args.pop("self")
#         core.Collection.__init__(self, **args)
        
    
class ModelProject(KGObject, HasAliasMixin):
    """docstring"""
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/modelproject/v0.1.0"
    #path = DEFAULT_NAMESPACE + "/simulation/modelproject/v0.1.1"
    type = ["prov:Entity", "nsg:ModelProject"]
    context = {
        "name": "schema:name",
        "label": "rdfs:label",
        "alias": "nsg:alias",
        "author": "schema:author",
        "owner": "nsg:owner",
        "organization": "nsg:organization",
        "PLAComponents": "nsg:PLAComponents",
        "private": "nsg:private",
        "collabID": "nsg:collabID",
        "brainRegion": "nsg:brainRegion",
        "species": "nsg:species",
        "celltype": "nsg:celltype",
        "abstractionLevel": "nsg:abstractionLevel",
        "modelOf": "nsg:modelOf",
        "description": "schema:description",
        "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
        "prov": "http://www.w3.org/ns/prov#",
        "schema": "http://schema.org/",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "dateCreated": "schema:dateCreated",
        "dcterms": "http://purl.org/dc/terms/",
        "instances": "dcterms:hasPart",
        "oldUUID": "nsg:providerId",
        "partOf": "nsg:partOf",
        "hasPart": "dcterms:hasPart"
    }
    attribute_map = {
        "model_of": (ModelScope, context["modelOf"]),
        "brain_region": (BrainRegion, context["brainRegion"]),
        "species": (Species, context["species"]),
        "celltype": (CellType, context["celltype"]),
        "abstraction_level": (AbstractionLevel, context["abstractionLevel"]),
    }
    # should be able to replace `attribute_map` by extending `fields`
    fields = (
        Field("name", basestring, "name", required=True),
        Field("owners", Person, "owner", required=True, multiple=True),
        Field("authors", Person, "author", required=True, multiple=True),
        Field("description", basestring, "description", required=True),
        Field("date_created", datetime, "dateCreated", required=True),
        Field("private", bool, "private", required=True),
        Field("collab_id", int, "collabID"),
        Field("alias", basestring, "alias"),
        Field("organization", Organization, "organization", multiple=True),
        Field("pla_components", basestring, "PLAComponents", multiple=True),
        Field("brain_region", BrainRegion, "brainRegion", multiple=True),
        Field("species", Species, "species"),
        Field("celltype", CellType, "celltype"),
        Field("abstraction_level", AbstractionLevel, "abstractionLevel"),
        Field("model_of", ModelScope, "modelOf"),
        Field("old_uuid", basestring, "oldUUID"),
        Field("parents", "brainsimulation.ModelProject", "partOf", multiple=True),
        #Field("instances", ("brainsimulation.ModelInstance", "brainsimulation.MEModel"),
        #      "dcterms:hasPart", multiple=True),
        # todo: kg query returns "hasPart", while nexus instances mostly use "dcterms:hasPart"
        #       suggest changing all instances to store "hasPart", with corrected context if needed
        Field("instances", ("brainsimulation.ModelInstance", "brainsimulation.MEModel"),
              "hasPart", multiple=True),
        Field("images", dict, "images", multiple=True)  # type should be Distribution?
    )

    def __init__(self, name, owners, authors, description, date_created, private, collab_id=None,
                 alias=None, organization=None, pla_components=None, brain_region=None,
                 species=None, celltype=None, abstraction_level=None, model_of=None,
                 old_uuid=None, parents=None, instances=None, images=None,
                 id=None, instance=None):
        args = locals()
        args.pop("self")
        KGObject.__init__(self, **args)

    @property
    def _existence_query(self):
        # allow multiple projects with the same name
        return {
            "op": "and",
            "value": [
                {
                    "path": "schema:name",
                    "op": "eq",
                    "value": self.name
                },
                {
                    "path": "schema:dateCreated",
                    "op": "eq",
                    "value": self.date_created.isoformat()
                }
            ]
        }

    @classmethod
    def list(cls, client, size=100, api='nexus', scope="released", resolved=False, **filters):
        """List all objects of this type in the Knowledge Graph"""
        if api == 'nexus':
            context = {
            'nsg': 'https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/'
            }
            filter_queries = []
            for name, value in filters.items():
                if name in cls.attribute_map:
                    concept_class, concept_uri = cls.attribute_map[name]
                    filter_queries.append({
                        'path': concept_uri,
                        'op': 'eq',
                        'value': concept_class(value).iri
                    })
                elif name in ("author", "owner"):
                    if not isinstance(value, Person):
                        raise TypeError("{} must be a Person object".format(name))
                    filter_queries.append({
                        "path": cls.context[name],
                        "op": "eq",
                        "value": value.id
                    })
                else:
                    raise Exception("The only supported filters are by '{supported_filters}'. "
                                    "You specified '{name}'".format(
                                        supported_filters="', '".join(chain(cls.attribute_map, ["author", "owner"])),
                                        name=name))
            if len(filter_queries) == 0:
                return client.list(cls, size=size)
            elif len(filter_queries) == 1:
                filter_query = filter_queries[0]
            else:
                filter_query = {
                    "op": "and",
                    "value": filter_queries
                }
            return KGQuery(cls, filter_query, context).resolve(client, size=size)
            # todo: handle resolved=True for nexus queries (i.e. do all the downstream resolutions  )
        else:
            # todo: handle author, owner
            filter_queries = {}
            for name, value in filters.items():
                if name in cls.attribute_map:
                    concept_class, concept_uri = cls.attribute_map[name]
                    filter_queries[name] = concept_class.iri_map[value]
                else:
                    filter_queries[name] = value
            return client.list(cls, size=size, api=api, scope=scope, filter=filter_queries, resolved=resolved)


    def authors_str(self, client):
        return ", ".join("{obj.given_name} {obj.family_name}".format(obj=obj.resolve(client))
                         for obj in self.authors)

    #def sub_projects(self):


class ModelInstance(KGObject):
    """docstring"""
    #path = DEFAULT_NAMESPACE + "/simulation/modelinstance/v0.1.2"
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/modelinstance/v0.1.1"
    type = ["prov:Entity", "nsg:ModelInstance"]
    # ScientificModelInstance
    #   - model -> linked ModelProject using partOf
    #   - version -> add field to ModelInstance.
    #   - description -> part of Entity
    #   - parameters -> linked ModelParameters
    #   - source -> (e.g. git repository) -> linked ModelScript
    #   - timestamp -> prov:generatedAtTime
    #   - code_format -> linked ModelScript
    #   - hash - general feature, don't put in schema
    #   - morphology - not needed for all models, use MEModel where we have a morphology
    # modelinstance/v0.1.2
    #   - fields of Entity + modelOf, brainRegion, species
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {"oldUUID": "nsg:providerId"}
    ]
    # fields:
    #  - fields of ModelInstance + eModel, morphology, mainModelScript, isPartOf (an MEModelRelease)
    fields = (
        Field("name", basestring, "name", required=True),
        # Field("author", Person, "person", required=False),
        Field("brain_region", BrainRegion, "brainRegion", required=False),
        Field("species", Species, "species", required=False),
        Field("model_of", (CellType, BrainRegion), "modelOf", required=False),  # should be True, but causes problems for a couple of cases at the moment
        Field("main_script", "brainsimulation.ModelScript", "mainModelScript", required=True),
        Field("release", basestring, "release", required=False),
        Field("version",  basestring, "version", required=True),
        Field("timestamp", datetime, "generatedAtTime", required=False),
        Field("part_of", KGObject, "isPartOf"),
        Field("description", basestring, "description"),
        Field("parameters", basestring, "parameters"),
        Field("old_uuid", basestring, "oldUUID")
    )

    def __init__(self, name, main_script, version, timestamp=None,
                 brain_region=None, species=None, model_of=None, release=None,
                 part_of=None, description=None, parameters=None,
                 old_uuid=None, id=None, instance=None):
        args = locals()
        args.pop("self")
        KGObject.__init__(self, **args)

    @property
    def project(self):
        query = {
            "path": "dcterms:hasPart",
            "op": "eq",
            "value": self.id
        }
        context = {
            "dcterms": "http://purl.org/dc/terms/"
        }
        return KGQuery(ModelProject, query, context)


class MEModel(ModelInstance):
    """docstring"""
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/memodel/v0.1.2"  # latest is 0.1.4, but all the data is currently under 0.1.2
    type = ["prov:Entity", "nsg:MEModel", "nsg:ModelInstance"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {"oldUUID": "nsg:providerId"}
    ]
    # fields:
    #  - fields of ModelInstance + eModel, morphology, mainModelScript, isPartOf (an MEModelRelease)
    fields = list(ModelInstance.fields) + [
        Field("morphology", "brainsimulation.Morphology", "morphology", required=True),
        Field("e_model",  "brainsimulation.EModel", "eModel", required=True),
        #Field("project", ModelProject, "isPartOf", required=True)  # conflicts with project property in parent class. To fix.
    ]

    def __init__(self, name, e_model, morphology, main_script, version, timestamp=None, #project,
                 brain_region=None, species=None, model_of=None,
                 release=None, part_of=None, description=None, parameters=None,
                 old_uuid=None, id=None, instance=None):
        args = locals()
        args.pop("self")
        KGObject.__init__(self, **args)


class Morphology(KGObject):
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/morphology/v0.1.1"
    type = ["prov:Entity", "nsg:Morphology"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ]
    fields = (
        Field("name", basestring, "name", required=True),
        Field("cell_type", CellType, "modelOf"),
        Field("distribution", Distribution, "distribution")
    )

    def __init__(self, name, cell_type=None, morphology_file=None, distribution=None,
                 id=None, instance=None):
        super(Morphology, self).__init__(name=name, cell_type=cell_type,
                                         distribution=distribution, id=id, instance=instance)
        if morphology_file:
            if distribution:
                raise ValueError("Cannot provide both morphology_file and distribution")
            self.morphology_file = morphology_file

    @property
    def morphology_file(self):
        if isinstance(self.distribution, list):
            return [d.location for d in self.distribution]
        elif self.distribution is None:
            return None
        else:
            return self.distribution.location

    @morphology_file.setter
    def morphology_file(self, value):
        if isinstance(value, list):
            self.distribution = [Distribution(location=mf) for mf in value]
        else:
            self.distribution = Distribution(location=value)


class ModelScript(KGObject):
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/emodelscript/v0.1.0"
    type = ["prov:Entity", "nsg:EModelScript"]  # generalize to other sub-types of script
    context =  [  # todo: root should be set by client to nexus or nexus-int or whatever as required
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {
            "license": "schema:license"
        }
    ]
    fields = (
        Field("name", basestring, "name", required=True),
        Field("code_format", basestring, "code_format"),
        Field("license", basestring, "license"),
        Field("distribution", Distribution,  "distribution")
    )

    def __init__(self, name, code_location=None, code_format=None, license=None,
                 distribution=None, id=None, instance=None):
        super(ModelScript, self).__init__(name=name, code_format=code_format, license=license,
                                          distribution=distribution, id=id, instance=instance)
        if code_location and distribution:
            raise ValueError("Cannot provide both code_location and distribution")
        if code_location:
            self.distribution = Distribution(location=code_location)

    @property
    def code_location(self):
        if self.distribution:
            return self.distribution.location
        else:
            return None


class EModel(ModelInstance):
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/emodel/v0.1.1"
    type = ["prov:Entity", "nsg:EModel"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ]
    fields = (
        Field("name", basestring, "name", required=True),
        Field("brain_region", BrainRegion, "brainRegion", required=False),
        Field("species", Species, "species", required=False),
        Field("model_of", (CellType, BrainRegion), "modelOf", required=False),
        Field("main_script", "brainsimulation.ModelScript", "mainModelScript", required=False),
        Field("release", basestring, "release", required=False),
        Field("version",  basestring, "version", required=False),
        Field("timestamp", datetime, "generatedAtTime", required=False),
        Field("part_of", KGObject, "isPartOf"),
        Field("description", basestring, "description"),
        Field("parameters", basestring, "parameters"),
        Field("old_uuid", basestring, "oldUUID")
    )

    def __init__(self, name, main_script=None, version=None, timestamp=None, #project,
                 brain_region=None, species=None, model_of=None,
                 release=None, part_of=None, description=None, parameters=None,
                 old_uuid=None, id=None, instance=None):
        args = locals()
        args.pop("self")
        KGObject.__init__(self, **args)

        
class ValidationTestDefinition(KGObject, HasAliasMixin):
    """docstring"""
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/validationtestdefinition/v0.1.0"
    #path = DEFAULT_NAMESPACE + "/simulation/validationtestdefinition/v0.1.2"
    type = ["prov:Entity", "nsg:ValidationTestDefinition"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {
            "name": "schema:name",
            "alias": "nsg:alias",
            "author": "schema:author",
            "brainRegion": "nsg:brainRegion",
            "species": "nsg:species",
            "celltype": "nsg:celltype",
            "abstractionLevel": "nsg:abstractionLevel",
            "description": "schema:description",
            "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
            "prov": "http://www.w3.org/ns/prov#",
            "schema": "http://schema.org/",
            "dateCreated": "schema:dateCreated",
            "testType": "nsg:testType",
            "referenceData": "nsg:referenceData",
            "dataType": "nsg:dataType",
            "recordingModality": "nsg:recordingModality",
            "status": "nsg:status",
            "scoreType": "nsg:scoreType",
            "oldUUID": "nsg:providerId"
        }
    ]
    fields = (
        Field("name", basestring, "name", required=True),
        Field("authors", Person, "author", multiple=True, required=True),
        Field("description", basestring, "description", required=False),
        Field("date_created", (date, datetime), "dateCreated", required=True),
        Field("alias", basestring, "alias"),
        Field("brain_region", BrainRegion, "brainRegion", multiple=True),
        Field("species", Species, "species"),
        Field("celltype", CellType, "celltype", multiple=True),
        Field("test_type", basestring, "testType"),
        Field("age", Age, "age"),
        Field("reference_data", KGObject, "referenceData"),
        Field("data_type", basestring, "dataType"),
        Field("recording_modality", basestring, "recordingModality"),
        Field("score_type", basestring, "scoreType"),
        Field("status", basestring, "status"),
        Field("old_uuid", basestring, "oldUUID")
    )

    @property
    def scripts(self):
        query = {
            "path": "nsg:implements",
            "op": "eq",
            "value": self.id
        }
        context = {
            "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/"
        }
        return KGQuery(ValidationScript, query, context)


class ValidationScript(KGObject):  # or ValidationImplementation
    """docstring"""
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/validationscript/v0.1.0"
    type = ["prov:Entity", "nsg:ModelValidationScript"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {
            "name": "schema:name",
            "description": "schema:description",
            "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
            "prov": "http://www.w3.org/ns/prov#",
            "schema": "http://schema.org/",
            "dateCreated": "schema:dateCreated",
            "repository": "schema:codeRepository",
            "version": "schema:version",
            "parameters": "nsg:parameters",
            "path": "nsg:path",
            "implements": "nsg:implements",
            "oldUUID": "nsg:providerId"
        }
    ]
    fields = (
        Field("name", basestring, "name", required=True),
        Field("date_created", (date, datetime), "dateCreated", required=True),
        Field("repository", IRI, "repository"),
        Field("version", basestring, "version"),
        Field("description", basestring, "description"),
        Field("parameters", basestring, "parameters"),
        Field("test_definition", ValidationTestDefinition, "implements"),
        Field("old_uuid", basestring, "oldUUID")
    )


class ValidationResult(KGObject):
    """docstring"""
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/validationresult/v0.1.0"
    #path = DEFAULT_NAMESPACE + "/simulation/validationresult/v0.1.1"
    type = ["prov:Entity", "nsg:ValidationResult"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {
            "name": "schema:name",
            "description": "schema:description",
            "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
            "prov": "http://www.w3.org/ns/prov#",
            "schema": "http://schema.org/",
            "dateCreated": "schema:dateCreated",
            "score": "nsg:score",
            "normalizedScore": "nsg:normalizedScore",
            "passed": "nsg:passedValidation",
            "wasGeneratedBy": "prov:wasGeneratedBy",
            "hadMember": "prov:hadMember",
            "collabID": "nsg:collabID",
            "oldUUID": "nsg:providerId",
            "hash": "nsg:digest"
        }
    ]
    fields = (
        Field("name", basestring, "name", required=True),
        Field("generated_by", "brainsimulation.ValidationActivity", "wasGeneratedBy"),
        Field("description", basestring, "description"),
        Field("score", (float, int), "score"),
        Field("normalized_score", (float, int), "normalizedScore"),
        Field("passed", bool, "passedValidation"),
        Field("timestamp", (date, datetime), "dateCreated"),
        Field("additional_data", KGObject, "hadMember", multiple=True),
        Field("old_uuid", basestring, "oldUUID"),
        Field("collab_id", (int, basestring), "collabID"),
        Field("hash", basestring, "hash")
    )


class ValidationActivity(KGObject):
    """
{
    "@context": [
        "{{base}}/contexts/neurosciencegraph/core/schema/v0.1.0",
        {
            "this": "{{base}}/schemas/modelvalidation/simulation/modelvalidation/v0.2.0/shapes/"
        },
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ],
    "@id": "{{base}}/schemas/modelvalidation/simulation/modelvalidation/v0.2.0",
    "@type": "nxv:Schema",
    "imports": [
        "{{base}}/schemas/neurosciencegraph/commons/activity/v0.1.1"
    ],
    "shapes": [
        {
            "@id": "this:ModelValidationShape",
            "@type": "sh:NodeShape",
            "and": [
                {
                    "node": "{{base}}/schemas/neurosciencegraph/commons/activity/v0.1.1/ActivityShape"
                },
                {
                    "property": [
                        {
                            "minCount": 3,
                            "path": "prov:used"
                        },
                        {
                            "class": "nsg:ValidationResult",
                            "description": "Generated validation result.",
                            "minCount": 1,
                            "name": "Result",
                            "path": "prov:generated",
                            "seeAlso": "{{base}}/schemas/neurosciencegraph/simulation/validationresult/v0.1.0/shapes/ValidationResultShape"
                        }
                    ]
                }
            ],
            "comment": "The analysis strategy/protocol is defined in a protocol.",
            "label": "Model or simulation report analysis shape",
            "nodekind": "sh:BlankNodeOrIRI",
            "targetClass": "nsg:ModelValidation"
        }
    ],
    "nxv:rev": 2,
    "nxv:published": true,
    "nxv:deprecated": false,
    "links": {
        "@context": "{{base}}/contexts/nexus/core/links/v0.2.0",
        "self": "{{base}}/schemas/modelvalidation/simulation/modelvalidation/v0.2.0"
    }
}    
    """
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/modelvalidation/v0.2.0"  # only present in nexus-int
    type = ["prov:Activity", "nsg:ModelValidation"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {
            "name": "schema:name",
            "description": "schema:description",
            "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
            "prov": "http://www.w3.org/ns/prov#",
            "schema": "http://schema.org/",
            "generated": "prov:generated",
            "used": "prov:used",
            "modelUsed": "prov:used",
            "testUsed": "prov:used",
            "dataUsed": "prov:used",
            "startedAtTime": "prov:startedAtTime",
            "endedAtTime": "prov:endedAtTime",
            "wasAssociatedWith": "prov:wasAssociatedWith",
            "referenceData": "nsg:referenceData"
        }
    ]
    fields = (
        Field("name", basestring, "name"),
        Field("model_instance", (ModelInstance, MEModel), "modelUsed", required=True),
        Field("test_script", ValidationScript, "testUsed", required=True),
        Field("reference_data", Collection, "dataUsed", required=True),
        Field("timestamp", datetime,  "startedAtTime", required=True),
        Field("result", ValidationResult, "generated", required=True),
        Field("started_by", Person, "wasAssociatedWith"),
        Field("end_timestamp",  datetime, "endedAtTime")
    )

    @property
    def _existence_query(self):
        # to fix: need an _and_ on model_instance, test_script, reference_data and timestamp
        return {
            "path": "prov:startedAtTime",
            "op": "eq",
            "value": self.timestamp.isoformat()
        }

    @property
    def duration(self):
        if self.end_timestamp:
            return self.end_timestamp - self.start_timestamp
        else:
            return 0.0

    @classmethod
    @cache
    def from_kg_instance(cls, instance, client, resolved=False):
        D = instance.data
        if resolved:
            D = cls._fix_keys(D)
        for otype in cls.type:
            if otype not in D["@type"]:
                # todo: profile - move compaction outside loop?
                compacted_types = compact_uri(D["@type"], standard_context)
                if otype not in compacted_types:
                    print("Warning: type mismatch {} - {}".format(otype, compacted_types))
        def filter_by_kg_type(items, type_name):
            filtered_items = []
            for item in as_list(items):
                if type_name in item["@type"] or type_name in compact_uri(item["@type"], standard_context):
                    filtered_items.append(item)
            return filtered_items
        try:
            model_instance = filter_by_kg_type(D["modelUsed"], "nsg:ModelInstance")[0]
        except KeyError:
            model_instance = filter_by_kg_type(D["used"], "nsg:ModelInstance")[0]
        try:
            reference_data = filter_by_kg_type(D["dataUsed"], "nsg:Collection")[0]
        except KeyError:
            reference_data = filter_by_kg_type(D["used"], "nsg:Collection")[0]
        try:
            test_script = filter_by_kg_type(D["testUsed"], "nsg:ModelValidationScript")[0]
        except KeyError:
            test_script = filter_by_kg_type(D["used"], "nsg:ModelValidationScript")[0]
        end_timestamp = D.get("endedAtTime")
        if end_timestamp:
            end_timestamp = date_parser.parse(end_timestamp)
        obj = cls(model_instance=build_kg_object(None, model_instance),
                  test_script=build_kg_object(ValidationScript, test_script),
                  reference_data=build_kg_object(None, reference_data),
                  timestamp=date_parser.parse(D.get("startedAtTime")),
                  result=build_kg_object(ValidationResult, D.get("generated")),
                  started_by=build_kg_object(Person, D.get("wasAssociatedWith")),
                  end_timestamp=end_timestamp,
                  id=D["@id"],
                  instance=instance)
        return obj


class VariableReport(KGObject):
    """docstring"""
    namespace = DEFAULT_NAMESPACE
    type = ["prov:Entity", "nsg:Entity", "nsg:VariableReportShape"]
    _path = "/simulation/variablereport/v0.1.0"
    context = {"name": "schema:name",
               "description": "schema:description",
               "variable": "nsg:variable",
               "target": "nsg:target",
               "schema": "http://schema.org/",
               "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
               "prov": "http://www.w3.org/ns/prov#"}
    fields = (Field("name", str, "name", required=True),
              Field("description", str, "description", required=False),
              Field("variable", str,"variable", required=True),
              Field("target", str, "target", required=True),
              Field("report_file", (Distribution, basestring), "distribution"))

    def __init__(self, name,
                 variable='',
                 target='soma',
                 description='',
                 report_file=None,
                 id=None,
                 instance=None):
        super(VariableReport, self).__init__(
            name=name,
            variable=variable, target=target, description=description,
            report_file=report_file,
            id=id, instance=instance
        )
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
        super(VariableReport, self).save(client)
        if self._file_to_upload:
            self.upload_attachment(self._file_to_upload, client)

    def upload_attachment(self, file_path, client):
        assert os.path.isfile(file_path)
        statinfo = os.stat(file_path)
        if statinfo.st_size > ATTACHMENT_SIZE_LIMIT:
            raise Exception("File is too large to store directly in the KnowledgeGraph, please upload it to a Swift container")
        # todo, use the Nexus HTTP client directly for the following
        headers = client._nexus_client._http_client.auth_client.get_headers()
        content_type, encoding = mimetypes.guess_type(file_path, strict=False)
        response = requests.put("{}/attachment?rev={}".format(self.id, self.rev or 1),
                                headers=headers,
                                files={
                                    "file": (os.path.basename(file_path),
                                             open(file_path, "rb"),
                                             content_type)
                                })
        if response.status_code < 300:
            logger.info("Added attachment {} to {}".format(file_path, self.id))
            self._file_to_upload = None
            self.report_file = Distribution.from_jsonld(response.json()["distribution"][0])
        else:
            raise Exception(str(response.content))

    def download(self, local_directory, client):
        for rf in as_list(self.report_file):
            rf.download(local_directory, client)


class SimulationActivity(KGObject):
    """  Here this is the Simulation *Activity*
    Schema (use the environment setting in Postman to replace {{base}} with the desired nexus endpoint) :
{
    "@context": [
        "{{base}}/contexts/neurosciencegraph/core/schema/v0.1.0",
        {
            "this": "{{base}}/schemas/modelvalidation/simulation/simulationactivity/v0.0.4/shapes/"
        },
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ],
    "@id": "{{base}}/schemas/modelvalidation/simulation/simulationactivity/v0.0.4",
    "@type": "nxv:Schema",
    "imports": [
        "{{base}}/schemas/neurosciencegraph/commons/activity/v0.1.4"
    ],
    "shapes": [
        {
            "@id": "this:SimulationActivityShape",
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
                            "class": "nsg:SimulationResult",
                            "description": "Generated simulation result.",
                            "minCount": 1,
                            "name": "Result",
                            "path": "prov:generated",
                            "seeAlso": "{{base}}/schemas/modelvalidation/simulation/simulationresult/v0.0.4/shapes/SimulationResultShape"
                        }
                    ]
                }
            ],
            "label": "Simulation report analysis shape",
            "nodekind": "sh:BlankNodeOrIRI",
            "targetClass": "nsg:SimulationActivity"
        }
    ],
    "links": {
        "@context": "{{base}}/contexts/nexus/core/links/v0.2.0",
        "self": "{{base}}/schemas/modelvalidation/simulation/simulationactivity/v0.0.4"
    }
}
    """
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/simulationactivity/v0.0.4"
    type = ["prov:Activity", "nsg:SimulationActivity"]
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
            "modelUsed": "prov:used",
            "simUsed": "prov:used",
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
        Field("model_instance", (ModelInstance, MEModel), "modelUsed", required=True),
        Field("simulation_script", "brainsimulation.SimulationScript", "simUsed", required=True),
        Field("configuration_used", "brainsimulation.SimulationConfiguration", "configUsed", required=True),
        Field("timestamp", datetime,  "startedAtTime", required=True),
        Field("result", "brainsimulation.SimulationResult", "generated", required=True),
        Field("started_by", Person, "wasAssociatedWith"),
        Field("end_timestamp",  datetime, "endedAtTime")
    )
    


class SimulationConfiguration(KGObject):
    """
{
    "@context": [
        "{{base}}/contexts/neurosciencegraph/core/schema/v0.1.0",
        {
            "this": "{{base}}/schemas/modelvalidation/simulation/simulationconfiguration/v0.0.2/shapes/"
        },
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ],
    "@id": "{{base}}/schemas/modelvalidation/simulation/simulationconfiguration/v0.0.2",
    "@type": "nxv:Schema",
    "imports": [
        "{{base}}/schemas/neurosciencegraph/commons/entity/v0.1.0"
    ],
    "shapes": [
        {
            "@id": "this:SimulationConfigurationShape",
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
            "label": "Simulation Configuration shape",
            "nodekind": "sh:BlankNodeOrIRI",
            "targetClass": "nsg:SimulationConfiguration"
        }
    ],
    "links": {
        "@context": "{{base}}/contexts/nexus/core/links/v0.2.0",
        "self": "{{base}}/schemas/modelvalidation/simulation/simulationconfiguration/v0.0.2"
    }
}
    """
    namespace = DEFAULT_NAMESPACE
    type = ["prov:Entity", "nsg:Entity", "nsg:SimulationConfiguration"]
    _path = "/simulation/simulationconfiguration/v0.0.2"
    context = {"schema": "http://schema.org/",
               "name": "schema:name",
               "description": "schema:description",
               "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/"}
    fields = (
        Field("name", basestring, "name", required=True),
        Field("description", basestring, "description"),
        # the following should store the machine-readable parameters:
        Field("json_description", basestring, "json_description") 
    )
    
            
class SimulationResult(KGObject):
    """
    Schema (use the environment setting in Postman to replace {{base}} with the desired nexus endpoint) :
{
    "@context": [
        "{{base}}/contexts/neurosciencegraph/core/schema/v0.1.0",
        {
            "this": "{{base}}/schemas/modelvalidation/simulation/simulationresult/v0.0.4/shapes/"
        },
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ],
    "@id": "{{base}}/schemas/modelvalidation/simulation/simulationresult/v0.0.4",
    "@type": "nxv:Schema",
    "imports": [
        "{{base}}/schemas/neurosciencegraph/commons/entity/v0.1.0"
    ],
    "shapes": [
        {
            "@id": "this:SimulationResultShape",
            "@type": "sh:NodeShape",
            "and": [
                {
                    "node": "{{base}}/schemas/neurosciencegraph/commons/entity/v0.1.0/shapes/EntityShape"
                },
                {
                    "property": [
                        {
                            "datatype": "xsd:string",
                            "description": "name of the simulation result",
                            "minCount": 1,
                            "name": "name",
                            "path": "schema:name"
                        }
                    ]
                }
            ],
            "label": "Simulation Result shape",
            "nodekind": "sh:BlankNodeOrIRI",
            "targetClass": "nsg:SimulationResult"
        }
    ],
    "links": {
        "@context": "{{base}}/contexts/nexus/core/links/v0.2.0",
        "self": "{{base}}/schemas/modelvalidation/simulation/simulationresult/v0.0.4"
    }
}
    """
    namespace = DEFAULT_NAMESPACE
    type = ["prov:Entity", "nsg:Entity", "nsg:SimulationResult"]
    _path = "/simulation/simulationresult/v0.0.4"
    context = {"schema": "http://schema.org/",
               "name": "schema:name",
               "description": "schema:description",
               "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
               "variable": "nsg:variable",
               "target": "nsg:target",
               "brainRegion": "nsg:brainRegion",
               "species": "nsg:species",
               "celltype": "nsg:celltype",
               "dataType": "nsg:dataType",
               "prov": "http://www.w3.org/ns/prov#",
               "startedAtTime": "prov:startedAtTime",
               "wasGeneratedBy": "prov:wasGeneratedBy"}
    fields = (Field("name", basestring, "name", required=True),
              Field("variable", basestring, "variable"),
              Field("target", basestring, "target"),
              Field("report_file", (Distribution, basestring), "distribution"),
              Field("generated_by", (ModelInstance, basestring), "wasGeneratedBy"),
              Field("data_type", basestring, "dataType"),
              Field("description", basestring, "description"),
              Field("parameters", basestring, "parameters"),
              Field("timestamp", datetime,  "startedAtTime"),
              Field("brain_region", BrainRegion, "brainRegion"),
              Field("species", Species, "species"),
              Field("celltype", CellType, "celltype"))

    def __init__(self,
                 name,
                 generated_by='',
                 report_file=None,
                 data_type = '',
                 variable='',
                 target='',
                 description='',
                 timestamp=None,
                 brain_region=None, species=None, celltype=None,
                 parameters=None,
                 id=None, instance=None):
        
        super(SimulationResult, self).__init__(
            name=name,
            generated_by=generated_by,
            report_file=report_file,
            data_type=data_type,
            variable=variable,
            target=target,
            description=description,
            parameters=parameters,
            timestamp=timestamp,
            brain_region=brain_region,
            species=species,
            celltype=celltype,
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
        super(SimulationResult, self).save(client)
        if self._file_to_upload:
            self.upload_attachment(self._file_to_upload, client)

    def upload_attachment(self, file_path, client):
        upload_attachment(self, file_path, client)
        
    def download(self, local_directory, client):
        for rf in as_list(self.report_file):
            rf.download(local_directory, client)

class SimulationScript(KGObject):  # or ValidationImplementation
    """docstring"""
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/validationscript/v0.1.0"
    type = ["prov:Entity", "nsg:ModelValidationScript"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {
            "name": "schema:name",
            "description": "schema:description",
            "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
            "prov": "http://www.w3.org/ns/prov#",
            "schema": "http://schema.org/",
            "dateCreated": "schema:dateCreated",
            "repository": "schema:codeRepository",
            "version": "schema:version",
            "parameters": "nsg:parameters",
            "path": "nsg:path",
            "implements": "nsg:implements",
            "oldUUID": "nsg:providerId"
        }
    ]
    fields = (
        Field("name", basestring, "name", required=True),
        Field("date_created", (date, datetime), "dateCreated", required=True),
        Field("repository", IRI, "repository"),
        Field("version", basestring, "version"),
        Field("description", basestring, "description"),
        Field("parameters", basestring, "parameters"),
        Field("test_definition", ValidationTestDefinition, "implements"),
        Field("old_uuid", basestring, "oldUUID")
    )
            
            
def list_kg_classes():
    """List all KG classes defined in this module"""
    return [obj for name, obj in inspect.getmembers(sys.modules[__name__])
            if inspect.isclass(obj) and issubclass(obj, KGObject) and obj.__module__ == __name__]


def use_namespace(namespace):
    """Set the namespace for all classes in this module."""
    for cls in list_kg_classes():
        cls.namespace = namespace
