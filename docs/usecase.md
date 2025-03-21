# ドメイン駆動設計に基づくユーザー認証システム

このドキュメントでは、ドメイン駆動設計（DDD）の原則に基づいたユーザー認証システムの主要なユースケースとその実装について詳細に説明します。

## プロジェクトの構成

プロジェクトは以下のようなディレクトリ構成に従います：

```
src/
├── app/
│   ├── domains/             # ドメイン層
│   │   ├── users/
│   │   │   ├── schemas/     # 値オブジェクト（Pydantic）
│   │   │   ├── entities/    # エンティティ（dataclass）
│   │   │   ├── services/    # ドメインサービス
│   │   │   └── repositories/ # リポジトリインターフェース
│   │   ├── social_accounts/
│   │   │   └── ...
│   │   └── auth/
│   │       └── ...
│   ├── usecases/            # アプリケーション層
│   │   ├── users/
│   │   ├── auth/
│   │   └── social_accounts/
│   ├── infrastructures/     # インフラ層
│   │   ├── users/
│   │   │   └── repositories/
│   │   ├── social_accounts/
│   │   │   └── repositories/
│   │   └── auth/
│   │       └── services/
│   └── core/                # 共通処理
│       ├── schemas/
│       └── services/
└── tests/                   # テストコード
    ├── users/
    ├── auth/
    └── social_accounts/
```

## ドメインモデル

### 値オブジェクト（Value Objects）

値オブジェクトは不変で、同じ属性を持つ2つのオブジェクトは等価です。

- **Email**: メールアドレスのバリデーションと正規化
- **Password**: パスワード強度の検証と安全な保存
- **FullName**: 姓名の構造化された表現
- **OAuthToken**: OAuthトークンの管理と有効期限チェック
- **OAuthUserInfo**: OAuthプロバイダから取得したユーザー情報

### エンティティ（Entities）

エンティティはユニークなIDを持ち、そのライフサイクルを通して一貫した識別子を維持します。

- **UserEntity**: ユーザー情報と関連操作
- **SocialAccountEntity**: ソーシャルアカウント連携情報

## ユースケース

### 1. ユーザー登録（メールとパスワード）

#### フロー:

1. ユーザーがメール、パスワード、ユーザー名、氏名を送信
2. メールアドレスの重複チェック
3. パスワードのハッシュ化
4. ユーザーエンティティの作成と保存
5. 確認メールの送信（非同期処理）
6. ユーザー情報の返却（DTOに変換）

#### 関連コンポーネント:

- **値オブジェクト**: Email, Password, FullName
- **エンティティ**: UserEntity
- **リポジトリ**: UserRepositoryInterface
- **アプリケーションサービス**: UserRegistrationService
- **ドメインサービス**: PasswordHasherService

#### コード例:

```python
# アプリケーションサービスの例
async def register_user(user_data: RegisterUserDTO) -> UserResponseDTO:
    # メールアドレスの重複チェック
    if await user_repository.email_exists(Email(email=user_data.email)):
        raise EmailAlreadyExistsError()

    # パスワードのハッシュ化
    hashed_password = password_hasher.generate_hashed_password(user_data.password)

    # ユーザーエンティティの作成
    user = UserEntity(
        username=user_data.username,
        email=Email(email=user_data.email),
        full_name=FullName(first_name=user_data.first_name, last_name=user_data.last_name)
    )
    user.set_password(hashed_password)

    # ユーザーの保存
    created_user = await user_repository.create_user(user)

    # 確認メールの送信（非同期）
    await email_service.send_verification_email(created_user.email)

    # DTOに変換して返却
    return UserResponseDTO.from_entity(created_user)
```

### 2. ユーザー認証（ログイン）

#### フロー:

1. ユーザーがメールとパスワードを送信
2. リポジトリを通じてユーザーを検索
3. パスワードの検証
4. アクセストークンとリフレッシュトークンの生成
5. トークンの返却（アクセストークンはレスポンスに、リフレッシュトークンはHTTPのみのCookieに）

#### 関連コンポーネント:

- **値オブジェクト**: Email, Password
- **エンティティ**: UserEntity
- **アプリケーションサービス**: AuthenticationService
- **ドメインサービス**: TokenGenerationService, PasswordHasherService

#### コード例:

```python
# アプリケーションサービスの例
async def authenticate_user(credentials: UserCredentialsDTO) -> AuthResponseDTO:
    # ユーザーの検索
    user = await user_repository.find_by_email(Email(email=credentials.email))
    if not user:
        raise InvalidCredentialsError()

    # パスワードの検証
    if not password_hasher.verify_password(credentials.password, user.hashed_password):
        raise InvalidCredentialsError()

    # トークンの生成
    access_token = token_service.generate_access_token(user.id, user.email.email)
    refresh_token = token_service.generate_refresh_token(user.id)

    # レスポンスの作成
    return AuthResponseDTO(
        access_token=access_token,
        token_type="bearer",
        user=UserResponseDTO.from_entity(user),
        refresh_token=refresh_token  # HTTPのみのCookieにセットするために返却
    )
```

### 3. Googleによるソーシャルログイン

#### フロー:

1. ユーザーをGoogleの認証ページにリダイレクト
2. 認証後、Googleからのコールバックを受信
3. コードを使用してアクセストークンを取得
4. トークンを使用してユーザー情報を取得
5. ソーシャルアカウント情報とユーザー情報の紐付け
   - 既存のソーシャルアカウントがある場合：トークン情報を更新
   - 新規の場合：
     - 同じメールのユーザーが存在すれば連携
     - 存在しなければ新規ユーザーを作成して連携
6. JWTトークンの生成と返却

#### 関連コンポーネント:

- **値オブジェクト**: OAuthToken, OAuthUserInfo
- **エンティティ**: UserEntity, SocialAccountEntity
- **リポジトリ**: UserRepositoryInterface, SocialAccountRepositoryInterface
- **ドメインサービス**: OAuthService

#### コード例:

```python
# アプリケーションサービスの例
async def handle_oauth_callback(provider: str, code: str) -> AuthResponseDTO:
    # OAuthトークンの取得
    oauth_token = await oauth_service.exchange_code_for_token(provider, code)

    # ユーザー情報の取得
    oauth_user_info = await oauth_service.get_user_info(provider, oauth_token)

    # ソーシャルアカウントの検索
    social_account = await social_account_repository.find_by_provider_and_id(
        provider,
        oauth_user_info.provider_user_id
    )

    if social_account:
        # 既存のソーシャルアカウントの場合、トークンを更新
        social_account.update_tokens(
            oauth_token.access_token,
            oauth_token.refresh_token,
            oauth_token.expires_at
        )
        await social_account_repository.update(social_account)
        user = await user_repository.find_by_id(social_account.user_id)
    else:
        # 新規ソーシャルアカウントの場合
        user = None
        if oauth_user_info.email:
            # メールアドレスが存在する場合、既存ユーザーを検索
            user = await user_repository.find_by_email(Email(email=oauth_user_info.email))

        if not user:
            # 新規ユーザーを作成
            user = UserEntity(
                username=f"{provider}_{oauth_user_info.provider_user_id}",
                email=Email(email=oauth_user_info.email) if oauth_user_info.email else None,
                full_name=FullName(
                    first_name=oauth_user_info.name.split()[0] if oauth_user_info.name else "",
                    last_name=" ".join(oauth_user_info.name.split()[1:]) if oauth_user_info.name and len(oauth_user_info.name.split()) > 1 else ""
                ) if oauth_user_info.name else None,
                profile_image_url=oauth_user_info.picture,
                is_verified=True  # OAuthによる認証は検証済みとみなす
            )
            user = await user_repository.create_user(user)

        # ソーシャルアカウントを作成して紐付け
        social_account = SocialAccountEntity(
            provider=provider,
            provider_user_id=oauth_user_info.provider_user_id,
            provider_email=oauth_user_info.email if oauth_user_info.email else None,
            user_id=user.id,
            access_token=oauth_token.access_token,
            refresh_token=oauth_token.refresh_token,
            token_expiry=oauth_token.expires_at,
            provider_profile_image_url=oauth_user_info.picture
        )
        await social_account_repository.create(social_account)

    # JWTトークンの生成
    access_token = token_service.generate_access_token(user.id, user.email.email if user.email else None)
    refresh_token = token_service.generate_refresh_token(user.id)

    return AuthResponseDTO(
        access_token=access_token,
        token_type="bearer",
        user=UserResponseDTO.from_entity(user),
        refresh_token=refresh_token
    )
```

### 4. メール確認プロセス

#### フロー:

1. ユーザー登録時に確認トークンを生成
2. 確認リンク付きメールを送信（非同期タスク）
3. ユーザーがメールのリンクをクリック
4. トークンの検証
5. ユーザーのverifiedフラグを更新

#### 関連コンポーネント:

- **値オブジェクト**: Email
- **エンティティ**: UserEntity
- **リポジトリ**: UserRepositoryInterface
- **アプリケーションサービス**: EmailVerificationService
- **ドメインサービス**: TokenGenerationService

#### コード例:

```python
# アプリケーションサービスの例
async def verify_email(token: str) -> bool:
    # トークンからユーザーIDを取得
    user_id = token_service.verify_email_verification_token(token)
    if not user_id:
        raise InvalidTokenError()

    # ユーザーの取得
    user = await user_repository.find_by_id(user_id)
    if not user:
        raise UserNotFoundError()

    # 既に検証済みの場合
    if user.is_verified:
        return True

    # ユーザーを検証済みとしてマーク
    user.mark_as_verified()
    await user_repository.update(user)

    return True
```

## インフラストラクチャ層の実装

### SQLAlchemyを活用したリポジトリ実装

プロジェクトでは、`base_crud.py`に定義されているジェネリックなCRUD操作クラスを活用して、効率的かつ一貫性のあるデータアクセス層を実装しています。

#### base_crud.pyの役割

`base_crud.py`は、SQLAlchemyを使用したCRUD操作の抽象クラスを提供しています。このクラスは以下の特徴を持ちます：

1. **ジェネリック型の活用**: 入力型(T)と出力型(U)をジェネリックとして定義し、様々なエンティティやDTOで再利用可能
2. **同期/非同期のサポート**: すべてのCRUD操作に対して同期メソッドと非同期メソッドの両方を提供
3. **SQLAlchemy統合**: SQLAlchemyのORM機能を活用した効率的なデータベースアクセス
4. **Pydanticとの連携**: SQLAlchemyモデルとPydanticモデル間の変換機能

```python
# base_crud.pyの主要コンポーネント
class CRUDInterface(abc.ABC, Generic[T, U]):
    """CRUD操作の汎用インターフェースクラス"""
    # 同期/非同期のCRUD操作を定義する抽象メソッド
    @abc.abstractmethod
    def create(self, obj_in: T) -> U: ...

    @abc.abstractmethod
    async def create_async(self, obj_in: T) -> U: ...

    # 他のCRUD操作（read, update, delete等）

class SQLAlchemyCRUD(CRUDInterface[T, U], abc.ABC, Generic[T, U]):
    """SQLAlchemyを使用したCRUD操作の抽象クラス"""
    def __init__(
        self,
        db_session: Session | AsyncSession,
        db_model: type[T],
        output_model: type[U],
    ):
        self.db_session = db_session
        self.db_model = db_model
        self.output_model = output_model

    # CRUD操作の具体的な実装
    # モデル間の変換ロジック
```

#### リポジトリ実装におけるbase_crudの活用

ドメイン層で定義されたリポジトリインターフェースの実装クラスでは、`SQLAlchemyCRUD`クラスを継承して具体的なデータアクセスロジックを実装します。

```python
# UserRepositoryImplの例
class UserRepositoryImpl(SQLAlchemyCRUD[CreateUserDTO, UserEntity], UserRepositoryInterface):
    def __init__(self, db_session: Session | AsyncSession):
        super().__init__(
            db_session=db_session,
            db_model=User,  # SQLAlchemyモデル
            output_model=UserEntityDTO  # Pydanticモデル
        )

    async def find_by_email(self, email: Email) -> UserEntity | None:
        result = await self.read_by_filter_async(email=email.email)
        return result[0] if result else None

    async def email_exists(self, email: Email) -> bool:
        return bool(await self.find_by_email(email))

    # UserRepositoryInterfaceの他のメソッド実装
```

この設計により、ドメイン層のリポジトリインターフェースと技術的な実装の詳細を明確に分離しながら、効率的なデータベースアクセスを実現しています。

## ドメイン設計の特徴

### 強力な値オブジェクト:

- **Email**: メールアドレスのバリデーションと正規化
- **Password**: パスワード強度の検証と安全な保存
- **FullName**: 名前の構造化された表現
- **OAuthToken**: トークンの有効期限管理とリフレッシュロジック

### 自己完結したエンティティ:

- **UserEntity**: ユーザー情報と操作メソッド（検証、論理削除、復元など）
- **SocialAccountEntity**: ソーシャル連携情報とトークン更新機能

### 明確なリポジトリインターフェース:

- ドメイン層で定義され、インフラ層で実装される抽象化
- ドメインロジックとデータアクセスの明確な分離

### 非同期操作のサポート:

- すべてのリポジトリメソッドが同期/非同期の両方をサポート
- FastAPIとの連携を容易にする設計

### 論理削除のサポート:

- エンティティの物理的削除ではなく論理削除を実装
- 削除されたデータの復元可能性を維持

## 実装例

### リポジトリの具体的実装

`base_crud.py`を活用したリポジトリ実装の例：

```python
# src/app/infrastructures/users/repositories/user_repository_impl.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from src.app.core.crud.base_crud import SQLAlchemyCRUD
from src.app.domains.users.entities.user_entity import UserEntity
from src.app.domains.users.repositories.user_repository import UserRepositoryInterface
from src.app.domains.users.schemas.user_schemas import Email
from src.app.infrastructures.users.dto.user_dto import UserEntityDTO, CreateUserDTO
from src.app.models.user import User


class UserRepositoryImpl(SQLAlchemyCRUD[CreateUserDTO, UserEntityDTO], UserRepositoryInterface):
    """UserRepositoryInterfaceの実装クラス"""

    def __init__(self, db_session: Session | AsyncSession):
        super().__init__(
            db_session=db_session,
            db_model=User,  # SQLAlchemyモデル
            output_model=UserEntityDTO  # 内部変換用のPydanticモデル
        )

    async def create_user(self, user: UserEntity) -> UserEntity:
        """ユーザーを作成します"""
        # エンティティからDTOへ変換
        user_dto = CreateUserDTO.from_entity(user)
        # SQLAlchemyCRUDのcreate_asyncメソッドを使用
        created_user_dto = await self.create_async(user_dto)
        # DTOからエンティティへ変換して返却
        return created_user_dto.to_entity()

    async def find_by_email(self, email: Email) -> UserEntity | None:
        """メールアドレスでユーザーを検索します"""
        results = await self.read_by_filter_async(email=email.email)
        if not results:
            return None
        # DTOからエンティティへ変換して返却
        return results[0].to_entity()

    async def email_exists(self, email: Email) -> bool:
        """メールアドレスが存在するか確認します"""
        return bool(await self.find_by_email(email))

    # 他のUserRepositoryInterfaceメソッドの実装
```

### DTOの例

```python
# src/app/infrastructures/users/dto/user_dto.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.app.core.schemas.global_value_objects import EntityUUID
from src.app.domains.users.entities.user_entity import UserEntity
from src.app.domains.users.schemas.user_schemas import Email, FullName


class UserEntityDTO(BaseModel):
    """UserエンティティのDTO（データ転送オブジェクト）"""
    id: Optional[int] = None
    username: str
    email: str
    full_name_first: Optional[str] = None
    full_name_last: Optional[str] = None
    hashed_password: Optional[str] = None
    is_verified: bool = False
    uuid: str
    profile_image_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    is_deleted: bool = False

    def to_entity(self) -> UserEntity:
        """DTOからエンティティに変換"""
        return UserEntity(
            id=self.id,
            username=self.username,
            email=Email(email=self.email),
            full_name=FullName(first_name=self.full_name_first, last_name=self.full_name_last)
                if self.full_name_first and self.full_name_last else None,
            hashed_password=self.hashed_password,
            is_verified=self.is_verified,
            uuid=EntityUUID(value=self.uuid),
            profile_image_url=self.profile_image_url,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
            is_deleted=self.is_deleted
        )


class CreateUserDTO(BaseModel):
    """ユーザー作成用DTO"""
    username: str
    email: str
    full_name_first: Optional[str] = None
    full_name_last: Optional[str] = None
    hashed_password: Optional[str] = None
    is_verified: bool = False
    uuid: str
    profile_image_url: Optional[str] = None

    @classmethod
    def from_entity(cls, entity: UserEntity) -> "CreateUserDTO":
        """エンティティからDTOに変換"""
        return cls(
            username=entity.username,
            email=entity.email.email,
            full_name_first=entity.full_name.first_name if entity.full_name else None,
            full_name_last=entity.full_name.last_name if entity.full_name else None,
            hashed_password=entity.hashed_password,
            is_verified=entity.is_verified,
            uuid=str(entity.uuid.value),
            profile_image_url=entity.profile_image_url
        )
```

### 参照ファイル

実際のコード実装については、関連するファイルを参照してください:

- [UserEntity](src/app/domains/users/entities/user_entity.py)
- [SocialAccountEntity](src/app/domains/social_accounts/entities/social_account_entity.py)
- [UserRepository](src/app/domains/users/repositories/user_repository.py)
- [BaseCRUD](src/app/core/crud/base_crud.py)
- [UserRepositoryImpl](src/app/infrastructures/users/repositories/user_repository_impl.py)
- [UserRegistrationService](src/app/usecases/users/user_registration_service.py)
- [AuthenticationService](src/app/usecases/auth/authentication_service.py)
