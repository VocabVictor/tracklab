"""datastore tests."""

import json
import os

import pytest
import tracklab
from tracklab.core import HistoryRecord, Record, HistoryItem

datastore = tracklab.sdk.internal.datastore


FNAME = "test.dat"

try:
    FileNotFoundError  # noqa: B018
except NameError:
    FileNotFoundError = OSError


def check(
    ds,
    chunk_sizes=tuple(),
    expected_records=0,
    expected_pad=0,
    expected_record_sizes=None,
):
    """Check datastore size after multiple items written."""
    record_sizes = []
    for _, chunk_size in enumerate(chunk_sizes):
        size = ds._write_data(b"\x01" * chunk_size)
        record_sizes.append(size)
    num = 7 + sum(chunk_sizes) + expected_records * 7 + expected_pad
    ds.close()
    s = os.stat(FNAME)
    assert s.st_size == num
    if expected_record_sizes is not None:
        assert tuple(record_sizes) == expected_record_sizes


@pytest.fixture()
def force_internal_process():
    tracklab._IS_INTERNAL_PROCESS = True
    yield
    tracklab._IS_INTERNAL_PROCESS = False


@pytest.fixture()
def with_datastore(request, force_internal_process):
    """Fixture which returns an initialized datastore."""
    try:
        os.unlink(FNAME)
    except FileNotFoundError:
        pass

    _ = force_internal_process  # required by DataStore
    s = datastore.DataStore()
    s.open_for_write(FNAME)

    def fin():
        os.unlink(FNAME)

    request.addfinalizer(fin)
    return s


def test_proto_write_partial(force_internal_process):
    """Serialize a record into a partial block."""
    data = dict(this=2, that=4)
    history = HistoryRecord()
    for k, v in data.items():
        history.add_item(k, v)
    rec = Record(history=history)

    _ = force_internal_process  # required by DataStore
    s = datastore.DataStore()
    s.open_for_write(FNAME)
    s.write(rec)
    s.close()


def test_data_write_full(with_datastore):
    """Write a full block."""
    sizes, records = tuple([32768 - 7 - 7]), 1
    check(with_datastore, chunk_sizes=sizes, expected_records=records)


def test_data_write_overflow(with_datastore):
    """Write one more than we can fit in a block."""
    ds = with_datastore
    ds._write_data(b"\x01" * (32768 - 7 - 7 + 1))
    ds.close()
    s = os.stat(FNAME)
    assert s.st_size == 32768 + 7 + 1


def test_data_write_pad(with_datastore):
    """Pad 6 bytes with zeros, then write next record."""
    ds = with_datastore
    ds._write_data(b"\x01" * (32768 - 7 - 7 - 6))
    ds._write_data(b"\x02" * (1))
    ds.close()
    s = os.stat(FNAME)
    assert s.st_size == 32768 + 7 + 1


def test_data_write_empty(with_datastore):
    """Write empty record with zero length, then write next record."""
    ds = with_datastore
    ds._write_data(b"\x01" * (32768 - 7 - 7 - 7))
    ds._write_data(b"\x02" * (1))
    ds.close()
    s = os.stat(FNAME)
    assert s.st_size == 32768 + 7 + 1


def test_data_write_split(with_datastore):
    """Leave just room for 1 more byte, then try to write 2."""
    ds = with_datastore
    ds._write_data(b"\x01" * (32768 - 7 - 7 - 8))
    ds._write_data(b"\x02" * (2))
    ds.close()
    s = os.stat(FNAME)
    assert s.st_size == 32768 + 7 + 1


def test_data_write_split_overflow(with_datastore):
    """Leave just room for 1 more byte, then write a block + 1 byte."""
    ds = with_datastore
    ds._write_data(b"\x01" * (32768 - 7 - 7 - 8))
    ds._write_data(b"\x02" * (2 + 32768 - 7))
    ds.close()
    s = os.stat(FNAME)
    assert s.st_size == 32768 * 2 + 7 + 1


def test_data_write_fill(with_datastore):
    """Leave just room for 1 more byte, then write a 1 byte, followed by another 1 byte."""
    sizes = tuple([32768 - 7 - 7 - 8, 1, 1])
    records = 3
    lengths = (7, 32753 + 7, 0), (32760, 8 + 32760, 0), (32768, 8 + 32768, 0)
    check(
        with_datastore,
        chunk_sizes=sizes,
        expected_records=records,
        expected_record_sizes=lengths,
    )
