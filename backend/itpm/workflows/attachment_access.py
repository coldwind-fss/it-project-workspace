from itpm.core.errors import require


class AttachmentAccess:
    """Explicit owner policies. Scoped demand/value ports are added with their packages."""
    def __init__(self, identity, collaboration):
        self.identity, self.collaboration = identity, collaboration
        self.owner_policies = {}
        self.token_upload = None
        self.review_download = None
        self.reference_guard = None

    def visible(self, u, p, kind, identifier, write=False):
        if kind in self.owner_policies:
            return self.owner_policies[kind](u, p, identifier, write)
        return self.collaboration.owner_visible(u, p, kind, identifier, write)

    def upload(self, u, p, kind, identifier, token):
        require(identifier and kind in {'demand_pool', 'demand_pool_supplement', 'demand_collection_response',
            'demand_pool_value_request', 'poc_workbench', 'business_request', 'collaboration',
            'collaboration_message', 'shared_activity', 'shared_activity_comment'}, '附件归属对象不合法')
        if token and self.token_upload:
            actor = self.token_upload(u, p, kind, identifier, token)
            if actor:
                return actor
        self.identity.authenticated(p)
        require(self.visible(u, p, kind, identifier, True), '无权向该业务协作对象上传附件', 403, 'FORBIDDEN')
        return p

    def download(self, u, p, row, token):
        public = bool(token and self.review_download and self.review_download(u, row, token))
        if token and not p.authenticated:
            require(public, '附件不存在或无权访问', 404, 'NOT_FOUND')
        require(p.authenticated or public, '附件链接需要有效令牌', 401, 'AUTH_REQUIRED')
        require(row and (public or self.visible(u, p, row['ownerType'], row['ownerId'])), '附件不存在或无权访问', 404, 'NOT_FOUND')

    def delete(self, u, p, row):
        self.identity.authenticated(p)
        require(row and self.visible(u, p, row['ownerType'], row['ownerId']), '附件不存在或无权删除', 404, 'NOT_FOUND')
        require(not self.reference_guard or not self.reference_guard(u, row), '附件已作为业务链接或回执证据留存，不能删除', 409, 'REFERENCED')
