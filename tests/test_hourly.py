import unittest

from src.hourly import MIN_N, comparable, delta, hourly, share


def row(day, minute, behavior, cam="front_cam_1"):
    return {"day": str(day), "minute": str(minute), "behavior": behavior, "cameras": cam}


class HourlyTests(unittest.TestCase):
    def setUp(self):
        rows = [row(1, 10, "feeding"), row(1, 20, "lying"), row(1, 65, "standing", "back_cam"),
                row(2, 70, "feeding")]
        self.data = hourly(rows)

    def test_hour_bucket_and_shares(self):
        self.assertEqual(self.data[1][0]["n"], 2)
        self.assertEqual(share(self.data[1][0], "feeding"), 50.0)
        self.assertEqual(share(self.data[1][1], "standing"), 100.0)

    def test_empty_hour_has_no_share(self):
        self.assertIsNone(share(self.data[2][0], "feeding"))
        self.assertIsNone(delta(self.data, 0, "feeding"))

    def test_front_cam_counts_exclude_back_cam(self):
        self.assertEqual(self.data[1][1]["front"], 0)
        self.assertEqual(self.data[2][1]["front_feeding"], 1)

    def test_small_samples_not_comparable(self):
        self.assertFalse(comparable(self.data, 1))
        self.assertGreater(MIN_N, 4)


if __name__ == "__main__":
    unittest.main()
