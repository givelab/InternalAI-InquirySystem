# 対象データが存在しない場合の例外
class RecordNotFoundError(Exception):
    pass


# 対象データがすでに存在する場合の例外
class RecordAlreadyExistsError(Exception):
    pass


# モデルのバリデーションに失敗した場合の例外
class ModelValidationError(Exception):
    pass
