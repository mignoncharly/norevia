from pathlib import Path

import pytest
from norevia_pipeline.sources.base import HttpSourceAdapter


@pytest.mark.asyncio
async def test_dataset_code_cannot_escape_raw_storage(tmp_path: Path) -> None:
    adapter = HttpSourceAdapter(tmp_path)
    adapter.source_code = "test"
    with pytest.raises(ValueError, match="unsupported path characters"):
        await adapter._preserve(dataset_code="../../outside", url="https://example.test")
