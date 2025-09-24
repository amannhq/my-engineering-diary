"""Execute Responses API calls for daily diary analysis."""

from __future__ import annotations

import json
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

from openai import OpenAI
from . import prepare_responses_payload


def _emit_log(event: str, **payload: Any) -> None:
    """Emit a structured log entry.
    
    Args:
        event: The event name
        **payload: Additional key-value pairs to include in the log
    """
    entry: Dict[str, Any] = {
        "timestamp": datetime.now(datetime.timezone.utc).isoformat(),
        "event": event,
        **payload,
    }
    print(json.dumps(entry, default=str))


def get_openai_client() -> OpenAI:  # pragma: no cover - thin wrapper, mocked in tests
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
    """Run daily analysis on the given log.

    Args:
        log_path: Path to the log file
        sanitized_markdown: Sanitized markdown content
        goal_ids: List of goal IDs
        metadata: Additional metadata

    Returns:
        Dictionary with analysis results

    Raises:
        ValueError: If the input is invalid or API response is malformed
        RuntimeError: For any unexpected errors during processing
    """
    try:
        # Input validation
        if not goal_ids:
            raise ValueError("No goal IDs provided for analysis")
        if not sanitized_markdown or not sanitized_markdown.strip():
            raise ValueError("No content to analyze (empty or invalid markdown)")

        _emit_log(
            "run_daily_analysis.start",
            log=str(log_path),
            model=metadata.get("model", "gpt-4.1"),
            artifact_dir=str(_artifact_dir(metadata)),
            goal_ids=goal_ids,
        )

        # Prepare the API payload
        try:
            payload = prepare_responses_payload.build_payload(
                log_path=log_path,
                sanitized_markdown=sanitized_markdown,
                goal_ids=goal_ids,
                summary=metadata.get("summary", ""),
                analysis_config={
                    "run_id": metadata.get("run_id", f"daily-{log_path.stem}"),
                    "artifact_path": str(_artifact_dir(metadata)),
                },
                sanitization_report=metadata.get("sanitization_report"),
            )
        except Exception as e:
            _emit_log(
                "run_daily_analysis.payload_error",
                log=str(log_path),
                error=str(e),
                error_type=type(e).__name__,
                traceback=traceback.format_exc()
            )
            raise RuntimeError(f"Failed to prepare API payload: {str(e)}") from e

        _emit_log(
            "run_daily_analysis.payload_prepared",
            log=str(log_path),
            request_id=payload.get("requestId"),
            warnings=payload.get("warnings", []),
        )

        # Make API request
        try:
            client = get_openai_client()
            model = metadata.get("model", "gpt-4.1")
            
            _emit_log(
                "run_daily_analysis.api_request",
                log=str(log_path),
                model=model,
                content_length=len(sanitized_markdown)
            )
            
            # Convert goal_ids list to comma-separated string for the API
            goal_ids_str = ",".join(goal_ids) if isinstance(goal_ids, list) else str(goal_ids)
            
            events = client.responses.create(
                model=model,
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
            
            if not events:
                raise ValueError("Empty response received from API")
                
        except Exception as e:
            _emit_log(
                "run_daily_analysis.api_error",
                log=str(log_path),
                error=str(e),
                error_type=type(e).__name__,
                traceback=traceback.format_exc()
            )
            raise RuntimeError(f"API request failed: {str(e)}") from e

        # Process API response
        try:
            events_list = list(events)
            if not events_list:
                raise ValueError("No events received in API response")
                
            # Convert events to a serializable format
            serializable_events = []
            for event in events_list:
                try:
                    if hasattr(event, 'model_dump'):  # Pydantic v2
                        serializable_events.append(event.model_dump())
                    elif hasattr(event, 'dict'):  # Pydantic v1
                        serializable_events.append(event.dict())
                    elif hasattr(event, 'to_dict'):  # Some custom objects
                        serializable_events.append(event.to_dict())
                    elif hasattr(event, '__dict__'):  # Regular Python objects
                        serializable_events.append({k: v for k, v in event.__dict__.items() if not k.startswith('_')})
                    else:
                        serializable_events.append(str(event))
                except Exception as e:
                    _emit_log(
                        "run_daily_analysis.event_serialization_warning",
                        log=str(log_path),
                        error=str(e),
                        event_type=str(type(event)),
                        event_repr=repr(event)[:200]  # First 200 chars to avoid huge logs
                    )
                    serializable_events.append({"error": f"Failed to serialize event: {str(e)}"})

            # Extract request ID with fallback
            request_id = _extract_request_id(events_list) or f"generated-{uuid.uuid4()}"
            
            _emit_log(
                "run_daily_analysis.api_response",
                log=str(log_path),
                event_count=len(serializable_events),
                request_id=request_id,
            )

            # Ensure artifact directory exists
            artifact_dir = _artifact_dir(metadata)
            artifact_dir.mkdir(parents=True, exist_ok=True)
            
            # Write events to file
            events_path = artifact_dir / "events.json"
            try:
                events_path.write_text(json.dumps(serializable_events, indent=2, default=str))
                _emit_log(
                    "run_daily_analysis.events_written", 
                    log=str(log_path), 
                    events_path=str(events_path),
                    file_size=events_path.stat().st_size
                )
            except Exception as e:
                _emit_log(
                    "run_daily_analysis.write_error",
                    log=str(log_path),
                    error=str(e),
                    events_path=str(events_path)
                )
                raise RuntimeError(f"Failed to write events to {events_path}: {str(e)}") from e

            # Extract usage information
            usage = _extract_usage(events_list) or {"prompt": 0, "completion": 0, "total": 0}
            _emit_log(
                "run_daily_analysis.usage_extracted", 
                log=str(log_path), 
                usage=usage,
                request_id=request_id
            )

            # Collect and validate steps
            steps = _collect_steps(events_list)
            if not steps:
                _emit_log(
                    "run_daily_analysis.no_steps_found",
                    log=str(log_path),
                    request_id=request_id,
                    event_count=len(events_list)
                )
            
            return {
                "request_id": request_id,
                "steps": steps,
                "events_path": events_path,
                "payload": payload,
                "usage": usage,
                "success": True
            }
            
        except Exception as e:
            _emit_log(
                "run_daily_analysis.processing_error",
                log=str(log_path),
                error=str(e),
                error_type=type(e).__name__,
                traceback=traceback.format_exc()
            )
            raise RuntimeError(f"Error processing API response: {str(e)}") from e
            
    except Exception as e:
        _emit_log(
            "run_daily_analysis.failed",
            log=str(log_path),
            error=str(e),
            error_type=type(e).__name__,
            traceback=traceback.format_exc()
        )
        raise  # Re-raise the exception after logging
