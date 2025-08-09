from src.models.repositories.repositories import UserRepository, AdminUserRepository, MailingRepository


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


class AdminUserService:
    def __init__(self, admin_user_repository: AdminUserRepository):
        self.admin_user_repository = admin_user_repository

    def create_user(self, user_info: dict):
        return self.admin_user_repository.create(data=user_info)

    def get_user(self, user_id):
        return self.admin_user_repository.read_by_id(user_id)


class MailingService:
    def __init__(self, mailing_repository: MailingRepository):
        self.mailing_repository = mailing_repository

    def create_mailing(self, mailing_info: dict):
        return self.mailing_repository.create(data=mailing_info)

    def get_mailing(self, mailing_id: int):
        return self.mailing_repository.read_by_id(mailing_id)
    
    def get_mailing_by_name(self, name: str):
        return self.mailing_repository.read_by(name=name)

    def get_all_mailings(self):
        return self.mailing_repository.read_all()
    
    def get_active_mailings(self):
        return self.mailing_repository.read_all_by(is_active=True)

    def update_mailing(self, mailing_id: int, data: dict):
        return self.mailing_repository.update(mailing_id, data)

    def update_last_mail_date(self, mailing_id: int):
        return self.mailing_repository.update_last_mail_date(mailing_id)

    def delete_mailing(self, mailing_id: int):
        return self.mailing_repository.delete_by_id(mailing_id)
