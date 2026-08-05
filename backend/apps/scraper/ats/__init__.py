"""ATS scrapers package."""
from .base import BaseATSScraper
from .greenhouse import GreenhouseScraper, fetch_greenhouse_jobs
from .lever import LeverScraper, fetch_lever_jobs
from .ashby import AshbyScraper, fetch_ashby_jobs
from .bamboohr import BambooHRScraper, fetch_bamboohr_jobs
from .workday import WorkdayScraper, fetch_workday_jobs
from .smartrecruiters import SmartRecruitersScraper, fetch_smartrecruiters_jobs
from .workable import WorkableScraper, fetch_workable_jobs
from .teamtailor import TeamtailorScraper, fetch_teamtailor_jobs
from .icims import IcimsScraper, fetch_icims_jobs
from .oracle import OracleScraper, fetch_oracle_jobs
from .sap import SAPScraper, fetch_sap_jobs

__all__ = [
    'BaseATSScraper',
    'GreenhouseScraper',
    'fetch_greenhouse_jobs',
    'LeverScraper',
    'fetch_lever_jobs',
    'AshbyScraper',
    'fetch_ashby_jobs',
    'BambooHRScraper',
    'fetch_bamboohr_jobs',
    'WorkdayScraper',
    'fetch_workday_jobs',
    'SmartRecruitersScraper',
    'fetch_smartrecruiters_jobs',
    'WorkableScraper',
    'fetch_workable_jobs',
    'TeamtailorScraper',
    'fetch_teamtailor_jobs',
    'IcimsScraper',
    'fetch_icims_jobs',
    'OracleScraper',
    'fetch_oracle_jobs',
    'SAPScraper',
    'fetch_sap_jobs',
]
