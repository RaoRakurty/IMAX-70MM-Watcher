import unittest
from watcher import best_blocks, seats_from_html, showtimes_from_html


class WatcherTests(unittest.TestCase):
    def test_showtime_parse(self):
        h = '''<a href="/TicketSeatMap/?TheaterId=207&amp;ShowtimeId=641727&amp;CinemarkMovieId=104867&amp;Showtime=2026-09-18T19:15:00">go</a>'''
        xs = showtimes_from_html(h, "104867")
        self.assertEqual(len(xs), 1)
        self.assertEqual(xs[0].showtime_id, "641727")
        self.assertEqual(xs[0].theater_id, "207")

    def test_seat_and_center_block(self):
        buttons = []
        for col, num in enumerate(range(8, 15), start=1):
            available = num in (11, 12)
            cls = "seatAvailable seatBlock" if available else "seatBlock"
            buttons.append(
                f'<button class="{cls}" available="{str(available)}" info="H,{num},8,{col},999"></button>'
            )
        seats = seats_from_html("".join(buttons))
        blocks = best_blocks(seats, ["H"], 2, 0.8)
        self.assertTrue(blocks)
        self.assertEqual(blocks[0]["labels"], ["H11", "H12"])


if __name__ == "__main__":
    unittest.main()
