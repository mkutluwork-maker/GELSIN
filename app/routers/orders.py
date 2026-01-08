from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..deps import get_db, require_roles, get_current_user
from ..models import User, UserRole, Restaurant, MenuItem, Order, OrderItem, Delivery, OrderStatus
from ..schemas import OrderCreate, OrderOut

router = APIRouter(prefix="/orders", tags=["orders"])

def compute_total(items: list[OrderItem]) -> float:
    return float(sum(i.price_snapshot * i.qty for i in items))

@router.post("", response_model=OrderOut)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.CUSTOMER)),
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == payload.restaurant_id).first()
    if not restaurant or not restaurant.is_open:
        raise HTTPException(status_code=400, detail="Restaurant not available")

    if not payload.items:
        raise HTTPException(status_code=400, detail="Order must contain at least 1 item")

    # mock payment
    if not payload.mock_payment_success:
        raise HTTPException(status_code=400, detail="Mock payment failed")

    order = Order(
        customer_id=user.id,
        restaurant_id=payload.restaurant_id,
        address_text=payload.address_text,
        status=OrderStatus.PAID,
        total=0.0,
    )
    db.add(order)
    db.flush()

    order_items: list[OrderItem] = []
    for it in payload.items:
        mi = db.query(MenuItem).filter(MenuItem.id == it.menu_item_id, MenuItem.is_active == True).first()
        if not mi or mi.restaurant_id != payload.restaurant_id:
            raise HTTPException(status_code=400, detail=f"Invalid menu item: {it.menu_item_id}")

        oi = OrderItem(
            order_id=order.id,
            menu_item_id=mi.id,
            name_snapshot=mi.name,
            price_snapshot=mi.price,
            qty=it.qty,
        )
        order_items.append(oi)
        db.add(oi)

    db.add(Delivery(order_id=order.id, courier_id=None))
    db.flush()

    order.total = compute_total(order_items)

    db.commit()
    db.refresh(order)
    return order

@router.get("/me", response_model=list[OrderOut])
def my_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role == UserRole.CUSTOMER:
        return db.query(Order).filter(Order.customer_id == user.id).order_by(Order.id.desc()).all()

    if user.role == UserRole.RESTAURANT:
        r = db.query(Restaurant).filter(Restaurant.owner_user_id == user.id).first()
        if not r:
            return []
        return db.query(Order).filter(Order.restaurant_id == r.id).order_by(Order.id.desc()).all()

    if user.role == UserRole.COURIER:
        return (
            db.query(Order)
            .join(Delivery, Delivery.order_id == Order.id)
            .filter(Delivery.courier_id == user.id)
            .order_by(Order.id.desc())
            .all()
        )

    return db.query(Order).order_by(Order.id.desc()).all()

@router.patch("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.CUSTOMER))):
    order = db.get(Order, order_id)
    if not order or order.customer_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status not in (OrderStatus.PAID, OrderStatus.CREATED):
        raise HTTPException(status_code=400, detail="Cannot cancel at this stage")

    order.status = OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)
    return order

@router.patch("/{order_id}/accept", response_model=OrderOut)
def restaurant_accept(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.RESTAURANT))):
    r = db.query(Restaurant).filter(Restaurant.owner_user_id == user.id).first()
    if not r:
        raise HTTPException(status_code=400, detail="Restaurant not found for user")

    order = db.get(Order, order_id)
    if not order or order.restaurant_id != r.id:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.PAID:
        raise HTTPException(status_code=400, detail="Order not in PAID status")

    order.status = OrderStatus.ACCEPTED
    db.commit()
    db.refresh(order)
    return order

@router.patch("/{order_id}/reject", response_model=OrderOut)
def restaurant_reject(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.RESTAURANT))):
    r = db.query(Restaurant).filter(Restaurant.owner_user_id == user.id).first()
    if not r:
        raise HTTPException(status_code=400, detail="Restaurant not found for user")

    order = db.get(Order, order_id)
    if not order or order.restaurant_id != r.id:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.PAID:
        raise HTTPException(status_code=400, detail="Order not in PAID status")

    order.status = OrderStatus.REJECTED
    db.commit()
    db.refresh(order)
    return order

@router.patch("/{order_id}/pickup", response_model=OrderOut)
def courier_pickup(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.COURIER))):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.ACCEPTED:
        raise HTTPException(status_code=400, detail="Order not ready for pickup")

    delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
    if not delivery:
        raise HTTPException(status_code=400, detail="Delivery record missing")

    if delivery.courier_id and delivery.courier_id != user.id:
        raise HTTPException(status_code=400, detail="Order already assigned")

    delivery.courier_id = user.id
    order.status = OrderStatus.PICKED_UP
    db.commit()
    db.refresh(order)
    return order

@router.patch("/{order_id}/deliver", response_model=OrderOut)
def courier_deliver(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.COURIER))):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
    if not delivery or delivery.courier_id != user.id:
        raise HTTPException(status_code=403, detail="Not your delivery")

    if order.status != OrderStatus.PICKED_UP:
        raise HTTPException(status_code=400, detail="Order not picked up")

    order.status = OrderStatus.DELIVERED
    db.commit()
    db.refresh(order)
    return order
