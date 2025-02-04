import numpy as np
import os
import pytest
from nexusformat.nexus import *


field1 = NXfield((1,2), name="f1", dtype=np.float32, units='m')
field2 = NXfield((3,4), name="f2", dtype=np.int16)
field3 = NXfield((5,6), name="f3", dtype=np.float32)


def test_link_creation():

    root = NXroot()    
    root["g1"] = NXgroup(f1=field1)
    root["g2"] = NXgroup()
    root["g2"].f1_link = NXlink(root["g1/f1"])

    assert "g1/f1" in root
    assert "g2/f1_link" in root
    assert root["g2/f1_link"].nxlink is root["g1/f1"]
    assert root["g2/f1_link"].nxtarget == "/g1/f1"

    root["g2/f2_link"] = NXlink(target="/g1/f1")

    assert root["g2/f2_link"].nxlink is root["g1/f1"]

    root["g2"].makelink(root["g1/f1"], name="f3_link")
    assert root["g2/f3_link"].nxlink is root["g1/f1"]


def test_linkfield_properties():

    root = NXroot()    
    root["g1"] = NXgroup(f1=field1)
    root["g2"] = NXgroup()
    root["g2"].f1_link = NXlink(root["g1/f1"])

    assert root["g2/f1_link"].shape == (2,)
    assert root["g2/f1_link"].dtype == np.float32

    root["g1/f1"].attrs["a1"] = 1
    assert "a1" in root["g2/f1_link"].attrs
    assert root["g2/f1_link"].a1 == 1


def test_linkgroup_properties():

    root = NXroot(NXentry())    
    root["entry/g1"] = NXgroup()
    root["entry/g1/g2"] = NXgroup(field1)
    root["entry/g3"] = NXlink("entry/g1/g2")

    assert "f1" in root["entry/g3"]
    assert len(root["entry/g3"]) == len(root["entry/g1/g2"])
    assert root["entry/g3"].nxtarget == "entry/g1/g2"
    assert root["entry/g1/g2/f1"].nxgroup is root["entry/g1/g2"]
    assert root["entry/g3"].nxgroup is root["entry"]
    assert root["entry/g3"].nxlink is root["entry/g1/g2"]


def test_external_field_links(tmpdir):

    filename = os.path.join(tmpdir, "file1.nxs")
    root = NXroot(NXentry())
    root.save(filename, mode="w")

    external_filename = os.path.join(tmpdir, "file2.nxs")
    external_root = NXroot(NXentry(field1))
    external_root.save(external_filename, mode="w")

    root["entry/f2"] = NXlink(target="entry/f1", file=external_filename)

    assert root["entry/f2"].nxtarget == "entry/f1"
    assert root["entry/f2"].nxfilepath == "entry/f1"
    assert root["entry/f2"].nxfilename == external_filename
    assert root["entry/f2"].nxfilemode == "r"
    assert root["entry/f2"].nxgroup == root["entry"]

    assert root["entry/f2"].file_exists()
    assert root["entry/f2"].path_exists()
    assert root["entry/f2"].shape == external_root["entry/f1"].shape
    assert root["entry/f2"][0] == external_root["entry/f1"][0]
    assert "units" in root["entry/f2"].attrs

def test_external_group_links(tmpdir):

    filename = os.path.join(tmpdir, "file1.nxs")
    root = NXroot(NXentry())
    root.save(filename, mode="w")

    external_filename = os.path.join(tmpdir, "file2.nxs")
    external_root = NXroot(NXentry(NXgroup(field1, name='g1', attrs={"a":"b"})))
    external_root.save(external_filename, mode="w")

    root["entry/g2"] = NXlink(target="entry/g1", file=external_filename)

    assert root["entry/g2"].nxtarget == "entry/g1"
    assert root["entry/g2"].nxfilepath == "entry/g1"
    assert root["entry/g2"].nxfilename == external_filename
    assert root["entry/g2"].nxfilemode == "r"
    assert root["entry/g2"].nxgroup == root["entry"]

    assert root["entry/g2"].file_exists()
    assert root["entry/g2"].path_exists()
    assert "f1" in root["entry/g2"]
    assert root["entry/g2/f1"][0] == external_root["entry/g1/f1"][0]
    assert "a" in root["entry/g2"].attrs
