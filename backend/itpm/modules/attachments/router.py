from fastapi import APIRouter, Request, Form, File, UploadFile
from itpm.infrastructure.router import ContractRouter
from fastapi.responses import FileResponse
from itpm.core.errors import require


def router(http, files, access):
    r = ContractRouter()

    @r.post('/api/business-attachments')
    async def upload(request: Request, ownerType: str = Form(...), ownerId: str = Form(...),
                     file: UploadFile = File(...), entryToken: str = Form('')):
        content = bytearray()
        try:
            while chunk := await file.read(1024 * 1024):
                content.extend(chunk)
                require(len(content) <= 50 * 1024 * 1024, '单个附件不能超过50MB', 413, 'TOO_LARGE')
            def execute(u, p):
                actor = access.upload(u, p, ownerType.strip(), ownerId.strip(), entryToken.strip())
                return files.save(u, actor, ownerType.strip(), ownerId.strip(), file.filename, file.content_type, content)
            return http.call(request, execute)
        finally:
            await file.close()

    @r.get('/api/business-attachments/{attachment_id}/download')
    def download(attachment_id: str, request: Request, reviewToken: str = ''):
        def execute(u, p):
            row = files.get(u, attachment_id)
            access.download(u, p, row, reviewToken)
            return FileResponse(files.download(row), media_type=row.get('mimeType') or 'application/octet-stream', filename=row.get('originalName') or 'attachment')
        return http.call(request, execute)

    @r.delete('/api/business-attachments/{attachment_id}')
    def delete(attachment_id: str, request: Request):
        def execute(u, p):
            row = files.get(u, attachment_id)
            access.delete(u, p, row)
            return files.delete(u, row)
        return http.call(request, execute)
    return r
