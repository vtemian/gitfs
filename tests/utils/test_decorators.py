# Copyright 2014-2016 Presslabs SRL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from threading import Event
from unittest.mock import MagicMock, call, patch

import pytest

from gitfs.utils.decorators.retry import retry
from gitfs.utils.decorators.while_not import while_not


class MockedWraps:
    def __init__(self, f):
        self.f = f

    def __call__(self, f):
        def decorated(*args, **kwargs):
            return f(*args, **kwargs)

        return decorated


class EmptyMock:
    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)


class TestRetryDecorator:
    def test_retry(self):
        mocked_time = MagicMock()
        mocked_method = MagicMock(side_effect=ValueError)

        with patch.multiple(
            "gitfs.utils.decorators.retry", wraps=MockedWraps, time=mocked_time
        ):
            again = retry(times=3)

            with pytest.raises(ValueError):
                again(mocked_method)("arg", kwarg="kwarg")

            mocked_time.sleep.assert_has_calls([call(3), call(3), call(3)])
            mocked_method.assert_has_calls([call("arg", kwarg="kwarg")])


class TestWhileNotDecorator:
    def test_while_not_with_invalid_event_type(self):
        mocked_method = MagicMock()
        mocked_self = EmptyMock(obj="obj")

        with patch.multiple("gitfs.utils.decorators.while_not", wraps=MockedWraps):
            with pytest.raises(TypeError):
                not_now = while_not("obj")
                not_now(mocked_method)(mocked_self, "arg", kwarg="kwarg")

    def test_while_not(self):
        an_event = Event()
        an_event.set()

        mocked_method = MagicMock()
        mocked_time = MagicMock()

        mocked_time.sleep.side_effect = lambda x: an_event.clear()
        mocked_method.__name__ = "name"

        with patch.multiple(
            "gitfs.utils.decorators.while_not", wraps=MockedWraps, time=mocked_time
        ):
            not_now = while_not(an_event)
            not_now(mocked_method)("arg", kwarg="kwarg")

            mocked_time.sleep.assert_called_once_with(0.2)
