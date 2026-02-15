# Chronos: Security Architecture & RBAC Implementation Guide

## Current Security Status

### ✅ Implemented (Iteration 15)

1. **Connector Security**
   - Rate limiting per connector (requests/minute, requests/hour)
   - Circuit breakers (auto-disable after failure threshold)
   - Domain allowlists (outbound fetch restrictions)
   - Retry logic with exponential backoff
   - Feature flags for connector enable/disable

2. **Data Integrity**
   - Immutable raw data storage
   - Checksum hashing for tamper detection
   - Schema validation (required field checks)
   - Unit validation (standard vs alternate units)
   - Outlier detection (statistical anomalies)
   - QA flags per data point

3. **Client-Side Security**
   - No API keys in client code (simulated fetches only)
   - Input validation for search queries
   - Safe rendering (React's built-in XSS protection)
   - No eval() or dangerous code execution

### ⚠️ Partially Implemented

1. **Types Defined, Awaiting Implementation**
   - `UserRole` interface exists in types.ts
   - `AuditLog` interface exists in types.ts
   - Permission strings defined but not enforced

### ❌ Not Yet Implemented (High Priority)

1. **Authentication & Authorization**
   - User login/signup
   - Role-based access control (RBAC)
   - Session management
   - Multi-factor authentication (MFA)

2. **Backend Security**
   - Server-side API key storage
   - Signed requests
   - CORS configuration
   - WAF protection
   - SQL injection prevention
   - SSRF protection

3. **Audit & Compliance**
   - Privileged action logging
   - User activity tracking
   - Data retention policies
   - GDPR compliance (account deletion)

---

## RBAC Design

### Roles & Permissions

```typescript
type Role = 'anonymous' | 'registered' | 'analyst' | 'admin'

const PERMISSIONS = {
  // Public (Anonymous)
  'view:charts': ['anonymous', 'registered', 'analyst', 'admin'],
  'view:sources': ['anonymous', 'registered', 'analyst', 'admin'],
  'view:methodology': ['anonymous', 'registered', 'analyst', 'admin'],
  
  // Registered Users
  'save:baskets': ['registered', 'analyst', 'admin'],
  'save:comparisons': ['registered', 'analyst', 'admin'],
  'export:data': ['registered', 'analyst', 'admin'],
  'create:permalinks': ['registered', 'analyst', 'admin'],
  
  // Analysts
  'edit:methodology-notes': ['analyst', 'admin'],
  'flag:data-quality': ['analyst', 'admin'],
  'submit:item-requests': ['analyst', 'admin'],
  'view:confidence-details': ['analyst', 'admin'],
  'export:audit-logs': ['analyst', 'admin'],
  
  // Admins
  'enable:connectors': ['admin'],
  'disable:connectors': ['admin'],
  'approve:new-items': ['admin'],
  'edit:source-registry': ['admin'],
  'manage:users': ['admin'],
  'view:audit-logs': ['admin'],
  'delete:data': ['admin'],
} as const
```

### Permission Check Implementation

```typescript
// src/lib/rbac.ts (to be created)

import type { UserRole } from './types'

export function hasPermission(
  userRole: UserRole['role'],
  permission: keyof typeof PERMISSIONS
): boolean {
  const allowedRoles = PERMISSIONS[permission]
  return allowedRoles.includes(userRole)
}

export function requirePermission(
  userRole: UserRole['role'],
  permission: keyof typeof PERMISSIONS
): void {
  if (!hasPermission(userRole, permission)) {
    throw new Error(`Permission denied: ${permission} requires ${PERMISSIONS[permission].join(' or ')}`)
  }
}

// Usage in components:
import { hasPermission } from '@/lib/rbac'

function AdminPanel({ user }: { user: UserRole }) {
  if (!hasPermission(user.role, 'enable:connectors')) {
    return <div>Access Denied</div>
  }
  
  return (
    <div>
      <h1>Connector Management</h1>
      {/* Admin-only UI */}
    </div>
  )
}
```

### UI Permission Gates

```typescript
// src/components/PermissionGate.tsx (to be created)

import { hasPermission } from '@/lib/rbac'
import type { UserRole } from '@/lib/types'

interface PermissionGateProps {
  user: UserRole
  permission: keyof typeof PERMISSIONS
  fallback?: React.ReactNode
  children: React.ReactNode
}

export function PermissionGate({ 
  user, 
  permission, 
  fallback = null, 
  children 
}: PermissionGateProps) {
  if (!hasPermission(user.role, permission)) {
    return <>{fallback}</>
  }
  
  return <>{children}</>
}

// Usage:
<PermissionGate 
  user={currentUser} 
  permission="edit:methodology-notes"
  fallback={<div>Analyst access required</div>}
>
  <MethodologyEditor />
</PermissionGate>
```

---

## Authentication Integration

### Recommended: Auth Provider Pattern

Use a third-party auth provider (Auth0, Clerk, Supabase Auth) for production:

```typescript
// src/lib/auth.ts (to be created)

import { useEffect, useState } from 'react'
import type { UserRole } from './types'

export function useAuth() {
  const [user, setUser] = useState<UserRole | null>(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    // Integrate with auth provider
    async function loadUser() {
      try {
        const authUser = await authProvider.getUser()
        if (authUser) {
          setUser({
            userId: authUser.id,
            role: authUser.metadata.role || 'registered',
            permissions: getPermissionsForRole(authUser.metadata.role),
            grantedAt: authUser.createdAt,
          })
        }
      } finally {
        setLoading(false)
      }
    }
    loadUser()
  }, [])
  
  return { user, loading }
}

export async function signIn(email: string, password: string) {
  return authProvider.signIn(email, password)
}

export async function signOut() {
  return authProvider.signOut()
}
```

### GitHub User Integration

Chronos already has access to GitHub user via `spark.user()`:

```typescript
// Get current GitHub user
const gitHubUser = await spark.user()
// Returns: { avatarUrl, email, id, isOwner, login }

// Map to Chronos roles
function getChronosRole(gitHubUser: GitHubUser): UserRole {
  return {
    userId: gitHubUser.id,
    role: gitHubUser.isOwner ? 'admin' : 'registered',
    permissions: gitHubUser.isOwner 
      ? getAllAdminPermissions()
      : getRegisteredPermissions(),
    grantedAt: new Date().toISOString(),
  }
}
```

---

## Audit Logging

### Audit Log Schema

Already defined in `types.ts`:

```typescript
export interface AuditLog {
  id: string
  userId: string
  action: string        // e.g., 'connector:enabled', 'item:approved'
  resource: string      // e.g., 'usda-ams-connector', 'eggs-dozen'
  timestamp: string
  metadata: Record<string, unknown>
  ipAddress?: string
}
```

### Implementation

```typescript
// src/lib/audit.ts (to be created)

import { useKV } from '@github/spark/hooks'
import type { AuditLog, UserRole } from './types'

export async function logAction(
  user: UserRole,
  action: string,
  resource: string,
  metadata: Record<string, unknown> = {}
): Promise<void> {
  const log: AuditLog = {
    id: crypto.randomUUID(),
    userId: user.userId,
    action,
    resource,
    timestamp: new Date().toISOString(),
    metadata,
  }
  
  // In production: send to backend
  console.log('[AUDIT]', log)
  
  // For now: append to KV store
  const logs = await spark.kv.get<AuditLog[]>('audit-logs') || []
  logs.push(log)
  await spark.kv.set('audit-logs', logs.slice(-1000)) // Keep last 1000
}

// Usage:
async function enableConnector(connectorId: string) {
  requirePermission(user.role, 'enable:connectors')
  
  // Perform action
  await updateConnectorStatus(connectorId, true)
  
  // Log it
  await logAction(user, 'connector:enabled', connectorId, {
    previousState: 'disabled',
    newState: 'enabled',
  })
}
```

### Audit Log Viewer

```typescript
// src/components/AuditLogView.tsx (to be created)

import { useEffect, useState } from 'react'
import type { AuditLog } from '@/lib/types'

export function AuditLogView() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  
  useEffect(() => {
    async function loadLogs() {
      const auditLogs = await spark.kv.get<AuditLog[]>('audit-logs') || []
      setLogs(auditLogs.reverse()) // Most recent first
    }
    loadLogs()
  }, [])
  
  return (
    <div>
      <h1>Audit Logs</h1>
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>User</th>
            <th>Action</th>
            <th>Resource</th>
          </tr>
        </thead>
        <tbody>
          {logs.map(log => (
            <tr key={log.id}>
              <td>{new Date(log.timestamp).toLocaleString()}</td>
              <td>{log.userId}</td>
              <td>{log.action}</td>
              <td>{log.resource}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

---

## API Security (Backend)

### Server-Side API Key Management

```typescript
// backend/src/config/secrets.ts (production)

export const API_KEYS = {
  USDA_AMS: process.env.USDA_AMS_API_KEY || '',
  EIA: process.env.EIA_API_KEY || '',
  BLS: process.env.BLS_API_KEY || '',
  FRED: process.env.FRED_API_KEY || '',
}

// Never expose these to frontend!
```

### Signed Requests

```typescript
// backend/src/middleware/signedRequest.ts

import crypto from 'crypto'

export function verifySignedRequest(req: Request): boolean {
  const signature = req.headers.get('X-Chronos-Signature')
  const timestamp = req.headers.get('X-Chronos-Timestamp')
  const body = await req.text()
  
  const expectedSignature = crypto
    .createHmac('sha256', process.env.SIGNING_SECRET!)
    .update(`${timestamp}:${body}`)
    .digest('hex')
  
  if (signature !== expectedSignature) {
    throw new Error('Invalid signature')
  }
  
  const requestTime = parseInt(timestamp)
  const now = Date.now()
  if (now - requestTime > 5 * 60 * 1000) { // 5 minutes
    throw new Error('Request too old')
  }
  
  return true
}
```

### Rate Limiting (Backend)

```typescript
// backend/src/middleware/rateLimit.ts

import rateLimit from 'express-rate-limit'

export const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per window
  message: 'Too many requests from this IP',
  standardHeaders: true,
  legacyHeaders: false,
})

export const connectorLimiter = (requestsPerMin: number) => 
  rateLimit({
    windowMs: 60 * 1000,
    max: requestsPerMin,
    message: 'Connector rate limit exceeded',
  })
```

### CORS Configuration

```typescript
// backend/src/middleware/cors.ts

const ALLOWED_ORIGINS = [
  'https://chronos.app',
  'https://www.chronos.app',
  process.env.NODE_ENV === 'development' ? 'http://localhost:5173' : null,
].filter(Boolean)

export const corsOptions = {
  origin: (origin: string, callback: Function) => {
    if (!origin || ALLOWED_ORIGINS.includes(origin)) {
      callback(null, true)
    } else {
      callback(new Error('Not allowed by CORS'))
    }
  },
  credentials: true,
}
```

---

## Data Privacy

### Minimal Data Collection

```typescript
// Only collect what's necessary
interface UserProfile {
  id: string           // Required
  email?: string       // Optional, only if user provides
  role: Role           // Required for RBAC
  createdAt: string    // Required
  lastLogin: string    // Required for security
  
  // DO NOT collect:
  // - Precise location (use coarse region selection)
  // - Financial data
  // - Browsing history
  // - Unnecessary metadata
}
```

### Account Deletion

```typescript
// src/lib/privacy.ts (to be created)

export async function deleteUserAccount(userId: string): Promise<void> {
  requirePermission(currentUser.role, 'delete:account')
  
  // Remove user profile
  await spark.kv.delete(`user:${userId}`)
  
  // Remove user's saved baskets
  await spark.kv.delete(`baskets:${userId}`)
  
  // Remove user's comparisons
  await spark.kv.delete(`comparisons:${userId}`)
  
  // Anonymize audit logs (keep for compliance, remove PII)
  const logs = await spark.kv.get<AuditLog[]>('audit-logs') || []
  const anonymized = logs.map(log => 
    log.userId === userId 
      ? { ...log, userId: 'DELETED_USER', ipAddress: undefined }
      : log
  )
  await spark.kv.set('audit-logs', anonymized)
  
  // Log the deletion
  await logAction(currentUser, 'account:deleted', userId, {
    deletedAt: new Date().toISOString(),
  })
}
```

---

## Implementation Checklist

### Phase 1: Authentication (Week 1-2)
- [ ] Integrate auth provider (Auth0/Clerk/Supabase)
- [ ] Create useAuth() hook
- [ ] Map GitHub users to Chronos roles
- [ ] Add sign-in/sign-out UI
- [ ] Store user sessions
- [ ] Protect registered-only features

### Phase 2: RBAC (Week 2-3)
- [ ] Implement hasPermission() utility
- [ ] Create PermissionGate component
- [ ] Add role checks to sensitive actions
- [ ] Show/hide UI based on permissions
- [ ] Test analyst vs admin access

### Phase 3: Audit Logging (Week 3-4)
- [ ] Implement logAction() utility
- [ ] Log all privileged actions
- [ ] Create AuditLogView component
- [ ] Add export audit logs feature
- [ ] Test log persistence

### Phase 4: Backend Security (Week 4-6)
- [ ] Move API keys to backend
- [ ] Implement signed requests
- [ ] Add rate limiting middleware
- [ ] Configure CORS properly
- [ ] Add input validation
- [ ] Test against common attacks (SSRF, injection)

### Phase 5: Privacy & Compliance (Week 6-7)
- [ ] Implement account deletion
- [ ] Add data retention policies
- [ ] Create privacy policy
- [ ] Add GDPR consent flows
- [ ] Test data export/deletion

---

## Security Best Practices

### Do's ✅
- ✅ Use environment variables for secrets
- ✅ Validate all user inputs
- ✅ Use HTTPS in production
- ✅ Hash sensitive data
- ✅ Log security events
- ✅ Keep dependencies updated
- ✅ Use least privilege principle
- ✅ Implement MFA for admins

### Don'ts ❌
- ❌ Store API keys in code
- ❌ Trust client-side validation
- ❌ Use HTTP in production
- ❌ Store passwords in plain text
- ❌ Ignore security warnings
- ❌ Give excessive permissions
- ❌ Skip audit logging

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Status**: Architecture defined, implementation pending  
**Priority**: High (Required for production deployment)
