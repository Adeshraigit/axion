from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthContext, get_current_user
from app.schemas.application import ApplicationCreate, ApplicationOut, ApplicationUpdate
from app.services.repositories.supabase_repository import supabase_repo

router = APIRouter()


@router.get("/{user_id}", response_model=list[ApplicationOut])
async def list_applications(
    user_id: str,
    auth: AuthContext = Depends(get_current_user),
) -> list[ApplicationOut]:
    if user_id != auth.user_id:
        raise HTTPException(status_code=403, detail="Forbidden: user mismatch")
    rows = await supabase_repo.list_applications(user_id, auth.access_token)
    return [ApplicationOut(**item) for item in rows]


@router.post("", response_model=ApplicationOut)
async def create_application(
    payload: ApplicationCreate,
    auth: AuthContext = Depends(get_current_user),
) -> ApplicationOut:
    if payload.user_id != auth.user_id:
        raise HTTPException(status_code=403, detail="Forbidden: user mismatch")
    created = await supabase_repo.create_application(
        user_id=payload.user_id,
        payload=payload,
        token=auth.access_token,
    )
    return ApplicationOut(**created)


@router.patch("/{user_id}/{application_id}", response_model=ApplicationOut)
async def update_application(
    user_id: str,
    application_id: str,
    payload: ApplicationUpdate,
    auth: AuthContext = Depends(get_current_user),
) -> ApplicationOut:
    if user_id != auth.user_id:
        raise HTTPException(status_code=403, detail="Forbidden: user mismatch")
    await supabase_repo.update_application(
        user_id=user_id,
        application_id=application_id,
        payload=payload,
        token=auth.access_token,
    )
    rows = await supabase_repo.list_applications(user_id, auth.access_token)
    for item in rows:
        if item.get("id") == application_id:
            return ApplicationOut(**item)
    raise HTTPException(status_code=404, detail="Application not found")
