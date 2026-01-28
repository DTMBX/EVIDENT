# BarberX Quick Reference Card

## 🚀 Start Development

### Run Flask API Locally
```bash
cd C:\web-dev\github-repos\BarberX.info
python app.py
# API: http://localhost:5000/api/v1
```

### Test API with Postman
```bash
# Import collection
postman_collection.json

# Or use cURL
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test123!","name":"Test User"}'
```

### Build MAUI App
```bash
cd C:\web-dev\github-repos\BarberX.info\src\BarberX.MatterDocket.MAUI
dotnet build
```

---

## 📍 Key Files

| File | Purpose |
|------|---------|
| `API-REFERENCE.md` | Complete API documentation |
| `API-QUICK-START.md` | 5-minute API tutorial |
| `postman_collection.json` | Postman API tests |
| `api/auth.py` | JWT authentication |
| `api/upload.py` | File upload endpoints |
| `api/analysis.py` | AI analysis endpoints |
| `Services/AuthService.cs` | MAUI auth service |
| `Services/UploadService.cs` | MAUI upload service |
| `Models/ApiModels.cs` | API response models |

---

## 🔐 Authentication Flow

```
1. POST /api/v1/auth/register → Get token
2. Store token securely
3. Use: Authorization: Bearer <token>
4. POST /api/v1/auth/refresh → Renew token
```

---

## 📤 Upload Flow

```
1. Login → Get JWT token
2. POST /api/v1/upload/pdf (with file)
3. Get file_id from response
4. POST /api/v1/analysis/start (with file_id)
5. Poll GET /api/v1/analysis/{id}/status
6. GET /api/v1/analysis/{id} → Get results
```

---

## 💳 Billing Flow

```
1. POST /api/v1/billing/create-checkout-session
2. Open checkout.url in browser
3. User pays on Stripe
4. Webhook updates user tier
5. Refresh user data
```

---

## 🎯 API Endpoints (Quick List)

### Auth (`/api/v1/auth`)
- `POST /register` - Create account
- `POST /login` - Get JWT token
- `POST /refresh` - Refresh token
- `GET /me` - Get current user
- `POST /logout` - Logout

### Upload (`/api/v1/upload`)
- `POST /pdf` - Upload PDF
- `POST /video` - Upload video
- `GET /status/{id}` - Check status

### Analysis (`/api/v1/analysis`)
- `POST /start` - Start analysis
- `GET /{id}` - Get results
- `GET /{id}/status` - Check status
- `GET /list` - List analyses

### User (`/api/v1/user`)
- `GET /profile` - Get profile
- `PUT /profile` - Update profile
- `POST /change-password` - Change password
- `GET /subscription` - Get subscription
- `GET /usage` - Get usage stats

### Billing (`/api/v1/billing`)
- `POST /create-checkout-session` - Stripe checkout
- `POST /portal` - Billing portal
- `POST /webhook` - Stripe webhooks

---

## 🔧 MAUI Services (Quick Reference)

```csharp
// Login
var authService = new AuthService(apiService);
var result = await authService.LoginAsync(email, password);

// Upload
var uploadService = new UploadService(apiService);
var upload = await uploadService.UploadPdfAsync(filePath);

// Analyze
var analysisService = new AnalysisService(apiService);
var analysis = await analysisService.StartAnalysisAsync(upload.FileId);

// Get User
var userService = new UserService(apiService);
var user = await userService.GetProfileAsync();

// Checkout
var billingService = new BillingService(apiService);
var checkout = await billingService.CreateCheckoutSessionAsync(priceId, tier);
```

---

## 🐛 Debugging

### API Not Responding
```bash
# Check if Flask is running
netstat -an | findstr 5000

# Check API logs
tail -f logs/barberx.log

# Test API directly
curl http://localhost:5000/api/v1/auth/login
```

### Token Expired
```csharp
// Auto-refresh in AuthService
await authService.IsAuthenticatedAsync(); // Refreshes if needed
```

### CORS Errors
```python
# Check CORS_ORIGINS in .env
CORS_ORIGINS=http://localhost:5000,https://barberx.info
```

---

## 📊 Tier Limits

| Tier | PDF Size | Video Size | AI Analysis |
|------|----------|------------|-------------|
| FREE | 10 MB | ❌ | ❌ |
| PRO | 100 MB | 1 GB | ✅ |
| PREMIUM | 500 MB | 5 GB | ✅ |
| ENTERPRISE | 5 GB | 20 GB | ✅ |

---

## 🚀 Deploy Commands

### Production Deployment
```bash
git add .
git commit -m "feat: Add REST API v1 + MAUI services"
git push origin main
# Render.com auto-deploys
```

### Environment Variables (Render.com)
```
SECRET_KEY=<generate with: python -c 'import secrets; print(secrets.token_hex(32))'>
DATABASE_URL=<postgresql connection string>
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
CORS_ORIGINS=https://barberx.info,https://www.barberx.info
```

---

## 📞 Support

- **Docs:** `API-REFERENCE.md`
- **Tutorial:** `API-QUICK-START.md`
- **MAUI Guide:** `PHASE-2-MAUI-PROGRESS.md`
- **Summary:** `SESSION-SUMMARY.md`

---

## ✅ Status

- **Phase 1 (API):** ✅ COMPLETE
- **Phase 2 (MAUI):** 🔧 50% COMPLETE
- **Phase 3 (UI):** 📋 PENDING
- **Phase 4 (Testing):** 📋 PENDING
- **Phase 5 (Deploy):** 📋 PENDING

**Next:** Complete MAUI services → Build ViewModels → Create UI
