from pyopenapi_gen import (
    IRSpec,
    IROperation,
    HTTPMethod,
)
from pyopenapi_gen.core.warning_collector import WarningCollector


def test_warning_collector_missing():
    # Create an operation with no tags, no summary, no description
    op = IROperation(
        operation_id="testOp",
        method=HTTPMethod.GET,
        path="/test",
        summary=None,
        description=None,
        parameters=[],
        request_body=None,
        responses=[],
        tags=[],
    )
    spec = IRSpec(title="T", version="0.1", schemas={}, operations=[op], servers=[])
    collector = WarningCollector()
    warnings = collector.collect(spec)

    assert isinstance(warnings, list)
    # Expect two warnings: missing_tags and missing_description
    codes = [w.code for w in warnings]
    assert "missing_tags" in codes
    assert "missing_description" in codes


def test_warning_collector_no_issues():
    # Operation with tags and summary
    op = IROperation(
        operation_id="okOp",
        method=HTTPMethod.POST,
        path="/ok",
        summary="All good",
        description="Detailed",
        parameters=[],
        request_body=None,
        responses=[],
        tags=["tag1"],
    )
    spec = IRSpec(title="T2", version="0.2", schemas={}, operations=[op], servers=[])
    collector = WarningCollector()
    warnings = collector.collect(spec)
    assert warnings == []
