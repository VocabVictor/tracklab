import shutil
import tempfile
from pathlib import Path

import pytest
import tracklab
from tracklab.apis.importers import validation
from tracklab.apis.importers.internals.internal import ImporterRun, RecordMaker
from tracklab.apis.importers.internals.util import for_each, parallelize

@pytest.fixture
def setup_dirs(request):
    config = request.param
    src_dir = Path(tempfile.mkdtemp())
    dst_dir = Path(tempfile.mkdtemp())

    # Populate directories based on the test case
    for filename, content, directory in config.get("create_files", []):
        dir_path = src_dir if directory == "src" else dst_dir
        file_path = dir_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)

    for subdir, directory in config.get("create_subdirs", []):
        dir_path = src_dir if directory == "src" else dst_dir
        subdir_path = dir_path / subdir
        subdir_path.mkdir(parents=True, exist_ok=True)

    yield src_dir, dst_dir, config["expected"]

    shutil.rmtree(src_dir)
    shutil.rmtree(dst_dir)

def test_parallelize():
    def safe_func(x):
        return x + 1

    result = set(parallelize(safe_func, [1, 2, 3]))
    expected = set([2, 3, 4])

    assert result == expected

    def unsafe_func(x):
        if x > 2:
            raise Exception("test")
        return x

    result = set(parallelize(unsafe_func, [1, 2, 3]))
    expected = set([1, 2, None])

    assert result == expected

def test_for_each():
    def safe_func(x):
        return x + 1

    result = set(for_each(safe_func, [1, 2, 3]))
    expected = set([2, 3, 4])
    assert result == expected

    result = set(for_each(safe_func, [1, 2, 3], parallel=True))
    expected = set([2, 3, 4])
    assert result == expected

    def unsafe_func(x):
        if x > 2:
            raise Exception("test")
        return x

    result = set(for_each(unsafe_func, [1, 2, 3]))
    expected = set([1, 2, None])
    assert result == expected

    result = set(for_each(unsafe_func, [1, 2, 3], parallel=True))
    expected = set([1, 2, None])
    assert result == expected

@pytest.mark.parametrize(
    "setup_dirs",
    [
        # 1. Src has an extra file
        {
            "create_files": [("unique_src_file.txt", "Content in source", "src")],
            "expected": {
                "left_only": ["unique_src_file.txt"],
                "right_only": [],
                "diff_files": [],
                "subdir_differences": {},
            },
        },
        # 2. Dst has an extra file
        {
            "create_files": [("unique_dst_file.txt", "Content in destination", "dst")],
            "expected": {
                "left_only": [],
                "right_only": ["unique_dst_file.txt"],
                "diff_files": [],
                "subdir_differences": {},
            },
        },
        # 3. Both have the same file with different content (commented for now; not sure why this fails in CI)
        # {
        #     "create_files": [
        #         ("common_file.txt", "Src content", "src"),
        #         ("common_file.txt", "Dst content", "dst"),
        #     ],
        #     "expected": {
        #         "left_only": [],
        #         "right_only": [],
        #         "diff_files": ["common_file.txt"],
        #         "subdir_differences": {},
        #     },
        # },
        # 4. Src has an extra file in a subdir
        {
            "create_subdirs": [("subdir", "src"), ("subdir", "dst")],
            "create_files": [("subdir/unique_src_file.txt", "Subdir content", "src")],
            "expected": {
                "left_only": [],
                "right_only": [],
                "diff_files": [],
                "subdir_differences": {
                    "subdir": {
                        "left_only": ["unique_src_file.txt"],
                        "right_only": [],
                        "diff_files": [],
                        "subdir_differences": {},
                    }
                },
            },
        },
    ],
    indirect=True,
)
# def test_compare_artifact_dirs(setup_dirs): # Artifact test removed
#     src_dir, dst_dir, expected = setup_dirs # Artifact test removed
#     differences = validation._compare_artifact_dirs(src_dir, dst_dir) # Artifact test removed
#  # Artifact test removed
#     assert set(differences["left_only"]) == set(expected["left_only"]) # Artifact test removed
#     assert set(differences["right_only"]) == set(expected["right_only"]) # Artifact test removed
#     assert set(differences["diff_files"]) == set(expected["diff_files"]) # Artifact test removed
#     assert differences["subdir_differences"] == expected["subdir_differences"] # Artifact test removed
#  # Artifact test removed
#  # Artifact test removed
@pytest.mark.parametrize(
    "file_setup, expected_problems",
    [
        # 1. No mismatch
        ((("test.txt", "content"), ("test.txt", "content")), set()),
        # 2. Digest mismatch and missing manifest entry due to different filenames
        (
            (("test.txt", "content"), ("test2.txt", "content")),
            {"digest mismatch", "missing manifest entry"},
        ),
        # 3. Digest mismatch and entry mismatch due to different content in the same file
        (
            (("test.txt", "content"), ("test.txt", "content2")),
            {"digest mismatch", "manifest entry mismatch"},
        ),
    ],
)
# def test_artifact_manifest_entry_mismatches(tmp_path, file_setup, expected_problems): # Artifact test removed
#     src_file, dst_file = file_setup # Artifact test removed
#     src_filename, src_content = src_file # Artifact test removed
#     dst_filename, dst_content = dst_file # Artifact test removed
#  # Artifact test removed
#     # Create and add file to source artifact # Artifact test removed
#     src_path = tmp_path / src_filename # Artifact test removed
#     src_path.write_text(src_content) # Artifact test removed
#     src_art = tracklab.Artifact("src_artifact", type="dataset") # Artifact test removed
#     src_art.add_file(str(src_path)) # Artifact test removed
#  # Artifact test removed
#     # Create and add file to destination artifact # Artifact test removed
#     dst_path = tmp_path / dst_filename # Artifact test removed
#     dst_path.write_text(dst_content) # Artifact test removed
#     dst_art = tracklab.Artifact("dst_artifact", type="dataset") # Artifact test removed
#     dst_art.add_file(str(dst_path)) # Artifact test removed
#  # Artifact test removed
#     # Compare artifacts and collect problems # Artifact test removed
#     problems = validation._compare_artifact_manifests(src_art, dst_art) # Artifact test removed
#     problems_set = set(problems) # Artifact test removed
#  # Artifact test removed
#     for p in expected_problems: # Artifact test removed
#         assert any(p in problem for problem in problems_set) # Artifact test removed
#  # Artifact test removed
#  # Artifact test removed
def test_make_metadata_file_even_if_not_importing_files():
    class TestingRun(ImporterRun): ...

    run = TestingRun()
    rm = RecordMaker(run)

    rec = rm._make_files_record(artifacts=False, files=False, media=False, code=False)
    files = rec.files.files

    # Make sure the metadata file is created
    assert len(files) == 1
    assert "wandb-metadata.json" in files[0].path
