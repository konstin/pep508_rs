from collections import namedtuple
import pytest
from unittest import mock

from pep508_rs import Requirement, MarkerEnvironment, Pep508Error, VersionSpecifier


def test_pep508():
    req = Requirement("numpy; python_version >= '3.7'")
    assert req.name == "numpy"
    env = MarkerEnvironment.current()
    assert req.evaluate_markers(env, [])
    req2 = Requirement("numpy; python_version < '3.7'")
    assert not req2.evaluate_markers(env, [])

    requests = Requirement(
        'requests [security,tests] >=2.8.1, ==2.8.* ; python_version > "3.8"'
    )
    assert requests.name == "requests"
    assert requests.extras == ["security", "tests"]
    assert requests.version_or_url == [
        VersionSpecifier(">=2.8.1"),
        VersionSpecifier("==2.8.*"),
    ]
    assert requests.marker == "python_version > '3.8'"


def test_marker():
    env = MarkerEnvironment.current()
    assert not Requirement("numpy; extra == 'science'").evaluate_markers(env, [])
    assert Requirement("numpy; extra == 'science'").evaluate_markers(env, ["science"])
    assert not Requirement(
        "numpy; extra == 'science' and extra == 'arrays'"
    ).evaluate_markers(env, ["science"])
    assert Requirement(
        "numpy; extra == 'science' or extra == 'arrays'"
    ).evaluate_markers(env, ["science"])


def check_marker_values():
    import sys
    import os
    import platform

    env = MarkerEnvironment.current()
    assert env.implementation_name == sys.implementation.name
    lib = env.implementation_version.version

    runtime = sys.implementation.version
    assert lib.major == runtime.major
    assert lib.minor == runtime.minor
    assert lib.micro == runtime.micro
    # assert lib.releaselevel == runtime.releaselevel
    # assert lib.serial == runtime.serial

    assert env.os_name == os.name
    assert env.platform_machine == platform.machine()
    assert env.platform_python_implementation == platform.python_implementation()
    assert env.platform_release == platform.release()
    assert env.platform_system == platform.system()
    assert env.python_full_version.string == platform.python_version()
    assert env.python_version.string == f"{lib.major}.{lib.minor}"
    assert env.sys_platform == sys.platform


class FakeVersionInfo(
    namedtuple("FakeVersionInfo", ["major", "minor", "micro", "releaselevel", "serial"])
):
    pass


def test_marker_values_on_final_release():
    fake_version = FakeVersionInfo(3, 10, 11, "final", 0)
    with mock.patch("sys.implementation.version", fake_version):
        check_marker_values()

    check_marker_values()


def test_marker_values_on_release_candidate():
    fake_version = FakeVersionInfo(3, 10, 11, "rc", 1)
    with mock.patch("sys.implementation.version", fake_version):
        check_marker_values()


def test_errors():
    with pytest.raises(
        Pep508Error,
        match="Expected an alphanumeric character starting the extra name, found 'ö'",
    ):
        Requirement("numpy[ö]; python_version < '3.7'")


def test_warnings(caplog):
    env = MarkerEnvironment.current()
    assert not Requirement("numpy; '3.6' < '3.7'").evaluate_markers(env, [])
    assert caplog.messages == [
        "Comparing two quoted strings with each other doesn't make sense: "
        "'3.6' < '3.7', evaluating to false"
    ]
    caplog.clear()
    assert not Requirement("numpy; 'a' < 'b'").evaluate_markers(env, [])
    assert caplog.messages == [
        "Comparing two quoted strings with each other doesn't make sense: "
        "'a' < 'b', evaluating to false"
    ]
    caplog.clear()
    Requirement("numpy; python_version >= '3.9.'").evaluate_markers(env, [])
    assert caplog.messages == [
        "Expected PEP 440 version to compare with python_version, found '3.9.', "
        "evaluating to false: Version `3.9.` doesn't match PEP 440 rules"
    ]
    caplog.clear()
    # pickleshare 0.7.5
    Requirement("numpy; python_version in '2.6 2.7 3.2 3.3'").evaluate_markers(env, [])
    assert caplog.messages == [
        "Expected PEP 440 version to compare with python_version, found '2.6 2.7 3.2 3.3', "
        "evaluating to false: Version `2.6 2.7 3.2 3.3` doesn't match PEP 440 rules"
    ]

