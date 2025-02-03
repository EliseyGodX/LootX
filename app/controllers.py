# from litestar import Controller, get, post, put, delete
# from litestar.dto import DTOData
# from litestar.di import Provide

# class AuthController(Controller):

#     def __init__(self, service: UserService):
#         self.service = service

#     @get("/{user_id}", response_model=UserDTO)
#     async def get_user(self, user_id: str) -> UserDTO:
#         return await self.service.get(user_id)
