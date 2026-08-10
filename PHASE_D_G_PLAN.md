# Phase D + G Implementation Plan

## Phase D: UX Polish (Frontend Focus)

### D1: Post-Login Onboarding Integration ✅ (Partial)
**Status:** Component exists, needs integration

**Existing:**
- `frontend/src/components/landing/OnboardingFlow.tsx` (3-step: career track → work mode → location)

**TODO:**
1. Create `/onboarding` route that shows after first login
2. Call backend API `PATCH /api/v1/career/onboarding/` on completion
3. Redirect to dashboard when `is_complete === true`
4. Add onboarding check in AuthContext

**Files to modify:**
- `frontend/src/pages/Onboarding.tsx` (new page wrapper)
- `frontend/src/routes.tsx` (add route)
- `frontend/src/contexts/AuthContext.tsx` (check onboarding status)

---

### D2: HTTP Client Consolidation
**Status:** Not started

**Issue:** Two HTTP clients exist:
- `services/client.ts` (old)
- `services/api.ts` (new, preferred)

**Action:**
1. Grep for `services/client` imports
2. Replace with `services/api`
3. Delete `services/client.ts`

**Commands:**
```bash
cd frontend
grep -r "from.*services/client" src/ | wc -l  # Count usages
# Then migrate each file
```

---

### D3: Employer Domain Verification (Backend)
**Status:** Not started

**Action:** Add domain matching on employer registration

**File:** `backend/apps/employers/views.py`

**Logic:**
```python
# In employer registration view
email_domain = user.email.split('@')[1]
company_domain = extract_domain(company.website)

if email_domain == company_domain:
    employer.is_verified = True  # Auto-verify
else:
    employer.verification_status = 'pending'  # Admin review
```

---

### D4: Application Tracker Page
**Status:** Not started

**Action:** Create user-facing application history page

**Files:**
- `frontend/src/pages/Applications.tsx` (new)
- API already exists: `GET /api/v1/employers/applications/`

**Features:**
- List applications with status (pending, reviewed, rejected, accepted)
- Filter by status
- View application details (cover letter, CV)
- Timeline view

---

## Phase G: Admin & Operations Tools

### G1: AI Cost Dashboard
**Status:** Not started

**Action:** Create admin view showing AI usage and costs

**Implementation:**
1. Create aggregation view in `apps/monitoring/views.py`
2. Query `RashidUsage` model for token usage
3. Query events for `AI_MODEL_CALLED`
4. Calculate costs: tokens × model rate
5. Display charts (daily, weekly, monthly)

**Models to query:**
- `apps.rashid.models.RashidUsage` (chat tokens)
- `apps.events.models.Event` (where event_type='ai_model_called')
- Calculate from metadata: model, tokens, cost

**Template:** `apps/monitoring/templates/ai_cost_dashboard.html`

**URL:** `/admin-dashboard/ai-costs/`

---

### G2: Prompt Versioning System
**Status:** Not started

**Action:** Store prompts in DB for easy editing without deployment

**Model:** `apps/intelligence/models.py`

```python
class PromptVersion(UUIDModel):
    name = models.CharField(max_length=100, db_index=True)
    version = models.IntegerField(default=1)
    content = models.TextField()
    model_target = models.CharField(max_length=50)  # 'haiku', 'sonnet', etc.
    is_active = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('name', 'version')
        
    def __str__(self):
        return f"{self.name} v{self.version}"
```

**Usage in AI services:**
```python
# Replace hardcoded prompts with:
prompt = PromptVersion.objects.get(name='cover_letter_generation', is_active=True).content
```

**Migration:** Create initial prompts from existing hardcoded strings

---

### G3: Scraper Health Dashboard Enhancement
**Status:** Partial (basic admin exists)

**Action:** Add health metrics to scraper admin

**File:** `apps/scraper/admin.py` or custom admin view

**Metrics to show:**
- Last run timestamp (per source)
- Success/failure rate (last 7 days)
- Jobs found per run
- Average run duration
- Error messages (last 5)

**Visual:** Traffic light indicators (🟢 healthy, 🟡 degraded, 🔴 failing)

---

### G4: GDPR Data Export & Deletion
**Status:** Not started

**Models:** `apps/accounts/models.py`

```python
class DataExportRequest(UUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ])
    file_path = models.CharField(max_length=500, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # 30 days
```

**API Endpoints:**
- `POST /api/v1/auth/data-export/` - Request export
- `GET /api/v1/auth/data-export/<id>/` - Check status / download
- `DELETE /api/v1/auth/account/` - Request account deletion

**Celery Task:** `apps/accounts/tasks.py`

```python
@shared_task
def generate_data_export(request_id):
    # Collect all user data:
    # - Profile, CV, applications, saved jobs
    # - Interview history, Rashid conversations
    # - Events, notifications
    # Package as JSON
    # Upload to S3 or save to media/
    # Update request status
```

---

## Implementation Order

### Week 1: Phase D (Frontend UX)
1. **D1**: Onboarding integration (4h)
2. **D2**: HTTP client consolidation (2h)
3. **D4**: Application tracker page (6h)
4. **D3**: Employer domain verification (2h)

**Total:** 14h

---

### Week 2: Phase G (Admin Tools)
1. **G2**: Prompt versioning model + migration (3h)
2. **G1**: AI cost dashboard (4h)
3. **G4**: GDPR export/deletion (6h)
4. **G3**: Scraper health dashboard (3h)

**Total:** 16h

---

## Testing Checklist

### Phase D Tests
- [ ] New user sees onboarding after first login
- [ ] Onboarding data saves to backend
- [ ] Onboarding skipped if already complete
- [ ] Application tracker shows correct statuses
- [ ] Employer with matching domain auto-verified
- [ ] Employer with mismatched domain pending

### Phase G Tests
- [ ] AI cost dashboard shows accurate totals
- [ ] Prompt changes in admin reflected in AI services
- [ ] Data export includes all user data
- [ ] Account deletion removes PII within 30 days
- [ ] Scraper dashboard shows real-time health

---

## Database Migrations Needed

1. **PromptVersion** model (G2)
2. **DataExportRequest** model (G4)
3. **Employer.is_verified** field (if doesn't exist) (D3)

---

## Dependencies Check

**Phase D:**
- ✅ OnboardingProgress API exists
- ✅ JobApplication API exists
- ✅ Auth context exists
- ❓ Need to check Employer model fields

**Phase G:**
- ✅ RashidUsage model exists
- ✅ Event model exists
- ✅ Admin framework ready
- ❓ Need S3 setup for data exports (or use local media/)

---

## Quick Wins (Start Here)

1. **G2: Prompt Versioning** - Easy, high value for iteration
2. **D1: Onboarding Integration** - Frontend component ready, just wire it up
3. **G1: AI Cost Dashboard** - Data exists, just aggregation needed
4. **D4: Application Tracker** - API exists, frontend only

---

## Notes

- **D2 (HTTP consolidation)** is technical debt cleanup, can be done anytime
- **D3 (Domain verification)** should happen on employer registration
- **G3 (Scraper health)** can use existing admin customization
- **G4 (GDPR)** is legally important, prioritize if EU users

---

**Ready to start?** Recommend beginning with **G2 (Prompt Versioning)** as it's foundational for other AI features.
