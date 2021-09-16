import datetime
from typing import Optional

import pydantic
import uvicorn
from fastapi import Depends, Header, HTTPException, applications, routing

from discounter import discounts, my_logging

router = routing.APIRouter()


class DiscountProxy:
    def __init__(self) -> None:
        self._proxy: Optional[discounts.Discount] = None

    def inject(self, proxy: discounts.Discount) -> None:
        self._proxy = proxy

    async def __call__(self) -> discounts.Discount:
        assert self._proxy is not None
        return self._proxy


discount_proxy = DiscountProxy()

# TODO: Replace this with OpenID Connect
async def current_user(x_current_user: str = Header(None)) -> str:
    if x_current_user is None:
        raise HTTPException(status_code=403, detail="X-Current-User header missing")

    return x_current_user


# TODO: Replace this with OpenID Connect
async def current_brand(x_current_brand: str = Header(None)) -> str:
    if x_current_brand is None:
        raise HTTPException(status_code=403, detail="X-Current-Brand header missing")

    return x_current_brand


def _format_rfc3339(v: datetime.datetime) -> str:
    return v.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _rfc339_now() -> str:
    return _format_rfc3339(datetime.datetime.now(tz=datetime.timezone.utc))


class CampaignModel(pydantic.BaseModel):
    amount: pydantic.PositiveInt
    currency: discounts.Currency
    voucher_expires: datetime.datetime
    campaign_begins: datetime.datetime
    campaign_ends: datetime.datetime
    max_issued: pydantic.PositiveInt

    @pydantic.root_validator
    def validate_dates(cls, values):  # pylint: disable=no-self-use, no-self-argument
        voucher_expires = values["voucher_expires"]
        campaign_begins = values["campaign_begins"]
        campaign_ends = values["campaign_ends"]

        if campaign_begins >= campaign_ends:
            raise ValueError(
                f"Invalid `campaign_begins`: was {campaign_begins} "
                f"but must be greater than {campaign_ends}"
            )

        if voucher_expires <= campaign_ends:
            raise ValueError(
                f"Invalid `voucher_expires` value: was {voucher_expires} "
                f"but must be greater than {campaign_ends}"
            )

        return values


class CampaignReply(pydantic.BaseModel):
    identifier: str


class VoucherReply(pydantic.BaseModel):
    code: str
    amount: int
    currency: discounts.Currency
    brand: str
    voucher_expires: str


class HealthReply(pydantic.BaseModel):
    when: str
    status: str


@router.get("/health", response_model=HealthReply)
def health_endpoint():
    return HealthReply(
        when=_rfc339_now(),
        status="healthy",
    )


@router.post("/discounts/register", response_model=CampaignReply)
async def register_campaign(
    value: CampaignModel, brand=Depends(current_brand), discount=Depends(discount_proxy)
):
    campaign = discounts.Campaign(
        amount=(value.amount, value.currency),
        brand=brand,
        voucher_expires=value.voucher_expires,
        campaign_begins=value.campaign_begins,
        campaign_ends=value.campaign_ends,
        max_issued=value.max_issued,
        num_issued=0,
    )
    identifier = await discount.register_campaign(campaign)

    return CampaignReply(identifier=str(identifier))


@router.post("/discounts/{identifier}", response_model=VoucherReply)
async def issue_voucher(
    identifier, discount=Depends(discount_proxy), user=Depends(current_user)
):
    try:
        voucher = await discount.issue_voucher(
            identifier, whom=user, when=datetime.datetime.now(tz=datetime.timezone.utc)
        )
    except (discounts.InvalidCampaign) as e:
        raise HTTPException(status_code=404, detail="Invalid campaign") from e
    except discounts.ExpiredCampaignError as e:
        raise HTTPException(status_code=404, detail="Expired campaign") from e
    except discounts.CampaignException as e:
        raise HTTPException(status_code=500) from e

    return VoucherReply(
        code=voucher.code,
        amount=voucher.amount[0],
        currency=voucher.amount[1],
        brand=voucher.brand,
        voucher_expires=_format_rfc3339(voucher.voucher_expires),
    )


def get_application(**options) -> applications.FastAPI:
    discount_proxy.inject(
        discounts.Discount(
            campaign_storage=discounts.VolatileStorage(),
            voucher_storage=discounts.VolatileStorage(),
            notify_fn=discounts.LogNotifier(),
        )
    )

    app = applications.FastAPI(**options)
    app.include_router(router)

    return app


def _server(
    app: applications.FastAPI,
) -> uvicorn.Server:
    kwargs = {
        "log_config": None,
        "lifespan": "on",
    }
    return uvicorn.Server(config=uvicorn.Config(app=app, **kwargs))


def main() -> None:
    my_logging.setup(__name__)
    server = _server(get_application())
    server.run()


def develop() -> None:
    my_logging.setup(__name__)
    server = _server(get_application(debug=True))
    server.run()
