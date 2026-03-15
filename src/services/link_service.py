import json
import secrets
import string
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.logger import logger
from src.core.redis_client import redis_client
from src.models.click_events import ClickEvent
from src.models.links import Link
from src.schemas.link import LinkCreate, LinkUpdate

ALPHABET = string.ascii_letters + string.digits


async def cache_redirect(code: str, url: str, ttl: int | None = None) -> None:
    ttl = ttl or settings.REDIS_CACHE_TTL_REDIRECT
    await redis_client.setex(f"redirect:{code}", ttl, url)


async def get_cached_redirect(code: str) -> str | None:
    return await redis_client.get(f"redirect:{code}")  # type: ignore[no-any-return]


async def invalidate_redirect_cache(code: str) -> None:
    await redis_client.delete(f"redirect:{code}")


async def cache_stats(
    link_id: int, stats: dict[str, Any], ttl: int | None = None
) -> None:
    ttl = ttl or settings.REDIS_CACHE_TTL_STATS
    await redis_client.setex(f"stats:{link_id}", ttl, json.dumps(stats))


async def get_cached_stats(link_id: int) -> dict[str, Any] | None:
    data = await redis_client.get(f"stats:{link_id}")
    return json.loads(data) if data else None  # type: ignore[no-any-return]


async def invalidate_stats_cache(link_id: int) -> None:
    await redis_client.delete(f"stats:{link_id}")


async def cache_search(original_url: str, short_code: str, ttl: int = 1800) -> None:
    import hashlib

    url_hash = hashlib.md5(original_url.encode()).hexdigest()
    await redis_client.setex(f"search:{url_hash}", ttl, short_code)


async def get_cached_search(original_url: str) -> str | None:
    import hashlib

    url_hash = hashlib.md5(original_url.encode()).hexdigest()
    return await redis_client.get(f"search:{url_hash}")  # type: ignore[no-any-return]


def generate_short_code(length: int = 8) -> str:
    length = max(6, min(12, length))
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


async def is_code_available(session: AsyncSession, code: str) -> bool:
    result = await session.execute(
        select(Link.id).where((Link.short_code == code) | (Link.custom_alias == code))
    )
    return result.scalar_one_or_none() is None


async def create_short_link(
    session: AsyncSession,
    payload: LinkCreate,
    user_id: int | None = None,
) -> Link:
    logger.info(f"Creating short link for: {payload.original_url}")

    short_code = generate_short_code(length=8)

    for _ in range(5):
        if await is_code_available(session, short_code):
            break
        short_code = generate_short_code(length=8)
    else:
        logger.error("Failed to generate unique short_code")
        raise ValueError("Не удалось сгенерировать уникальный код")

    custom_alias = payload.custom_alias
    if custom_alias:
        if not await is_code_available(session, custom_alias):
            logger.warning(f"Custom alias already exists: {custom_alias}")
            raise ValueError("Этот алиас уже занят")

    expires_at_naive = None
    if payload.expires_at:
        if payload.expires_at.tzinfo is not None:
            expires_at_naive = payload.expires_at.replace(tzinfo=None)
        else:
            expires_at_naive = payload.expires_at

    link = Link(
        user_id=user_id,
        short_code=short_code,
        custom_alias=custom_alias,
        original_url=str(payload.original_url).strip(),
        expires_at=expires_at_naive,
    )

    session.add(link)
    await session.commit()
    await session.refresh(link)

    logger.info(f"Link created: {link.short_code} → {link.original_url[:50]}...")
    return link


async def get_link_by_code(session: AsyncSession, code: str) -> Link | None:
    logger.debug(f"Ищу активну ссылку для редиреска {code}")
    result = await session.execute(
        select(Link).where(
            Link.is_active == True,
            ((Link.short_code == code) | (Link.custom_alias == code)),
            (Link.expires_at.is_(None) | (Link.expires_at > func.now())),
        )
    )
    link = result.scalar_one_or_none()
    if link:
        logger.debug(f"Link found {link.short_code}")
    else:
        logger.debug(f"Linl not found {code}")
    return link


async def get_link_by_id(
    session: AsyncSession, link_id: int, user_id: int | None = None
) -> Link | None:
    logger.debug(f"loccong link bu id {link_id}")
    qwery = select(Link).where(Link.id == link_id)
    if user_id is not None:
        qwery = qwery.where(Link.user_id == user_id)
    result = await session.execute(qwery)
    return result.scalar_one_or_none()


async def update_link(session: AsyncSession, link: Link, payload: LinkUpdate) -> Link:
    logger.info(f"Update link {link.short_code}")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field == "expires_at" and value:
                if hasattr(value, "tzinfo") and value.tzinfo is not None:
                    value = value.replace(tzinfo=None)
            setattr(link, field, value)
    await session.commit()
    await session.refresh(link)
    logger.info(f"Update link {link.short_code}")
    return link


async def delete_link(session: AsyncSession, link: Link) -> bool:
    logger.info(f"delete link {link.short_code}")
    link.is_active = False
    await session.commit()
    return True


async def record_click(
    session: AsyncSession,
    link: Link,
    ip_address: str | None,
    country_code: str | None,
    device_type: str | None,
) -> ClickEvent:
    logger.debug(f"Record Ckickevent {link.short_code}")
    click = ClickEvent(
        link_id=link.id,
        ip_address=ip_address,
        country_code=country_code,
        device_type=device_type,
    )
    session.add(click)
    link.clicks_count += 1
    link.last_clicked_at = datetime.now(UTC).replace(tzinfo=None)
    # link.last_clicked_at = datetime.now(timezone.utc)
    await session.commit()
    logger.info(f"click recorded {link.short_code}")
    return click


async def get_link_stats(session: AsyncSession, link_id: int) -> dict:

    unique_ips_result = await session.execute(
        select(func.count(distinct(ClickEvent.ip_address))).where(
            ClickEvent.link_id == link_id
        )
    )
    unique_ips = unique_ips_result.scalar() or 0

    last_click_result = await session.execute(
        select(func.max(ClickEvent.created_at)).where(ClickEvent.link_id == link_id)
    )
    last_clicked_at = last_click_result.scalar()

    country_result = await session.execute(
        select(ClickEvent.country_code, func.count())
        .where(ClickEvent.link_id == link_id, ClickEvent.country_code.is_not(None))
        .group_by(ClickEvent.country_code)
    )
    clicks_by_country = {row[0]: row[1] for row in country_result.all()}

    device_result = await session.execute(
        select(ClickEvent.device_type, func.count())
        .where(ClickEvent.link_id == link_id, ClickEvent.device_type.is_not(None))
        .group_by(ClickEvent.device_type)
    )
    clicks_by_device = {row[0]: row[1] for row in device_result.all()}

    return {
        "total_clicks": None,
        "unique_ips": unique_ips,
        "last_clicked_at": last_clicked_at,
        "clicks_by_country": clicks_by_country,
        "clicks_by_device": clicks_by_device,
    }
