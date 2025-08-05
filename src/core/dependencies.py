from src.core.config import load_config
from src.models.db.postgres_conn import Database
from src.models.repositories import UserRepository, ManagerUserRepository, PostPlanRepository
from src.views.services import UserService, ManagerUserService, PostPlanService

config = load_config()

database = Database(db_url=config.db.url)

user_repository = UserRepository(session_factory=database.session)
user_service = UserService(user_repository=user_repository)

manager_user_repository = ManagerUserRepository(session_factory=database.session)
manager_user_service = ManagerUserService(manager_user_repository=manager_user_repository)

post_plan_repository = PostPlanRepository(session_factory=database.session)
post_plan_service = PostPlanService(post_plan_repository=post_plan_repository)
