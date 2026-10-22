from typing import List
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.entities import User
from backend.app.schemas.applications import RouteStageResponse, RouteTypeResponse
from backend.app.schemas.common import DataResponse
from backend.app.services.workflow_service import WorkflowService

router = APIRouter()


@router.get("/routes", response_model=DataResponse[List[RouteTypeResponse]], summary="List Active Workflow Routes")
def list_workflow_routes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves all currently active workflow routes and their configured stages.
    """
    routes = WorkflowService.list_active_routes(db)
    result = []
    for r in routes:
        stages = WorkflowService.get_route_stages(db, route_type_id=r.id, route_version=r.current_version)
        route_dict = {
            "id": r.id,
            "name": r.name,
            "code": r.code,
            "description": r.description,
            "is_active": r.is_active,
            "current_version": r.current_version,
            "stages": [RouteStageResponse.model_validate(s) for s in stages],
        }
        result.append(RouteTypeResponse.model_validate(route_dict))

    return {"data": result}


@router.get("/routes/{route_id}", response_model=DataResponse[RouteTypeResponse], summary="Get Workflow Route Specification")
def get_workflow_route(
    route_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves detailed specification of an active workflow route with all ordered stages.
    """
    route = WorkflowService.get_route_by_id(db, route_id)
    stages = WorkflowService.get_route_stages(db, route_type_id=route.id, route_version=route.current_version)

    route_data = {
        "id": route.id,
        "name": route.name,
        "code": route.code,
        "description": route.description,
        "is_active": route.is_active,
        "current_version": route.current_version,
        "stages": [RouteStageResponse.model_validate(s) for s in stages],
    }
    return {"data": RouteTypeResponse.model_validate(route_data)}
