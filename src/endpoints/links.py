from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import logger
from src.db.session import get_session
from src.endpoints.deps import get_current_active_user, get_current_user
from src.models.user import User
from src.schemas.analytics import LinkStats
from src.schemas.link import LinkCreate, LinkOut, LinkRedirect, LinkUpdate
from src.services.link_service import (
    cache_redirect,
    cache_stats,
    create_short_link,
    delete_link,
    get_cached_redirect,
    get_cached_stats,
    get_link_by_code,
    get_link_stats,
    invalidate_redirect_cache,
    invalidate_stats_cache,
    record_click,
    update_link,
)

router = APIRouter(prefix="/links", tags=["Links"])


@router.post("/shorten", response_model=LinkOut, status_code=status.HTTP_201_CREATED)
async def shorten_link(
    payload: LinkCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_current_user),
) -> LinkOut:
    user_id = current_user.id if current_user else None

    try:
        link = await create_short_link(db, payload, user_id=user_id)
        return link
    except ValueError as e:
        logger.warning(f"failed to create link {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{code}", response_model=LinkRedirect)
async def redirect_to_original(
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    cached_url = await get_cached_redirect(code)
    if cached_url:
        logger.debug(f"Cache hit for redirect: {code}")
        return RedirectResponse(url=cached_url, status_code=302)

    link = await get_link_by_code(db, code)
    if not link:
        logger.warning(f" Link not found: {code}")
        raise HTTPException(status_code=404, detail="Link not found")

    await cache_redirect(code, link.original_url)

    await record_click(
        db,
        link,
        ip_address=request.client.host if request.client else None,
        country_code=None,
        device_type=None,
    )

    logger.debug(f"Redirecting: {code} → {link.original_url}")
    return RedirectResponse(url=link.original_url, status_code=302)


@router.get("/{code}/info", response_model=LinkOut)
async def get_link_info(
    code: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> LinkOut:
    link = await get_link_by_code(db, code)
    if not link:
        raise HTTPException(status_code=404, detail="link not found")
    if link.user_id and link.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return link


@router.patch("/{code}", response_model=LinkOut)
async def update_link_endpoint(
    code: str,
    payload: LinkUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> LinkOut:
    link = await get_link_by_code(db, code)

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    if link.user_id and link.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    updated = await update_link(db, link, payload)
    await invalidate_redirect_cache(link.short_code)
    if link.custom_alias:
        await invalidate_redirect_cache(link.custom_alias)
    await invalidate_stats_cache(link.id)
    return updated


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link_endpoint(
    code: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> None:
    link = await get_link_by_code(db, code)

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    if link.user_id and link.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    await invalidate_redirect_cache(link.short_code)
    if link.custom_alias:
        await invalidate_redirect_cache(link.custom_alias)
    await invalidate_stats_cache(link.id)

    await delete_link(db, link)
    return  # 204 No Content


@router.get("/{code}/stats", response_model=LinkStats)
async def get_link_stats_endpoint(
    code: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> LinkStats:
    link = await get_link_by_code(db, code)
    if not link:
        raise HTTPException(404, "Link not found")

    cached_stats = await get_cached_stats(link.id)
    if cached_stats:
        logger.debug(f"🚀 Cache hit for stats: {link.id}")
        return cached_stats

    stats = await get_link_stats(db, link.id)
    stats["total_clicks"] = link.clicks_count

    await cache_stats(link.id, stats)

    return stats
