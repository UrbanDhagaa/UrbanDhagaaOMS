import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


# ── Health check ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_healthcheck(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ── Full order workflow ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_seed_and_login(client: AsyncClient):
    # Seed admin (idempotent)
    seed_res = await client.post("/api/v1/auth/seed-admin")
    assert seed_res.status_code == 200

    # Login with admin
    login_res = await client.post("/api/v1/auth/login", json={
        "email": "admin@urbandhagaa.com",
        "password": "Admin@12345"
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Check /me
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "admin@urbandhagaa.com"

    import uuid
    uid = uuid.uuid4().hex[:6]

    # Create Customer
    cust_payload = {
        "company_name": f"Tata Consultancy Services {uid}",
        "customer_type": "CORPORATE",
        "gstin": "27AAACT2727Q1ZW",
        "payment_terms": "50_ADVANCE_50_DISPATCH",
        "credit_limit": 500000.0,
        "contacts": [{
            "name": "Rajesh Kumar",
            "email": "rajesh@tcs.com",
            "phone": "+91 9820012345",
            "designation": "Procurement Lead",
            "is_primary": True
        }],
        "addresses": [{
            "address_type": "BILLING",
            "address_line1": "TCS Olympus, Hiranandani",
            "city": "Mumbai",
            "state": "Maharashtra",
            "postal_code": "400076",
            "country": "India",
            "is_default": True
        }]
    }
    cust_res = await client.post("/api/v1/customers/", json=cust_payload, headers=headers)
    assert cust_res.status_code == 201
    customer = cust_res.json()
    assert customer["customer_code"].startswith("CUST-")
    customer_id = customer["id"]

    # Create Order
    order_payload = {
        "customer_id": customer_id,
        "category": "MER",
        "priority": "HIGH",
        "customer_po_reference": "PO-TCS-2026-99",
        "items": [
            {
                "item_name": "Premium Bio-Wash Polo T-Shirt (Navy Blue)",
                "specifications": {"size": "L", "gsm": 240, "embroidery": "Chest Left Logo"},
                "quantity": 100,
                "unit_price": 450.00,
                "tax_rate": 18.00
            },
            {
                "item_name": "Custom Metal Insulated Water Bottle 750ml",
                "specifications": {"colour": "Matte Black", "laser_engraving": "Yes"},
                "quantity": 100,
                "unit_price": 350.00,
                "tax_rate": 18.00
            }
        ]
    }
    ord_res = await client.post("/api/v1/orders/", json=order_payload, headers=headers)
    assert ord_res.status_code == 201
    order = ord_res.json()
    assert order["order_number"].startswith("UD-")
    assert order["order_status"] == "Draft"
    assert order["total_amount"] > 0
    order_id = order["id"]

    # Confirm Order
    confirm_res = await client.post(
        f"/api/v1/orders/{order_id}/confirm",
        json={"note": "Client approved sample"},
        headers=headers
    )
    assert confirm_res.status_code == 200
    confirmed_order = confirm_res.json()
    assert confirmed_order["order_status"] == "Confirmed"

    # Create order with manual company_name (without pre-existing customer_id)
    manual_order_payload = {
        "company_name": f"Zomato Media Private Limited {uid}",
        "category": "GFT",
        "priority": "MEDIUM",
        "items": [
            {
                "item_name": "Branded Ceramic Coffee Mug",
                "quantity": 25,
                "unit_price": 200.00,
                "tax_rate": 18.00
            }
        ]
    }
    manual_res = await client.post("/api/v1/orders/", json=manual_order_payload, headers=headers)
    assert manual_res.status_code == 201
    manual_order = manual_res.json()
    assert manual_order["order_number"].startswith("UD-")
    assert manual_order["customer"]["company_name"] == f"Zomato Media Private Limited {uid}"

    # Check Dashboard KPIs
    kpi_res = await client.get("/api/v1/reports/dashboard-kpis", headers=headers)
    assert kpi_res.status_code == 200
    kpis = kpi_res.json()
    assert kpis["total_orders"] >= 2
    assert kpis["confirmed_orders"] >= 1


    # Cancel manual_order and verify payment modifications are strictly blocked
    cancel_res = await client.post(
        f"/api/v1/orders/{manual_order['id']}/cancel",
        json={"reason": "Test cancellation"},
        headers=headers
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["order_status"] == "Cancelled"

    # Attempt to change payment status on cancelled order -> MUST fail with 400
    fail_status_res = await client.post(
        f"/api/v1/orders/{manual_order['id']}/status",
        json={
            "dimension": "payment",
            "new_status": "Partially Paid",
            "note": "Illegal payment status change"
        },
        headers=headers
    )
    assert fail_status_res.status_code == 400
    assert "Payment status and amount cannot be modified" in fail_status_res.json()["detail"]

    # Attempt to record payment allocation to cancelled order -> MUST fail with 400
    manual_cust_id = manual_order["customer"]["id"] if "customer" in manual_order and manual_order["customer"] else manual_order.get("customer_id")
    fail_pay_res = await client.post(
        "/api/v1/payments/",
        json={
            "customer_id": manual_cust_id,
            "amount": 1000.0,
            "payment_method": "NEFT",
            "received_date": "2026-10-22",
            "allocations": [
                {
                    "order_id": manual_order["id"],
                    "allocated_amount": 1000.0
                }
            ]
        },
        headers=headers
    )
    assert fail_pay_res.status_code == 400
    assert "Cannot allocate payment to cancelled order" in fail_pay_res.json()["detail"]

