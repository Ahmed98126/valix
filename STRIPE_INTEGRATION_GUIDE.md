# Stripe Integration Guide for Invo Sync

## 🎯 Overview

Stripe integration for Invo Sync is **relatively straightforward** to implement. Here's what you need to know:

## ✅ Difficulty Level: **Easy to Medium**

### Why It's Easy:
1. **Stripe has excellent Python SDK** - `stripe` package is well-documented
2. **FastAPI integration is simple** - Just add endpoints
3. **Stripe Checkout** - Pre-built payment UI (easiest option)
4. **Webhooks** - Easy to set up for subscription management

### What Makes It Medium:
1. **Subscription management** - Need to track plans, billing cycles
2. **Webhook security** - Need to verify webhook signatures
3. **Database schema** - Need to add subscription tables

---

## 📋 Implementation Steps

### **Step 1: Install Stripe SDK**

```bash
pip install stripe
```

Add to `requirements.txt`:
```
stripe>=7.0.0
```

---

### **Step 2: Add Stripe Keys to Environment**

Update `.env`:
```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

---

### **Step 3: Create Subscription Model**

Add to `app/models.py`:
```python
class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    plan = Column(String, nullable=False)  # 'starter', 'professional', 'enterprise'
    status = Column(String, nullable=False)  # 'active', 'canceled', 'past_due'
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

### **Step 4: Create Payment Endpoints**

Add to `main.py`:
```python
import stripe
from app.config import STRIPE_SECRET_KEY

stripe.api_key = STRIPE_SECRET_KEY

@app.post("/api/create-checkout-session")
async def create_checkout_session(
    plan: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create Stripe Checkout session."""
    tenant_id = get_tenant_id(user, request)
    
    # Get plan price ID from Stripe
    price_ids = {
        'starter': 'price_...',
        'professional': 'price_...',
        'enterprise': 'price_...'
    }
    
    checkout_session = stripe.checkout.Session.create(
        customer_email=user.email,
        payment_method_types=['card'],
        line_items=[{
            'price': price_ids[plan],
            'quantity': 1,
        }],
        mode='subscription',
        success_url=f'https://yourdomain.com/success?session_id={{CHECKOUT_SESSION_ID}}',
        cancel_url='https://yourdomain.com/pricing',
        metadata={
            'tenant_id': tenant_id,
            'user_id': user.id
        }
    )
    
    return {'checkout_url': checkout_session.url}
```

---

### **Step 5: Handle Webhooks**

```python
@app.post("/api/stripe-webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle different event types
    if event['type'] == 'checkout.session.completed':
        # Subscription created
        session = event['data']['object']
        tenant_id = session['metadata']['tenant_id']
        # Create subscription record
        ...
    
    elif event['type'] == 'customer.subscription.updated':
        # Subscription updated
        ...
    
    elif event['type'] == 'customer.subscription.deleted':
        # Subscription canceled
        ...
    
    return {'status': 'success'}
```

---

### **Step 6: Add Pricing Page**

Create `templates/pricing.html` with:
- Plan selection
- "Subscribe" buttons that call `/api/create-checkout-session`
- Redirect to Stripe Checkout

---

## 🎨 UI Integration

### **Option 1: Stripe Checkout (Easiest)**
- Pre-built payment UI
- Handles all payment forms
- Mobile responsive
- Just redirect users to checkout URL

### **Option 2: Stripe Elements (More Control)**
- Custom payment form
- More design flexibility
- Requires more frontend work

**Recommendation**: Start with Stripe Checkout, upgrade to Elements later if needed.

---

## 📊 Subscription Management

### **Track Subscription Status**

Add middleware to check subscription:
```python
def check_subscription(user: User, session: Session):
    """Check if user's tenant has active subscription."""
    subscription = session.query(Subscription).filter(
        Subscription.tenant_id == user.tenant_id,
        Subscription.status == 'active'
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=403, detail="Subscription required")
    
    # Check if subscription is expired
    if subscription.current_period_end < datetime.utcnow():
        raise HTTPException(status_code=403, detail="Subscription expired")
```

---

## 🔒 Security Best Practices

1. **Never expose secret keys** - Only use in backend
2. **Verify webhook signatures** - Always validate Stripe webhooks
3. **Use HTTPS** - Required for Stripe
4. **Store customer IDs** - Link Stripe customers to tenants

---

## 📝 Next Steps

1. **Create Stripe account** - Get API keys
2. **Create products/prices** - Set up plans in Stripe Dashboard
3. **Test with test mode** - Use test cards
4. **Set up webhooks** - Point to your webhook endpoint
5. **Go live** - Switch to live mode when ready

---

## 💡 Estimated Implementation Time

- **Basic integration**: 2-4 hours
- **Full subscription management**: 1-2 days
- **Testing & polish**: 1 day

**Total**: ~3-4 days for complete implementation

---

## 🚀 Quick Start

1. Sign up at https://stripe.com
2. Get API keys from dashboard
3. Install: `pip install stripe`
4. Follow steps above
5. Test with Stripe test cards

**Stripe provides excellent documentation and support!**

