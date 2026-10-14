from itpm.infrastructure.database import Repository


class DeliveryRepository(Repository):
    def __init__(self,db):
        super().__init__(db,['requirement_delivery_baselines','collaboration_link_requests','requirement_delivery_feedback'])
