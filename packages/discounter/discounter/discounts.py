import asyncio
import dataclasses
import datetime
import enum
import logging
import uuid
from typing import Awaitable, Callable, Protocol, Tuple, TypeVar

logger = logging.getLogger(__name__)


class Currency(str, enum.Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    SEK = "SEK"


UserT = TypeVar("UserT")


class CampaignException(Exception):
    pass


class ExpiredCampaignError(CampaignException):
    pass


class InvalidCampaign(CampaignException):
    pass


@dataclasses.dataclass(frozen=True)
class _Base:
    amount: Tuple[int, Currency]
    brand: str
    voucher_expires: datetime.datetime


@dataclasses.dataclass(frozen=True)
class Campaign(_Base):
    campaign_begins: datetime.datetime
    campaign_ends: datetime.datetime
    max_issued: int
    num_issued: int

    # TODO: Validate the bounds here, rather than in the server


@dataclasses.dataclass(frozen=True)
class Voucher(_Base):
    claimant: str
    code: str
    issued: datetime.datetime
    consumed: bool

    @staticmethod
    def from_campaign(
        campaign: Campaign, whom: UserT, when: datetime.datetime
    ) -> "Voucher":
        if not campaign.campaign_begins <= when <= campaign.campaign_ends:
            raise ExpiredCampaignError

        if campaign.num_issued >= campaign.max_issued:
            raise ExpiredCampaignError

        claimant = str(whom)
        if not claimant:
            raise ValueError

        # TODO: Use nicer format
        code = str(uuid.uuid4())

        return Voucher(
            amount=campaign.amount,
            brand=campaign.brand,
            voucher_expires=campaign.voucher_expires,
            code=code,
            claimant=claimant,
            issued=when,
            consumed=False,
        )


class CampaignStorageT(Protocol):
    async def persist(self, obj: Campaign, identifier=None) -> str:
        ...

    async def get(self, key) -> Campaign:
        ...


class VoucherStorageT(Protocol):
    async def persist(self, obj: Voucher, identifier=None) -> str:
        ...

    async def get(self, key) -> Voucher:
        ...


class Discount:
    def __init__(
        self,
        campaign_storage: CampaignStorageT,
        voucher_storage: VoucherStorageT,
        notify_fn: Callable[[Voucher], Awaitable[None]],
    ) -> None:

        self._campaign_storage = campaign_storage
        self._voucher_storage = voucher_storage
        self._notify_fn = notify_fn

    async def register_campaign(self, campaign: Campaign) -> str:
        identifier = await self._campaign_storage.persist(campaign)
        return identifier

    async def view(self, identifier) -> Campaign:
        try:
            return await self._campaign_storage.get(identifier)
        except KeyError as err:
            raise InvalidCampaign from err

    async def issue_voucher(
        self, identifier: str, whom: UserT, when: datetime.datetime
    ):
        try:
            campaign = await self._campaign_storage.get(identifier)
        except KeyError as err:
            raise InvalidCampaign from err

        voucher = Voucher.from_campaign(campaign, whom, when)
        campaign = dataclasses.replace(campaign, num_issued=campaign.num_issued + 1)

        # TODO: Add constraints to limit voucher to one per user
        # TODO: Consider to handle the persistance in a transaction
        await self._voucher_storage.persist(voucher, voucher.code)
        await self._campaign_storage.persist(campaign, identifier)
        await self._notify_fn(voucher)

        return voucher


T = TypeVar("T")


class VolatileStorage:
    def __init__(self):
        self._database = {}
        self._lock = asyncio.Lock()

    async def persist(self, obj: T, identifier=None) -> str:
        async with self._lock:
            if identifier is None:
                identifier = str(uuid.uuid4())
                assert identifier not in self._database
            self._database[identifier] = obj

        return identifier

    async def get(self, identifier: str) -> T:
        async with self._lock:
            return self._database[identifier]


class LogNotifier:  # pylint: disable=too-few-public-methods
    async def __call__(self, value: Voucher) -> None:
        logger.error("Notifying brand about new voucher %s", value)
