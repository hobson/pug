import os.environ

from jira.client import JIRA

from django.core.management.base import BaseCommand, CommandError

# FIXME, these should be imported and settable in settings.py
JIRA_URI = os.environ.get('JIRA_URI', 'https://jira.sharplabs.com')
# os.environ.setdefault('JIRA_URI', JIRA_URI)
CRED_PATH = '/home/Hobson/.jira.cred'
try:
    with open(CRED_PATH, 'Ur') as fpin:
        JIRA_UN, JIRA_PW = (fpin.readline(), fpin.readline())
except:
    JIRA_UN = os.environ.get('JIRA_UN', 'admin')
    JIRA_PW = os.environ.get('JIRA_PW', 'admin')



class Command(BaseCommand):
    help = ("Creates a Jira issue.")
    jira = JIRA(server=JIRA_URI, basic_auth=(JIRA_UN, JIRA_PW))
    projects = jira.projects()
    # do this in __init__?
    try:
        project = (p for p in jira.projects() if p.key == 'SASBD').next()
    except:
        project = jira.projects()[0]

    def handle(self, summary=None, description=None, typ='Bug', project='SASBD', *args, **options):

        if description:
            description = str(description)

        if not summary:
            if not description:
                raise CommandError("You must provide an issue title or name or short description")
            else:
                summary = str(description)[:min(len(description), 76)] + '...'

        description = str(description or summary) 
        self.jira.create_issue(project={'key': project}, summary=summary,
                               description=description, issuetype={'name': typ})

