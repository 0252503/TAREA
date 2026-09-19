from pydantic import BaseModel, Field, field_validator


class PredictorRequest(BaseModel):
    """Body del POST /api/model.

    Ejemplo:
        {"email_type": "gmail.com", "country": "France", "city": "Paris"}

    Los tres campos son texto libre y no enums. Un Enum obligaria a
    recompilar el codigo cada vez que se agregue un pais o una ciudad a la
    base; la validacion util aqui es de formato, no de catalogo cerrado.
    """

    email_type: str = Field(..., examples=["gmail.com"])
    country: str = Field(..., examples=["France"])
    city: str = Field(..., examples=["Paris"])

    @field_validator("email_type", "country", "city")
    @classmethod
    def limpiar_texto(cls, valor: str) -> str:
        # Debe coincidir EXACTAMENTE con normalizar() de TrainModel.py:
        # el modelo aprendio categorias en minusculas y sin espacios.
        valor = str(valor).strip().lower()
        if not valor:
            raise ValueError("el campo no puede estar vacio")
        return valor

    @field_validator("email_type")
    @classmethod
    def validar_dominio(cls, email_type: str) -> str:
        # Se tolera que manden el correo completo y se extrae el dominio,
        # que es lo que realmente aprendio el modelo.
        if "@" in email_type:
            email_type = email_type.split("@")[-1]
        if "." not in email_type:
            raise ValueError("email_type debe ser un dominio, por ejemplo gmail.com")
        return email_type
