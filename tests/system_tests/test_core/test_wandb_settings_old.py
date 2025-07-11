from unittest import mock

import tracklab


def test__global_path_None(user, test_settings):  # noqa: N802
    # test that we don't crash if we can't find a global path to write settings to
    with mock.patch("tracklab.old.settings.Settings._global_path", return_value=None):
        run = tracklab.init(settings=test_settings())
        run.finish()
        assert tracklab.old.settings.Settings._global_path() is None
        assert run is not None
