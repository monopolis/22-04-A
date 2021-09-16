import asyncio
import contextlib
import datetime

import pytest

from discounter import discounts

# Pylint does not play nice with pytest fixtures...
# pylint: disable=redefined-outer-name


@contextlib.contextmanager
def _no_error():
    yield


@pytest.fixture
def discount():
    notifications = []

    async def notify(value):
        notifications.append(value)

    obj = discounts.Discount(
        discounts.VolatileStorage(), discounts.VolatileStorage(), notify
    )
    obj.notifications = notifications

    return obj


@pytest.fixture
def base_campaign():
    return discounts.Campaign(
        amount=(10, discounts.Currency.EUR),
        brand="Wayne Enterprises",
        voucher_expires=_date(day=10),
        campaign_begins=_date(day=1),
        campaign_ends=_date(day=10),
        max_issued=10,
        num_issued=0,
    )


def _date(
    year=2022, month=4, day=1, hour=0, minute=0, seconds=0
):  # pylint: disable=too-many-arguments
    return datetime.datetime(
        year, month, day, hour, minute, seconds, tzinfo=datetime.timezone.utc
    )


@pytest.mark.asyncio
async def test_can_register_campaign(discount, base_campaign):
    identifier = await discount.register_campaign(base_campaign)
    assert identifier


@pytest.mark.asyncio
async def test_issue_voucher_from_unregisterd_campaign(discount: discounts.Discount):
    whom = "Bruce Wayne"
    when = _date(day=2)
    identifier = "missing"

    with pytest.raises(discounts.InvalidCampaign):
        await discount.issue_voucher(identifier, whom=whom, when=when)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "when, handler",
    [
        (_date(month=1), pytest.raises(discounts.ExpiredCampaignError)),
        (_date(day=1), _no_error()),
        (_date(day=10), _no_error()),
        (_date(day=11), pytest.raises(discounts.ExpiredCampaignError)),
    ],
)
async def test_issue_voucher_from_registered_campaign(
    discount: discounts.Discount, base_campaign: discounts.Campaign, when, handler
):
    identifier = await discount.register_campaign(base_campaign)
    whom = "Bruce Wayne"

    with handler:
        voucher = await discount.issue_voucher(identifier, whom=whom, when=when)
        assert voucher.code
        assert voucher.issued == when
        assert voucher.claimant == str(whom)


@pytest.mark.asyncio
async def test_cant_issue_too_many_vouchers(
    discount: discounts.Discount, base_campaign: discounts.Campaign
):
    whom = "Bruce Wayne"
    when = _date(day=2)
    identifier = await discount.register_campaign(base_campaign)
    num_attempts = 1000

    tasks = await asyncio.gather(
        *[discount.issue_voucher(identifier, whom, when) for _ in range(num_attempts)],
        return_exceptions=True
    )

    num_exceptions = sum(
        1 for task in tasks if isinstance(task, discounts.ExpiredCampaignError)
    )
    assert num_exceptions == (num_attempts - base_campaign.max_issued)
