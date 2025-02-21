import streamlit as st
from datetime import datetime, timedelta
from support_system import (
    CustomerDetails, 
    CustomerTier, 
    Order,
    OrderStatus,
    Item,
    agent,
    shipping_info_db,
    knowledge_base
)

# Page configuration
st.set_page_config(
    page_title="Agentic Customer Support System",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    .css-1d391kg {
        padding: 1rem 1rem;
    }
    .status-badge {
        padding: 0.2rem 0.5rem;
        border-radius: 0.5rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .user-message {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .assistant-message {
        background-color: #e8f0fe;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
    
if 'current_customer' not in st.session_state:
    # Initialize demo customer
    st.session_state.current_customer = CustomerDetails(
        customer_id="CUST001",
        name="John Doe",
        email="john.doe@example.com",
        phone="+1234567890",
        tier=CustomerTier.PREMIUM,
        total_orders=5,
        total_spent=1500.50,
        last_purchase_date=datetime.utcnow() - timedelta(days=7),
        orders=[
            Order(
                order_id="#12345",
                status=OrderStatus.SHIPPED,
                items=[
                    Item(
                        item_id="ITEM001",
                        name="Premium Headphones",
                        quantity=1,
                        price=299.99,
                        sku="SKU123",
                        category="Electronics"
                    )
                ],
                total_amount=299.99,
                order_date=datetime.utcnow() - timedelta(days=7),
                shipping_address="123 Main St, Anytown, USA",
                tracking_number="FDX123456789"
            )
        ]
    )

# Sidebar - Customer Information
with st.sidebar:
    st.title("Customer Profile")
    
    # Profile header with tier badge
    st.markdown(f"""
        <h2 style='margin-bottom: 0;'>Customer Profile</h2>
        <span style='background-color: #1f77b4; color: white; padding: 2px 8px; border-radius: 10px;'>{st.session_state.current_customer.tier.value.upper()}</span>
    """, unsafe_allow_html=True)
    
    # Customer Information Card
    st.markdown("""---""")
    st.subheader("Basic Information")
    cols = st.columns(2)
    with cols[0]:
        st.markdown("**ID**")
        st.markdown("**Name**")
        st.markdown("**Email**")
        st.markdown("**Phone**")
        st.markdown("**Joined**")
    with cols[1]:
        st.markdown(f"`{st.session_state.current_customer.customer_id}`")
        st.markdown(st.session_state.current_customer.name)
        st.markdown(f"[{st.session_state.current_customer.email}](mailto:{st.session_state.current_customer.email})")
        st.markdown(st.session_state.current_customer.phone)
        st.markdown(st.session_state.current_customer.last_purchase_date.strftime('%Y-%m-%d'))

    # Customer Statistics
    st.markdown("""---""")
    st.subheader("Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Orders", st.session_state.current_customer.total_orders)
    with col2:
        st.metric("Total Spent", f"${st.session_state.current_customer.total_spent:.2f}")
    with col3:
        st.metric("Last Order", st.session_state.current_customer.last_purchase_date.strftime('%Y-%m-%d'))

    # Recent Orders
    st.markdown("""---""")
    st.subheader("Recent Orders")
    for order in st.session_state.current_customer.orders:
        with st.expander(f"Order {order.order_id}", expanded=True):
            # Order status badge
            status_color = {
                OrderStatus.SHIPPED: "#28a745",
                OrderStatus.PENDING: "#ffc107",
                OrderStatus.PROCESSING: "#17a2b8",
                OrderStatus.DELIVERED: "#28a745",
                OrderStatus.CANCELLED: "#dc3545"
            }.get(order.status, "#6c757d")
            
            st.markdown(f"""
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span>Order {order.order_id}</span>
                    <span style='background-color: {status_color}; color: white; padding: 2px 8px; border-radius: 10px;'>
                        {order.status.value.upper()}
                    </span>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
                **Date:** {order.order_date.strftime('%Y-%m-%d')}  
                **Total:** ${order.total_amount:.2f}
                
                **Items:**
            """)
            for item in order.items:
                st.markdown(f"• {item.name} (x{item.quantity})")

            if order.tracking_number and order.order_id in shipping_info_db:
                st.markdown("**Tracking Information**")
                tracking_info = shipping_info_db.get(order.order_id, {})
                if tracking_info:
                    st.markdown(f"""
                        **Carrier:** {tracking_info['carrier']}  
                        **Status:** {tracking_info['status']}  
                        **Location:** {tracking_info['current_location']}
                    """)

# Main chat area
main_container = st.container()
with main_container:
    st.title("AI Customer Support System")
    
    # Chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"""
                    <div class="user-message">
                        <strong>You:</strong><br>{message['content']}
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="assistant-message">
                        <strong>Support AI:</strong><br>{message['content']}
                    </div>
                """, unsafe_allow_html=True)
                if "metadata" in message:
                    with st.expander("Response Details"):
                        cols = st.columns(3)
                        with cols[0]:
                            st.markdown(f"**Sentiment:** {message['metadata']['sentiment']}")
                        with cols[1]:
                            st.markdown(f"**Confidence:** {message['metadata']['confidence_score']:.2%}")
                        with cols[2]:
                            st.markdown(f"**Type:** {message['metadata']['response_type']}")

    # Input area
    st.markdown("""---""")
    input_container = st.container()
    with input_container:
        col1, col2, col3 = st.columns([6, 2, 1])
        with col1:
            user_input = st.text_input("Type your message...", key="user_input", placeholder="Ask about orders, shipping, returns, or any other support...")
        with col2:
            send_pressed = st.button("Send Message", use_container_width=True)
        with col3:
            clear_pressed = st.button("Clear", use_container_width=True)

        if clear_pressed:
            st.session_state.chat_history = []
            st.rerun()

        if send_pressed and user_input:
            # Add user message to history
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input
            })
            
            try:
                # Get AI response
                response = agent.run_sync(
                    user_prompt=user_input,
                    deps=st.session_state.current_customer
                )
                
                # Add AI response to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response.data.response,
                    "metadata": {
                        "sentiment": response.data.sentiment,
                        "needs_escalation": response.data.needs_escalation,
                        "follow_up_required": response.data.follow_up_required,
                        "response_type": response.data.response_type.value,
                        "confidence_score": response.data.confidence_score,
                        "suggested_actions": response.data.suggested_actions
                    }
                })
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Knowledge base in collapsed sections at the bottom
st.markdown("""---""")
kb_container = st.container()
with kb_container:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.expander("📦 Shipping Policies"):
            for method, duration in knowledge_base["shipping_policies"].items():
                st.markdown(f"**{method.title()}**  \n{duration}")
    
    with col2:
        with st.expander("↩️ Return Policies"):
            for tier, policy in knowledge_base["return_policies"].items():
                st.markdown(f"**{tier.title()}**  \n{policy}")
    
    with col3:
        with st.expander("⚡ Warranty Information"):
            for category, info in knowledge_base["warranty_info"].items():
                st.markdown(f"**{category.title()}**  \n{info}")

if __name__ == "__main__":
    st.info("Customer Support System is ready to assist!")