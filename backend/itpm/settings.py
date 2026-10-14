from dataclasses import dataclass,field
from pathlib import Path
from sqlalchemy.engine import make_url
import os

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    database_url: str
    profile: str = 'dev'
    public_base: str = '/pm/'
    public_url: str = 'http://127.0.0.1:3003/pm/'
    static_dir: Path = ROOT / 'frontend/dist'
    attachment_dir: Path = ROOT / '.runtime/attachments'
    pool_size: int = 2
    pool_timeout: int = 5
    integration_mode: str = 'fake'
    worker_enabled: bool = False
    preview_login: bool = False
    read_auth: bool = True  # V2BC01 approved on 2026-10-13.
    intake_webhook_secret: str = ''
    performance_user_id: str = ''
    work_sync_token: str = ''
    dingtalk_app_key: str = ''
    dingtalk_app_secret: str = field(default='',repr=False)
    dingtalk_corp_id: str = ''
    dingtalk_agent_id: str = ''
    dingtalk_robot_code: str = ''

    def __post_init__(self):
        u = make_url(self.database_url)
        if u.get_backend_name() != 'postgresql' or not u.host or not u.database:
            raise ValueError('PostgreSQL configuration required')
        if self.profile in {'dev', 'test'}:
            if u.host != '127.0.0.1' or u.port != 55432 or not u.database.startswith('pm_test_rebuild_'):
                raise ValueError('isolated database target required')
        if self.profile not in {'dev', 'test', 'preview','production'} or self.integration_mode not in {'fake', 'disabled','real'}:
            raise ValueError('unsupported profile/integration mode')
        if self.integration_mode=='real' and (self.profile!='production' or not self.dingtalk_app_key or not self.dingtalk_app_secret):
            raise ValueError('real integration requires an explicit production profile and credentials')
        if self.pool_size < 1 or self.pool_size > 5:
            raise ValueError('invalid worker/pool configuration')
        if not self.public_base.startswith('/') or not self.public_base.endswith('/') or '..' in self.public_base:
            raise ValueError('invalid public base')
        if self.preview_login and self.profile not in {'dev', 'test'}:
            raise ValueError('local preview login only')
        if not self.read_auth and self.profile!='test':raise ValueError('internal session checks must remain enabled')

    @classmethod
    def from_env(cls):
        url = os.environ.get('ITPM_DATABASE_URL', '')
        if not url:
            raise ValueError('ITPM_DATABASE_URL required')
        return cls(database_url=url, profile=os.environ.get('ITPM_PROFILE', 'dev'),
            public_base=os.environ.get('ITPM_PUBLIC_BASE', '/pm/'),
            public_url=os.environ.get('ITPM_PUBLIC_URL', 'http://127.0.0.1:3003/pm/'),
            preview_login=os.environ.get('ITPM_PREVIEW_LOGIN') == '1',
            read_auth=os.environ.get('ITPM_READ_AUTH','1') == '1',
            worker_enabled=os.environ.get('ITPM_WORKER_ENABLED')=='1',
            integration_mode=os.environ.get('ITPM_INTEGRATION_MODE','fake' if os.environ.get('ITPM_PROFILE','dev') in {'dev','test'} else 'disabled'),
            dingtalk_app_key=os.environ.get('ITPM_DINGTALK_APP_KEY',''),dingtalk_app_secret=os.environ.get('ITPM_DINGTALK_APP_SECRET',''),
            dingtalk_corp_id=os.environ.get('ITPM_DINGTALK_CORP_ID',''),dingtalk_agent_id=os.environ.get('ITPM_DINGTALK_AGENT_ID',''),dingtalk_robot_code=os.environ.get('ITPM_DINGTALK_ROBOT_CODE',''),
            intake_webhook_secret=os.environ.get('ITPM_BUSINESS_INTAKE_WEBHOOK_SECRET',''),
            performance_user_id=os.environ.get('ITPM_PERFORMANCE_USER_ID',''),
            work_sync_token=os.environ.get('ITPM_WORK_SYNC_TOKEN',''))
