import unittest
from research.gap_window_20261113 import pairwise_lags,effective_n
class TestGap(unittest.TestCase):
 def test_gaps(self):
  self.assertEqual([v[1] for v in pairwise_lags([0,1,3,4],[0.,1.,3.,4.],2)],[2,1])
 def test_perfect_linear(self):
  self.assertAlmostEqual(pairwise_lags([0,1,2,3],[0.,1.,2.,3.],1)[0][2],1)
 def test_independent(self): self.assertEqual(effective_n(100,[0]),100)
 def test_correlated(self): self.assertEqual(effective_n(100,[0.5,0]),50)
 def test_duplicate(self):
  with self.assertRaises(ValueError): pairwise_lags([1,1],[2.,3.],1)
