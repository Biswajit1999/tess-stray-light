import numpy as np
import pytest
from cadence_exposure import window_duty_cycle, weighted_flux_mean

def test_disjoint_duty():
    assert window_duty_cycle([0, 2], [1, 3], 0, 4) == pytest.approx(.5)

def test_overlapping_intervals_not_double_counted():
    assert window_duty_cycle([0, .5], [1, 1.5], 0, 2) == pytest.approx(.75)

def test_clipped_intervals():
    assert window_duty_cycle([-1, 1], [.5, 3], 0, 2) == pytest.approx(.75)

def test_weighted_mean_and_error():
    mean, se = weighted_flux_mean([1, 3], [1, 1], [1, 1], [True, True])
    assert mean == pytest.approx(2)
    assert se == pytest.approx(1/np.sqrt(2))

def test_mask_exclusion():
    assert weighted_flux_mean([1, 100], [1, 1], [1, 1], [True, False]) == (1., 1.)

def test_invalid_mask():
    with pytest.raises(ValueError):
        weighted_flux_mean([1, 2], [1, 1], [1, 1], [0, 1])
