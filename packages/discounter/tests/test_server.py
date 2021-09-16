from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from discounter import server

# Pylint does not play nice with pytest fixtures...
# pylint: disable=redefined-outer-name


@pytest.fixture()
def client():
    return TestClient(server.get_application())


_VALID_CAMPAIGN: Dict[str, Any] = {
    "amount": 1,
    "currency": "USD",
    "voucher_expires": "2022-04-10T23:26:01.251Z",
    "campaign_begins": "2022-04-02T23:26:01.251Z",
    "campaign_ends": "2022-04-03T23:26:01.251Z",
    "max_issued": 1,
}


def test_valid_parameters_for_generate_codes(client):
    response = client.post(
        "/discounts/register",
        json=_VALID_CAMPAIGN,
        headers={"X-Current-Brand": "Wayne Enterprises"},
    )
    assert response.status_code == 200, f"{response.json()}"


@pytest.mark.parametrize(
    "params",
    [
        # Invalid amount
        {**_VALID_CAMPAIGN, "amount": 0},
        # Invalid max_issued
        {**_VALID_CAMPAIGN, "max_issued": 0},
        # Invalid currency
        {**_VALID_CAMPAIGN, "currency": "BTC"},
        # voucher expires before campaign ends
        {**_VALID_CAMPAIGN, "voucher_expires": _VALID_CAMPAIGN["campaign_ends"]},
        # campaign begins after campaign ends
        {
            **_VALID_CAMPAIGN,
            "campaign_ends": _VALID_CAMPAIGN["campaign_begins"],
            "campaign_begins": _VALID_CAMPAIGN["campaign_ends"],
        },
    ],
)
def test_invalid_parameters_for_generate_codes(client, params):
    response = client.post(
        "/discounts/register",
        json=params,
        headers={"X-Current-Brand": "Wayne Enterprises"},
    )
    assert response.status_code == 422, f"{response.json()}"


@pytest.fixture()
def identifier(client):
    response = client.post(
        "/discounts/register",
        json=_VALID_CAMPAIGN,
        headers={"X-Current-Brand": "Wayne Enterprises"},
    )
    return response.json()["identifier"]


def test_can_issue_voucher(client, identifier):
    response = client.post(
        f"/discounts/{identifier}", headers={"X-Current-User": "Bruce Wayne"}
    )
    assert response.status_code == 200, f"{response.json()}"


def test_cannot_issue_too_many_vouchers(client, identifier):
    response = client.post(
        f"/discounts/{identifier}", headers={"X-Current-User": "Bruce Wayne"}
    )
    assert response.status_code == 200, f"{response.json()}"
    response = client.post(
        f"/discounts/{identifier}", headers={"X-Current-User": "Bruce Wayne"}
    )
    assert response.status_code == 404, f"{response.json()}"


def test_cannot_register_campaign_without_brand(client):
    response = client.post(
        "/discounts/register",
        json=_VALID_CAMPAIGN,
    )
    assert response.status_code == 403, f"{response.json()}"


def test_cannot_issue_voucher_without_user(client, identifier):
    response = client.post(f"/discounts/{identifier}")
    assert response.status_code == 403, f"{response.json()}"
