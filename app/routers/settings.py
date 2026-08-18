from fastapi import APIRouter, Depends, HTTPException # type: ignore
from sqlalchemy.orm import Session # type: ignore

from app.db.database import get_db
from app.Schemas.app_connection import ( # type: ignore
    AppConnectionResponse,
)
from app.services.app_connection_service import (
    get_user_app_connections,
    connect_app,
    disconnect_app,
)

TEST_USER_ID = 1

router = APIRouter(
    prefix="/api/settings",
    tags=["Settings"],
)

@router.get(
    "/apps",
    response_model=list[AppConnectionResponse],
)
def get_connected_apps(
    db: Session = Depends(get_db),
):
    return get_user_app_connections(
        db=db,
        user_id=TEST_USER_ID,
    )
    

@router.post(
    "/apps/{app_id}/connect",
    response_model=AppConnectionResponse,
)
def connect_application(
    app_id: str,
    db: Session = Depends(get_db),
):
    allowed_apps = {
        "notion",
        "stackoverflow",
    }

    if app_id not in allowed_apps:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported app: {app_id}",
        )

    return connect_app(
        db=db,
        user_id=TEST_USER_ID,
        app_id=app_id,
    )
    

@router.delete(
    "/apps/{app_id}/disconnect",
    response_model=AppConnectionResponse,
)
def disconnect_application(
    app_id: str,
    db: Session = Depends(get_db),
):
    connection = disconnect_app(
        db=db,
        user_id=TEST_USER_ID,
        app_id=app_id,
    )

    if not connection:
        raise HTTPException(
            status_code=404,
            detail="App connection not found",
        )

    return connection