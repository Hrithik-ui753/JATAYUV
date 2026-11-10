<<<<<<< HEAD
﻿from fastapi import APIRouter, Depends, HTTPException
=======
from fastapi import APIRouter, Depends, HTTPException
>>>>>>> origin/main
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.mission import Mission
from backend.app.models.reconstruction import Reconstruction
from backend.app.models.user import User
<<<<<<< HEAD
from backend.app.schemas.reconstruction import MissionReconstructionResponse as ReconstructionResponse
=======
from backend.app.schemas.reconstruction import ReconstructionResponse
>>>>>>> origin/main
from backend.app.api.deps import get_current_user

router = APIRouter(tags=["Reconstructions"])


@router.get(
    "/reconstructions/{reconstruction_id}",
    response_model=ReconstructionResponse,
)
def get_reconstruction(
    reconstruction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reco = db.query(Reconstruction).filter(Reconstruction.id == reconstruction_id).first()
    if not reco:
        raise HTTPException(status_code=404, detail="Reconstruction not found")
    mission = db.query(Mission).filter(Mission.id == reco.mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Reconstruction mission not found")
    if current_user.role != "admin" and mission.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorised to view this reconstruction"
        )
    return ReconstructionResponse.model_validate(reco)
