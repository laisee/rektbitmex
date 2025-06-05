import logging
from database import init_rekkage_db, init_pid_db

logger = logging.getLogger(__name__)


def addRekt():
    """Initialize the rekkage table."""
    init_rekkage_db()


def addPID():
    """Initialize the PID table."""
    init_pid_db()


if __name__ == "__main__":
    addRekt()
    addPID()
