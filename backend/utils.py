from passlib.context import CryptContext
#on utilise passlib librairy pour le hashage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")
#bycrypt est un algorithme de hashage 
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password :str, hashed_password: str)->bool:
    return pwd_context.verify(plain_password, hashed_password)
