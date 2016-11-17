Escafil
~~~~~~~

Escafil is a minimal client for the Kubernetes API::

    from escafil import Kubernetes, APIObject

    kube = Kubernetes('http://localhost:8001')

    class Pod(APIObject):
        pass

    kube.list(Pod)
    pod = kube.get(Pod, 'my-pod', namespace='default')
    print(pod['spec']['containers'][0]['name'])

The API is not yet stable; use at your own risk.
