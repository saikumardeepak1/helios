from unittest.mock import MagicMock, patch

from app.workers.worker import main


def test_main_configures_logging_before_starting_the_worker() -> None:
    with (
        patch("app.workers.worker.configure_logging") as mock_configure_logging,
        patch("app.workers.worker.Worker") as mock_worker_cls,
        patch("app.workers.worker.Redis"),
    ):
        mock_worker_instance = MagicMock()
        mock_worker_cls.return_value = mock_worker_instance

        main()

        mock_configure_logging.assert_called_once()
        mock_worker_cls.assert_called_once()
        mock_worker_instance.work.assert_called_once()


def test_main_listens_on_the_default_queue() -> None:
    with (
        patch("app.workers.worker.configure_logging"),
        patch("app.workers.worker.Worker") as mock_worker_cls,
        patch("app.workers.worker.Redis"),
    ):
        main()

        queues = mock_worker_cls.call_args[0][0]
        assert len(queues) == 1
        assert queues[0].name == "default"
