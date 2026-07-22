import argparse
import asyncio
import json
import os
from pathlib import Path

from norevia_pipeline.sources.destatis import DestatisAdapter
from norevia_pipeline.sources.eurostat import EurostatAdapter


async def run(source: str, dataset: str, raw_root: Path) -> None:
    adapter = (
        EurostatAdapter(raw_root)
        if source == "eurostat"
        else DestatisAdapter(
            raw_root, os.getenv("DESTATIS_USERNAME", "GAST"), os.getenv("DESTATIS_PASSWORD", "GAST")
        )
    )
    if not await adapter.check_availability():
        raise SystemExit(f"Source unavailable: {source}")
    artifact = await adapter.download(dataset)
    print(
        json.dumps(
            {
                "source": artifact.source_code,
                "dataset": artifact.dataset_code,
                "sha256": artifact.sha256,
                "path": str(artifact.path),
                "retrievedAt": artifact.retrieved_at.isoformat(),
            }
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preserve and validate an official Norevia source dataset"
    )
    parser.add_argument("source", choices=["eurostat", "destatis"])
    parser.add_argument("dataset")
    parser.add_argument("--raw-root", type=Path, default=Path("raw"))
    args = parser.parse_args()
    asyncio.run(run(args.source, args.dataset, args.raw_root))


if __name__ == "__main__":
    main()
