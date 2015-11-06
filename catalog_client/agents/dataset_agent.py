# Report dataset state and configuration
# Report nodes
# Report node versions

# Note: Only run one instance of this collector.  It grabs cluster-wide
# information and reports it.

from os import environ

import yaml
import treq

from twisted.internet.defer import gatherResults
from twisted.python.filepath import FilePath

from .agentlib import get_client


class _Collector(object):
    def __init__(self, flocker_client, base_url):
        self._client = flocker_client
        self._base_url = base_url

    def collect(self):
        d1 = self._client.get(self._base_url + "/configuration/datasets")
        d1.addCallback(treq.json_content)

        d2 = self._client.get(self._base_url + "/state/datasets")
        d2.addCallback(treq.json_content)

        d3 = self._client.get(self._base_url + "/state/nodes")
        d3.addCallback(treq.json_content)

        ds = [d1, d2, d3]

        d = gatherResults(ds)
        d.addCallback(
            lambda (config, state, nodes): dict(
                config=config, state=state, nodes=nodes,
            )
        )
        return d

def collector():
    config_path = FilePath(environ[b"FLOCKER_CONFIGURATION_PATH"])
    with config_path.child(b"agent.yml").open() as config:
        agent_config = yaml.load(config.read())
        target_hostname = agent_config[u"control-service"][u"hostname"]

    return _Collector(
        flocker_client=get_client(
            certificates_path=config_path,
            user_key_filename="user.key",
            user_certificate_filename="user.crt",
        ),
        base_url="https://{hostname}:4523/v1".format(hostname=target_hostname),
    )