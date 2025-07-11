import unittest.mock

import tracklab
import tracklab.sdk.verify.verify as wandb_verify
from tracklab.apis import InternalApi


def test_check_logged_in(user):
    internal_api = unittest.mock.MagicMock(spec=InternalApi)
    internal_api.api_key = None
    assert not wandb_verify.check_logged_in(internal_api, "localhost:8000")

    run = tracklab.init()
    assert wandb_verify.check_logged_in(InternalApi(), run.settings.base_url)
    run.finish()
