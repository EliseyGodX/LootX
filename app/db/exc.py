class DatabaseError(Exception): ...
class UniqueUsernameError(DatabaseError): ...
class UniqueEmailError(DatabaseError): ...
class ActivateUserError(DatabaseError): ...
class TeamsAlreadyExistsError(DatabaseError): ...
class TeamsNotExistsError(DatabaseError): ...
class UniqueTeamNameError(DatabaseError): ...
class UserNotExistsError(DatabaseError): ...
class InvalidCredentialsError(DatabaseError): ...
class UserNotFoundError(DatabaseError): ...
class RaiderNotFoundError(DatabaseError): ...
class RaiderNotUnique(DatabaseError): ...
class WoWItemNotFoundError(DatabaseError): ...
