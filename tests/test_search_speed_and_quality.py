import unittest
import time
from app.services.search_service import get_search_service

class TestSearchSpeedAndQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.svc = get_search_service()

    def test_company_suggestions_speed(self):
        t0 = time.time()
        res_empty = self.svc.get_suggestions("company", "")
        t_empty = (time.time() - t0) * 1000
        self.assertGreater(len(res_empty), 0, "Empty company suggestions should return prominent companies")
        self.assertLess(t_empty, 150.0, f"Empty company suggestions took {t_empty:.2f}ms, should be < 150ms")

        t1 = time.time()
        res_q = self.svc.get_suggestions("company", "swi")
        t_q = (time.time() - t1) * 1000
        self.assertGreater(len(res_q), 0, "Query 'swi' should match Swiggy")
        self.assertLess(t_q, 50.0, f"Filtered company suggestions took {t_q:.2f}ms, should be < 50ms")

    def test_role_suggestions_speed(self):
        t0 = time.time()
        res_empty = self.svc.get_suggestions("role", "")
        t_empty = (time.time() - t0) * 1000
        self.assertGreater(len(res_empty), 0, "Empty role suggestions should return verified categories")
        self.assertLess(t_empty, 100.0, f"Empty role suggestions took {t_empty:.2f}ms, should be < 100ms")

        t1 = time.time()
        res_q = self.svc.get_suggestions("role", "soft")
        t_q = (time.time() - t1) * 1000
        self.assertTrue(any("Software" in r["label"] for r in res_q))
        self.assertLess(t_q, 50.0, f"Filtered role suggestions took {t_q:.2f}ms, should be < 50ms")

    def test_role_synonym_normalization(self):
        syns_space = set(self.svc.get_role_synonyms("Full Stack"))
        syns_hyphen = set(self.svc.get_role_synonyms("full-stack"))
        syns_compact = set(self.svc.get_role_synonyms("fullstack"))

        self.assertTrue("full stack" in syns_space)
        self.assertTrue("full stack" in syns_hyphen)
        self.assertTrue("full stack" in syns_compact)

    def test_intern_word_boundaries(self):
        syns_intern = self.svc.get_role_synonyms("intern")
        from app.services.search_service import role_matches
        self.assertTrue(role_matches(syns_intern, "Software Engineering Intern"))
        self.assertFalse(role_matches(syns_intern, "Internal Communications Lead"))
        self.assertFalse(role_matches(syns_intern, "Internet Protocol Engineer"))

    def test_search_jobs_speed_and_results(self):
        t0 = time.time()
        res = self.svc.search_jobs(search_type="role", search_term="software engineer", page=1, page_size=10)
        t_elapsed = (time.time() - t0) * 1000
        self.assertGreater(res["total_count"], 0)
        self.assertLessEqual(len(res["results"]), 10)
        self.assertLess(t_elapsed, 1500.0, f"Search took {t_elapsed:.2f}ms, should be < 1500ms")

if __name__ == "__main__":
    unittest.main()
