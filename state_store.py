"""Firestore-backed state with transactional, expiring ownership leases.

No cloud import or credentials are needed for the local watcher or unit tests.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone


class LeaseLost(RuntimeError):
    pass


class FirestoreStore:
    def __init__(self, project: str, database: str = "imax-watcher", client=None):
        from google.cloud import firestore
        self.firestore = firestore
        self.client = client or firestore.Client(project=project, database=database)
        self.ref = self.client.collection("watcher_states").document("imax")

    def _transaction(self, operation):
        @self.firestore.transactional
        def apply(transaction):
            snapshot = self.ref.get(transaction=transaction, timeout=15)
            return operation(transaction, snapshot.to_dict() or {})
        return apply(self.client.transaction(max_attempts=3))

    def acquire(self, owner: str, lease_seconds: int = 360):
        def operation(tx, data):
            now = datetime.now(timezone.utc)
            if data.get("lease_until", now) > now:
                return None
            state = json.loads(data.get("state_json", "{}"))
            tx.set(self.ref, {"lease_owner": owner,
                             "lease_until": now + timedelta(seconds=lease_seconds)}, merge=True)
            return state
        return self._transaction(operation)

    def _write(self, owner: str, state: dict, release: bool):
        encoded = json.dumps(state, sort_keys=True, separators=(",", ":"))
        if len(encoded.encode()) > 750_000:
            raise ValueError("State exceeds safety limit; refusing truncated state")

        def operation(tx, data):
            now = datetime.now(timezone.utc)
            if data.get("lease_owner") != owner or data.get("lease_until", now) <= now:
                raise LeaseLost("State ownership expired or changed")
            update = {"state_json": encoded, "updated_at": now}
            if release:
                update.update(lease_owner=None, lease_until=now)
            tx.set(self.ref, update, merge=True)
        self._transaction(operation)

    def save(self, owner: str, state: dict):
        self._write(owner, state, release=False)

    def release(self, owner: str, state: dict):
        self._write(owner, state, release=True)

    def seed(self, state: dict):
        """Import only once; never replace existing production state."""
        if not isinstance(state.get("movies"), dict):
            raise ValueError("Seed must contain a movies object")
        # Deployment imports a comparison baseline, never a health signal.
        clean = {"version": 3, "movies": state["movies"], "outbox": []}
        for movie in clean["movies"].values():
            movie.pop("last_success_at", None)
            movie.pop("last_attempt", None)
        for key in ("backoff_until", "backoff_reason"):
            if key in state:
                clean[key] = state[key]
        encoded = json.dumps(clean)
        if len(encoded.encode()) > 750_000:
            raise ValueError("Seed exceeds safety limit")

        def operation(tx, data):
            if data:
                raise ValueError("State already exists; seed import refused")
            tx.create(self.ref, {"state_json": encoded, "updated_at": datetime.now(timezone.utc)})
        self._transaction(operation)
