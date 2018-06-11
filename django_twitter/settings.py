import os

# INSTALLED_APPS = ('django_commander', )
APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)).decode('utf-8')).replace('\\', '/')
# DJANGO_COMMANDER_COMMAND_FOLDERS = [
#     os.path.abspath(os.path.join(APP_ROOT, "commands").decode('utf-8')).replace('\\', '/')
# ]