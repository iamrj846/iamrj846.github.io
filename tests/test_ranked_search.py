import unittest
import re
from app.services.ats_service import generate_job_tags, extract_tags
from app.services.search_service import (
    calculate_ranked_tag_score,
    normalize_search_token,
    EQUIVALENCE_MAP,
    STEM_SYNONYMS
)

class TestRankedTagSemanticSearch(unittest.TestCase):

    def test_twenty_tags_boundary(self):
        """Verify that every job receives exactly 20 relevant tags."""
        test_roles = [
            ("Senior Frontend Developer (React)", "Swiggy", "Bengaluru, India", "Frontend Engineer", "Remote", "Senior"),
            ("Backend Engineer - Java / Spring Boot", "Razorpay", "Bengaluru", "Backend Engineer", "In-Office", "Entry level"),
            ("Full Stack Software Engineer", "Atlassian", "Remote", "Full Stack Engineer", "Remote", "Senior"),
            ("Staff Machine Learning Engineer", "Google", "Hyderabad", "AI / Machine Learning Engineer", "Hybrid", "Senior"),
            ("QA Automation Engineer (Selenium / Cypress)", "Flipkart", "Bengaluru", "QA / SDET", "In-Office", "Entry level"),
            ("Software Engineering Intern 2026", "Microsoft", "Noida", "Intern / Trainee", "In-Office", "Entry level"),
            ("Cloud DevOps Engineer (Kubernetes, AWS)", "Cisco", "Bengaluru", "DevOps / Cloud Engineer", "Hybrid", "Senior")
        ]

        for title, company, loc, role_cat, wp, exp in test_roles:
            tags = generate_job_tags(
                title=title,
                company=company,
                location=loc,
                role_category=role_cat,
                workplace_type=wp,
                experience_level=exp
            )
            self.assertEqual(len(tags), 20, f"Role '{title}' produced {len(tags)} tags instead of 20: {tags}")
            # Ensure no duplicates (case-insensitive)
            lowers = [t.lower() for t in tags]
            self.assertEqual(len(lowers), len(set(lowers)), f"Duplicate tags found in '{title}': {tags}")

    def test_user_four_ranking_cases(self):
        """
        Verify the exact 4 ranking cases specified by user:
        Job 1: Frontend UI UX Design React Angular Engineer ... Full stack (Rank 20)
        Job 2: Backend Java Python Engineer ... test ... Full stack (Rank 20)
        Job 3: Python Backend Java Engineer testing ... Full stack (Rank 20)
        """
        # User specified tags for the 3 jobs
        job1_tags = [
            "frontend", "UI", "UX", "design", "React", "Angular", "Engineer",
            "TypeScript", "JavaScript", "HTML5", "CSS3", "Single Page Applications",
            "State Management", "Senior", "Remote", "Bengaluru", "India", "Responsive Web Design", "Web", "Full stack"
        ]
        job2_tags = [
            "backend", "Java", "Python", "Engineer", "Microservices", "test",
            "REST APIs", "SQL", "Database Design", "System Design", "Scalability",
            "High Availability", "Senior", "Remote", "Bengaluru", "India", "Concurrency", "Caching", "Docker", "Full stack"
        ]
        job3_tags = [
            "Python", "backend", "Java", "Engineer", "testing", "Microservices",
            "REST APIs", "SQL", "Database Design", "System Design", "Scalability",
            "High Availability", "Senior", "Remote", "Bengaluru", "India", "Docker", "Caching", "Kubernetes", "Full stack"
        ]

        # Case 1: Search "Engineer" -> Job 2, Job 3, Job 1
        s1 = calculate_ranked_tag_score("Engineer", job1_tags)
        s2 = calculate_ranked_tag_score("Engineer", job2_tags)
        s3 = calculate_ranked_tag_score("Engineer", job3_tags)
        self.assertGreater(s2, s1, f"Job 2 ({s2}) should outrank Job 1 ({s1}) for 'Engineer'")
        self.assertGreater(s3, s1, f"Job 3 ({s3}) should outrank Job 1 ({s1}) for 'Engineer'")
        self.assertEqual(s2, s3, f"Job 2 ({s2}) and Job 3 ({s3}) should tie on Engineer rank (both Rank 4)")

        # Case 2: Search "Frontend Engineer" -> Job 1, Job 2, Job 3
        fe1 = calculate_ranked_tag_score("Frontend Engineer", job1_tags)
        fe2 = calculate_ranked_tag_score("Frontend Engineer", job2_tags)
        fe3 = calculate_ranked_tag_score("Frontend Engineer", job3_tags)
        self.assertGreater(fe1, fe2, f"Job 1 ({fe1}) should outrank Job 2 ({fe2}) for 'Frontend Engineer'")
        self.assertGreater(fe1, fe3, f"Job 1 ({fe1}) should outrank Job 3 ({fe3}) for 'Frontend Engineer'")

        # Case 3: Search "Tester" -> Job 3, Job 2 (Job 1 excluded)
        t1 = calculate_ranked_tag_score("Tester", job1_tags)
        t2 = calculate_ranked_tag_score("Tester", job2_tags)
        t3 = calculate_ranked_tag_score("Tester", job3_tags)
        self.assertEqual(t1, 0.0, f"Job 1 should score 0 for 'Tester', got {t1}")
        self.assertGreater(t3, t2, f"Job 3 ({t3}) should outrank Job 2 ({t2}) for 'Tester'")
        self.assertGreater(t2, 0.0, f"Job 2 should score > 0 for 'Tester', got {t2}")

        # Case 4: Search "Backend" -> Job 2, Job 3 (Job 1 excluded)
        b1 = calculate_ranked_tag_score("Backend", job1_tags)
        b2 = calculate_ranked_tag_score("Backend", job2_tags)
        b3 = calculate_ranked_tag_score("Backend", job3_tags)
        self.assertEqual(b1, 0.0, f"Job 1 should score 0 for 'Backend', got {b1}")
        self.assertGreater(b2, b3, f"Job 2 ({b2}) should outrank Job 3 ({b3}) for 'Backend'")
        self.assertGreater(b3, 0.0, f"Job 3 should score > 0 for 'Backend', got {b3}")

    def test_equivalence_normalization(self):
        """Verify Full Stack == fullstack == full-stack, etc."""
        tags = ["Full Stack", "React", "Node.js", "TypeScript"] + [f"tag_{i}" for i in range(5, 21)]
        s_space = calculate_ranked_tag_score("Full Stack", tags)
        s_hyphen = calculate_ranked_tag_score("full-stack", tags)
        s_nospace = calculate_ranked_tag_score("fullstack", tags)
        self.assertGreater(s_space, 0.0)
        self.assertEqual(s_space, s_hyphen, "full-stack must yield identical score to Full Stack")
        self.assertEqual(s_space, s_nospace, "fullstack must yield identical score to Full Stack")

        from app.services.search_service import SearchService
        svc = SearchService()
        syns_space = set(svc.get_role_synonyms("Full Stack"))
        syns_hyphen = set(svc.get_role_synonyms("full-stack"))
        syns_nospace = set(svc.get_role_synonyms("fullstack"))
        self.assertTrue("full stack" in syns_space and "full stack" in syns_hyphen and "full stack" in syns_nospace)
        self.assertTrue("fullstack" in syns_space and "fullstack" in syns_hyphen and "fullstack" in syns_nospace)

    def test_strict_negative_word_boundaries(self):
        """Verify intern != internal, internet."""
        # A job with 'internal communications' tags
        internal_tags = ["internal communications", "strategy", "pr", "marketing"] + [f"tag_{i}" for i in range(5, 21)]
        score_intern = calculate_ranked_tag_score("intern", internal_tags, title="Internal Communications Manager")
        self.assertEqual(score_intern, 0.0, f"'intern' must not match 'internal', but got score {score_intern}")

        # A job with 'internet security' tags
        internet_tags = ["internet security", "cybersecurity", "network"] + [f"tag_{i}" for i in range(4, 21)]
        score_internet = calculate_ranked_tag_score("intern", internet_tags, title="Internet Security Engineer")
        self.assertEqual(score_internet, 0.0, f"'intern' must not match 'internet', but got score {score_internet}")

        # A job with genuine 'internship' tags
        intern_tags = ["Internship", "software engineer", "college intern"] + [f"tag_{i}" for i in range(4, 21)]
        score_real_intern = calculate_ranked_tag_score("intern", intern_tags, title="Software Engineering Intern")
        self.assertGreater(score_real_intern, 0.0, "Real intern job must match")

    def test_case_independence(self):
        """Verify search is case independent."""
        tags = ["Python", "Django", "Backend"] + [f"tag_{i}" for i in range(4, 21)]
        s_lower = calculate_ranked_tag_score("python", tags)
        s_title = calculate_ranked_tag_score("Python", tags)
        s_upper = calculate_ranked_tag_score("PYTHON", tags)
        self.assertGreater(s_lower, 0.0)
        self.assertEqual(s_lower, s_title)
        self.assertEqual(s_lower, s_upper)

if __name__ == "__main__":
    unittest.main()
