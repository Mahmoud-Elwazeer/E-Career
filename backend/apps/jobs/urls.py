from django.urls import path
from apps.jobs.views import (
    CompanyListView, CompanyDetailView,
    SourceListView, SourceDetailView,
    TagListView, TagDetailView,
    JobListView, JobDetailView, JobApplyView, SimilarJobsView,
    JobSaveView, JobUnsaveView, JobAskRashidView, match_explanation,
)

urlpatterns = [
    # Companies
    path("companies/", CompanyListView.as_view(), name="company-list"),
    path("companies/<slug:slug>/", CompanyDetailView.as_view(), name="company-detail"),
    # Sources
    path("sources/", SourceListView.as_view(), name="source-list"),
    path("sources/<slug:slug>/", SourceDetailView.as_view(), name="source-detail"),
    # Tags
    path("tags/", TagListView.as_view(), name="tag-list"),
    path("tags/<slug:slug>/", TagDetailView.as_view(), name="tag-detail"),
    # Jobs
    path("", JobListView.as_view(), name="job-list"),
    path("<slug:slug>/", JobDetailView.as_view(), name="job-detail"),
    path("<slug:slug>/apply/", JobApplyView.as_view(), name="job-apply"),
    path("<slug:slug>/similar/", SimilarJobsView.as_view(), name="job-similar"),
    path("<slug:slug>/save/", JobSaveView.as_view(), name="job-save"),
    path("<slug:slug>/unsave/", JobUnsaveView.as_view(), name="job-unsave"),
    path("<slug:slug>/ask-rashid/", JobAskRashidView.as_view(), name="job-ask-rashid"),
    path("<uuid:job_id>/match-explanation/", match_explanation, name="job-match-explanation"),
]
