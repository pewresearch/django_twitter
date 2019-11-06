# TODO: if you ever get the unit test to successfully toggle the override itself
#  then you can use this code to make sure that it's all working okay
# import copy
#
# from django.test import TestCase as DjangoTestCase, override_settings
# from django.conf import settings
#
# # https://stackoverflow.com/questions/31705420/unit-test-to-check-for-ungenerated-migrations
#
#
# @override_settings(
#     TWITTER_APP="testapp",
#     MIGRATION_MODULES={
#         "testapp": "testapp.migrations.testapp_models",
#         "django_twitter": None,
#     },
# )
# class TestAppMigrationsCheck(DjangoTestCase):
#     def setUp(self):
#         print("WOOT2")
#         from django.utils import translation
#
#         self.saved_locale = translation.get_language()
#         translation.deactivate_all()
#
#     def tearDown(self):
#         if self.saved_locale is not None:
#             from django.utils import translation
#
#             translation.activate(self.saved_locale)
#
#     def test_missing_migrations(self):
#         from django.db import connection
#         from django.apps.registry import apps
#         from django.db.migrations.executor import MigrationExecutor
#
#         executor = MigrationExecutor(connection)
#         from django.db.migrations.autodetector import MigrationAutodetector
#         from django.db.migrations.state import ProjectState
#
#         autodetector = MigrationAutodetector(
#             executor.loader.project_state(), ProjectState.from_apps(apps)
#         )
#         changes = autodetector.changes(graph=executor.loader.graph)
#         self.assertEqual({}, changes)
#
#
# #
# # @override_settings(
# #     TWITTER_APP="django_twitter",
# #     MIGRATION_MODULES={"testapp": "testapp.migrations.django_twitter_models"},
# # )
# # class DjangoTwitterMigrationsCheck(DjangoTestCase):
# #     def setUp(self):
# #         from django.utils import translation
# #
# #         self.saved_locale = translation.get_language()
# #         translation.deactivate_all()
# #         import django
# #
# #         django.setup()
# #
# #     def tearDown(self):
# #         if self.saved_locale is not None:
# #             from django.utils import translation
# #
# #             translation.activate(self.saved_locale)
# #
# #     def test_missing_migrations(self):
# #         from django.db import connection
# #         from django.apps.registry import apps
# #         from django.db.migrations.executor import MigrationExecutor
# #
# #         executor = MigrationExecutor(connection)
# #         from django.db.migrations.autodetector import MigrationAutodetector
# #         from django.db.migrations.state import ProjectState
# #
# #         autodetector = MigrationAutodetector(
# #             executor.loader.project_state(), ProjectState.from_apps(apps)
# #         )
# #         changes = autodetector.changes(graph=executor.loader.graph)
# #         import pdb
# #
# #         pdb.set_trace()
# #         self.assertEqual({}, changes)
