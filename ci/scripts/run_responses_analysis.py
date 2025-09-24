"""Execute Responses API calls for daily diary analysis."""

from __future__ import annotations

import json
import datetime as dt
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .prepare_responses_payload import build_payload


def _emit_log(event: str, **payload: Any) -> None:
    entry: Dict[str, Any] = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "event": event,
        **payload,
    }
    print(json.dumps(entry, default=str))


def get_openai_client():  # pragma: no cover - thin wrapper, mocked in tests
    from openai import OpenAI

    return OpenAI()


def _artifact_dir(metadata: Dict[str, Any]) -> Path:
    path = metadata.get("artifact_dir")
    if path:
        return Path(path)
    return Path("ci/daily-reports")


def _collect_steps(events: Iterable[Any]) -> List[str]:
    steps: List[str] = []
    for event in events:
        # Handle both dict and object response formats
        if hasattr(event, 'get'):  # Dictionary format
            if event.get("type") == "response.output_text.delta":
                delta = event.get("delta")
                if delta:
                    steps.append(str(delta))
        elif hasattr(event, 'type'):  # Object format
            if event.type == "response.output_text.delta" and hasattr(event, 'delta') and event.delta:
                steps.append(str(event.delta))
    return steps


def _extract_request_id(events: Iterable[Any]) -> str:
    for event in events:
        # Handle both dict and tuple response formats
        if hasattr(event, 'get'):  # Dictionary format
            if event.get("type") == "response.completed":
                response = event.get("response") or {}
                response_id = response.get("id")
                if response_id:
                    return str(response_id)
        elif hasattr(event, 'response'):  # Object format
            if hasattr(event, 'type') and event.type == "response.completed":
                if hasattr(event.response, 'id') and event.response.id:
                    return str(event.response.id)
    return ""


def _extract_usage(events: Iterable[Any]) -> Dict[str, int]:
    for event in events:
        # Handle both dict and tuple response formats
        if hasattr(event, 'get'):  # Dictionary format
            if event.get("type") == "response.completed":
                response = event.get("response") or {}
                usage = response.get("usage") or {}
                return {
                "prompt": int(usage.get("prompt_tokens", 0) or 0),
                "completion": int(usage.get("completion_tokens", 0) or 0),
                "total": int(usage.get("total_tokens", 0) or 0),
            }
    return {"prompt": 0, "completion": 0, "total": 0}


def run_daily_analysis(
    log_path: Path,
    sanitized_markdown: str,
    goal_ids: List[str],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    _emit_log(
        "run_daily_analysis.start",
        log=str(log_path),
        model=metadata.get("model", "gpt-4.1"),
        artifact_dir=metadata.get("artifact_dir"),
        goal_ids=goal_ids,
    )

    payload = build_payload(
        log_path=log_path,
        sanitized_markdown=sanitized_markdown,
        goal_ids=goal_ids,
        summary=metadata.get("summary", ""),
        analysis_config={
            "run_id": metadata.get("run_id", "pending"),
            "artifact_path": metadata.get("artifact_path"),
        },
        sanitization_report=metadata.get("sanitization_report"),
    )

    _emit_log(
        "run_daily_analysis.payload_prepared",
        log=str(log_path),
        request_id=payload.get("requestId"),
        warnings=payload.get("warnings", []),
    )

    client = get_openai_client()
    _emit_log("run_daily_analysis.api_request", log=str(log_path), model=metadata.get("model", "gpt-4.1"))
    # Convert goal_ids list to comma-separated string for the API
    goal_ids_str = ",".join(goal_ids) if isinstance(goal_ids, list) else str(goal_ids)
    
    events = client.responses.create(
        model=metadata.get("model", "gpt-4.1"),
        input=[
            {
                "role": "system",
                "content": metadata.get("system_prompt", "Analyze the daily log."),
            },
            {
                "role": "user",
                "content": sanitized_markdown,
            },
        ],
        metadata={"goalIds": goal_ids_str, "logRef": str(log_path)},
    )

    # Convert events to a serializable format
    events_list = list(events)
    serializable_events = []
    
    for event in events_list:
        if hasattr(event, 'model_dump'):  # Pydantic v2
            serializable_events.append(event.model_dump())
        elif hasattr(event, 'dict'):  # Pydantic v1
            serializable_events.append(event.dict())
        elif hasattr(event, 'to_dict'):  # Some custom objects
            serializable_events.append(event.to_dict())
        elif hasattr(event, '__dict__'):  # Regular Python objects
            serializable_events.append(event.__dict__)
        else:
            # Fallback to string representation
            serializable_events.append(str(event))
    
    _emit_log(
        "run_daily_analysis.api_response",
        log=str(log_path),
        event_count=len(serializable_events),
        request_id=_extract_request_id(events_list),  # Use original events for extraction
    )

    # Write the serializable data to file
    artifact_dir = _artifact_dir(metadata)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    events_path = artifact_dir / "events.json"
    events_path.write_text(json.dumps(serializable_events, indent=2, default=str))
    _emit_log("run_daily_analysis.events_written", log=str(log_path), events_path=str(events_path))

    usage = _extract_usage(events_list)
    _emit_log("run_daily_analysis.usage_extracted", log=str(log_path), usage=usage)

    return {
        "request_id": _extract_request_id(events_list),
        "steps": _collect_steps(events_list),
        "events_path": events_path,
        "payload": payload,
        "usage": usage,
    }
