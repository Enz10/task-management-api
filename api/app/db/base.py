# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base # noqa
# Import your models here
from app.models.user import User # noqa
# from app.models.item import Item # noqa # Example if you had an Item model
