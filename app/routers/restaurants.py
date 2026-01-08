from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..deps import get_db, require_roles
from ..models import Restaurant, MenuItem, UserRole, User
from ..schemas import RestaurantCreate, MenuItemCreate

router = APIRouter(prefix="/restaurants", tags=["restaurants"])

@router.get("")
def list_restaurants(db: Session = Depends(get_db)):
    return db.query(Restaurant).all()

@router.post("")
def create_restaurant(
    payload: RestaurantCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.RESTAURANT)),
):
    if db.query(Restaurant).filter(Restaurant.owner_user_id == user.id).first():
        raise HTTPException(status_code=400, detail="Restaurant already exists for this user")

    r = Restaurant(name=payload.name, address=payload.address, owner_user_id=user.id)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r

@router.get("/{restaurant_id}/menu")
def list_menu(restaurant_id: int, db: Session = Depends(get_db)):
    return db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id, MenuItem.is_active == True).all()

@router.post("/{restaurant_id}/menu")
def add_menu_item(
    restaurant_id: int,
    payload: MenuItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.RESTAURANT)),
):
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if r.owner_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your restaurant")

    item = MenuItem(restaurant_id=restaurant_id, name=payload.name, price=payload.price, is_active=True)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
