from pydantic import BaseModel, Field, field_validator

class AirlineCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=3, description="Код из 3 заглавных латинских букв")
    name: str = Field(..., max_length=100)

    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        if not v.isalpha() or not v.isupper():
            raise ValueError('Код должен состоять из 3 заглавных латинских букв')
        return v

class AirlineResponse(BaseModel):
    code: str
    name: str
    class Config:
        from_attributes = True