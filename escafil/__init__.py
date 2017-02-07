import json
import requests
from urllib.parse import urljoin

CLUSTER_URL = 'https://kubernetes.default'
CLUSTER_CACERT_PATH = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'
CLUSTER_TOKEN_PATH = '/var/run/secrets/kubernetes.io/serviceaccount/token'


def validate_namespace(cls, namespace):
    if namespace and not cls.namespaced:
        raise ValueError('{} is not namespaced'.format(cls.__name__))

    return namespace


class Kubernetes:
    def __init__(self, url=None, cacert=None, token=None, in_cluster=False):
        if in_cluster:
            self.url = CLUSTER_URL
            self.cacert = CLUSTER_CACERT_PATH
            with open(CLUSTER_TOKEN_PATH, 'r') as f:
                self.token = f.read()
        else:
            self.url = url
            self.cacert = cacert
            self.token = token

    def request(self, method, path, *args, **kwargs):
        url = urljoin(self.url, path)

        kwargs['headers'] = kwargs.get('headers', {})

        if self.token:
            kwargs['headers']['authorization'] = (
                'Bearer {}'.format(self.token)
            )

        if self.cacert:
            kwargs['verify'] = self.cacert

        resp = requests.request(method, url, *args, **kwargs)

        if not resp.status_code < 400:
            raise KubernetesError(resp.json()['message'], resp)

        return resp

    def resource_url(
        self, api, collection=None, name=None, namespace=None,
        subresource=None
    ):
        components = [api]
        if namespace:
            components.extend(['namespaces', namespace])
        if collection:
            components.append(collection)
        if name:
            if not collection:
                raise ValueError(
                    'collection is required for URLs with names'
                )
            components.append(name)
        if subresource:
            components.append(subresource)
        return '/' + '/'.join(components)

    def get(self, cls, name, namespace=None):
        namespace = validate_namespace(cls, namespace)
        return cls(self, {
            'metadata': {
                'name': name,
                'namespace': namespace,
            }
        }).refresh()

    def create(self, cls, body, namespace=None):
        namespace = validate_namespace(cls, namespace)
        url = self.resource_url(
            cls.api,
            collection=cls.collection,
            namespace=namespace,
        )
        resp = self.request(
            'POST',
            url,
            data=json.dumps(body),
            headers={'content-type': 'application/json'},
        )
        return cls(self, resp.json())

    def list(
        self, cls, field_selector=None, label_selector=None, namespace=None
    ):
        namespace = validate_namespace(cls, namespace)

        params = {}

        if field_selector is not None:
            params['fieldSelector'] = field_selector

        if label_selector is not None:
            params['labelSelector'] = label_selector

        url = self.resource_url(
            cls.api,
            collection=cls.collection,
            namespace=namespace,
        )
        resp = self.request('GET', url, params=params)
        items = resp.json()['items'] or []
        return [cls(self, item) for item in items]


class KubernetesError(Exception):
    def __init__(self, message, response):
        self.message = message
        self.response = response


class APIObjectMeta(type):
    def __init__(cls, name, bases, dict_):
        super(APIObjectMeta, cls).__init__(name, bases, dict_)

        if name == 'APIObject':
            return

        if not cls.collection:
            cls.collection = name.lower() + 's'


class APIObject(metaclass=APIObjectMeta):
    api = 'api/v1'
    collection = None
    namespaced = True

    def __init__(self, client, data):
        self.client = client
        self.data = data

    def __getitem__(self, *args, **kwargs):
        return self.data.__getitem__(*args, **kwargs)

    def name(self):
        return self['metadata']['name']

    def uid(self):
        return self['metadata']['uid']

    def namespace(self):
        return self['metadata'].get('namespace')

    def labels(self):
        return self['metadata'].get('labels', {})

    def annotations(self):
        return self['metadata'].get('annotations', {})

    def url(self):
        return self.client.resource_url(
            self.api,
            collection=self.collection,
            name=self.name(),
            namespace=self.namespace(),
        )

    def refresh(self):
        self.data = self.client.request('GET', self.url()).json()
        return self

    def patch(self, patch):
        headers = {'content-type': 'application/strategic-merge-patch+json'}
        self.client.request(
            'PATCH', self.url(), headers=headers, data=json.dumps(patch)
        )

    def delete(self, data=None):
        headers = {'content-type': 'application/json'}

        if data:
            data = json.dumps(data)

        self.client.request(
            'DELETE', self.url(), headers=headers, data=data
        )

    def __repr__(self):
        return '<{} "{}">'.format(
            self.__class__.__name__,
            self.name(),
        )
