import importlib
from unittest.mock import Mock, patch

from utils import storage

import config


def test_scheduler_interval(monkeypatch, tmp_path):
    storage.init(tmp_path / "sched.db")
    monkeypatch.setattr(config, 'CRON_EXPRESSION', None, raising=False)
    monkeypatch.setattr(config, 'PARSING_INTERVAL', 42, raising=False)
    scheduler_mock = Mock()
    with patch('apscheduler.schedulers.asyncio.AsyncIOScheduler', return_value=scheduler_mock):
        import main
        importlib.reload(main)
        scheduler = main.create_scheduler()
        scheduler_mock.add_job.assert_called_with(
            main.async_job,
            'interval',
            minutes=42,
            id='parse_job',
            name='Parse job',
            replace_existing=True
        )


def test_scheduler_cron(monkeypatch, tmp_path):
    storage.init(tmp_path / "sched.db")
    monkeypatch.setattr(config, 'CRON_EXPRESSION', '*/5 * * * *', raising=False)
    scheduler_mock = Mock()
    trigger_mock = Mock()
    with patch('apscheduler.schedulers.asyncio.AsyncIOScheduler', return_value=scheduler_mock), \
         patch('apscheduler.triggers.cron.CronTrigger.from_crontab', return_value=trigger_mock) as cron_patch:
        import main
        importlib.reload(main)
        scheduler = main.create_scheduler()
        cron_patch.assert_called_with('*/5 * * * *')
        scheduler_mock.add_job.assert_called_with(
            main.async_job,
            trigger_mock,
            id='parse_job',
            name='Parse job',
            replace_existing=True
        )

