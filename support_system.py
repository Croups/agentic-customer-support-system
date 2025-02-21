from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json
import nest_asyncio
from pydantic import BaseModel, Field, field_validator
from pydantic_ai import Agent, ModelRetry, RunContext, Tool
from pydantic_ai.models.openai import OpenAIModel

nest_asyncio.apply()

class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    ON_HOLD = "on_hold"

class QueryCategory(str, Enum):
    SHIPPING = "shipping"
    BILLING = "billing"
    TECHNICAL = "technical"
    PRODUCT = "product"
    RETURNS = "returns"
    GENERAL = "general"

class CustomerTier(str, Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    VIP = "vip"

class Item(BaseModel):
    """Enhanced structure for order items."""
    item_id: str
    name: str
    quantity: int
    price: float
    sku: str
    category: str
    in_stock: bool = True
    warranty_info: Optional[str] = None
    return_eligible: bool = True
    return_window_days: int = 30
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v < 0:
            raise ValueError('Price must be non-negative')
        return v

class Order(BaseModel):
    """Enhanced structure for order details."""
    order_id: str
    status: OrderStatus
    items: List[Item]
    total_amount: float
    order_date: datetime
    shipping_address: Optional[str] = None
    billing_address: Optional[str] = None
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    customer_notes: Optional[str] = None
    is_gift: bool = False
    gift_message: Optional[str] = None
    payment_method: str = "credit_card"
    shipping_method: str = "standard"
    return_deadline: Optional[datetime] = None
    
    @field_validator('return_deadline')
    @classmethod
    def set_return_deadline(cls, v: Optional[datetime], info) -> datetime:
        if v is None and 'order_date' in info.data:
            return info.data['order_date'] + timedelta(days=30)
        return v

class CustomerInteraction(BaseModel):
    """Structure for tracking customer interactions."""
    interaction_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    channel: str
    query_type: QueryCategory
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    satisfaction_score: Optional[int] = None
    notes: Optional[str] = None

class CustomerDetails(BaseModel):
    """Enhanced structure for customer information."""
    customer_id: str
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    tier: CustomerTier = CustomerTier.BASIC
    orders: Optional[List[Order]] = None
    joined_date: datetime = Field(default_factory=datetime.utcnow)
    total_orders: int = 0
    total_spent: float = 0.0
    last_purchase_date: Optional[datetime] = None
    preferred_language: str = "en"
    marketing_preferences: Dict[str, bool] = Field(default_factory=dict)
    interaction_history: List[CustomerInteraction] = Field(default_factory=list)
    saved_payment_methods: List[Dict[str, str]] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None

    @field_validator('total_spent')
    @classmethod
    def validate_total_spent(cls, v: float) -> float:
        if v < 0:
            raise ValueError('Total spent must be non-negative')
        return v

class ResponseModel(BaseModel):
    """Enhanced structured response with metadata."""
    response: str
    needs_escalation: bool
    follow_up_required: bool
    sentiment: str = Field(description="Customer sentiment analysis")
    response_type: QueryCategory
    confidence_score: float = Field(ge=0.0, le=1.0)
    suggested_actions: List[str] = Field(default_factory=list)
    references: Dict[str, str] = Field(default_factory=dict)
    response_time: datetime = Field(default_factory=datetime.utcnow)
    auto_actions_taken: List[str] = Field(default_factory=list)
    knowledge_base_refs: List[str] = Field(default_factory=list)
    escalation_reason: Optional[str] = None
    satisfaction_prediction: float = Field(ge=0.0, le=1.0)

# Enhanced shipping information database
shipping_info_db: Dict[str, Dict[str, Any]] = {
    "#12345": {
        "status": "Shipped on 2024-12-01",
        "carrier": "FedEx",
        "tracking_number": "FDX123456789",
        "estimated_delivery": "2024-12-03",
        "current_location": "Chicago, IL",
        "updates": [
            {"timestamp": "2024-12-01 08:00", "status": "Package picked up"},
            {"timestamp": "2024-12-01 20:00", "status": "In transit"}
        ]
    },
    "#67890": {
        "status": "Out for delivery",
        "carrier": "UPS",
        "tracking_number": "1Z999999999",
        "estimated_delivery": "2024-12-02",
        "current_location": "Local Delivery Facility",
        "updates": [
            {"timestamp": "2024-12-01 07:00", "status": "Package processed"},
            {"timestamp": "2024-12-02 06:00", "status": "Out for delivery"}
        ]
    }
}

# Knowledge base for quick reference
knowledge_base: Dict[str, Any] = {
    "shipping_policies": {
        "standard": "5-7 business days",
        "express": "2-3 business days",
        "overnight": "Next business day"
    },
    "return_policies": {
        "standard": "30 days from delivery",
        "premium": "60 days from delivery",
        "vip": "90 days from delivery"
    },
    "warranty_info": {
        "electronics": "1 year standard warranty",
        "furniture": "5 year limited warranty",
        "accessories": "90 days limited warranty"
    }
}

model = OpenAIModel("gpt-4")

# Enhanced agent with additional context
agent = Agent(
    model=model,
    result_type=ResponseModel,
    deps_type=CustomerDetails,
    retries=3,
    system_prompt=(
        "You are an advanced customer support agent with deep knowledge of our systems. "
        "When customers ask about their order status:"
        "1. If they don't specify an order ID but have recent orders, tell them about their most recent order"
        "2. If they specify an order ID, look up that specific order"
        "3. Include shipping tracking information if available"
        "4. Be specific about dates and status"
        "\n\n"
        "Analyze queries carefully and provide structured, empathetic responses. "
        "Consider the customer's tier status when providing support. "
        "Maintain a professional yet friendly tone throughout the interaction."
    ),
)

@agent.system_prompt
async def add_customer_context(ctx: RunContext[CustomerDetails]) -> str:
    """Add comprehensive customer context to system prompt."""
    customer = ctx.deps
    
    # Get order details
    order_details = []
    if customer.orders:
        for order in customer.orders:
            order_info = {
                "order_id": order.order_id,
                "status": order.status.value,
                "order_date": order.order_date.strftime("%Y-%m-%d"),
                "tracking_number": order.tracking_number,
                "items": [{"name": item.name, "quantity": item.quantity} for item in order.items],
                "total_amount": order.total_amount
            }
            # Add shipping info if available
            if order.order_id in shipping_info_db:
                order_info["shipping_status"] = shipping_info_db[order.order_id]
            order_details.append(order_info)

    context = {
        "customer_details": {
            "name": customer.name,
            "tier": customer.tier.value,
            "total_orders": customer.total_orders,
        },
        "orders": order_details,
        "shipping_info_available": list(shipping_info_db.keys())
    }
    
    return json.dumps(context, default=str)

@agent.tool_plain()
def get_order_and_shipping_status(order_id: Optional[str] = None) -> Dict[str, Any]:
    """Get detailed order and shipping status. If no order_id is provided, returns the most recent order."""
    try:
        # Get the customer's orders from context
        customer = agent.current_context.deps
        
        if not customer.orders:
            return {
                "status": "error",
                "message": "No orders found for this customer.",
                "data": None
            }
        
        if order_id:
            # Clean up order_id format if needed
            if not order_id.startswith('#'):
                order_id = f"#{order_id.strip()}"
                
            # Find specific order
            order = next((o for o in customer.orders if o.order_id == order_id), None)
            if not order:
                return {
                    "status": "error",
                    "message": f"Order {order_id} not found. Please check the order number and try again.",
                    "data": None
                }
        else:
            # Get most recent order
            order = sorted(customer.orders, key=lambda x: x.order_date, reverse=True)[0]
        
        # Prepare response
        response = {
            "status": "success",
            "message": "Order information retrieved successfully",
            "data": {
                "order_id": order.order_id,
                "status": order.status.value,
                "order_date": order.order_date.strftime("%Y-%m-%d"),
                "total_amount": order.total_amount,
                "items": [{"name": item.name, "quantity": item.quantity} for item in order.items]
            }
        }
        
        # Add shipping info if available
        if order.order_id in shipping_info_db:
            response["data"]["shipping_info"] = shipping_info_db[order.order_id]
        
        return response
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"An error occurred while retrieving order information: {str(e)}",
            "data": None
        }


@agent.tool_plain()
def get_policy_info(policy_type: str, customer_tier: str) -> Dict[str, Any]:
    """Get policy information based on customer tier."""
    if policy_type not in knowledge_base:
        raise ModelRetry(f"Unknown policy type: {policy_type}")
    return knowledge_base[policy_type]

# Example usage
customer = CustomerDetails(
    customer_id="1",
    name="John Doe",
    email="john.doe@example.com",
    tier=CustomerTier.PREMIUM,
    interaction_history=[
        CustomerInteraction(
            interaction_id="INT001",
            channel="chat",
            query_type=QueryCategory.SHIPPING,
            resolved=True
        )
    ]
)

response = agent.run_sync(
    user_prompt="What's the status of my last order #12345?", 
    deps=customer
)