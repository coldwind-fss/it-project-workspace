from itpm.infrastructure.database import Repository


class DemandRepository(Repository):
    def __init__(self,db):
        super().__init__(db,['demand_pool_items','demand_pool_l3_branches','demand_pool_evaluations',
            'demand_pool_reviews','demand_pool_confirmations','demand_pool_supplements','demand_pool_pocs'])
