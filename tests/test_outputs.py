from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
str = type('')


import sys
from time import sleep, time
try:
    from math import isclose
except ImportError:
    from gpiozero.compat import isclose

import pytest

from gpiozero.pins.mock import MockPin, MockPWMPin
from gpiozero import *


def teardown_function(function):
    MockPin.clear_pins()

def test_output_initial_values():
    pin = MockPin(2)
    with OutputDevice(pin, initial_value=False) as device:
        assert pin.function == 'output'
        assert not pin.state
    with OutputDevice(pin, initial_value=True) as device:
        assert pin.state
        state = pin.state
    with OutputDevice(pin, initial_value=None) as device:
        assert state == pin.state

def test_output_write_active_high():
    pin = MockPin(2)
    with OutputDevice(pin) as device:
        device.on()
        assert pin.state
        device.off()
        assert not pin.state

def test_output_write_active_low():
    pin = MockPin(2)
    with OutputDevice(pin, active_high=False) as device:
        device.on()
        assert not pin.state
        device.off()
        assert pin.state

def test_output_write_closed():
    with OutputDevice(MockPin(2)) as device:
        device.close()
        assert device.closed
        device.close()
        assert device.closed
        with pytest.raises(GPIODeviceClosed):
            device.on()

def test_output_write_silly():
    pin = MockPin(2)
    with OutputDevice(pin) as device:
        pin.function = 'input'
        with pytest.raises(AttributeError):
            device.on()

def test_output_value():
    pin = MockPin(2)
    with OutputDevice(pin) as device:
        assert not device.value
        assert not pin.state
        device.on()
        assert device.value
        assert pin.state
        device.value = False
        assert not device.value
        assert not pin.state

def test_output_digital_toggle():
    pin = MockPin(2)
    with DigitalOutputDevice(pin) as device:
        assert not device.value
        assert not pin.state
        device.toggle()
        assert device.value
        assert pin.state
        device.toggle()
        assert not device.value
        assert not pin.state

@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'),
                    reason='timing is too random on pypy')
def test_output_blink_background():
    pin = MockPin(2)
    with DigitalOutputDevice(pin) as device:
        start = time()
        device.blink(0.1, 0.1, n=2)
        assert isclose(time() - start, 0, abs_tol=0.05)
        device._blink_thread.join() # naughty, but ensures no arbitrary waits in the test
        assert isclose(time() - start, 0.4, abs_tol=0.05)
        pin.assert_states_and_times([
            (0.0, False),
            (0.0, True),
            (0.1, False),
            (0.1, True),
            (0.1, False)
            ])

@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'),
                    reason='timing is too random on pypy')
def test_output_blink_foreground():
    pin = MockPin(2)
    with DigitalOutputDevice(pin) as device:
        start = time()
        device.blink(0.1, 0.1, n=2, background=False)
        assert isclose(time() - start, 0.4, abs_tol=0.05)
        pin.assert_states_and_times([
            (0.0, False),
            (0.0, True),
            (0.1, False),
            (0.1, True),
            (0.1, False)
            ])

def test_output_blink_interrupt_on():
    pin = MockPin(2)
    with DigitalOutputDevice(pin) as device:
        device.blink(1, 0.1)
        sleep(0.2)
        device.off() # should interrupt while on
        pin.assert_states([False, True, False])

def test_output_blink_interrupt_off():
    pin = MockPin(2)
    with DigitalOutputDevice(pin) as device:
        device.blink(0.1, 1)
        sleep(0.2)
        device.off() # should interrupt while off
        pin.assert_states([False, True, False])

def test_output_pwm_bad_initial_value():
    with pytest.raises(ValueError):
        PWMOutputDevice(MockPin(2), initial_value=2)

def test_output_pwm_not_supported():
    with pytest.raises(AttributeError):
        PWMOutputDevice(MockPin(2))

def test_output_pwm_states():
    pin = MockPWMPin(2)
    with PWMOutputDevice(pin) as device:
        device.value = 0.1
        device.value = 0.2
        device.value = 0.0
        pin.assert_states([0.0, 0.1, 0.2, 0.0])

def test_output_pwm_read():
    pin = MockPWMPin(2)
    with PWMOutputDevice(pin, frequency=100) as device:
        assert device.frequency == 100
        device.value = 0.1
        assert isclose(device.value, 0.1)
        assert isclose(pin.state, 0.1)
        assert device.is_active
        device.frequency = None
        assert not device.value
        assert not device.is_active
        assert device.frequency is None

def test_output_pwm_write():
    pin = MockPWMPin(2)
    with PWMOutputDevice(pin) as device:
        device.on()
        device.off()
        pin.assert_states([False, True, False])

def test_output_pwm_toggle():
    pin = MockPWMPin(2)
    with PWMOutputDevice(pin) as device:
        device.toggle()
        device.value = 0.5
        device.value = 0.1
        device.toggle()
        device.off()
        pin.assert_states([False, True, 0.5, 0.1, 0.9, False])

def test_output_pwm_active_high_read():
    pin = MockPWMPin(2)
    with PWMOutputDevice(pin, active_high=False) as device:
        device.value = 0.1
        assert isclose(device.value, 0.1)
        assert isclose(pin.state, 0.9)
        device.frequency = None
        assert device.value

def test_output_pwm_bad_value():
    with pytest.raises(ValueError):
        PWMOutputDevice(MockPWMPin(2)).value = 2

def test_output_pwm_write_closed():
    device = PWMOutputDevice(MockPWMPin(2))
    device.close()
    with pytest.raises(GPIODeviceClosed):
        device.on()

def test_output_pwm_write_silly():
    pin = MockPWMPin(2)
    with PWMOutputDevice(pin) as device:
        pin.function = 'input'
        with pytest.raises(AttributeError):
            device.off()

@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'),
                    reason='timing is too random on pypy')
def test_output_pwm_blink_background():
    pin = MockPWMPin(2)
    with PWMOutputDevice(pin) as device:
        start = time()
        device.blink(0.1, 0.1, n=2)
        assert isclose(time() - start, 0, abs_tol=0.05)
        device._blink_thread.join()
        assert isclose(time() - start, 0.4, abs_tol=0.05)
        pin.assert_states_and_times([
            (0.0, 0),
            (0.0, 1),
            (0.1, 0),
            (0.1, 1),
            (0.1, 0)
            ])

@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'),
                    reason='timing is too random on pypy')
def test_output_pwm_blink_foreground():
    pin = MockPWMPin(2)
    with PWMOutputDevice(pin) as device:
        start = time()
        device.blink(0.1, 0.1, n=2, background=False)
        assert isclose(time() - start, 0.4, abs_tol=0.05)
        pin.assert_states_and_times([
            (0.0, 0),
            (0.0, 1),
            (0.1, 0),
            (0.1, 1),
            (0.1, 0)
            ])

@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'),
                    reason='timing is too random on pypy')
def test_output_pwm_fade_background():
    pin = MockPWMPin(2)
    with PWMOutputDevice(pin) as device:
        start = time()
        device.blink(0, 0, 0.2, 0.2, n=2)
        assert isclose(time() - start, 0, abs_tol=0.05)
        device._blink_thread.join()
        assert isclose(time() - start, 0.8, abs_tol=0.05)
        pin.assert_states_and_times([
            (0.0, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            ])

@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'),
                    reason='timing is too random on pypy')
def test_output_pwm_fade_foreground():
    pin = MockPWMPin(2)
    with PWMOutputDevice(pin) as device:
        start = time()
        device.blink(0, 0, 0.2, 0.2, n=2, background=False)
        assert isclose(time() - start, 0.8, abs_tol=0.05)
        pin.assert_states_and_times([
            (0.0, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            ])

@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'),
                    reason='timing is too random on pypy')
def test_output_pwm_pulse_background():
    pin = MockPWMPin(2)
    with PWMOutputDevice(pin) as device:
        start = time()
        device.pulse(0.2, 0.2, n=2)
        assert isclose(time() - start, 0, abs_tol=0.05)
        device._blink_thread.join()
        assert isclose(time() - start, 0.8, abs_tol=0.05)
        pin.assert_states_and_times([
            (0.0, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            ])

@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'),
                    reason='timing is too random on pypy')
def test_output_pwm_pulse_foreground():
    pin = MockPWMPin(2)
    with PWMOutputDevice(pin) as device:
        start = time()
        device.pulse(0.2, 0.2, n=2, background=False)
        assert isclose(time() - start, 0.8, abs_tol=0.05)
        pin.assert_states_and_times([
            (0.0, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            ])

@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'),
                    reason='timing is too random on pypy')
def test_output_pwm_pulse_background():
    pin = MockPWMPin(2)
    with PWMOutputDevice(pin) as device:
        device.pulse(0.2, 0.2, n=2)
        device._blink_thread.join()
        pin.assert_states_and_times([
            (0.0, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            ])

@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'),
                    reason='timing is too random on pypy')
def test_output_pwm_pulse_foreground():
    pin = MockPWMPin(2)
    with PWMOutputDevice(pin) as device:
        device.pulse(0.2, 0.2, n=2, background=False)
        pin.assert_states_and_times([
            (0.0, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            ])

def test_output_pwm_blink_interrupt():
    pin = MockPWMPin(2)
    with PWMOutputDevice(pin) as device:
        device.blink(1, 0.1)
        sleep(0.2)
        device.off() # should interrupt while on
        pin.assert_states([0, 1, 0])

def test_rgbled_missing_pins():
    with pytest.raises(ValueError):
        RGBLED()

def test_rgbled_initial_value():
    r, g, b = (MockPWMPin(i) for i in (1, 2, 3))
    with RGBLED(r, g, b, initial_value=(0.1, 0.2, 0)) as device:
        assert r.frequency
        assert g.frequency
        assert b.frequency
        assert isclose(r.state, 0.1)
        assert isclose(g.state, 0.2)
        assert isclose(b.state, 0.0)

def test_rgbled_value():
    r, g, b = (MockPWMPin(i) for i in (1, 2, 3))
    with RGBLED(r, g, b) as device:
        assert not device.is_active
        assert device.value == (0, 0, 0)
        device.on()
        assert device.is_active
        assert device.value == (1, 1, 1)
        device.off()
        assert not device.is_active
        assert device.value == (0, 0, 0)

def test_rgbled_toggle():
    r, g, b = (MockPWMPin(i) for i in (1, 2, 3))
    with RGBLED(r, g, b) as device:
        assert not device.is_active
        assert device.value == (0, 0, 0)
        device.toggle()
        assert device.is_active
        assert device.value == (1, 1, 1)
        device.toggle()
        assert not device.is_active
        assert device.value == (0, 0, 0)

@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'),
                    reason='timing is too random on pypy')
def test_rgbled_blink_background():
    r, g, b = (MockPWMPin(i) for i in (1, 2, 3))
    with RGBLED(r, g, b) as device:
        start = time()
        device.blink(0.1, 0.1, n=2)
        assert isclose(time() - start, 0, abs_tol=0.05)
        device._blink_thread.join()
        assert isclose(time() - start, 0.4, abs_tol=0.05)
        expected = [
            (0.0, 0),
            (0.0, 1),
            (0.1, 0),
            (0.1, 1),
            (0.1, 0)
            ]
        r.assert_states_and_times(expected)
        g.assert_states_and_times(expected)
        b.assert_states_and_times(expected)

@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'),
                    reason='timing is too random on pypy')
def test_rgbled_blink_foreground():
    r, g, b = (MockPWMPin(i) for i in (1, 2, 3))
    with RGBLED(r, g, b) as device:
        start = time()
        device.blink(0.1, 0.1, n=2, background=False)
        assert isclose(time() - start, 0.4, abs_tol=0.05)
        expected = [
            (0.0, 0),
            (0.0, 1),
            (0.1, 0),
            (0.1, 1),
            (0.1, 0)
            ]
        r.assert_states_and_times(expected)
        g.assert_states_and_times(expected)
        b.assert_states_and_times(expected)

@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'),
                    reason='timing is too random on pypy')
def test_rgbled_fade_background():
    r, g, b = (MockPWMPin(i) for i in (1, 2, 3))
    with RGBLED(r, g, b) as device:
        start = time()
        device.blink(0, 0, 0.2, 0.2, n=2)
        assert isclose(time() - start, 0, abs_tol=0.05)
        device._blink_thread.join()
        assert isclose(time() - start, 0.8, abs_tol=0.05)
        expected = [
            (0.0, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            ]
        r.assert_states_and_times(expected)
        g.assert_states_and_times(expected)
        b.assert_states_and_times(expected)

@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'),
                    reason='timing is too random on pypy')
def test_rgbled_fade_foreground():
    r, g, b = (MockPWMPin(i) for i in (1, 2, 3))
    with RGBLED(r, g, b) as device:
        start = time()
        device.blink(0, 0, 0.2, 0.2, n=2, background=False)
        assert isclose(time() - start, 0.8, abs_tol=0.05)
        expected = [
            (0.0, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            ]
        r.assert_states_and_times(expected)
        g.assert_states_and_times(expected)
        b.assert_states_and_times(expected)

@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'),
                    reason='timing is too random on pypy')
def test_rgbled_pulse_background():
    r, g, b = (MockPWMPin(i) for i in (1, 2, 3))
    with RGBLED(r, g, b) as device:
        start = time()
        device.pulse(0.2, 0.2, n=2)
        assert isclose(time() - start, 0, abs_tol=0.05)
        device._blink_thread.join()
        assert isclose(time() - start, 0.8, abs_tol=0.05)
        expected = [
            (0.0, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            ]
        r.assert_states_and_times(expected)
        g.assert_states_and_times(expected)
        b.assert_states_and_times(expected)

@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'),
                    reason='timing is too random on pypy')
def test_rgbled_pulse_foreground():
    r, g, b = (MockPWMPin(i) for i in (1, 2, 3))
    with RGBLED(r, g, b) as device:
        start = time()
        device.pulse(0.2, 0.2, n=2, background=False)
        assert isclose(time() - start, 0.8, abs_tol=0.05)
        expected = [
            (0.0, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            (0.04, 0.2),
            (0.04, 0.4),
            (0.04, 0.6),
            (0.04, 0.8),
            (0.04, 1),
            (0.04, 0.8),
            (0.04, 0.6),
            (0.04, 0.4),
            (0.04, 0.2),
            (0.04, 0),
            ]
        r.assert_states_and_times(expected)
        g.assert_states_and_times(expected)
        b.assert_states_and_times(expected)

def test_rgbled_blink_interrupt():
    r, g, b = (MockPWMPin(i) for i in (1, 2, 3))
    with RGBLED(r, g, b) as device:
        device.blink(1, 0.1)
        sleep(0.2)
        device.off() # should interrupt while on
        r.assert_states([0, 1, 0])
        g.assert_states([0, 1, 0])
        b.assert_states([0, 1, 0])

def test_rgbled_close():
    r, g, b = (MockPWMPin(i) for i in (1, 2, 3))
    with RGBLED(r, g, b) as device:
        assert not device.closed
        device.close()
        assert device.closed
        device.close()
        assert device.closed

def test_motor_missing_pins():
    with pytest.raises(ValueError):
        Motor()

def test_motor_pins():
    f = MockPWMPin(1)
    b = MockPWMPin(2)
    with Motor(f, b) as device:
        assert device.forward_device.pin is f
        assert device.backward_device.pin is b

def test_motor_close():
    f = MockPWMPin(1)
    b = MockPWMPin(2)
    with Motor(f, b) as device:
        device.close()
        assert device.closed
        assert device.forward_device.pin is None
        assert device.backward_device.pin is None
        device.close()
        assert device.closed

def test_motor_value():
    f = MockPWMPin(1)
    b = MockPWMPin(2)
    with Motor(f, b) as device:
        device.value = -1
        assert device.is_active
        assert device.value == -1
        assert b.state == 1 and f.state == 0
        device.value = 1
        assert device.is_active
        assert device.value == 1
        assert b.state == 0 and f.state == 1
        device.value = 0.5
        assert device.is_active
        assert device.value == 0.5
        assert b.state == 0 and f.state == 0.5
        device.value = 0
        assert not device.is_active
        assert not device.value
        assert b.state == 0 and f.state == 0

def test_motor_bad_value():
    f = MockPWMPin(1)
    b = MockPWMPin(2)
    with Motor(f, b) as device:
        with pytest.raises(ValueError):
            device.value = 2

def test_motor_reverse():
    f = MockPWMPin(1)
    b = MockPWMPin(2)
    with Motor(f, b) as device:
        device.forward()
        assert device.value == 1
        assert b.state == 0 and f.state == 1
        device.reverse()
        assert device.value == -1
        assert b.state == 1 and f.state == 0

