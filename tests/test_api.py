# pylint: disable=missing-function-docstring, missing-module-docstring
# pylint: disable=missing-class-docstring, invalid-name, unused-argument

import unittest

from shmelegram import app, db
from shmelegram.rest_api import user, chat, message


class ApiBaseTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def tearDown(self):
        pass
