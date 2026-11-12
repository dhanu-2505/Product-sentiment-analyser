from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import Product, SavedProduct, User
from app.services.auth import get_current_user

router = APIRouter(tags=['saved-products'])


class SaveProductRequest(BaseModel):
    product_id: int


@router.post('/saved-products', status_code=status.HTTP_201_CREATED)
def save_product(payload: SaveProductRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail='Product not found.')

    existing = db.query(SavedProduct).filter(SavedProduct.user_id == current_user.id, SavedProduct.product_id == payload.product_id).first()
    if existing:
        return {'id': existing.id, 'user_id': current_user.id, 'product_id': payload.product_id, 'saved': True}

    saved = SavedProduct(user_id=current_user.id, product_id=payload.product_id)
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return {'id': saved.id, 'user_id': current_user.id, 'product_id': payload.product_id, 'saved': True}


@router.get('/saved-products')
def list_saved_products(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = db.query(SavedProduct).filter(SavedProduct.user_id == current_user.id).order_by(SavedProduct.saved_at.desc()).all()
    return {'count': len(items), 'items': [{'id': item.id, 'product_id': item.product_id, 'saved_at': item.saved_at.isoformat()} for item in items]}


@router.get('/watchlist')
def get_watchlist(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = db.query(SavedProduct).filter(SavedProduct.user_id == current_user.id).order_by(SavedProduct.saved_at.desc()).all()
    payload = []
    for item in items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        payload.append({
            'id': item.id,
            'product_id': item.product_id,
            'saved_at': item.saved_at.isoformat() if item.saved_at else None,
            'product_name': product.name if product else 'Unknown product',
            'brand': product.brand if product else None,
            'category': product.category if product else None,
            'average_rating': float(product.average_rating or 0) if product else 0,
        })
    return {'count': len(payload), 'items': payload}


@router.post('/watchlist')
def add_watchlist_item(payload: SaveProductRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return save_product(payload=payload, db=db, current_user=current_user)


@router.delete('/saved-products/{saved_id}')
def remove_saved_product(saved_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(SavedProduct).filter(SavedProduct.id == saved_id, SavedProduct.user_id == current_user.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail='Saved product not found.')
    db.delete(item)
    db.commit()
    return {'deleted': True, 'saved_id': saved_id}
