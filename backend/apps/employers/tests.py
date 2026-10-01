"""
Comprehensive tests for multi-seat employer / EmployerTeamMember (item 2.8).

Covers:
- Model tests (creation, constraints, __str__)
- Permission tests (all 5 permission classes, both paths)
- ViewSet endpoint tests (list, invite, accept, partial_update, destroy)
"""
import pytest
from django.test import RequestFactory
from django.utils import timezone
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.employers.models import EmployerProfile, EmployerTeamMember
from apps.employers.permissions import (
    IsEmployer,
    IsVerifiedEmployer,
    IsOwnerEmployer,
    CanPostJobs,
    CanViewApplicants,
    _get_team_membership,
)
from apps.jobs.models import Company

User = get_user_model()


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def factory():
    return RequestFactory()


@pytest.fixture
def team_company(db):
    return Company.objects.create(
        name="Team Corp",
        slug="team-corp",
        industry="technology",
        website="https://teamcorp.example.com",
        is_active=True,
    )


@pytest.fixture
def other_company(db):
    return Company.objects.create(
        name="Other Corp",
        slug="other-corp",
        industry="finance",
        website="https://othercorp.example.com",
        is_active=True,
    )


@pytest.fixture
def employer_owner(db, team_company):
    """User with employer role and an EmployerProfile linked to team_company."""
    user = User.objects.create_user(
        email="owner@teamcorp.com",
        password="Pass1234!",
        first_name="Owner",
        last_name="Boss",
        role="employer",
    )
    EmployerProfile.objects.create(
        user=user,
        company=team_company,
        job_title="CEO",
        is_verified=True,
    )
    return user


@pytest.fixture
def unverified_employer(db, team_company):
    """Employer user whose profile is NOT verified."""
    user = User.objects.create_user(
        email="unverified@teamcorp.com",
        password="Pass1234!",
        first_name="Unverified",
        last_name="Employer",
        role="employer",
    )
    EmployerProfile.objects.create(
        user=user,
        company=team_company,
        job_title="Manager",
        is_verified=False,
    )
    return user


@pytest.fixture
def team_member_owner(db, team_company, employer_owner):
    """Team member with owner role (already accepted)."""
    user = User.objects.create_user(
        email="team-owner@teamcorp.com",
        password="Pass1234!",
        first_name="Team",
        last_name="Owner",
        role="user",
    )
    member = EmployerTeamMember.objects.create(
        user=user,
        company=team_company,
        role="owner",
        invited_by=employer_owner,
        accepted_at=timezone.now(),
        is_active=True,
    )
    return user, member


@pytest.fixture
def team_member_admin(db, team_company, employer_owner):
    """Team member with admin role (already accepted)."""
    user = User.objects.create_user(
        email="team-admin@teamcorp.com",
        password="Pass1234!",
        first_name="Team",
        last_name="Admin",
        role="user",
    )
    member = EmployerTeamMember.objects.create(
        user=user,
        company=team_company,
        role="admin",
        invited_by=employer_owner,
        accepted_at=timezone.now(),
        is_active=True,
    )
    return user, member


@pytest.fixture
def team_member_recruiter(db, team_company, employer_owner):
    """Team member with recruiter role (already accepted)."""
    user = User.objects.create_user(
        email="team-recruiter@teamcorp.com",
        password="Pass1234!",
        first_name="Team",
        last_name="Recruiter",
        role="user",
    )
    member = EmployerTeamMember.objects.create(
        user=user,
        company=team_company,
        role="recruiter",
        invited_by=employer_owner,
        accepted_at=timezone.now(),
        is_active=True,
    )
    return user, member


@pytest.fixture
def team_member_hiring_manager(db, team_company, employer_owner):
    """Team member with hiring_manager role (already accepted)."""
    user = User.objects.create_user(
        email="team-hm@teamcorp.com",
        password="Pass1234!",
        first_name="Team",
        last_name="HiringManager",
        role="user",
    )
    member = EmployerTeamMember.objects.create(
        user=user,
        company=team_company,
        role="hiring_manager",
        invited_by=employer_owner,
        accepted_at=timezone.now(),
        is_active=True,
    )
    return user, member


@pytest.fixture
def team_member_viewer(db, team_company, employer_owner):
    """Team member with viewer role (already accepted)."""
    user = User.objects.create_user(
        email="team-viewer@teamcorp.com",
        password="Pass1234!",
        first_name="Team",
        last_name="Viewer",
        role="user",
    )
    member = EmployerTeamMember.objects.create(
        user=user,
        company=team_company,
        role="viewer",
        invited_by=employer_owner,
        accepted_at=timezone.now(),
        is_active=True,
    )
    return user, member


@pytest.fixture
def pending_member(db, team_company, employer_owner):
    """Team member invited but NOT yet accepted."""
    user = User.objects.create_user(
        email="pending@teamcorp.com",
        password="Pass1234!",
        first_name="Pending",
        last_name="Member",
        role="user",
    )
    member = EmployerTeamMember.objects.create(
        user=user,
        company=team_company,
        role="recruiter",
        invited_by=employer_owner,
        accepted_at=None,
        is_active=True,
    )
    return user, member


@pytest.fixture
def deactivated_member(db, team_company, employer_owner):
    """Team member who was deactivated."""
    user = User.objects.create_user(
        email="deactivated@teamcorp.com",
        password="Pass1234!",
        first_name="Deactivated",
        last_name="Member",
        role="user",
    )
    member = EmployerTeamMember.objects.create(
        user=user,
        company=team_company,
        role="admin",
        invited_by=employer_owner,
        accepted_at=timezone.now(),
        is_active=False,
    )
    return user, member


@pytest.fixture
def plain_user(db):
    """User with no employer profile and no team membership."""
    return User.objects.create_user(
        email="plain@example.com",
        password="Pass1234!",
        first_name="Plain",
        last_name="User",
        role="user",
    )


@pytest.fixture
def invitee_user(db):
    """User who can be invited to a team."""
    return User.objects.create_user(
        email="invitee@example.com",
        password="Pass1234!",
        first_name="Invitee",
        last_name="Person",
        role="user",
    )


def _auth_client(user):
    """Return an APIClient authenticated as the given user."""
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


def _make_request(factory, user=None):
    """Build a minimal request object for permission checks."""
    request = factory.get("/fake/")
    if user:
        request.user = user
    else:
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()
    return request


# ============================================================================
# MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestEmployerTeamMemberModel:

    def test_create_with_each_role(self, team_company, employer_owner):
        """Verify a team member can be created with every valid role."""
        roles = ["owner", "admin", "recruiter", "hiring_manager", "viewer"]
        for i, role in enumerate(roles):
            user = User.objects.create_user(
                email=f"role-{role}@test.com",
                password="Pass1234!",
                first_name="Role",
                last_name=role.capitalize(),
            )
            member = EmployerTeamMember.objects.create(
                user=user,
                company=team_company,
                role=role,
                invited_by=employer_owner,
            )
            assert member.role == role
            assert member.is_active is True
            assert member.accepted_at is None

    def test_unique_together_user_company(self, team_company, employer_owner):
        """The same user cannot be added to the same company twice."""
        user = User.objects.create_user(
            email="dup@test.com",
            password="Pass1234!",
            first_name="Dup",
            last_name="User",
        )
        EmployerTeamMember.objects.create(
            user=user,
            company=team_company,
            role="viewer",
            invited_by=employer_owner,
        )
        with pytest.raises(IntegrityError):
            EmployerTeamMember.objects.create(
                user=user,
                company=team_company,
                role="admin",
                invited_by=employer_owner,
            )

    def test_str_representation(self, team_member_admin):
        user, member = team_member_admin
        expected = f"{user.email} @ {member.company.name} ({member.role})"
        assert str(member) == expected

    def test_default_role_is_viewer(self, team_company, employer_owner):
        user = User.objects.create_user(
            email="default-role@test.com",
            password="Pass1234!",
            first_name="Default",
            last_name="Role",
        )
        member = EmployerTeamMember.objects.create(
            user=user,
            company=team_company,
            invited_by=employer_owner,
        )
        assert member.role == "viewer"

    def test_ordering_by_invited_at_desc(self, team_company, employer_owner):
        """Members are ordered by -invited_at (newest first)."""
        users = []
        for i in range(3):
            u = User.objects.create_user(
                email=f"order-{i}@test.com",
                password="Pass1234!",
                first_name=f"Order{i}",
                last_name="Test",
            )
            EmployerTeamMember.objects.create(
                user=u,
                company=team_company,
                role="viewer",
                invited_by=employer_owner,
            )
            users.append(u)
        members = list(
            EmployerTeamMember.objects.filter(company=team_company)
        )
        # Newest should be first
        assert members[0].user == users[-1]


# ============================================================================
# HELPER: _get_team_membership
# ============================================================================

@pytest.mark.django_db
class TestGetTeamMembership:

    def test_returns_active_accepted_member(self, team_member_admin):
        user, member = team_member_admin
        result = _get_team_membership(user)
        assert result is not None
        assert result.id == member.id

    def test_returns_none_for_pending(self, pending_member):
        user, _ = pending_member
        assert _get_team_membership(user) is None

    def test_returns_none_for_deactivated(self, deactivated_member):
        user, _ = deactivated_member
        assert _get_team_membership(user) is None

    def test_returns_none_for_plain_user(self, plain_user):
        assert _get_team_membership(plain_user) is None


# ============================================================================
# PERMISSION TESTS
# ============================================================================

@pytest.mark.django_db
class TestIsEmployerPermission:

    def test_employer_profile_owner_passes(self, factory, employer_owner):
        perm = IsEmployer()
        request = _make_request(factory, employer_owner)
        assert perm.has_permission(request, None) is True

    def test_active_accepted_team_member_passes(self, factory, team_member_recruiter):
        perm = IsEmployer()
        user, _ = team_member_recruiter
        request = _make_request(factory, user)
        assert perm.has_permission(request, None) is True

    def test_pending_team_member_fails(self, factory, pending_member):
        perm = IsEmployer()
        user, _ = pending_member
        request = _make_request(factory, user)
        assert perm.has_permission(request, None) is False

    def test_deactivated_team_member_fails(self, factory, deactivated_member):
        perm = IsEmployer()
        user, _ = deactivated_member
        request = _make_request(factory, user)
        assert perm.has_permission(request, None) is False

    def test_plain_user_fails(self, factory, plain_user):
        perm = IsEmployer()
        request = _make_request(factory, plain_user)
        assert perm.has_permission(request, None) is False

    def test_unauthenticated_fails(self, factory):
        perm = IsEmployer()
        request = _make_request(factory, user=None)
        assert perm.has_permission(request, None) is False


@pytest.mark.django_db
class TestIsVerifiedEmployerPermission:

    def test_verified_employer_owner_passes(self, factory, employer_owner):
        perm = IsVerifiedEmployer()
        request = _make_request(factory, employer_owner)
        assert perm.has_permission(request, None) is True

    def test_unverified_employer_fails(self, factory, unverified_employer):
        perm = IsVerifiedEmployer()
        request = _make_request(factory, unverified_employer)
        assert perm.has_permission(request, None) is False

    def test_team_member_with_verified_company_passes(
        self, factory, team_member_admin, employer_owner
    ):
        """Team member passes when the company has at least one verified employer."""
        perm = IsVerifiedEmployer()
        user, _ = team_member_admin
        request = _make_request(factory, user)
        # employer_owner has is_verified=True for same company
        assert perm.has_permission(request, None) is True

    def test_team_member_without_verified_company_fails(
        self, factory, other_company
    ):
        """Team member fails when no employer profile on their company is verified."""
        user = User.objects.create_user(
            email="no-verified@other.com",
            password="Pass1234!",
            first_name="NoVer",
            last_name="User",
            role="user",
        )
        EmployerTeamMember.objects.create(
            user=user,
            company=other_company,
            role="admin",
            accepted_at=timezone.now(),
            is_active=True,
        )
        perm = IsVerifiedEmployer()
        request = _make_request(factory, user)
        assert perm.has_permission(request, None) is False

    def test_plain_user_fails(self, factory, plain_user):
        perm = IsVerifiedEmployer()
        request = _make_request(factory, plain_user)
        assert perm.has_permission(request, None) is False

    def test_unauthenticated_fails(self, factory):
        perm = IsVerifiedEmployer()
        request = _make_request(factory, user=None)
        assert perm.has_permission(request, None) is False


@pytest.mark.django_db
class TestIsOwnerEmployerPermission:
    """
    IsOwnerEmployer uses has_object_permission.
    It checks two patterns: obj.employer and obj.user.
    """

    def _make_obj_with_employer(self, employer_profile):
        """Create a mock obj that has an .employer attribute."""

        class FakeObj:
            pass

        obj = FakeObj()
        obj.employer = employer_profile
        return obj

    def _make_obj_with_user_and_company(self, user, company):
        """Create a mock obj with .user and .company_id."""

        class FakeObj:
            pass

        obj = FakeObj()
        obj.user = user
        obj.company_id = company.id
        return obj

    def test_employer_profile_owner_passes(self, factory, employer_owner):
        perm = IsOwnerEmployer()
        request = _make_request(factory, employer_owner)
        obj = self._make_obj_with_employer(employer_owner.employer_profile)
        assert perm.has_object_permission(request, None, obj) is True

    def test_owner_team_member_passes(
        self, factory, employer_owner, team_member_owner
    ):
        perm = IsOwnerEmployer()
        user, _ = team_member_owner
        request = _make_request(factory, user)
        obj = self._make_obj_with_employer(employer_owner.employer_profile)
        assert perm.has_object_permission(request, None, obj) is True

    def test_admin_team_member_passes(
        self, factory, employer_owner, team_member_admin
    ):
        perm = IsOwnerEmployer()
        user, _ = team_member_admin
        request = _make_request(factory, user)
        obj = self._make_obj_with_employer(employer_owner.employer_profile)
        assert perm.has_object_permission(request, None, obj) is True

    def test_recruiter_team_member_fails(
        self, factory, employer_owner, team_member_recruiter
    ):
        perm = IsOwnerEmployer()
        user, _ = team_member_recruiter
        request = _make_request(factory, user)
        obj = self._make_obj_with_employer(employer_owner.employer_profile)
        assert perm.has_object_permission(request, None, obj) is False

    def test_viewer_team_member_fails(
        self, factory, employer_owner, team_member_viewer
    ):
        perm = IsOwnerEmployer()
        user, _ = team_member_viewer
        request = _make_request(factory, user)
        obj = self._make_obj_with_employer(employer_owner.employer_profile)
        assert perm.has_object_permission(request, None, obj) is False

    def test_plain_user_fails(self, factory, employer_owner, plain_user):
        perm = IsOwnerEmployer()
        request = _make_request(factory, plain_user)
        obj = self._make_obj_with_employer(employer_owner.employer_profile)
        assert perm.has_object_permission(request, None, obj) is False

    # --- obj.user path ---

    def test_obj_user_owner_passes(self, factory, employer_owner, team_company):
        perm = IsOwnerEmployer()
        request = _make_request(factory, employer_owner)
        obj = self._make_obj_with_user_and_company(employer_owner, team_company)
        assert perm.has_object_permission(request, None, obj) is True

    def test_obj_user_admin_team_member_passes(
        self, factory, team_member_admin, team_company
    ):
        perm = IsOwnerEmployer()
        user, _ = team_member_admin
        other_user = User.objects.create_user(
            email="some-other@test.com",
            password="Pass1234!",
            first_name="Some",
            last_name="Other",
        )
        request = _make_request(factory, user)
        obj = self._make_obj_with_user_and_company(other_user, team_company)
        assert perm.has_object_permission(request, None, obj) is True


@pytest.mark.django_db
class TestCanPostJobsPermission:

    def test_verified_employer_passes(self, factory, employer_owner):
        perm = CanPostJobs()
        request = _make_request(factory, employer_owner)
        assert perm.has_permission(request, None) is True

    def test_unverified_employer_fails(self, factory, unverified_employer):
        perm = CanPostJobs()
        request = _make_request(factory, unverified_employer)
        assert perm.has_permission(request, None) is False

    def test_owner_team_member_passes(
        self, factory, team_member_owner, employer_owner
    ):
        perm = CanPostJobs()
        user, _ = team_member_owner
        request = _make_request(factory, user)
        assert perm.has_permission(request, None) is True

    def test_admin_team_member_passes(
        self, factory, team_member_admin, employer_owner
    ):
        perm = CanPostJobs()
        user, _ = team_member_admin
        request = _make_request(factory, user)
        assert perm.has_permission(request, None) is True

    def test_recruiter_team_member_passes(
        self, factory, team_member_recruiter, employer_owner
    ):
        perm = CanPostJobs()
        user, _ = team_member_recruiter
        request = _make_request(factory, user)
        assert perm.has_permission(request, None) is True

    def test_hiring_manager_team_member_fails(
        self, factory, team_member_hiring_manager, employer_owner
    ):
        perm = CanPostJobs()
        user, _ = team_member_hiring_manager
        request = _make_request(factory, user)
        assert perm.has_permission(request, None) is False

    def test_viewer_team_member_fails(
        self, factory, team_member_viewer, employer_owner
    ):
        perm = CanPostJobs()
        user, _ = team_member_viewer
        request = _make_request(factory, user)
        assert perm.has_permission(request, None) is False

    def test_plain_user_fails(self, factory, plain_user):
        perm = CanPostJobs()
        request = _make_request(factory, plain_user)
        assert perm.has_permission(request, None) is False

    def test_unauthenticated_fails(self, factory):
        perm = CanPostJobs()
        request = _make_request(factory, user=None)
        assert perm.has_permission(request, None) is False


@pytest.mark.django_db
class TestCanViewApplicantsPermission:
    """
    CanViewApplicants uses has_object_permission.
    obj must have .employer.user and .company_id.
    """

    def _make_obj(self, employer_profile, company):
        class FakeObj:
            pass
        obj = FakeObj()
        obj.employer = employer_profile
        obj.company_id = company.id
        return obj

    def test_employer_owner_passes(self, factory, employer_owner, team_company):
        perm = CanViewApplicants()
        request = _make_request(factory, employer_owner)
        obj = self._make_obj(employer_owner.employer_profile, team_company)
        assert perm.has_object_permission(request, None, obj) is True

    def test_owner_team_member_passes(
        self, factory, team_member_owner, employer_owner, team_company
    ):
        perm = CanViewApplicants()
        user, _ = team_member_owner
        request = _make_request(factory, user)
        obj = self._make_obj(employer_owner.employer_profile, team_company)
        assert perm.has_object_permission(request, None, obj) is True

    def test_admin_team_member_passes(
        self, factory, team_member_admin, employer_owner, team_company
    ):
        perm = CanViewApplicants()
        user, _ = team_member_admin
        request = _make_request(factory, user)
        obj = self._make_obj(employer_owner.employer_profile, team_company)
        assert perm.has_object_permission(request, None, obj) is True

    def test_recruiter_team_member_passes(
        self, factory, team_member_recruiter, employer_owner, team_company
    ):
        perm = CanViewApplicants()
        user, _ = team_member_recruiter
        request = _make_request(factory, user)
        obj = self._make_obj(employer_owner.employer_profile, team_company)
        assert perm.has_object_permission(request, None, obj) is True

    def test_hiring_manager_team_member_passes(
        self, factory, team_member_hiring_manager, employer_owner, team_company
    ):
        perm = CanViewApplicants()
        user, _ = team_member_hiring_manager
        request = _make_request(factory, user)
        obj = self._make_obj(employer_owner.employer_profile, team_company)
        assert perm.has_object_permission(request, None, obj) is True

    def test_viewer_team_member_fails(
        self, factory, team_member_viewer, employer_owner, team_company
    ):
        perm = CanViewApplicants()
        user, _ = team_member_viewer
        request = _make_request(factory, user)
        obj = self._make_obj(employer_owner.employer_profile, team_company)
        assert perm.has_object_permission(request, None, obj) is False

    def test_plain_user_fails(
        self, factory, plain_user, employer_owner, team_company
    ):
        perm = CanViewApplicants()
        request = _make_request(factory, plain_user)
        obj = self._make_obj(employer_owner.employer_profile, team_company)
        assert perm.has_object_permission(request, None, obj) is False

    def test_unauthenticated_fails(self, factory, employer_owner, team_company):
        perm = CanViewApplicants()
        request = _make_request(factory, user=None)
        obj = self._make_obj(employer_owner.employer_profile, team_company)
        assert perm.has_object_permission(request, None, obj) is False


# ============================================================================
# VIEWSET / ENDPOINT TESTS
# ============================================================================

TEAM_BASE = "/api/v1/employer/team/"


@pytest.mark.django_db
class TestEmployerTeamListEndpoint:

    def test_employer_owner_can_list(self, employer_owner, team_member_admin):
        client = _auth_client(employer_owner)
        resp = client.get(TEAM_BASE)
        assert resp.status_code == 200
        assert resp.data["success"] is True
        assert isinstance(resp.data["data"], list)

    def test_team_member_can_list(self, team_member_admin, employer_owner):
        user, _ = team_member_admin
        client = _auth_client(user)
        resp = client.get(TEAM_BASE)
        assert resp.status_code == 200
        assert resp.data["success"] is True

    def test_plain_user_forbidden(self, plain_user):
        client = _auth_client(plain_user)
        resp = client.get(TEAM_BASE)
        assert resp.status_code == 403

    def test_unauthenticated_forbidden(self):
        client = APIClient()
        resp = client.get(TEAM_BASE)
        assert resp.status_code == 401


@pytest.mark.django_db
class TestEmployerTeamInviteEndpoint:

    def test_employer_owner_can_invite(
        self, employer_owner, invitee_user
    ):
        client = _auth_client(employer_owner)
        resp = client.post(
            TEAM_BASE + "invite/",
            {"email": invitee_user.email, "role": "recruiter"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["success"] is True
        assert resp.data["data"]["role"] == "recruiter"
        # Verify DB
        member = EmployerTeamMember.objects.get(user=invitee_user)
        assert member.company == employer_owner.employer_profile.company
        assert member.invited_by == employer_owner
        assert member.accepted_at is None

    def test_team_member_can_invite(
        self, team_member_admin, employer_owner, invitee_user
    ):
        user, _ = team_member_admin
        client = _auth_client(user)
        resp = client.post(
            TEAM_BASE + "invite/",
            {"email": invitee_user.email, "role": "viewer"},
            format="json",
        )
        assert resp.status_code == 201

    def test_duplicate_invite_conflict(self, employer_owner, team_member_admin):
        """Inviting an existing team member returns 409."""
        user, _ = team_member_admin
        client = _auth_client(employer_owner)
        resp = client.post(
            TEAM_BASE + "invite/",
            {"email": user.email, "role": "viewer"},
            format="json",
        )
        assert resp.status_code == 409
        assert resp.data["success"] is False

    def test_invite_nonexistent_email_creates_pending_invite(self, employer_owner):
        # Behavior change (feature): inviting someone who hasn't registered yet
        # now creates a PENDING email invite rather than failing. They link in
        # when they sign up / accept with that email.
        client = _auth_client(employer_owner)
        resp = client.post(
            TEAM_BASE + "invite/",
            {"email": "nobody@nowhere.com", "role": "viewer"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["pending_registration"] is True
        assert resp.data["data"]["is_pending"] is True
        assert resp.data["data"]["invite_email"] == "nobody@nowhere.com"

    def test_invite_invalid_role_fails(self, employer_owner, invitee_user):
        client = _auth_client(employer_owner)
        resp = client.post(
            TEAM_BASE + "invite/",
            {"email": invitee_user.email, "role": "superadmin"},
            format="json",
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestEmployerTeamAcceptEndpoint:

    def test_accept_pending_invitation(self, pending_member):
        # Fixed: `accept` now overrides get_permissions to require only
        # IsAuthenticated, so a pending member (blocked by IsEmployer) can
        # accept their invite. This previously 403'd — a real design flaw.
        user, member = pending_member
        assert member.accepted_at is None
        client = _auth_client(user)
        resp = client.post(TEAM_BASE + "accept/")
        assert resp.status_code == 200
        assert resp.data["success"] is True
        member.refresh_from_db()
        assert member.accepted_at is not None

    def test_already_accepted_returns_404(self, team_member_admin):
        """If already accepted, there is no pending invitation."""
        user, _ = team_member_admin
        client = _auth_client(user)
        resp = client.post(TEAM_BASE + "accept/")
        assert resp.status_code == 404


@pytest.mark.django_db
class TestEmployerTeamUpdateEndpoint:

    def test_update_role(self, employer_owner, team_member_viewer):
        user, member = team_member_viewer
        client = _auth_client(employer_owner)
        resp = client.patch(
            f"{TEAM_BASE}{member.id}/",
            {"role": "recruiter"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["success"] is True
        member.refresh_from_db()
        assert member.role == "recruiter"

    def test_update_with_invalid_role_keeps_old(
        self, employer_owner, team_member_viewer
    ):
        user, member = team_member_viewer
        client = _auth_client(employer_owner)
        resp = client.patch(
            f"{TEAM_BASE}{member.id}/",
            {"role": "nonexistent_role"},
            format="json",
        )
        assert resp.status_code == 200
        member.refresh_from_db()
        assert member.role == "viewer"  # unchanged


@pytest.mark.django_db
class TestEmployerTeamDeleteEndpoint:

    def test_soft_delete_member(self, employer_owner, team_member_viewer):
        user, member = team_member_viewer
        assert member.is_active is True
        client = _auth_client(employer_owner)
        resp = client.delete(f"{TEAM_BASE}{member.id}/")
        assert resp.status_code == 204
        member.refresh_from_db()
        assert member.is_active is False

    def test_delete_nonexistent_returns_404(self, employer_owner):
        client = _auth_client(employer_owner)
        resp = client.delete(f"{TEAM_BASE}99999/")
        assert resp.status_code == 404


# ============================================================================
# Employer verification request (self-serve, persisted + event-emitting)
# ============================================================================

PROFILE_BASE = "/api/v1/employer/profile/"


@pytest.mark.django_db
class TestRequestVerification:
    def test_request_verification_persists_timestamp(self, unverified_employer):
        client = _auth_client(unverified_employer)
        resp = client.post(PROFILE_BASE + "request_verification/",
                            {"note": "Our domain is teamcorp.example.com"}, format="json")
        assert resp.status_code == 200
        assert resp.data["status"] == "pending"
        unverified_employer.employer_profile.refresh_from_db()
        prof = unverified_employer.employer_profile
        assert prof.verification_requested_at is not None
        assert prof.verification_note == "Our domain is teamcorp.example.com"

    def test_request_verification_without_note(self, unverified_employer):
        client = _auth_client(unverified_employer)
        resp = client.post(PROFILE_BASE + "request_verification/", {}, format="json")
        assert resp.status_code == 200
        unverified_employer.employer_profile.refresh_from_db()
        assert unverified_employer.employer_profile.verification_requested_at is not None

    def test_already_verified_cannot_request(self, employer_owner):
        # employer_owner fixture is is_verified=True.
        client = _auth_client(employer_owner)
        resp = client.post(PROFILE_BASE + "request_verification/", {}, format="json")
        assert resp.status_code == 400

    def test_profile_exposes_verification_requested_at(self, unverified_employer):
        client = _auth_client(unverified_employer)
        client.post(PROFILE_BASE + "request_verification/", {}, format="json")
        resp = client.get(PROFILE_BASE)
        assert resp.status_code == 200
        assert resp.data["verification_requested_at"] is not None


# ============================================================================
# Company profile management (/employer/profile/company/)
# ============================================================================

COMPANY_BASE = "/api/v1/employer/profile/company/"


@pytest.mark.django_db
class TestCompanyManagement:
    def test_owner_can_read_company(self, employer_owner, team_company):
        client = _auth_client(employer_owner)
        resp = client.get(COMPANY_BASE)
        assert resp.status_code == 200
        assert resp.data["name"] == team_company.name

    def test_owner_can_edit_company(self, employer_owner, team_company):
        client = _auth_client(employer_owner)
        resp = client.patch(COMPANY_BASE, {"about": "We build things.", "size": "11-50"}, format="json")
        assert resp.status_code == 200
        team_company.refresh_from_db()
        assert team_company.about == "We build things."
        assert team_company.size == "11-50"

    def test_admin_team_member_can_edit(self, team_member_admin, team_company):
        user, _ = team_member_admin
        client = _auth_client(user)
        resp = client.patch(COMPANY_BASE, {"headquarters": "Cairo"}, format="json")
        assert resp.status_code == 200
        team_company.refresh_from_db()
        assert team_company.headquarters == "Cairo"

    def test_recruiter_cannot_edit(self, team_member_recruiter, team_company):
        user, _ = team_member_recruiter
        client = _auth_client(user)
        resp = client.patch(COMPANY_BASE, {"about": "nope"}, format="json")
        assert resp.status_code == 403
        team_company.refresh_from_db()
        assert team_company.about != "nope"

    def test_recruiter_can_still_read(self, team_member_recruiter):
        user, _ = team_member_recruiter
        client = _auth_client(user)
        resp = client.get(COMPANY_BASE)
        assert resp.status_code == 200

    def test_slug_and_verification_are_not_editable(self, employer_owner, team_company):
        client = _auth_client(employer_owner)
        original_slug = team_company.slug
        resp = client.patch(
            COMPANY_BASE,
            {"slug": "hacked-slug", "is_verified": True, "name": "Renamed Co"},
            format="json",
        )
        assert resp.status_code == 200
        team_company.refresh_from_db()
        assert team_company.slug == original_slug       # read-only, unchanged
        assert team_company.is_verified is False         # read-only, unchanged
        assert team_company.name == "Renamed Co"          # editable, changed

    def test_plain_user_has_no_company(self, plain_user):
        client = _auth_client(plain_user)
        resp = client.get(COMPANY_BASE)
        # IsEmployer blocks a non-employer before the action runs.
        assert resp.status_code in (403, 404)


# ============================================================================
# Email invites to non-registered users (pending -> linked on accept)
# ============================================================================

@pytest.mark.django_db
class TestEmailInviteFlow:
    def test_pending_email_invite_has_null_user(self, employer_owner, team_company):
        client = _auth_client(employer_owner)
        resp = client.post(
            TEAM_BASE + "invite/",
            {"email": "newhire@example.com", "role": "recruiter"},
            format="json",
        )
        assert resp.status_code == 201
        member = EmployerTeamMember.objects.get(invite_email="newhire@example.com", company=team_company)
        assert member.user_id is None
        assert member.accepted_at is None

    def test_duplicate_email_invite_conflicts(self, employer_owner):
        client = _auth_client(employer_owner)
        payload = {"email": "dupe@example.com", "role": "viewer"}
        first = client.post(TEAM_BASE + "invite/", payload, format="json")
        assert first.status_code == 201
        second = client.post(TEAM_BASE + "invite/", payload, format="json")
        assert second.status_code == 409

    def test_accept_links_pending_email_invite_after_signup(self, employer_owner, team_company):
        # Owner invites an email that isn't registered yet.
        client = _auth_client(employer_owner)
        client.post(
            TEAM_BASE + "invite/",
            {"email": "later@example.com", "role": "recruiter"},
            format="json",
        )
        # That person registers and then accepts.
        newcomer = User.objects.create_user(
            email="later@example.com", password="Pass1234!", role="user",
        )
        newcomer_client = _auth_client(newcomer)
        resp = newcomer_client.post(TEAM_BASE + "accept/")
        assert resp.status_code == 200
        member = EmployerTeamMember.objects.get(invite_email="later@example.com", company=team_company)
        assert member.user_id == newcomer.id
        assert member.accepted_at is not None

    def test_existing_user_invite_still_works(self, employer_owner, invitee_user, team_company):
        client = _auth_client(employer_owner)
        resp = client.post(
            TEAM_BASE + "invite/",
            {"email": invitee_user.email, "role": "recruiter"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["pending_registration"] is False
        member = EmployerTeamMember.objects.get(user=invitee_user, company=team_company)
        assert member.role == "recruiter"


# ============================================================================
# Seat entitlement + employer billing snapshot
# ============================================================================

BILLING_BASE = "/api/v1/employer/profile/billing/"


@pytest.mark.django_db
class TestSeatsAndBilling:
    def _assign_plan(self, company, **plan_kwargs):
        from apps.core.models import SubscriptionPlan, CompanySubscription
        plan = SubscriptionPlan.objects.create(name=f"Plan {company.id}", **plan_kwargs)
        CompanySubscription.objects.create(company=company, plan=plan, status="active")
        return plan

    def test_billing_snapshot_without_plan(self, employer_owner, team_company):
        client = _auth_client(employer_owner)
        resp = client.get(BILLING_BASE)
        assert resp.status_code == 200
        assert resp.data["has_subscription"] is False
        # Owner created a team row at company creation in real flow; here the
        # fixture made a profile only, so seats_used reflects actual rows.
        assert "seats_used" in resp.data["usage"]

    def test_billing_snapshot_with_plan_reports_limits(self, employer_owner, team_company):
        self._assign_plan(team_company, seat_limit=3, job_posting_limit=10)
        client = _auth_client(employer_owner)
        resp = client.get(BILLING_BASE)
        assert resp.status_code == 200
        assert resp.data["has_subscription"] is True
        assert resp.data["plan"]["seat_limit"] == 3
        assert resp.data["usage"]["seats_limit"] == 3

    def test_seat_limit_blocks_invite_over_cap(self, employer_owner, team_company):
        # seat_limit=1; the owner's own team row consumes it, so the next invite
        # must be denied with 403.
        from apps.employers.models import EmployerTeamMember
        EmployerTeamMember.objects.create(
            user=employer_owner, company=team_company, role="owner",
            is_active=True, accepted_at=timezone.now(),
        )
        self._assign_plan(team_company, seat_limit=1)
        client = _auth_client(employer_owner)
        resp = client.post(
            TEAM_BASE + "invite/",
            {"email": "overflow@example.com", "role": "recruiter"},
            format="json",
        )
        assert resp.status_code == 403

    def test_no_plan_means_unlimited_seats(self, employer_owner, team_company):
        client = _auth_client(employer_owner)
        # No subscription -> no seat cap -> invite succeeds.
        resp = client.post(
            TEAM_BASE + "invite/",
            {"email": "freeseat@example.com", "role": "viewer"},
            format="json",
        )
        assert resp.status_code == 201
