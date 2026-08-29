"""
ATS Compatibility Scoring Service.

Heuristic-based scoring engine that evaluates CV text for ATS
(Applicant Tracking System) compatibility. No AI calls needed.
"""
from __future__ import annotations

import re
from collections import Counter


STANDARD_SECTION_HEADERS = {
    "experience", "work experience", "professional experience", "employment",
    "education", "academic background",
    "skills", "technical skills", "core competencies",
    "summary", "professional summary", "objective", "career objective",
    "contact", "contact information",
    "certifications", "certificates", "licenses",
    "projects", "publications", "awards", "languages", "references",
}

PROFESSIONAL_KEYWORDS = {
    "managed", "developed", "led", "implemented", "designed", "created",
    "improved", "analyzed", "coordinated", "delivered", "achieved",
    "increased", "reduced", "optimized", "built", "launched", "trained",
    "supervised", "collaborated", "negotiated", "resolved", "maintained",
    "organized", "planned", "executed", "evaluated", "presented",
    "proficient", "experienced", "responsible", "team", "project",
}

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"[\+]?[\d\s\-\(\)]{7,15}")
LOCATION_KEYWORDS = {
    "city", "state", "country", "address", "location",
    "cairo", "egypt", "remote", "new york", "london", "dubai",
}


class ATSScoringService:

    def score(self, cv_text: str, job_description: str = "") -> dict:
        if not cv_text or not cv_text.strip():
            return {
                "overall_score": 0,
                "section_scores": {
                    "keyword_density": 0,
                    "section_headers": 0,
                    "contact_info": 0,
                    "formatting": 0,
                    "length": 0,
                },
                "recommendations": ["Upload a CV to get an ATS compatibility score."],
            }

        scores = {
            "keyword_density": self._score_keywords(cv_text, job_description),
            "section_headers": self._score_section_headers(cv_text),
            "contact_info": self._score_contact_info(cv_text),
            "formatting": self._score_formatting(cv_text),
            "length": self._score_length(cv_text),
        }

        weights = {
            "keyword_density": 0.30,
            "section_headers": 0.25,
            "contact_info": 0.15,
            "formatting": 0.15,
            "length": 0.15,
        }
        overall = sum(scores[k] * weights[k] for k in scores)

        recommendations = self._generate_recommendations(scores, cv_text, job_description)

        return {
            "overall_score": round(overall),
            "section_scores": scores,
            "recommendations": recommendations,
        }

    def _score_keywords(self, cv_text: str, job_description: str) -> int:
        cv_lower = cv_text.lower()
        cv_words = set(re.findall(r"\b[a-z]{3,}\b", cv_lower))

        if job_description.strip():
            jd_words = re.findall(r"\b[a-z]{3,}\b", job_description.lower())
            jd_counter = Counter(jd_words)
            top_jd_words = {w for w, _ in jd_counter.most_common(30) if len(w) > 3}
            stop = {"the", "and", "for", "with", "that", "this", "from", "have", "will", "been", "your", "they", "what", "about", "which", "when", "their"}
            top_jd_words -= stop
            if not top_jd_words:
                return 50
            overlap = cv_words & top_jd_words
            ratio = len(overlap) / len(top_jd_words)
            return min(100, round(ratio * 120))

        found = cv_words & PROFESSIONAL_KEYWORDS
        ratio = len(found) / max(len(PROFESSIONAL_KEYWORDS) * 0.4, 1)
        return min(100, round(ratio * 100))

    def _score_section_headers(self, cv_text: str) -> int:
        lines = cv_text.split("\n")
        found_headers = set()
        for line in lines:
            cleaned = line.strip().lower().rstrip(":")
            if cleaned in STANDARD_SECTION_HEADERS:
                found_headers.add(cleaned)
            elif any(h in cleaned for h in STANDARD_SECTION_HEADERS if len(h) > 4):
                found_headers.add(cleaned)

        essential = {"experience", "education", "skills"}
        essential_found = sum(
            1 for e in essential
            if any(e in h for h in found_headers)
        )

        base = (essential_found / len(essential)) * 70
        bonus = min(30, len(found_headers) * 6)
        return min(100, round(base + bonus))

    def _score_contact_info(self, cv_text: str) -> int:
        score = 0
        if EMAIL_PATTERN.search(cv_text):
            score += 40
        if PHONE_PATTERN.search(cv_text):
            score += 30
        cv_lower = cv_text.lower()
        if any(kw in cv_lower for kw in LOCATION_KEYWORDS):
            score += 30
        return min(100, score)

    def _score_formatting(self, cv_text: str) -> int:
        score = 100
        lines = cv_text.split("\n")

        special_char_ratio = sum(1 for c in cv_text if c in "★●◆►▪◉✓✗⟶→←↑↓") / max(len(cv_text), 1)
        if special_char_ratio > 0.01:
            score -= 30

        long_lines = sum(1 for l in lines if len(l) > 120)
        if long_lines > len(lines) * 0.3:
            score -= 20

        empty_ratio = sum(1 for l in lines if not l.strip()) / max(len(lines), 1)
        if empty_ratio > 0.5:
            score -= 15

        if any(len(l) > 200 for l in lines):
            score -= 15

        return max(0, score)

    def _score_length(self, cv_text: str) -> int:
        word_count = len(cv_text.split())
        if word_count < 100:
            return 20
        if word_count < 200:
            return 50
        if word_count < 400:
            return 75
        if word_count <= 1000:
            return 100
        if word_count <= 1500:
            return 85
        if word_count <= 2000:
            return 70
        return 40

    def _generate_recommendations(self, scores: dict, cv_text: str, job_description: str) -> list[str]:
        recs = []

        if scores["section_headers"] < 60:
            recs.append("Add clear section headers: Experience, Education, Skills. ATS systems rely on these to parse your CV.")

        if scores["contact_info"] < 70:
            missing = []
            if not EMAIL_PATTERN.search(cv_text):
                missing.append("email address")
            if not PHONE_PATTERN.search(cv_text):
                missing.append("phone number")
            if missing:
                recs.append(f"Add your {' and '.join(missing)} — most ATS systems require contact information.")

        if scores["keyword_density"] < 50:
            if job_description:
                recs.append("Your CV is missing key terms from the job description. Mirror the exact language used in the posting.")
            else:
                recs.append("Include more action verbs and professional keywords (managed, developed, implemented, etc.).")

        if scores["formatting"] < 70:
            recs.append("Simplify formatting — avoid special characters and keep lines under 120 characters for better ATS parsing.")

        if scores["length"] < 60:
            word_count = len(cv_text.split())
            if word_count < 300:
                recs.append("Your CV seems short. Aim for 400-1000 words to provide enough detail for ATS keyword matching.")
            else:
                recs.append("Your CV may be too long. Consider trimming to 1-2 pages (400-1000 words) for optimal ATS processing.")

        if not recs:
            recs.append("Your CV has good ATS compatibility. Keep it updated with relevant keywords for each application.")

        return recs


ats_scoring_service = ATSScoringService()
