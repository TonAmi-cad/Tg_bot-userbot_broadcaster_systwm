from src.models.repositories import UserRepository, ManagerUserRepository, PostPlanRepository


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, user_info: dict):
        return self.user_repository.create(data=user_info)

    def update_user(self, user_id, user_info: dict):
        return self.user_repository.update(user_id, user_info)

    def get_user(self, user_id):
        return self.user_repository.read_by_id(user_id)

    def get_all_users(self):
        return self.user_repository.read_all()

    def delete_user(self, user_id):
        return self.user_repository.delete_by_id(user_id)


class ManagerUserService:
    def __init__(self, manager_user_repository: ManagerUserRepository):
        self.manager_user_repository = manager_user_repository

    def create_user(self, user_info: dict):
        return self.manager_user_repository.create(data=user_info)

    def get_user(self, user_id):
        return self.manager_user_repository.read_by_id(user_id)


class PostPlanService:
    def __init__(self, post_plan_repository: PostPlanRepository):
        self.post_plan_repository = post_plan_repository

    def create_post(self, post_info: dict):
        return self.post_plan_repository.create(data=post_info)

    def get_post(self, post_id: int):
        return self.post_plan_repository.read_by_id(post_id)

    def get_post_by_name(self, file_name: str):
        return self.post_plan_repository.read_by(file_name=file_name)

    def get_motivational_post(self):
        return self.post_plan_repository.read_by(motivation=True)

    def get_active_posts(self):
        return self.post_plan_repository.read_all_by(hide=False, motivation=False)

    def get_all_posts(self):
        return self.post_plan_repository.read_all()

    def get_all_regular_posts(self):
        return self.post_plan_repository.get_all_regular_posts()

    def update_period_for_all_motivational(self, period_minutes: int):
        return self.post_plan_repository.update_period_for_all_motivational(period_minutes)

    def update_period_for_all_regular(self, period_hours: int):
        return self.post_plan_repository.update_period_for_all_regular(period_hours)

    def update_post(self, post_id: int, data: dict):
        return self.post_plan_repository.update(post_id, data)

    def delete_post(self, post_id: int):
        return self.post_plan_repository.delete_by_id(post_id)
