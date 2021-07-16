#!/usr/bin/env python

"""
This script creates an inventory in Ansible Tower based on information in NetBox.

Add this script as a "custom script" in "Inventory scripts" in Ansible Tower.
Then create a new inventory using the newly added inventory script.
Once executed, the inventory will contain hosts defined in NetBox.

Modify the variables NETBOX_HOST_URL and NETBOX_AUTH_TOKEN according to your NetBox setup.
"""

from __future__ import print_function, unicode_literals

import argparse
from collections import defaultdict
import json
import six

from six.moves.urllib.parse import urlencode, urlparse

if six.PY2:
    from httplib import HTTPSConnection, HTTPConnection
else:
    from http.client import HTTPSConnection, HTTPConnection

NETBOX_HOST_URL = 'https://example.com'
NETBOX_AUTH_TOKEN = '0123456789abcdef0123456789abcdef01234567'


class Device(object):
    """A NetBox device.

    This class implements the data model of a NetBox Device object that
    can be serialised by this module's `NetBoxInventory`.
    """
    default_ssh_port = 22
    default_ssh_user = 'root'
    api_url = '/api/dcim/devices/'

    def __init__(self, ns):
        """Store the namespace.

        Parameters:
            ns:dict The raw data payload for this NetBox object
        """
        self._ns = ns

    @property
    def name(self):
        """The name of this object.

        This is used as the FQDN of the host in Ansible Tower.

        Returns:
            str
        """
        return self._ns['name']

    @property
    def ip_address(self):
        """The primary IP address of this host.

        Returns:
            str
        """
        if self._ns['primary_ip'] is None:
            address = "0.0.0.0"
        else:
            address = self._ns['primary_ip']['address'].split('/')[0]
        return address

    @property
    def platform(self):
        """The platform of this object.

        Returns:
            str
        """
        if self._ns['platform'] is None:
            platform = "undefined"
        else:
            platform = self._ns['platform']['slug']
        return platform

    @property
    def device_role(self):
        """The device role of this object.

        Returns:
            str
        """
        if self._ns['device_role'] is None:
            device_role = "undefined"
        else:
            device_role = self._ns['device_role']['slug']
        return device_role

    @property
    def hostvars(self):
        """The Host Vars associated with this object.

        These are typically used as Ansible Facts in the execution of a Job.

        Returns:
            Dict[str, str]
        """
        return {
            self.name: {
                'ansible_port': self.default_ssh_port,
                'ansible_host': self.ip_address,
                'ansible_user': self.default_ssh_user,
                'netbox_device_role': self.device_role,
                'netbox_platform': self.platform,
                'netbox_tags': [slug_dict['slug'] for slug_dict in self._ns['tags']],
                'netbox_status': self._ns['status']['value']
            }
        }

    def __getitem__(self, item):
        """Attribute queries on this object are delegated to its namespace."""
        return self._ns[item]


class HttpClient(object):
    """A simple HTTP client that is based on the Python 2's stdlib."""

    def __init__(self, host_url, headers=None):
        """Initialise the object with the host URL and any headers to use.

        Parameters:
            host_url:str the URL of the host, e.g. https://tower.local
            headers:Dict any headers to include in the HTTP requests
        """
        url = urlparse(host_url)
        conn_type = HTTPConnection if url.scheme == 'http' else HTTPSConnection
        self.conn = conn_type(url.netloc)
        self.headers = {} if headers is None else headers

    def get(self, path, params=None):
        """Perform a GET request for a given path on the remote host.

        Parameters:
            path:str The URL path
        Returns:
            Response The response object provided by the library.
        """
        encoded_params = urlencode(params or {})
        self.conn.request('GET', path, encoded_params, self.headers)
        return self.conn.getresponse()


class NetBoxInventory(object):
    """A NetBox inventory for the DCIM Device type"""
    grouping = 'site'
    entity_type = Device

    def __init__(self, host_url, token='', http_client=None):
        """Initialise with the host URL, the API Token, and a given client.

        Parameters:
            host_url:str The URL of the host, e.g. https://tower.local
            token:AnyStr A valid NetBox API token
            http_client:HttpClient This module's http client
        """
        headers = {'Authorization': 'Token ' + token} if token else {}
        self.client = http_client or HttpClient(host_url, headers=headers)

    @property
    def entities(self):
        """The entities, i.e. hosts, associated with this inventory.

        Returns:
            Generator[Device, None, None]
        """
        next_path = self.entity_type.api_url
        while next_path:
            response = self.client.get(next_path)
            data = json.load(response)
            next_path = data['next']
            for item in data['results']:
                yield self.entity_type(item)

    def as_ansible_namespace(self):
        """Serialise the objects into an Ansible Tower compatible namespace.

        Objects must implement the following interface:

            class Object:
                @property
                @abstractmethod
                def name(self) -> Text:
                    '''The name of the host, i.e. the FQDN.'''

                @property
                @abstractmethod
                def hostvars(self) -> Dict[str, Dict[str, Dict[str, str]]]:
                    '''The HostVars for this host.'''
        """
        ns = defaultdict(lambda: defaultdict(list))
        _meta_ns = defaultdict(dict)
        for entity in self.entities:
            device_group = entity[self.grouping]['slug']
            ns[device_group]['hosts'] += [entity.name]
            _meta_ns['hostvars'].update(entity.hostvars)
        ns.update({'_meta': _meta_ns})
        return ns


def main():
    """Show help or dump NetBox device information in Ansible format."""

    parser = argparse.ArgumentParser()
    parser.add_argument('--list', dest='list', action='store_true')
    args = parser.parse_args()
    netbox_inv = NetBoxInventory(NETBOX_HOST_URL, token=NETBOX_AUTH_TOKEN)
    if args.list:
        print(json.dumps(netbox_inv.as_ansible_namespace()))
    else:
        parser.print_usage()


if __name__ == '__main__':
    main()
