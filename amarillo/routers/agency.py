import logging
import time
from typing import List

from fastapi import APIRouter, HTTPException, status, Depends

from requests.exceptions import HTTPError
from amarillo.models.Carpool import Carpool, Agency
from amarillo.routers.agencyconf import verify_api_key, verify_admin_api_key, verify_permission_for_same_agency_or_admin
from amarillo.services.agencies import AgencyService
from amarillo.services.importing import Ride2GoImporter, NoiImporter, AmarilloImporter
from amarillo.services.sync import Syncer
from amarillo.stores.filebasedstore import FileBasedStore
from amarillo.utils.container import container
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agency",
    tags=["agency"]
)

store = FileBasedStore()


@router.get("/{agency_id}",
            operation_id="getAgencyById",
            summary="Find agency by ID",
            response_model=Agency,
            description="Find agency by ID",
            # TODO next to the status codes are "Links". There is nothing shown now.
            # Either show something there, or hide the Links, or do nothing.
            responses={ 
                status.HTTP_404_NOT_FOUND: {"description": "Agency not found"},
            },
            )
async def get_agency(agency_id: str, admin_api_key: str = Depends(verify_api_key)) -> Agency:
    agencies: AgencyService = container['agencies']
    agency = agencies.get_agency(agency_id)
    agency_exists = agency is not None

    if not agency_exists:
        message = f"Agency with id {agency_id} does not exist."
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    logger.info(f"Get agency {agency_id}.")

    return agency

# TODO add push batch endpoint

@router.post("/{agency_id}/sync",
             operation_id="sync",
             summary="Synchronizes all carpool offers",
             response_model=List[Carpool],
             responses={
                 status.HTTP_200_OK: {
                     "description": "Carpool created"},
                 status.HTTP_404_NOT_FOUND: {
                     "description": "Agency does not exist"},
                 status.HTTP_500_INTERNAL_SERVER_ERROR: {
                     "description": "Import error"}
             })
async def sync(agency_id: str, requesting_agency_id: str = Depends(verify_api_key)) -> List[Carpool]:
    await verify_permission_for_same_agency_or_admin(agency_id, requesting_agency_id)

    try:
        agency = container["agencyconf"].get_agency_conf(agency_id)
        if agency is None or agency.offers_download_url is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Agency does not exist or does not support sync."
            )
        return await Syncer(store, container["agencyconf"]).sync(agency_id, agency.offers_download_url)

    except HTTPError:
        logger.warn("HTTPError on sync for agency %s", agency_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Error retrieving carpools from agency."
        )
    except ValueError:
        logger.warning("ValueError on sync for agency %s", agency_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agency does not exist or does not support sync."
        )
    except BaseException:
        logger.exception("BaseException on sync for agency %s", agency_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong during import."
        )