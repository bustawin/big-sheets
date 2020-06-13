import inspect

import punq

Scope = punq.Scope


class Registry(punq.Registry):
    def register_concrete_service(self, service, scope):
        # Fixes https://github.com/bobthemighty/punq/issues/37
        if not inspect.isclass(service):
            raise punq.InvalidRegistrationException(
                "The service %s can't be registered as its own implementation"
                % (repr(service))
            )
        self[service].append(
            punq.Registration(
                service, scope, service, self._get_needs_for_ctor(service), {}
            )
        )


class Container(punq.Container):
    def __init__(self):
        self.registrations = Registry()
        self.register(Container, instance=self)
        self._singletons = {}
