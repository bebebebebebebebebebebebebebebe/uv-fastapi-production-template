from pydantic import BaseModel


class BaseEmailData(BaseModel):
    to_email: str
    subject: str
    body: str


class VerifyEmailData(BaseEmailData):
    link: str
