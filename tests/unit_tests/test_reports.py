"""Test reports module - disabled as BetaReport no longer exists in local-only TrackLab."""

# import json
# from unittest import mock
# 
# import pytest
# import tracklab
# from tracklab import Api
# # from tracklab.apis.public.reports import BetaReport  # Removed - BetaReport no longer exists
# 
# # All tests are disabled since BetaReport class no longer exists in local-only TrackLab
# 
# # @pytest.mark.usefixtures("patch_apikey", "patch_prompt")
# # def test_report_properties_from_path():
# #     """Test that BetaReport properties work correctly when created via from_path."""
# #     path = "test/test/reports/My-Report--XYZ"
# #     with mock.patch.object(wandb, "login", mock.MagicMock()):
# #         report = Api().from_path(path)
# #
# #         assert report.id is not None
# #         assert isinstance(report.name, (str, type(None)))
# #         assert isinstance(report.display_name, (str, type(None)))
# #         assert isinstance(report.description, (str, type(None)))
# #         assert isinstance(report.user, (dict, type(None)))
# #         assert isinstance(report.spec, (dict, type(None)))
# #         assert isinstance(report.updated_at, (str, type(None)))
# #         assert isinstance(report.created_at, (str, type(None)))
# #         assert isinstance(report.url, (str, type(None)))
# 
# # Additional test functions commented out...