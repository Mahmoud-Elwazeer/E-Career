# HTTP Client Consolidation Guide

## Overview

We've standardized on a single HTTP client to simplify the codebase and reduce confusion.

**New standard:** `services/api.ts` (axios-based)

## Before (Multiple Clients)

```typescript
// Old approach #1 - axios client
import api from "@/services/api";
const response = await api.get("/api/v1/jobs/");

// Old approach #2 - fetch wrapper
import { apiRequest } from "@/services/client";
const data = await apiRequest("/jobs/");
```

## After (Unified Client)

```typescript
// New unified approach
import api from "@/lib/api";
const response = await api.get("/api/v1/jobs/");
const data = response.data;
```

## Migration Steps

### 1. Replace `services/client.ts` imports

**Before:**
```typescript
import { apiRequest } from "@/services/client";

const data = await apiRequest<JobsResponse>("/jobs/", {
  method: "GET",
  params: { limit: 10 }
});
```

**After:**
```typescript
import api from "@/lib/api";

const response = await api.get<JobsResponse>("/api/v1/jobs/", {
  params: { limit: 10 }
});
const data = response.data;
```

### 2. Replace direct `services/api.ts` imports

**Before:**
```typescript
import api from "@/services/api";
const response = await api.get("/api/v1/jobs/");
```

**After:**
```typescript
import api from "@/lib/api";
const response = await api.get("/api/v1/jobs/");
```

### 3. Files using `apiRequest` (fetch-based)

These files need migration to axios-based api:

- `src/services/auth.ts`
- `src/services/userdata.ts`
- `src/services/admin.ts`
- `src/services/jobs.ts`
- `src/hooks/use-auth.tsx`

**Example migration:**

```typescript
// Before (fetch)
import { apiRequest } from "@/services/client";

export async function login(email: string, password: string) {
  return apiRequest<AuthResponse>("/auth/login/", {
    method: "POST",
    body: { email, password }
  });
}

// After (axios)
import api from "@/lib/api";

export async function login(email: string, password: string) {
  const response = await api.post<AuthResponse>("/api/v1/auth/login/", {
    email,
    password
  });
  return response.data;
}
```

## Benefits

✅ **Single source of truth** - One client to maintain
✅ **Consistent error handling** - Same interceptors everywhere  
✅ **Better TypeScript support** - Axios has superior typing
✅ **Automatic token refresh** - Built into api.ts
✅ **Easier testing** - Mock one client instead of two

## Files to Migrate (Phase D2)

Priority order:

1. **High priority** (auth-critical):
   - [ ] `src/services/auth.ts`
   - [ ] `src/hooks/use-auth.tsx`

2. **Medium priority** (feature-critical):
   - [ ] `src/services/jobs.ts`
   - [ ] `src/services/userdata.ts`
   - [ ] `src/services/admin.ts`

3. **Low priority** (once complete, remove `services/client.ts`):
   - [ ] Any remaining imports

## Testing

After migration, verify:

1. Login/logout flow works
2. Token refresh on 401 works
3. API calls include proper headers
4. Error handling works as expected

## Deprecation Timeline

- **Phase D2** (now): Create unified `lib/api.ts` entry point
- **Phase E** (next): Migrate all `apiRequest` usage to axios
- **Phase F**: Remove `services/client.ts` entirely
