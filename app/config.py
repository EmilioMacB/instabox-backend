import json
import boto3
from botocore.exceptions import ClientError

AWS_REGION = "us-east-1"
SECRET_NAME = "instabox/rds/credentials"
S3_BUCKET_NAME = "instabox-app-emilio-maciel"


def get_db_credentials() -> dict:
    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager",
        region_name=AWS_REGION
    )

    try:
        response = client.get_secret_value(SecretId=SECRET_NAME)
    except ClientError as e:
        raise RuntimeError(f"Error al obtener secreto desde Secrets Manager: {e}")

    secret_str = response.get("SecretString")
    if not secret_str:
        raise ValueError("El secreto no contiene una cadena válida.")

    return json.loads(secret_str)


def get_database_url() -> str:
    creds = get_db_credentials()
    user = creds["username"]
    password = creds["password"]
    host = creds["host"]
    port = creds.get("port", 5432)
    dbname = creds["dbname"]

    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
