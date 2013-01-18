# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Manages dynamic properties of an application and/or its modules.

An application must explicitly declare properties and provide a type, doc string
and default value for each. The default property values are overridden by
the new values found in the environment variable with the same name. Those are
further overridden by the values found in the datastore. We also try to do all
of this with performance in mind.
"""

__author__ = 'Pavel Simakov (psimakov@google.com)'


import logging
import os
from google.appengine.ext import db


class ConfigProperty(object):
    """A property with name, type, doc_string and a default value."""

    def __init__(self, name, value_type, doc_string, default_value=None):
        self._name = name
        self._type = value_type
        self._doc_string = doc_string
        self._default_value = value_type(default_value)
        self._value = None

        Registry.registered[name] = self

    @property
    def name(self):
        return self._name

    @property
    def value_type(self):
        return self._type

    @property
    def doc_string(self):
        return self._doc_string

    @property
    def default_value(self):
        return self._default_value

    @property
    def value(self):
        """Get the latest value from datastore, environment or use default."""
        if not self._value:
            if self._name in os.environ:
                try:
                    return self._type(os.environ[self._name])
                except Exception:  # pylint: disable-msg=broad-except
                    logging.error(
                        'Property %s failed to cast to type %s; removing.',
                        self._name, self._type)
                    del os.environ[self._name]
                    return self._default_value
            else:
                return self._default_value
        return self._type(self._value)


class Registry(object):
    """Holds all registered properties."""
    registered = {}


class ConfigPropertyEntity(db.Model):
    """A class that represents a named configuration property."""
    namespace = db.StringProperty()
    name = db.StringProperty()
    value = db.StringProperty()
    is_draft = db.BooleanProperty()


def run_all_unit_tests():
    """Runs all unit tests for this modules."""
    str_prop = ConfigProperty('gcb-str-prop', str, ('doc for str_prop'), 'foo')
    int_prop = ConfigProperty('gcb-int-prop', int, ('doc for int_prop'), 123)

    assert str_prop.default_value == 'foo'
    assert str_prop.value == 'foo'
    assert int_prop.default_value == 123
    assert int_prop.value == 123

    # Check os.environ override works.
    os.environ[str_prop.name] = 'bar'
    assert str_prop.value == 'bar'
    del os.environ[str_prop.name]
    assert str_prop.value == 'foo'

    # Check os.environ override with type casting.
    os.environ[int_prop.name] = '12345'
    assert int_prop.value == 12345

    # Check setting of value is disallowed.
    try:
        str_prop.value = 'foo'
        raise Exception()
    except AttributeError:
        pass

    # Check value of bad type is disregarded.
    os.environ[int_prop.name] = 'foo bar'
    assert int_prop.value == int_prop.default_value


if __name__ == '__main__':
    run_all_unit_tests()
