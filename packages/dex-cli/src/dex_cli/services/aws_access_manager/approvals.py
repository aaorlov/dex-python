from __future__ import annotations

from typing import Any, Literal

import httpx

from dex_cli.config import get_account
from dex_cli.utils import time_left

SortBy = Literal["createdAt", "updatedAt"]
Order = Literal["asc", "desc"]
Mode = Literal["owner", "approver"]
RequestStatus = Literal["GRANTED", "PENDING", "REJECTED", "EXPIRED"]

PRESELECTED_PAIRS: frozenset[tuple[str, str]] = frozenset({
  ("D_RVT_VEHICLEAPPS", "PowerUser"),
  ("P_RVT_SERVICES", "ConnectedServicesLead"),
  ("S_RVT_VEHICLEAPPS", "PowerUser"),
})


class ApprovalsService:
  """Interact with the pre-approvals API."""

  def __init__(self, id_token: str, alias: str) -> None:
    self._client = httpx.Client(
      headers={"Authorization": f"Bearer {id_token}"},
      timeout=15,
    )
    self._base_url = get_account(alias).api_url

  def list_approved_preapprovals(
    self,
    *,
    limit: int = 25,
    mode: Mode = "owner",
    sort_by: SortBy = "createdAt",
    order: Order = "desc",
  ) -> list[dict[str, Any]]:
    """Fetch pre-approvals from the API.

    Maps to ``GET /pre-approvals?limit=…&mode=…&sortBy=…&order=…``.
    """
    response = self._client.get(
      f"{self._base_url}/pre-approvals",
      params={
        "limit": limit,
        "mode": mode,
        "sortBy": sort_by,
        "order": order,
      },
    )
    response.raise_for_status()
    all_preapprovals = response.json()["preApprovals"]
    approved = [p for p in all_preapprovals if p["status"] == "APPROVED"]
    return sorted(approved, key=lambda p: (p.get("account", {}).get("name", "").split("_", 1), p.get("permissionSet", {}).get("name", "")))

  def list_requests(
    self,
    *,
    limit: int = 25,
    mode: Mode = "owner",
    status: RequestStatus = "GRANTED",
  ) -> list[dict[str, Any]]:
    """Fetch access requests from the API.

    Maps to ``GET /requests?limit=…&mode=…&status=…``.
    """
    response = self._client.get(
      f"{self._base_url}/requests",
      params={
        "limit": limit,
        "mode": mode,
        "status": status,
      },
    )
    response.raise_for_status()
    return response.json()["requests"]

  def list_preapproval_choices(self) -> list[dict[str, Any]]:
    """Combine pre-approvals and requests into selectable choices.

    Returns a list of dicts with keys:
      - ``label``: display string with account, permission set, expiry, and ACTIVE status
      - ``item``: the original pre-approval dict
      - ``is_active``: ``True`` if a matching GRANTED request already exists
      - ``is_preselected``: ``True`` if the (account, permission set) pair is in
        ``PRESELECTED_PAIRS`` and the choice is not already active
    """
    preapprovals = self.list_approved_preapprovals()
    requests = self.list_requests()

    granted_preapproval_ids: set[str] = {
      r["preApprovalId"]
      for r in requests
      if r.get("status") == "GRANTED" and "preApprovalId" in r
    }

    choices: list[dict[str, Any]] = []
    for item in preapprovals:
      preapproval_id = item.get("id", "")
      is_active = preapproval_id in granted_preapproval_ids
      acct = item.get("account", {}).get("name", item.get("accountId", ""))
      ps = item.get("permissionSet", {}).get("name", item.get("permissionSetId", ""))
      expires = time_left(item.get("expiresAt", ""))
      label = f"{acct} / {ps} (expires in {expires})"
      is_preselected = not is_active and (acct, ps) in PRESELECTED_PAIRS
      choices.append({
        "label": label,
        "item": item,
        "is_active": is_active,
        "is_preselected": is_preselected,
      })

    return choices

  def create_request(
    self,
    preapproval: dict[str, Any],
    *,
    ticket_number: str = "N/A"
  ) -> dict[str, Any]:
    """Create an access request from a pre-approval.

    Maps to ``POST /requests``.
    """
    account_data = preapproval.get("account", {})
    ps_data = preapproval.get("permissionSet", {})

    payload = {
      "accountId": account_data.get("id", preapproval.get("accountId", "")),
      "accountName": account_data.get("name", ""),
      "accountEmail": account_data.get("email", ""),
      "isSoxCompliant": account_data.get("isSoxCompliant", False),
      "duration": 43200,
      "ticketNumber": ticket_number,
      "description": "",
      "preApprovalId": preapproval["id"],
      "permissionSetId": ps_data.get("id", preapproval.get("permissionSetId", "")),
      "permissionSetName": ps_data.get("name", ""),
    }

    response = self._client.post(f"{self._base_url}/requests", json=payload)
    response.raise_for_status()
    return response.json()["request"]

  def close(self) -> None:
    self._client.close()

  def __enter__(self) -> ApprovalsService:
    return self

  def __exit__(self, *_: object) -> None:
    self.close()
