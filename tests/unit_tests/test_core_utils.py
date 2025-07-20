"""Tests for TrackLab core utilities (research/experiment management)."""

import pytest
from datetime import datetime
import tempfile
import shutil

from tracklab.core.utils import (
    parse_research_path,
    list_researches,
    list_experiments,
    get_experiment_runs,
    find_latest_run,
    get_research_summary,
    validate_research_name,
    validate_experiment_name,
)
from tracklab.core.storage import DataStore, data_store_context
from tracklab.core.core_records import RunRecord


class TestParseResearchPath:
    """Test parsing research/experiment paths."""
    
    @pytest.mark.parametrize(
        "path, expected_research, expected_experiment",
        [
            # Valid paths
            ("paper1/baseline", "paper1", "baseline"),
            ("deep-learning-2024/exp1", "deep-learning-2024", "exp1"),
            ("research_v2/ablation_study", "research_v2", "ablation_study"),
            # Invalid paths
            ("", "", ""),
            ("single_component", "", ""),
            ("too/many/components", "", ""),
            ("/leading_slash", "", ""),
            ("trailing_slash/", "", ""),
            # Paths with spaces (should be trimmed)
            (" paper1 / exp1 ", "paper1", "exp1"),
        ],
    )
    def test_parse_research_path_variations(self, path, expected_research, expected_experiment):
        """Test parse_research_path with various input combinations."""
        research, experiment = parse_research_path(path)
        assert research == expected_research
        assert experiment == expected_experiment


class TestResearchManagement:
    """Test research and experiment management functions."""
    
    @pytest.fixture
    def temp_datastore(self):
        """Create a temporary datastore for testing."""
        temp_dir = tempfile.mkdtemp()
        with data_store_context(temp_dir) as store:
            yield store
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def populated_datastore(self, temp_datastore):
        """Create a datastore with sample research data."""
        store = temp_datastore
        
        # Create sample runs across different researches and experiments
        test_runs = [
            # Research: "nlp-paper-2024"
            RunRecord(
                run_id="nlp-001",
                research_name="nlp-paper-2024",
                experiment_name="baseline-bert",
                display_name="BERT Baseline",
                start_time=datetime(2024, 1, 10, 9, 0),
                tags=["baseline", "bert"]
            ),
            RunRecord(
                run_id="nlp-002",
                research_name="nlp-paper-2024",
                experiment_name="baseline-bert",
                display_name="BERT Baseline with augmentation",
                start_time=datetime(2024, 1, 11, 10, 0),
                tags=["baseline", "bert", "augmented"]
            ),
            RunRecord(
                run_id="nlp-003",
                research_name="nlp-paper-2024",
                experiment_name="improved-roberta",
                display_name="RoBERTa with custom head",
                start_time=datetime(2024, 1, 15, 14, 0),
                tags=["improved", "roberta"]
            ),
            # Research: "cv-paper-2024"
            RunRecord(
                run_id="cv-001",
                research_name="cv-paper-2024",
                experiment_name="resnet50",
                display_name="ResNet50 baseline",
                start_time=datetime(2024, 1, 5, 8, 0),
                tags=["baseline", "resnet"]
            ),
            RunRecord(
                run_id="cv-002",
                research_name="cv-paper-2024",
                experiment_name="efficientnet",
                display_name="EfficientNet-B0",
                start_time=datetime(2024, 1, 20, 16, 0),
                tags=["efficient", "sota"]
            ),
        ]
        
        for run in test_runs:
            store.write_run_record(run)
        
        return store
    
    def test_list_researches(self, populated_datastore):
        """Test listing all research projects."""
        researches = list_researches(populated_datastore)
        assert len(researches) == 2
        assert "nlp-paper-2024" in researches
        assert "cv-paper-2024" in researches
        # Should be sorted
        assert researches == ["cv-paper-2024", "nlp-paper-2024"]
    
    def test_list_experiments_for_research(self, populated_datastore):
        """Test listing experiments within a research."""
        # NLP paper experiments
        nlp_experiments = list_experiments(populated_datastore, "nlp-paper-2024")
        assert len(nlp_experiments) == 2
        assert "baseline-bert" in nlp_experiments
        assert "improved-roberta" in nlp_experiments
        
        # CV paper experiments
        cv_experiments = list_experiments(populated_datastore, "cv-paper-2024")
        assert len(cv_experiments) == 2
        assert "resnet50" in cv_experiments
        assert "efficientnet" in cv_experiments
    
    def test_get_experiment_runs(self, populated_datastore):
        """Test getting runs for a specific experiment."""
        bert_runs = get_experiment_runs(
            populated_datastore, 
            "nlp-paper-2024", 
            "baseline-bert"
        )
        assert len(bert_runs) == 2
        # Should be sorted by time, newest first
        assert bert_runs[0].run_id == "nlp-002"
        assert bert_runs[1].run_id == "nlp-001"
    
    def test_find_latest_run_scenarios(self, populated_datastore):
        """Test finding latest run with different filters."""
        # Latest overall
        latest = find_latest_run(populated_datastore)
        assert latest.run_id == "cv-002"  # Most recent overall
        
        # Latest in NLP research
        latest_nlp = find_latest_run(populated_datastore, research_name="nlp-paper-2024")
        assert latest_nlp.run_id == "nlp-003"
        
        # Latest in specific experiment
        latest_bert = find_latest_run(
            populated_datastore,
            research_name="nlp-paper-2024",
            experiment_name="baseline-bert"
        )
        assert latest_bert.run_id == "nlp-002"
    
    def test_research_summary(self, populated_datastore):
        """Test getting research summary statistics."""
        summary = get_research_summary(populated_datastore, "nlp-paper-2024")
        
        assert summary["research_name"] == "nlp-paper-2024"
        assert summary["num_experiments"] == 2
        assert summary["num_runs"] == 3
        assert set(summary["experiments"]) == {"baseline-bert", "improved-roberta"}
    
    def test_empty_datastore_operations(self, temp_datastore):
        """Test operations on empty datastore."""
        assert list_researches(temp_datastore) == []
        assert list_experiments(temp_datastore, "nonexistent") == []
        assert find_latest_run(temp_datastore) is None
        
        summary = get_research_summary(temp_datastore, "nonexistent")
        assert summary["num_experiments"] == 0
        assert summary["num_runs"] == 0


class TestValidationFunctions:
    """Test name validation functions."""
    
    @pytest.mark.parametrize(
        "name, is_valid",
        [
            # Valid names
            ("paper2024", True),
            ("deep-learning-research", True),
            ("exp_v1.2", True),
            ("NLP-BERT-2024", True),
            ("research123", True),
            # Invalid names
            ("", False),
            ("research/with/slash", False),
            ("a" * 101, False),  # Too long
            ("---", False),  # No alphanumeric
            ("...", False),  # No alphanumeric
            ("research name", True),  # Spaces are allowed
        ],
    )
    def test_validate_research_name(self, name, is_valid):
        """Test research name validation."""
        assert validate_research_name(name) == is_valid
    
    @pytest.mark.parametrize(
        "name, is_valid",
        [
            # Valid experiment names
            ("baseline", True),
            ("exp-v2.1", True),
            ("ablation_study_1", True),
            ("SOTA-model", True),
            # Invalid names (same rules as research)
            ("", False),
            ("exp/test", False),
            ("x" * 101, False),
        ],
    )
    def test_validate_experiment_name(self, name, is_valid):
        """Test experiment name validation."""
        assert validate_experiment_name(name) == is_valid


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def temp_datastore(self):
        """Create a temporary datastore for testing."""
        temp_dir = tempfile.mkdtemp()
        with data_store_context(temp_dir) as store:
            yield store
        shutil.rmtree(temp_dir)
    
    def test_parse_none_path(self):
        """Test parsing None path."""
        assert parse_research_path(None) == ("", "")
    
    def test_runs_with_different_timestamps(self, temp_datastore):
        """Test finding latest run based on timestamps."""
        # Create runs with different timestamps
        run1 = RunRecord(
            run_id="r1",
            research_name="test", 
            experiment_name="exp1",
            start_time=datetime(2024, 1, 1, 10, 0, 0)
        )
        
        run2 = RunRecord(
            run_id="r2", 
            research_name="test", 
            experiment_name="exp1",
            start_time=datetime(2024, 1, 2, 10, 0, 0)  # Later timestamp
        )
        
        run3 = RunRecord(
            run_id="r3", 
            research_name="test", 
            experiment_name="exp2",
            start_time=datetime(2024, 1, 3, 10, 0, 0)  # Latest but different experiment
        )
        
        temp_datastore.write_run_record(run1)
        temp_datastore.write_run_record(run2)
        temp_datastore.write_run_record(run3)
        
        # Test finding latest in specific experiment
        latest = find_latest_run(temp_datastore, 
                               research_name="test",
                               experiment_name="exp1")
        assert latest.run_id == "r2"  # Should find the later one in exp1
        
        # Test finding latest overall in research
        latest_overall = find_latest_run(temp_datastore, research_name="test")
        assert latest_overall.run_id == "r3"  # Should find the latest overall
    
    def test_special_characters_in_names(self, temp_datastore):
        """Test handling special characters in research/experiment names."""
        run = RunRecord(
            run_id="special",
            research_name="research-2024_v1.0",
            experiment_name="exp@1 (test)",
            display_name="Special chars test"
        )
        temp_datastore.write_run_record(run)
        
        researches = list_researches(temp_datastore)
        assert "research-2024_v1.0" in researches
        
        experiments = list_experiments(temp_datastore, "research-2024_v1.0")
        assert "exp@1 (test)" in experiments