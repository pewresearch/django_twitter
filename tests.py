import unittest


class NonDBTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_load_app(self):
        from django_pewtils import load_app

        load_app("testapp")

    def tearDown(self):
        pass
