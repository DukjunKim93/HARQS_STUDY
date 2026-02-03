import logging
from pathlib import Path

from QSUtils.Utils.logging_config import LoggingConfig, configure_logging


def test_configure_logging_creates_file(tmp_path: Path, monkeypatch):
    log_dir = tmp_path / "logs"
    cfg = LoggingConfig(
        app_name="QSMonitor",
        level="DEBUG",
        log_dir=log_dir,
        log_file="test.log",
        to_console=False,
    )

    # Ensure fresh root logger
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    configure_logging(cfg)

    # Root should have handlers and file should be created after first log
    logger = logging.getLogger("test")
    logger.debug("hello")

    assert (log_dir / "test.log").exists()
    assert root.level == logging.DEBUG
