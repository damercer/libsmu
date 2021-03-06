from __future__ import print_function, division

from itertools import chain
import sys
import time

import pytest

from pysmu import Session, SampleDrop, DeviceError
from misc import prompt


def _add_device(session):
    if session.scan() == 0:
        # no devices plugged in
        raise ValueError

    session.add(session.available_devices[0])
    return session, session.devices[0]


# single device session fixture
@pytest.fixture(scope='function')
def session(request):
    s = Session(add_all=False)
    s, _ = _add_device(s)
    yield s

    # force session destruction
    s._close()


@pytest.fixture(scope='function')
def device(session):
    return session.devices[0]


def test_read_continuous_dataflow_ignore(session, device):
    """Verify workflows that lead to data flow issues are ignored by default."""
    session.start(0)
    time.sleep(.5)
    # by default, data flow issues are ignored so no exception should be raised here
    samples = device.read(1000)
    assert len(samples) == 1000


def test_read_continuous_dataflow_raises():
    """Verify workflows that lead to data flow issues."""
    # create a session that doesn't ignore data flow issues
    session = Session(add_all=False, ignore_dataflow=False)
    session.scan()
    session.add(session.available_devices[0])
    device = session.devices[0]

    session.start(0)
    time.sleep(.5)
    with pytest.raises(SampleDrop):
        device.read(1000)

    # force session destruction
    session._close()


def test_read_continuous_large_request(session, device):
    """Request more samples than fits in the read queues under default settings in continuous mode."""
    session.start(0)

    samples = device.read(100000, -1)
    assert len(samples) == 100000

    samples = device.read(100000, 100)
    assert len(samples) > 0


def test_read_noncontinuous_large_request(device):
    """Request more samples than fits in the read queues under default settings in non-continuous mode.

    Internally, pysmu splits up the request into sizes smaller than the
    internal queue size, runs all the separate requests, and then returns the
    data.
    """
    samples = device.get_samples(100000)
    assert len(samples) == 100000


def test_read_continuous_timeout(session, device):
    """Verify read calls with timeouts work in continuous mode."""
    session.start(0)

    # Grab 1000 samples with a timeout of 110ms.
    samples = device.read(1000, 110)

    # Which should be long enough to get all 1000 samples.
    assert len(samples) == 1000


def _read_hotplug(session, device, status):
    """Verify no stalls when unplugging a device during reads."""
    printed = False
    num_samples = 0
    start = time.time()
    if status == 'continuous':
        session.start(0)

    with pytest.raises(DeviceError) as excinfo:
        while True:
            if time.time() - start > 10:
                pytest.fail('failed to unplug the device within 10 seconds')

            if status == 'continuous':
                samples = device.read(10000, -1)
            else:
                samples = device.get_samples(10000)
            num_samples += len(samples)

            if not printed:
                print('\nACTION: unplug the device within 10 seconds')
                printed = True

            sys.stdout.write('\rreceived samples: {}'.format(num_samples))
            sys.stdout.flush()

    assert 'device detached' == str(excinfo.value)

    sys.stdout.write('\n')
    prompt('plug the device back in')
    session, device = _add_device(session)


@pytest.mark.interactive
def test_read_noncontinuous_hotplug(session, device):
    """Verify no stalls when unplugging a device during noncontinuous reads."""
    _read_hotplug(session, device, 'noncontinuous')


@pytest.mark.interactive
def test_read_continuous_hotplug(session, device):
    """Verify no stalls when unplugging a device during continuous reads."""
    _read_hotplug(session, device, 'continuous')


@pytest.mark.interactive
def test_read_initial_data():
    """Verify data values of HI-Z samples on initial attach.

    See https://github.com/analogdevicesinc/m1k-fw/issues/9 for details.
    """
    sys.stdout.write('\n')
    prompt('unplug the device, ground the metal USB connector, and plug it back in')

    # create our own session to avoid detach exceptions
    session = Session(add_all=False)
    session, device = _add_device(session)

    samples = device.get_samples(100)
    assert len(samples) == 100

    # verify all samples are near 0
    tests = []
    for sample in samples:
        for x in chain.from_iterable(sample):
            tests.append(abs(round(x)) == 0)

    # old firmware versions exhibit bad data, newer versions should fix the issue
    if float(device.fwver) <= 2.10:
        assert not all(tests)
    else:
        assert all(tests)

    # request a bunch of extra samples to flush bad values
    device.get_samples(10000)
    # force session destruction
    session._close()


@pytest.mark.long
def test_read_continuous_sample_rates(session, device):
    """Verify streaming HI-Z data values and speed from 100 kSPS to 10 kSPS every ~5k SPS."""
    sample_count = 0

    failures = []
    failure_vals = []
    failure_samples = []
    sys.stdout.write('\n')

    for rate in range(100, 5, -5):
        sample_count = long(0)
        failure = False
        session.sample_rate = rate * 1000
        sample_rate = session.sample_rate

        # Make sure the session got configured properly.
        if sample_rate < 0:
            print("failed to configure session: {}".format(sample_rate))
            continue

        # Verify we're within the minimum configurable range from the specified target.
        assert abs((rate * 1000) - sample_rate) <= 256
        sys.stdout.write("running test at {} SPS: ".format(sample_rate))

        start = time.time()
        session.start(0)

        while True:
            end = time.time()
            clk_diff = end - start
            # Run each session for a minute.
            if clk_diff > 60:
                break

            # Grab 1000 samples in a non-blocking fashion in HI-Z mode.
            samples = device.read(1000)

            # Which all should be near 0.
            for sample in samples:
                sample_count += 1
                for x in chain.from_iterable(sample):
                    if abs(round(x)) != 0:
                        failure = True
                        failure_vals.append(x)
                        failure_samples.append(sample_count)

                # show output progress per second
                if sample_count % sample_rate == 0:
                    if failure:
                        failure = False
                        sys.stdout.write('#')
                    else:
                        sys.stdout.write('*')
                    sys.stdout.flush()

        sys.stdout.write('\n')

        failures.append(len(failure_samples))

        # check if bad sample values were received and display them if any exist
        if failure_samples:
            print("{} bad sample(s):".format(len(failure_samples)))
            for i, x in enumerate(failure_samples):
                print("sample: {}, expected: 0, received: {}".format(x, failure_vals[i]))

        failure_samples = []
        failure_vals = []

        samples_per_second = int(round(sample_count / clk_diff))
        # Verify we're running within 250 SPS of the configured sample rate.
        sample_rate_diff = int(samples_per_second - sample_rate)
        assert abs(sample_rate_diff) <= 250
        print("received {} samples in {} seconds: ~{} SPS ({} SPS difference)".format(
            sample_count, int(round(clk_diff)), samples_per_second, sample_rate_diff))

        # Stop the session.
        session.end()

    # fail test if any sample rates returned bad values
    assert not any(failures)
