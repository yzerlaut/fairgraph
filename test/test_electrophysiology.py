# encoding: utf-8
"""
Tests of fairgraph.electrophysiology module, using a mock Http client
which returns data loaded from the files in the test_data directory.
"""

from fairgraph.base import KGQuery, KGProxy, as_list, Distribution
from fairgraph.commons import BrainRegion, CellType, QuantitativeValue
from fairgraph.core import use_namespace as use_core_namespace
from fairgraph.electrophysiology import (
    Trace, MultiChannelMultiTrialRecording, PatchedCell, Slice, BrainSlicingActivity,
    PatchedSlice, PatchedCellCollection, PatchClampActivity, PatchClampExperiment,
    QualifiedTraceGeneration, QualifiedMultiTraceGeneration,
    IntraCellularSharpElectrodeExperiment, IntraCellularSharpElectrodeRecordedCell,
    IntraCellularSharpElectrodeRecordedCellCollection,
    IntraCellularSharpElectrodeRecordedSlice, IntraCellularSharpElectrodeRecording,
    ElectrodeImplantationActivity, ExtracellularElectrodeExperiment, ImplantedBrainTissue,
    list_kg_classes, use_namespace as use_electrophysiology_namespace)
from fairgraph.minds import Dataset

from .utils import kg_client, MockKGObject, test_data_lookup, BaseTestKG
from pyxus.resources.entity import Instance

import pytest


test_data_lookup.update({
    "/v0/data/neuralactivity/experiment/brainslicing/v0.1.0/": "test/test_data/nexus/electrophysiology/brainslicing_list_0_10.json",
    "/v0/data/neuralactivity/experiment/brainslicingactivity/v0.1.0/": "test/test_data/nexus/electrophysiology/brainslicingactivity_list_0_10.json",
    "/v0/data/neuralactivity/experiment/intracellularsharpelectrodeexperiment/v0.1.0/": "test/test_data/nexus/electrophysiology/intracellularsharpelectrodeexperiment_list_0_10.json",
    "/v0/data/neuralactivity/experiment/intrasharprecordedcell/v0.1.0/": "test/test_data/nexus/electrophysiology/intracellularsharpelectroderecordedcell_list_0_10.json",
    "/v0/data/neuralactivity/experiment/intrasharprecordedcellcollection/v0.1.0/": "test/test_data/nexus/electrophysiology/intracellularsharpelectroderecordedcellcollection_list_0_10.json",
    "/v0/data/neuralactivity/experiment/intrasharprecordedslice/v0.1.0/": "test/test_data/nexus/electrophysiology/intracellularsharpelectroderecordedslice_list_0_10.json",
    "/v0/data/neuralactivity/experiment/intrasharpelectrode/v0.1.0/": "test/test_data/nexus/electrophysiology/intracellularsharpelectroderecording_list_0_10.json",
    "/v0/data/neuralactivity/electrophysiology/multichannelmultitrialrecording/v0.1.0/": "test/test_data/nexus/electrophysiology/multichannelmultitrialrecording_list_0_10.json",
    "/v0/data/neuralactivity/electrophysiology/multitrace/v0.1.0/": "test/test_data/nexus/electrophysiology/multitrace_list_0_10.json",
    "/v0/data/neuralactivity/electrophysiology/multitrace/v0.1.1/": "test/test_data/nexus/electrophysiology/multitrace_list_0_10.json",
    "/v0/data/neuralactivity/experiment/multitracegeneration/v0.1.0/": "test/test_data/nexus/electrophysiology/multitracegeneration_list_0_10.json",
    "/v0/data/neuralactivity/experiment/patchclampactivity/v0.1.0/": "test/test_data/nexus/electrophysiology/patchclampactivity_list_0_10.json",
    "/v0/data/neuralactivity/experiment/patchclampexperiment/v0.1.0/": "test/test_data/nexus/electrophysiology/patchclampexperiment_list_0_10.json",
    "/v0/data/neuralactivity/experiment/patchedcell/v0.1.0/": "test/test_data/nexus/electrophysiology/patchedcell_list_0_50.json",
    "/v0/data/neuralactivity/experiment/patchedcellcollection/v0.1.0/": "test/test_data/nexus/electrophysiology/patchedcellcollection_list_0_10.json",
    "/v0/data/neuralactivity/experiment/patchedslice/v0.1.0/": "test/test_data/nexus/electrophysiology/patchedslice_list_0_10.json",
    "/v0/data/neuralactivity/electrophysiology/multitracegeneration/v0.1.0/": "test/test_data/nexus/electrophysiology/qualifiedmultitracegeneration_list_0_10.json",
    "/v0/data/neuralactivity/experiment/qualifiedtracegeneration/v0.1.0/": "test/test_data/nexus/electrophysiology/qualifiedtracegeneration_list_0_10.json",
    "/v0/data/neuralactivity/core/slice/v0.1.0/": "test/test_data/nexus/electrophysiology/slice_list_0_10.json",
    "/v0/data/neuralactivity/electrophysiology/stimulusexperiment/v0.1.0/": "test/test_data/nexus/electrophysiology/patchclampexperiment_list_0_10.json",
    "/v0/data/neuralactivity/electrophysiology/stimulusexperiment/v0.2.1/": "test/test_data/nexus/electrophysiology/intracellularsharpelectrodeexperiment_list_0_10.json",
    "/v0/data/neuralactivity/electrophysiology/trace/v0.1.0/": "test/test_data/nexus/electrophysiology/trace_list_0_10.json",
    "/v0/data/neuralactivity/electrophysiology/tracegeneration/v0.1.0/": "test/test_data/nexus/electrophysiology/tracegeneration_list_0_10.json",
    "/v0/data/neuralactivity/experiment/wholecellpatchclamp/v0.1.0/": "test/test_data/nexus/electrophysiology/wholecellpatchclamp_list_0_10.json",
    "/v0/data/neuralactivity/experiment/patchedcell/v0.1.0/5ab24291-8dca-4a45-a484-8a8c28d396e2": "test/test_data/nexus/electrophysiology/patchedcell_example.json",

    "/query/neuralactivity/experiment/patchedcell/v0.1.0/fgModified/instances": "test/test_data/kgquery/electrophysiology/patchedcell_list_simple_0_10.json",
    "/query/neuralactivity/experiment/patchedcell/v0.1.0/fgResolvedModified/instances": "test/test_data/kgquery/electrophysiology/patchedcell_list_resolved_0_10.json",
    "/query/neuralactivity/experiment/brainslicing/v0.1.0/fgResolved/instances": "test/test_data/kgquery/electrophysiology/brainslicingactivity_list_resolved_0_10.json",
    "/query/neuralactivity/electrophysiology/stimulusexperiment/v0.2.1/fgResolved/instances": "test/test_data/kgquery/electrophysiology/intracellularsharpelectrodeexperiment_list_resolved_0_10.json",
    "/query/neuralactivity/experiment/intrasharprecordedcell/v0.1.0/fgResolvedModified/instances": "test/test_data/kgquery/electrophysiology/intracellularsharpelectroderecordedcell_list_resolved_0_10.json",
    "/query/neuralactivity/experiment/intrasharprecordedcellcollection/v0.1.0/fgResolved/instances": "test/test_data/kgquery/electrophysiology/intracellularsharpelectroderecordedcellcollection_list_resolved_0_10.json",
    "/query/neuralactivity/experiment/intrasharprecordedslice/v0.1.0/fgResolved/instances": "test/test_data/kgquery/electrophysiology/intracellularsharpelectroderecordedslice_list_resolved_0_10.json",
    "/query/neuralactivity/experiment/intrasharpelectrode/v0.1.0/fgResolved/instances": "test/test_data/kgquery/electrophysiology/intracellularsharpelectroderecording_list_resolved_0_10.json",
    "/query/neuralactivity/electrophysiology/multitrace/v0.1.0/fgResolved/instances": "test/test_data/kgquery/electrophysiology/multichannelmultitrialrecording_list_resolved_0_10.json",
    "/query/neuralactivity/electrophysiology/multitrace/v0.1.1/fgResolved/instances": "test/test_data/kgquery/electrophysiology/multichannelmultitrialrecording_list_resolved_0_10.json",
    "/query/neuralactivity/experiment/wholecellpatchclamp/v0.1.0/fgResolved/instances": "test/test_data/kgquery/electrophysiology/patchclampactivity_list_resolved_0_10.json",
    "/query/neuralactivity/electrophysiology/stimulusexperiment/v0.1.0/fgResolved/instances": "test/test_data/kgquery/electrophysiology/patchclampexperiment_list_resolved_0_10.json",
    "/query/neuralactivity/experiment/patchedcellcollection/v0.1.0/fgResolved/instances": "test/test_data/kgquery/electrophysiology/patchedcellcollection_list_resolved_0_10.json",
    "/query/neuralactivity/experiment/patchedslice/v0.1.0/fgResolved/instances": "test/test_data/kgquery/electrophysiology/patchedslice_list_resolved_0_10.json",
    "/query/neuralactivity/electrophysiology/multitracegeneration/v0.1.0/fgResolved/instances": "test/test_data/kgquery/electrophysiology/qualifiedmultitracegeneration_list_resolved_0_10.json",
    "/query/neuralactivity/electrophysiology/tracegeneration/v0.1.0/fgResolved/instances": "test/test_data/kgquery/electrophysiology/qualifiedtracegeneration_list_resolved_0_10.json",
    "/query/neuralactivity/core/slice/v0.1.0/fgResolved/instances": "test/test_data/kgquery/electrophysiology/slice_list_resolved_0_10.json",
    "/query/neuralactivity/electrophysiology/trace/v0.1.0/fgResolved/instances": "test/test_data/kgquery/electrophysiology/trace_list_resolved_0_10.json",

    "/query/neuralactivity/experiment/brainslicing/v0.1.0/fgSimple/instances": "test/test_data/kgquery/electrophysiology/brainslicingactivity_list_resolved_0_10.json",
    "/query/neuralactivity/electrophysiology/stimulusexperiment/v0.2.1/fgSimple/instances": "test/test_data/kgquery/electrophysiology/intracellularsharpelectrodeexperiment_list_resolved_0_10.json",
    "/query/neuralactivity/experiment/intrasharprecordedcell/v0.1.0/fgModified/instances": "test/test_data/kgquery/electrophysiology/intracellularsharpelectroderecordedcell_list_resolved_0_10.json",
    "/query/neuralactivity/experiment/intrasharprecordedcellcollection/v0.1.0/fgSimple/instances": "test/test_data/kgquery/electrophysiology/intracellularsharpelectroderecordedcellcollection_list_resolved_0_10.json",
    "/query/neuralactivity/experiment/intrasharprecordedslice/v0.1.0/fgSimple/instances": "test/test_data/kgquery/electrophysiology/intracellularsharpelectroderecordedslice_list_resolved_0_10.json",
    "/query/neuralactivity/experiment/intrasharpelectrode/v0.1.0/fgSimple/instances": "test/test_data/kgquery/electrophysiology/intracellularsharpelectroderecording_list_resolved_0_10.json",
    "/query/neuralactivity/electrophysiology/multitrace/v0.1.0/fgSimple/instances": "test/test_data/kgquery/electrophysiology/multichannelmultitrialrecording_list_resolved_0_10.json",
    "/query/neuralactivity/electrophysiology/multitrace/v0.1.1/fgSimple/instances": "test/test_data/kgquery/electrophysiology/multichannelmultitrialrecording_list_resolved_0_10.json",
    "/query/neuralactivity/experiment/wholecellpatchclamp/v0.1.0/fgSimple/instances": "test/test_data/kgquery/electrophysiology/patchclampactivity_list_resolved_0_10.json",
    "/query/neuralactivity/electrophysiology/stimulusexperiment/v0.1.0/fgSimple/instances": "test/test_data/kgquery/electrophysiology/patchclampexperiment_list_resolved_0_10.json",
    "/query/neuralactivity/experiment/patchedcellcollection/v0.1.0/fgSimple/instances": "test/test_data/kgquery/electrophysiology/patchedcellcollection_list_resolved_0_10.json",
    "/query/neuralactivity/experiment/patchedslice/v0.1.0/fgSimple/instances": "test/test_data/kgquery/electrophysiology/patchedslice_list_resolved_0_10.json",
    "/query/neuralactivity/electrophysiology/multitracegeneration/v0.1.0/fgSimple/instances": "test/test_data/kgquery/electrophysiology/qualifiedmultitracegeneration_list_resolved_0_10.json",
    "/query/neuralactivity/electrophysiology/tracegeneration/v0.1.0/fgSimple/instances": "test/test_data/kgquery/electrophysiology/qualifiedtracegeneration_list_resolved_0_10.json",
    "/query/neuralactivity/core/slice/v0.1.0/fgSimple/instances": "test/test_data/kgquery/electrophysiology/slice_list_resolved_0_10.json",
    "/query/neuralactivity/electrophysiology/trace/v0.1.0/fgSimple/instances": "test/test_data/kgquery/electrophysiology/trace_list_resolved_0_10.json",
})

use_core_namespace("neuralactivity")
use_electrophysiology_namespace("neuralactivity")


class TestPatchedCell(BaseTestKG):
    class_under_test = PatchedCell

    def test_list_nexus(self, kg_client):
        cells = PatchedCell.list(kg_client, api="nexus", size=50)
        assert len(cells) == 30
        assert cells[0].brain_location == BrainRegion("hippocampus CA1")
        assert isinstance(cells[0].collection, KGQuery)
        assert cells[0].cell_type == CellType("hippocampus CA1 pyramidal cell")
        assert isinstance(cells[0].experiments, KGQuery)
        assert cells[0].pipette_id is None
        assert cells[0].seal_resistance is None
        assert cells[0].pipette_resistance is None
        assert cells[0].liquid_junction_potential is None
        assert cells[0].labeling_compound is None
        assert cells[0].reversal_potential_cl == QuantitativeValue(-16.0, unit_text="mV")

    def test_list_with_filter(self, kg_client):
        cells = PatchedCell.list(kg_client, api="nexus", brain_region=BrainRegion("hippocampus CA1"), size=50)
        assert len(cells) == 26

    def test_list_kgquery_simple(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=False)
        assert len(objects) == 10, len(objects)

    def test_list_kgquery_resolved(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=True)
        assert len(objects) == 10, len(objects)

    def test_get_from_uri_nexus(self, kg_client):
        uri = "https://nexus.humanbrainproject.org/v0/data/neuralactivity/experiment/patchedcell/v0.1.0/5ab24291-8dca-4a45-a484-8a8c28d396e2"
        cell = PatchedCell.from_uri(uri, kg_client, api="nexus")
        assert isinstance(cell, PatchedCell)
        assert cell.id == uri
        assert cell.brain_location == [BrainRegion('lobule 5 of the cerebellar vermis'),
                                       BrainRegion('lobule 6 of the cerebellar vermis'),
                                       BrainRegion('lobule 7 of the cerebellar vermis'),
                                       BrainRegion('lobule 8 of the cerebellar vermis')]
        assert isinstance(cell.collection, KGQuery)
        assert isinstance(cell.experiments, KGQuery)

    def test_get_from_uri_kgquery_simple(self, kg_client):  # TODO: UPDATE STORED QUERY
        uri = "https://nexus.humanbrainproject.org/v0/data/neuralactivity/experiment/patchedcell/v0.1.0/b813a2f7-5e87-4827-81cd-0008da041648"
        cell = PatchedCell.from_uri(uri, kg_client, api="query", resolved=False)
        assert isinstance(cell, PatchedCell)
        assert cell.brain_location == [BrainRegion('5th cerebellar lobule'),
                                       BrainRegion('6th cerebellar lobule'),
                                       BrainRegion('7th cerebellar lobule'),
                                       BrainRegion('8th cerebellar lobule')]
        assert isinstance(cell.collection, KGQuery)
        assert isinstance(cell.experiments, KGQuery)

    def test_get_from_uri_kgquery_resolved(self, kg_client):
        uri = "https://nexus.humanbrainproject.org/v0/data/neuralactivity/experiment/patchedcell/v0.1.0/b813a2f7-5e87-4827-81cd-0008da041648"
        cell = PatchedCell.from_uri(uri, kg_client, api="query", resolved=True)
        assert isinstance(cell, PatchedCell)
        assert cell.id == uri
        assert cell.brain_location == [BrainRegion('5th cerebellar lobule'),
                                       BrainRegion('6th cerebellar lobule'),
                                       BrainRegion('7th cerebellar lobule'),
                                       BrainRegion('8th cerebellar lobule')]
        assert isinstance(cell.collection, KGQuery)
        assert isinstance(cell.experiments, KGQuery)

    def test_get_from_uuid(self, kg_client):
        uri = "https://nexus.humanbrainproject.org/v0/data/neuralactivity/experiment/patchedcell/v0.1.0/5ab24291-8dca-4a45-a484-8a8c28d396e2"
        a = PatchedCell.from_uri(uri, kg_client, api="nexus")
        b = PatchedCell.from_uuid("5ab24291-8dca-4a45-a484-8a8c28d396e2", kg_client, api="nexus")
        assert a == b
        assert a.id == uri

    def test_get_from_uri_with_cache(self, kg_client):
        assert len(kg_client.cache) == 0
        assert kg_client._nexus_client._http_client.request_count == 0
        uri = "https://nexus.humanbrainproject.org/v0/data/neuralactivity/experiment/patchedcell/v0.1.0/5ab24291-8dca-4a45-a484-8a8c28d396e2"
        # 1st call
        cell1 = PatchedCell.from_uri(uri, kg_client, api="nexus")
        assert len(kg_client.cache) == 1
        assert kg_client._nexus_client._http_client.request_count == 1
        assert uri in kg_client.cache
        # 2nd call
        cell2 = PatchedCell.from_uri(uri, kg_client, api="nexus")
        assert kg_client._nexus_client._http_client.request_count == 1  # should be unchanged if cache was used
        # 3rd call, without cache
        cell3 = PatchedCell.from_uri(uri, kg_client, use_cache=False, api="nexus")
        assert kg_client._nexus_client._http_client.request_count == 2
        assert cell1.id == cell2.id == cell3.id == uri

    def test_by_name_nexus(self, kg_client):
        cell = PatchedCell.by_name("sub2epsp.samp1", kg_client, api="nexus")
        assert cell.uuid == "5ab24291-8dca-4a45-a484-8a8c28d396e2"

    def test_by_name_nexus_not_found(self, kg_client):
        cell = PatchedCell.by_name("qwertyuiop", kg_client, api="nexus")
        assert cell is None

    def test_by_name_kgquery(self, kg_client):
        cell = PatchedCell.by_name("GF1.samp1", kg_client, api="query")
        assert cell.uuid == "b813a2f7-5e87-4827-81cd-0008da041648"

    def test_round_trip(self, kg_client):
        cell1 = PatchedCell("example001",
                            brain_location=BrainRegion("primary auditory cortex"),
                            collection=None,
                            cell_type=CellType("pyramidal cell"),
                            experiments=None,
                            pipette_id=31,
                            seal_resistance=QuantitativeValue(1.2, "GΩ"),
                            pipette_resistance=QuantitativeValue(1.5, "MΩ"),
                            liquid_junction_potential=QuantitativeValue(5.0, "mV"),
                            labeling_compound="0.1% biocytin ",
                            reversal_potential_cl=QuantitativeValue(-65, "mV"))
        instance = Instance(PatchedCell.path, cell1._build_data(kg_client), Instance.path)
        instance.data["@id"] = "http://fake_uuid_93f9cd9a9b"
        instance.data["@type"] = PatchedCell.type
        cell2 = PatchedCell.from_kg_instance(instance, kg_client)
        for field in ("name", "brain_location", "cell_type",
                      "pipette_id", "seal_resistance", "pipette_resistance",
                      "liquid_junction_potential", "labeling_compound",
                      "reversal_potential_cl"):
            assert getattr(cell1, field) == getattr(cell2, field)

    def test_repr(self):
        try:
            unicode
        except NameError:
            cell = PatchedCell("example001",
                               brain_location=BrainRegion("primary auditory cortex"),
                               collection=None,
                               cell_type=CellType("pyramidal cell"),
                               experiments=None,
                               pipette_id=31,
                               seal_resistance=QuantitativeValue(1.2, "GΩ"),
                               pipette_resistance=QuantitativeValue(1.5, "MΩ"),
                               liquid_junction_potential=None,
                               labeling_compound="0.1% biocytin ",
                               reversal_potential_cl=None)
            expected_repr = ("PatchedCell(name='example001', "
                             "brain_location=BrainRegion('primary auditory cortex', 'http://purl.obolibrary.org/obo/UBERON_0034751'), "
                             "cell_type=CellType('pyramidal cell', 'http://purl.obolibrary.org/obo/CL_0000598'), "
                             "pipette_id=31, seal_resistance=QuantitativeValue(1.2 'GΩ'), "
                             "pipette_resistance=QuantitativeValue(1.5 'MΩ'), "
                             "labeling_compound='0.1% biocytin ', id=None)")
            assert repr(cell) == expected_repr
        else:
            pytest.skip(
                "The remaining lifespan of Python 2 is too short to fix unicode representation errors")


class TestTrace(BaseTestKG):
    class_under_test = Trace

    def test_list_nexus(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="nexus", size=10)
        assert len(objects) == 10, len(objects)

    def test_list_kgquery_simple(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=False)
        assert len(objects) == 10, len(objects)

    def test_list_kgquery_resolved(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=True)
        assert len(objects) == 10, len(objects)

    def test_round_trip(self, kg_client):
        trace1 = Trace("example001",
                       data_location=Distribution("http://example.com/example.csv",
                                                  content_type="text/tab-separated-values"),
                       generated_by=MockKGObject(id="http://fake_uuid_abc123", type=PatchClampExperiment.type),
                       generation_metadata=MockKGObject(id="http://fake_uuid_def456", type=QualifiedTraceGeneration.type),
                       channel=42,
                       data_unit="mV",
                       time_step=QuantitativeValue(0.1, "ms"),
                       part_of=MockKGObject(id="http://fake_uuid_ghi789", type=Dataset.type))
        instance = Instance(Trace.path, trace1._build_data(kg_client), Instance.path)
        instance.data["@id"] = "http://fake_uuid_6a5d6ecf87"
        instance.data["@type"] = Trace.type
        trace2 = Trace.from_kg_instance(instance, kg_client)
        for field in ("name", "data_location", "channel", "data_unit", "time_step"):
            assert getattr(trace1, field) == getattr(trace2, field)
        for field in ("generated_by", "generation_metadata", "part_of"):
            obj1 = getattr(trace1, field)
            obj2 = getattr(trace2, field)
            assert isinstance(obj2, KGProxy)
            assert obj1.id == obj2.id
            assert obj1.type == obj2.type


class TestMultiChannelMultiTrialRecording(BaseTestKG):
    class_under_test = MultiChannelMultiTrialRecording

    def test_list_nexus(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="nexus", size=10)
        assert len(objects) == 4, len(objects)

    def test_list_kgquery_simple(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=False)
        assert len(objects) == 10, len(objects)

    def test_list_kgquery_resolved(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=True)
        assert len(objects) == 10, len(objects)


class TestSlice(BaseTestKG):
    class_under_test = Slice

    def test_list_nexus(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="nexus", size=10)
        assert len(objects) == 10, len(objects)

    def test_list_kgquery_simple(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=False)
        assert len(objects) == 10, len(objects)

    def test_list_kgquery_resolved(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=True)
        assert len(objects) == 10, len(objects)


class TestBrainSlicingActivity(BaseTestKG):
    class_under_test = BrainSlicingActivity

    def test_list_nexus(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="nexus", size=10)
        assert len(objects) == 10, len(objects)

    def test_list_kgquery_simple(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=False)
        assert len(objects) == 10, len(objects)

    def test_list_kgquery_resolved(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=True)
        assert len(objects) == 10, len(objects)


class TestPatchedSlice(BaseTestKG):
    class_under_test = PatchedSlice

    def test_list_nexus(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="nexus", size=10)
        assert len(objects) == 10, len(objects)

    def test_list_kgquery_simple(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=False)
        assert len(objects) == 10, len(objects)

    def test_list_kgquery_resolved(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=True)
        assert len(objects) == 10, len(objects)


class TestPatchedCellCollection(BaseTestKG):
    class_under_test = PatchedCellCollection

    def test_list_nexus(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="nexus", size=10)
        assert len(objects) == 10, len(objects)

    def test_list_kgquery_resolved(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=True)
        assert len(objects) == 10, len(objects)


class TestPatchClampActivity(BaseTestKG):
    class_under_test = PatchClampActivity

    def test_list_nexus(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="nexus", size=10)
        assert len(objects) == 10, len(objects)

    def test_list_kgquery_simple(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=False)
        assert len(objects) == 10, len(objects)

    def test_list_kgquery_resolved(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=True)
        assert len(objects) == 10, len(objects)


class TestPatchClampExperiment(BaseTestKG):
    class_under_test = PatchClampExperiment

    def test_list_nexus(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="nexus", size=10)
        assert len(objects) == 10, len(objects)

    def test_list_kgquery_simple(self, kg_client):
        cls = self.class_under_test
        cls.set_strict_mode(False, field_name="name")  # some examples have empty names
        cls.set_strict_mode(False, field_name="stimulus")
        objects = cls.list(kg_client, api="query", size=10, resolved=False)
        assert len(objects) == 10, len(objects)

    def test_list_kgquery_resolved(self, kg_client):
        cls = self.class_under_test
        cls.set_strict_mode(False, field_name="name")  # some examples have empty names
        cls.set_strict_mode(False, field_name="stimulus")
        objects = cls.list(kg_client, api="query", size=10, resolved=True)
        assert len(objects) == 10, len(objects)


class TestQualifiedTraceGeneration(BaseTestKG):
    class_under_test = QualifiedTraceGeneration

    def test_list_nexus(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="nexus", size=10)
        assert len(objects) == 10, len(objects)

    def test_list_kgquery_simple(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=False)
        assert len(objects) == 10, len(objects)

    def test_list_kgquery_resolved(self, kg_client):
        cls = self.class_under_test
        IntraCellularSharpElectrodeExperiment.set_strict_mode(False, "stimulus")
        objects = cls.list(kg_client, api="query", size=10, resolved=True)
        assert len(objects) == 10, len(objects)


class TestQualifiedMultiTraceGeneration(BaseTestKG):
    class_under_test = QualifiedMultiTraceGeneration

    def test_list_nexus(self, kg_client):
        tracegens = QualifiedMultiTraceGeneration.list(kg_client, api="nexus", size=10)
        assert len(tracegens) == 10, len(objects)

    def test_list_kgquery_simple(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=False)
        assert len(objects) == 10, len(objects)

    def test_list_kgquery_resolved(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=True)
        assert len(objects) == 10, len(objects)


class TestIntraCellularSharpElectrodeRecordedCell(BaseTestKG):
    class_under_test = IntraCellularSharpElectrodeRecordedCell

    def test_list_nexus(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="nexus", size=10)
        assert len(objects) == 8, len(objects)

    def test_list_kgquery_simple(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=False)
        assert len(objects) == 8, len(objects)

    def test_list_kgquery_resolved(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=True)
        assert len(objects) == 8, len(objects)


class TestIntraCellularSharpElectrodeRecording(BaseTestKG):
    class_under_test = IntraCellularSharpElectrodeRecording

    def test_list_nexus(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="nexus", size=10)
        assert len(objects) == 8, len(objects)

    def test_list_kgquery_simple(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=False)
        assert len(objects) == 8, len(objects)

    def test_list_kgquery_resolved(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=True)
        assert len(objects) == 8, len(objects)


class TestIntraCellularSharpElectrodeRecordedCellCollection(BaseTestKG):
    class_under_test = IntraCellularSharpElectrodeRecordedCellCollection

    def test_list_nexus(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="nexus", size=10)
        assert len(objects) == 8, len(objects)

    def test_list_kgquery_simple(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=False)
        assert len(objects) == 8, len(objects)

    def test_list_kgquery_resolved(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=True)
        assert len(objects) == 8, len(objects)


class TestIntraCellularSharpElectrodeRecordedSlice(BaseTestKG):
    class_under_test = IntraCellularSharpElectrodeRecordedSlice

    def test_list_nexus(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="nexus", size=10)
        assert len(objects) == 8, len(objects)

    def test_list_kgquery_simple(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=False)
        assert len(objects) == 8, len(objects)

    def test_list_kgquery_resolved(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=True)
        assert len(objects) == 8, len(objects)


class TestIntraCellularSharpElectrodeExperiment(BaseTestKG):
    class_under_test = IntraCellularSharpElectrodeExperiment

    def test_list_nexus(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="nexus", size=10)
        assert len(objects) == 8, len(objects)

    def test_list_kgquery_simple(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=False)
        assert len(objects) == 8, len(objects)

    def test_list_kgquery_resolved(self, kg_client):
        cls = self.class_under_test
        objects = cls.list(kg_client, api="query", size=10, resolved=True)
        assert len(objects) == 8, len(objects)


class TestModuleFunctions(object):

    def test_list_kg_classes(self):
        expected_classes = set((
            Trace, MultiChannelMultiTrialRecording, PatchedCell, Slice, BrainSlicingActivity,
            PatchedSlice, PatchedCellCollection, PatchClampActivity, PatchClampExperiment,
            QualifiedTraceGeneration, QualifiedMultiTraceGeneration,
            IntraCellularSharpElectrodeExperiment, IntraCellularSharpElectrodeRecordedCell,
            IntraCellularSharpElectrodeRecordedCellCollection,
            IntraCellularSharpElectrodeRecordedSlice, IntraCellularSharpElectrodeRecording,
            ElectrodeImplantationActivity, ImplantedBrainTissue,
            ExtracellularElectrodeExperiment
        ))
        assert set(list_kg_classes()) == expected_classes
