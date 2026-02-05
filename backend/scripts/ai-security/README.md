# AI Security Scripts

Production-ready AI-powered login security and analytics monitoring tools.

## Active Scripts

### `test_ai_system.py`

**Status:** ✅ Production Active

Comprehensive system health checker for all AI security components.

**Tests:**

1. Dependencies (PyOD, PostHog, Redis, user-agents)
2. Flask integration (app, blueprints, database)
3. Anomaly detector (IForest training and scoring)
4. Redis connection (optional session management)
5. PostHog configuration (API key validation)
6. Database (user count, sample data)

**Usage:**

```bash
python scripts/ai-security/test_ai_system.py
```

**Output:** 6-component system status summary

---

### `test_posthog.py`

**Status:** ✅ Production Active

Validates PostHog analytics integration and event delivery.

**Tests:**

- API key validation
- Client initialization
- Test event transmission
- Dashboard connectivity

**Usage:**

```bash
python scripts/ai-security/test_posthog.py
```

**Expected:** Test event appears in PostHog dashboard within 60 seconds

---

### `train_login_security.py`

**Status:** ✅ Production Active

Trains the Isolation Forest anomaly detection model on login history.

**Process:**

1. Extracts real login events from database
2. Adds synthetic anomalies for balanced training
3. Trains IForest model with 5% contamination rate
4. Saves model to `models/login_detector.pkl`

**Usage:**

```bash
python scripts/ai-security/train_login_security.py
```

**When to Run:**

- After user base grows (every 100-500 new users)
- Weekly for active systems
- After detecting unusual pattern clusters

**Output:** Model file saved to `models/login_detector.pkl`

---

## Production Status

All scripts are **actively monitoring** the production system:

- **AI Anomaly Detection:** ✅ Active (threshold: 0.7)
- **PostHog Analytics:** ✅ Active (API key configured)
- **Device Fingerprinting:** ✅ Active (user-agents parser)
- **Email Verification:** ✅ Active (suspicious login challenge)
- **Login History Tracking:** ✅ Active (all events logged)

## Configuration

### Required Environment Variables (.env)

```bash
POSTHOG_API_KEY=phc_MQSIUsK4Ta36VOp8QESAFAD5W0c22nDv5T5m9GDVO1C
POSTHOG_HOST=https://app.posthog.com
DATABASE_URL=your_database_url
```

### Optional (Advanced)

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=optional
```

## Dependencies

```
pyod==1.1.0              # Anomaly detection
posthog==3.1.0           # Analytics tracking
redis==5.0.1             # Session management (optional)
user-agents              # Device fingerprinting
Flask-Bcrypt             # Password hashing
```

## Cost

**Total:** $0/month (all free tier)

- PyOD: Free (open source)
- PostHog: Free tier (1M events/month)
- Redis: Free (localhost, optional)
- user-agents: Free (open source)

## Monitoring Dashboard

**PostHog:** https://app.posthog.com

- Real-time event tracking
- User behavior analytics
- Funnel analysis
- Retention metrics

## Support

For issues or questions about AI security:

1. Check system status: `python scripts/ai-security/test_ai_system.py`
2. Verify PostHog: `python scripts/ai-security/test_posthog.py`
3. Retrain model: `python scripts/ai-security/train_login_security.py`
4. Review logs: `logs/` directory
5. Contact: dtb33@pm.me

---

**Last Updated:** January 30, 2026
**System Status:** 🟢 All Systems Operational
