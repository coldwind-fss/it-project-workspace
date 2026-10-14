import hashlib
import mimetypes
import re
import uuid
from pathlib import Path
from itpm.core.errors import require


class FileStorage:
    def __init__(self, root):
        self.root = Path(root).resolve()

    def path(self, key):
        target = (self.root / key).resolve()
        return target if target.is_relative_to(self.root) and target != self.root else None

    def put(self, owner, filename, mime, content, extensions):
        require(content, '不能上传空文件')
        require(len(content) <= 50 * 1024 * 1024, '单个附件不能超过50MB', 413, 'TOO_LARGE')
        raw=Path(str(filename or 'attachment')).name.strip() or 'attachment'
        name = re.sub(r'[^\w.\-\u4e00-\u9fff ()]', '_', raw, flags=re.UNICODE)[:180]
        extension = Path(name).suffix.lower()
        mime = str(mime or 'application/octet-stream').lower()
        allowed = mime.startswith(('image/', 'video/', 'text/')) or mime in {
            'application/pdf', 'application/msword', 'application/vnd.ms-excel', 'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/zip', 'application/x-7z-compressed', 'application/x-rar-compressed'}
        require(extension in extensions or allowed, '暂不支持该文件类型')
        if extension not in extensions:
            extension = mimetypes.guess_extension(mime) or ''
        stored = uuid.uuid4().hex + extension
        key = owner + '/' + stored
        target = self.path(key)
        require(target is not None, '附件存储路径不合法')
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_suffix(target.suffix + '.part')
        try:
            temp.write_bytes(content)
            temp.replace(target)
        except Exception:
            temp.unlink(missing_ok=True)
            target.unlink(missing_ok=True)
            raise
        return {'originalName': name, 'storedName': stored, 'mimeType': mime, 'fileExtension': extension,
            'sizeBytes': len(content), 'sha256': hashlib.sha256(content).hexdigest(), 'storageKey': key}

    def remove(self, key):
        target = self.path(key)
        if target:
            target.unlink(missing_ok=True)
