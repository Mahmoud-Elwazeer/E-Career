"""
Test script for the scraper module.
Run with: python test_scraper.py
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Test imports
print("=" * 60)
print("Testing Scraper Module")
print("=" * 60)

# Test 1: Import URL resolver
print("\n1. Testing URL resolver...")
try:
    from apps.scraper.pipeline.url_resolver import is_direct_company_url, extract_domain
    
    # Test blocked domains
    assert is_direct_company_url('https://www.linkedin.com/jobs/view/123') == False, "LinkedIn should be blocked"
    assert is_direct_company_url('https://indeed.com/job/123') == False, "Indeed should be blocked"
    
    # Test allowed ATS
    assert is_direct_company_url('https://boards.greenhouse.io/stripe/jobs/123') == True, "Greenhouse should be allowed"
    assert is_direct_company_url('https://jobs.lever.co/company/123') == True, "Lever should be allowed"
    
    # Test company domain
    assert is_direct_company_url('https://careers.google.com/jobs/123') == True, "Company domain should be allowed"
    
    print("   ✅ URL resolver working correctly")
except Exception as e:
    print(f"   ❌ URL resolver failed: {e}")

# Test 2: Import legitimacy checker
print("\n2. Testing legitimacy checker...")
try:
    from apps.scraper.pipeline.legitimacy import calculate_legitimacy_score, is_legitimate
    
    test_job = {
        'title': 'Software Engineer',
        'description': 'We are looking for a talented software engineer to join our team. You will be working on exciting projects using Python and Django. This is a great opportunity to grow your skills and work with a talented team.',
        'company': 'Google',
    }
    
    score, flags = calculate_legitimacy_score(test_job)
    print(f"   Score: {score}, Flags: {flags}")
    assert score >= 0.6, "Legitimate job should have score >= 0.6"
    
    print("   ✅ Legitimacy checker working correctly")
except Exception as e:
    print(f"   ❌ Legitimacy checker failed: {e}")

# Test 3: Import normalizer
print("\n3. Testing normalizer...")
try:
    from apps.scraper.pipeline.normalizer import (
        normalize_employment_type,
        normalize_experience_level,
        normalize_remote_type,
    )
    
    assert normalize_employment_type('Full-time') == 'full_time', "Full-time should normalize"
    assert normalize_employment_type('Part Time') == 'part_time', "Part Time should normalize"
    assert normalize_employment_type('Contract') == 'contract', "Contract should normalize"
    
    assert normalize_experience_level('Senior') == 'senior', "Senior should normalize"
    assert normalize_experience_level('Junior') == 'entry', "Junior should normalize"
    
    assert normalize_remote_type('Remote') == 'remote', "Remote should normalize"
    assert normalize_remote_type('Hybrid') == 'hybrid', "Hybrid should normalize"
    
    print("   ✅ Normalizer working correctly")
except Exception as e:
    print(f"   ❌ Normalizer failed: {e}")

# Test 4: Import deduplicator
print("\n4. Testing deduplicator...")
try:
    from apps.scraper.pipeline.deduplicator import generate_job_hash, generate_job_slug
    
    job_hash = generate_job_hash({
        'company': 'Google',
        'title': 'Software Engineer',
        'location': 'Mountain View',
    })
    
    assert len(job_hash) == 64, "SHA256 hash should be 64 chars"
    
    slug = generate_job_slug('Google', 'Software Engineer', '123')
    assert 'google' in slug.lower(), "Slug should contain company name"
    
    print("   ✅ Deduplicator working correctly")
except Exception as e:
    print(f"   ❌ Deduplicator failed: {e}")

# Test 5: Import ATS scrapers
print("\n5. Testing ATS scrapers...")
try:
    from apps.scraper.ats.greenhouse import GreenhouseScraper, fetch_greenhouse_jobs
    from apps.scraper.ats.lever import LeverScraper, fetch_lever_jobs
    from apps.scraper.ats.ashby import AshbyScraper, fetch_ashby_jobs
    from apps.scraper.ats.bamboohr import BambooHRScraper, fetch_bamboohr_jobs
    
    # Test Greenhouse scraper instantiation
    scraper = GreenhouseScraper('stripe')
    assert scraper.get_platform_name() == 'greenhouse'
    
    print("   ✅ ATS scrapers imported correctly")
except Exception as e:
    print(f"   ❌ ATS scrapers import failed: {e}")

# Test 6: Test actual API call (optional)
print("\n6. Testing Greenhouse API call...")
try:
    import requests
    response = requests.get('https://api.greenhouse.io/v1/boards/stripe/jobs?content=true', timeout=10)
    if response.status_code == 200:
        data = response.json()
        job_count = len(data.get('jobs', []))
        print(f"   ✅ Greenhouse API working - found {job_count} jobs from Stripe")
    else:
        print(f"   ⚠️ Greenhouse API returned status {response.status_code}")
except Exception as e:
    print(f"   ⚠️ Greenhouse API call failed: {e}")

print("\n" + "=" * 60)
print("Scraper Module Tests Complete!")
print("=" * 60)