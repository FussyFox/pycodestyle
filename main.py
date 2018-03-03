"""Lambda function that executes pycodestyle, a static file linter."""
import json
import os
import tarfile
import tempfile
import time
from io import BytesIO
from subprocess import Popen, PIPE, STDOUT

import boto3
import jwt
from botocore.vendored import requests


my_env = os.environ.copy()
PYTHONPATH = 'PYTHONPATH'
my_env[PYTHONPATH] = ":".join([
    os.path.dirname(os.path.realpath(__file__)),
    my_env.get(PYTHONPATH, ''),
])

ARCHIVE_URL = 'https://api.github.com/repos/{owner}/{repo}/tarball/{sha}'
STATUS_URL = 'https://api.github.com/repos/{owner}/{repo}/statuses/{sha}'

PEM = os.environ.get('PEM')

S3_REGION = 'eu-west-1'
S3 = boto3.client('s3', region_name=S3_REGION)
BUCKET = os.environ['BUCKET']

INTEGRATION_ID = os.environ.get('INTEGRATION_ID')

STANDARD = 'PEP8'

CMD = 'pycodestyle'
CMD_ARGS = [
    '.',
]


def get_hook(event):
    """Get GitHub web hook data from full SNS message."""
    return json.loads(event['Records'][0]['Sns']['Message'])


def download_code(owner, repo, sha, token):
    """Download code to local filesystem storage."""
    archive_url = ARCHIVE_URL.format(owner=owner, repo=repo, sha=sha)
    headers = {
        'Authorization': 'token %s' % token
    }
    response = requests.get(archive_url, headers=headers)
    with BytesIO() as bs:
        bs.write(response.content)
        bs.seek(0)
        path = tempfile.mktemp()
        with tarfile.open(fileobj=bs, mode='r:gz') as fs:
            fs.extractall(path)
        folder = os.listdir(path)[0]
        return os.path.join(path, folder)


def parse_hook(hook):
    """
    Parse GitHub web hook and return relevant data.

    Returns:
        tuple[str, str, str]: Return owner, repository name and commit hash.

    """
    repo = hook['repository']['name']
    owner = hook['repository']['owner']['login']
    sha = None
    try:
        # Hooks is push event
        sha = hook['head_commit']['id']
    except KeyError:
        # Hook is pull request event
        code_has_changed = hook['action'] in [
            "opened", "edited", "reopened"
        ]
        is_onwer = hook['pull_request']['user']['login'] == owner
        if code_has_changed and not is_onwer:
            sha = hook['pull_request']['head']['sha']
    return owner, repo, sha


def get_token(installation_id):
    """Get OAuth access token from GibHub via the installations API."""
    now = int(time.time())
    exp = 300
    payload = {
        # issued at time
        'iat': now,
        # JWT expiration time
        'exp': now + exp,
        # Integration's GitHub identifier
        'iss': INTEGRATION_ID
    }
    bearer = jwt.encode(payload, PEM, algorithm='RS256')
    headers = {
        'Accept': 'application/vnd.github.machine-man-preview+json',
        'Authorization': 'Bearer %s' % bearer.decode(encoding='UTF-8')
    }
    url = (
        'https://api.github.com/installations/'
        '%s/access_tokens' % installation_id
    )
    res = requests.post(url, headers=headers)
    return res.json()['token']


def run_process(owner, repo, sha, code_path):
    """
    Run linter command as sub-processes.

    Returns:
        tuple[int, str]: Tuple containing exit code and URI to log file.

    """
    process = Popen(
        ['python', '-m', CMD] + CMD_ARGS,
        stdout=PIPE, stderr=STDOUT,
        cwd=code_path, env=my_env,
    )
    process.wait()
    log = process.stdout.read()

    key = os.path.join(CMD, owner, repo, "%s.log" % sha)
    S3.put_object(
        ACL='public-read',
        Bucket=BUCKET,
        Key=key,
        Body=log,
        ContentType='text/plain'
    )
    return (
        process.returncode,
        "https://{0}.s3.amazonaws.com/{1}".format(BUCKET, key),
    )


def handle(event, context):
    """AWS Lambda function handler."""
    hook = get_hook(event)
    owner, repo, sha = parse_hook(hook)

    if sha is None:
        return  # Do not execute linter.

    installation_id = hook['installation']['id']
    status_url = STATUS_URL.format(owner=owner, repo=repo, sha=sha)
    token = get_token(installation_id)
    headers = {'Authorization': 'token %s' % token}
    data = {
        "state": "pending",
        "context": STANDARD,
    }
    requests.post(status_url, json=data, headers=headers).raise_for_status()

    code_path = download_code(owner, repo, sha, token)
    code, data["target_url"] = run_process(owner, repo, sha, code_path)

    if code == 0:
        data.update({
            "state": "success",
            "description": "%s succeeded!" % CMD,
        })
    else:
        data.update({
            "state": "failure",
            "description": "%s failed!" % CMD,
        })

    requests.post(status_url, json=data, headers=headers).raise_for_status()
